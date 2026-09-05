import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from polyocr.api.errors import ServiceError
from polyocr.core.config import Settings
from polyocr.main import create_app
from polyocr.services.ocr import OCRService
from polyocr.services.translation import TranslationService


def png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(output, format="PNG")
    return output.getvalue()


class FakeOCRBackend:
    def predict(self, image: object) -> list[dict[str, object]]:
        return [{"rec_texts": ["hello"], "rec_scores": [0.99], "dt_polys": [[]]}]


class MismatchedTranslationProvider:
    async def translate(
        self, texts: list[str], source_language: str | None, target_language: str
    ) -> list[str]:
        return ["only one"]


def make_client() -> TestClient:
    settings = Settings(
        auth_enabled=True,
        api_key="test-secret",
        max_upload_mb=1,
        max_image_pixels=100,
        max_translation_items=2,
        max_translation_chars=10,
    )
    app = create_app(
        settings=settings,
        ocr_service=OCRService(lambda _language: FakeOCRBackend()),
        translation_service=TranslationService(MismatchedTranslationProvider(), settings),
    )
    return TestClient(app)


def test_validation_errors_use_unified_error_shape() -> None:
    response = make_client().post(
        "/v2/translate",
        headers={"X-API-Key": "test-secret"},
        json={"texts": [], "target_language": "zh"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["request_id"]
    assert "detail" not in body


def test_http_errors_use_unified_error_shape() -> None:
    response = make_client().post(
        "/v1/ocr",
        files={"file": ("image.png", png_bytes(), "image/png")},
        data={"language": "en", "score_threshold": "0.5"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_threshold_is_rejected_by_http_boundary() -> None:
    response = make_client().post(
        "/v1/ocr",
        headers={"X-API-Key": "test-secret"},
        files={"file": ("image.png", png_bytes(), "image/png")},
        data={"language": "en", "score_threshold": "1.2"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_pixel_limit_returns_client_error() -> None:
    output = io.BytesIO()
    Image.new("RGB", (11, 10), "white").save(output, format="PNG")
    response = make_client().post(
        "/v1/ocr",
        headers={"X-API-Key": "test-secret"},
        files={"file": ("image.png", output.getvalue(), "image/png")},
        data={"language": "en", "score_threshold": "0.5"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "image_too_large"


def test_translation_item_and_character_limits() -> None:
    client = make_client()
    too_many = client.post(
        "/v2/translate",
        headers={"X-API-Key": "test-secret"},
        json={"texts": ["a", "b", "c"], "target_language": "zh"},
    )
    too_long = client.post(
        "/v2/translate",
        headers={"X-API-Key": "test-secret"},
        json={"texts": ["12345678901"], "target_language": "zh"},
    )
    assert too_many.status_code == 422
    assert too_long.status_code == 422


def test_translation_result_mismatch_is_a_bad_gateway() -> None:
    response = make_client().post(
        "/v2/translate",
        headers={"X-API-Key": "test-secret"},
        json={"texts": ["one", "two"], "target_language": "zh"},
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "translation_result_mismatch"


@pytest.mark.parametrize("language", ["klingon", "cyrillic", "eslav", "zz", "xx-YY"])
def test_unsupported_language_is_rejected_at_the_boundary(language: str) -> None:
    """An unknown language must be a 422, not a late 503 from model loading."""
    response = make_client().post(
        "/v1/ocr",
        headers={"X-API-Key": "test-secret"},
        files={"file": ("image.png", png_bytes(), "image/png")},
        data={"language": language, "score_threshold": "0.5"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_language"


@pytest.mark.parametrize(
    ("request_language", "reported_language"),
    [("fr", "fr"), ("french", "fr"), ("法文", "fr"), ("ru", "ru"), ("ZH", "zh")],
)
def test_supported_languages_are_accepted_and_echoed_canonically(
    request_language: str, reported_language: str
) -> None:
    response = make_client().post(
        "/v1/ocr",
        headers={"X-API-Key": "test-secret"},
        files={"file": ("image.png", png_bytes(), "image/png")},
        data={"language": request_language, "score_threshold": "0.5"},
    )
    assert response.status_code == 200
    assert response.json()["language"] == reported_language


def test_language_catalogue_is_published_with_scripts_and_aliases() -> None:
    response = make_client().get("/v1/languages")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["languages"])
    assert body["count"] >= 70
    codes = {item["code"] for item in body["languages"]}
    assert {"fr", "de", "es", "pt", "ru", "zh", "en", "ar", "hi"} <= codes
    french = next(item for item in body["languages"] if item["code"] == "fr")
    assert french["paddle_code"] == "fr"
    assert french["script"] == "Latin"
    assert "french" in french["aliases"]


def test_misconfigured_default_language_fails_at_startup() -> None:
    with pytest.raises(ServiceError) as exc:
        create_app(
            settings=Settings(auth_enabled=False, default_language="not-a-language"),
            ocr_service=OCRService(lambda _language: FakeOCRBackend()),
        )
    assert exc.value.code == "unsupported_language"
