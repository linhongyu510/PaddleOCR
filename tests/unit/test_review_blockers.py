import asyncio
import io
import threading
import time
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from polyocr.api.errors import ServiceError
from polyocr.core.config import Settings
from polyocr.services.model_manager import ModelManager
from polyocr.services.ocr import OCRService, decode_image, normalize_ocr_result
from polyocr.services.translation import validate_translation_result
from polyocr.vl import decode_vl_input


def png_bytes(width: int = 8, height: int = 8) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(output, format="PNG")
    return output.getvalue()


def test_dotenv_file_is_loaded(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "POLYOCR_AUTH_ENABLED=false\nPOLYOCR_MAX_IMAGE_PIXELS=12345\n",
        encoding="utf-8",
    )
    settings = Settings(_env_file=env_file)
    assert settings.auth_enabled is False
    assert settings.max_image_pixels == 12345


def test_invalid_threshold_is_rejected_before_backend_call() -> None:
    class Backend:
        calls = 0

        def predict(self, image: object) -> list[object]:
            self.calls += 1
            return []

    backend = Backend()
    service = OCRService(lambda _language: backend)
    with pytest.raises(ServiceError) as exc:
        asyncio.run(service.recognize(png_bytes(), "en", 1.1))
    assert exc.value.code == "invalid_score_threshold"
    assert backend.calls == 0


def test_image_pixel_limit_is_enforced_after_decode() -> None:
    with pytest.raises(ServiceError) as exc:
        decode_image(png_bytes(20, 20), max_bytes=10_000, max_pixels=399)
    assert exc.value.code == "image_too_large"


def test_paddleocr_3_predict_mapping_result_is_normalized() -> None:
    result = [
        {
            "rec_texts": ["keep", "drop"],
            "rec_scores": [0.91, 0.2],
            "dt_polys": [
                [[0, 0], [10, 0], [10, 10], [0, 10]],
                [[20, 20], [30, 20], [30, 30], [20, 30]],
            ],
        }
    ]
    items = normalize_ocr_result(result, 0.5)
    assert [(item.text, item.score, item.bbox) for item in items] == [
        ("keep", 0.91, [0, 0, 10, 10])
    ]


def test_paddleocr_3_json_wrapped_result_is_normalized() -> None:
    class Result:
        json = {
            "res": {
                "rec_texts": ["hello"],
                "rec_scores": [0.98],
                "rec_polys": [[[1, 2], [5, 2], [5, 8], [1, 8]]],
            }
        }

    items = normalize_ocr_result([Result()], 0.5)
    assert items[0].text == "hello"
    assert items[0].bbox == [1, 2, 5, 8]


def test_legacy_ocr_result_remains_supported() -> None:
    result = [[[[[0, 0], [10, 0], [10, 10], [0, 10]], ("legacy", 0.88)]]]
    assert normalize_ocr_result(result, 0.5)[0].text == "legacy"


def test_ocr_runs_blocking_predict_in_worker_thread() -> None:
    main_thread = threading.get_ident()

    class Backend:
        called_from = main_thread

        def predict(self, image: object) -> list[object]:
            self.called_from = threading.get_ident()
            return []

    backend = Backend()
    service = OCRService(lambda _language: backend)
    asyncio.run(service.recognize(png_bytes(), "en", 0.5))
    assert backend.called_from != main_thread


def test_ocr_concurrency_is_bounded() -> None:
    class Backend:
        active = 0
        maximum = 0
        lock = threading.Lock()

        def predict(self, image: object) -> list[object]:
            with self.lock:
                self.active += 1
                self.maximum = max(self.maximum, self.active)
            time.sleep(0.03)
            with self.lock:
                self.active -= 1
            return []

    backend = Backend()
    service = OCRService(lambda _language: backend, max_concurrency=2, workers=4)

    async def run() -> None:
        await asyncio.gather(*(service.recognize(png_bytes(), "en", 0.5) for _ in range(5)))
        service.close()

    asyncio.run(run())
    assert backend.maximum == 2


def test_model_cache_uses_normalized_language_and_is_thread_safe() -> None:
    calls: list[str] = []

    def factory(language: str) -> object:
        calls.append(language)
        return object()

    manager = ModelManager(factory)
    first = manager.get("zh")
    second = manager.get("中文")
    assert first is second
    assert calls == ["ch"]


def test_translation_input_limits_are_validated() -> None:
    with pytest.raises(ValidationError):
        Settings(max_translation_items=0)


def test_translation_result_count_must_match_input() -> None:
    with pytest.raises(ServiceError) as exc:
        validate_translation_result(["one"], expected_count=2)
    assert exc.value.code == "translation_result_mismatch"


def test_vl_rejects_url_input() -> None:
    with pytest.raises(ServiceError) as exc:
        decode_vl_input("https://example.com/document.png", max_bytes=1024)
    assert exc.value.code == "url_input_forbidden"


def test_vl_rejects_oversized_base64() -> None:
    import base64

    payload = base64.b64encode(b"x" * 11).decode()
    with pytest.raises(ServiceError) as exc:
        decode_vl_input(payload, max_bytes=10)
    assert exc.value.code == "file_too_large"
