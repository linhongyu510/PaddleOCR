import base64
import importlib.util
from pathlib import Path
from types import ModuleType

from fastapi.testclient import TestClient

from polyocr.core.config import Settings


ROOT = Path(__file__).parents[2]


def load_vl_app_module() -> ModuleType:
    path = ROOT / "deployment" / "paddleocr-vl" / "app.py"
    spec = importlib.util.spec_from_file_location("polyocr_vl_app", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakePipeline:
    def predict(self, input_data: bytes) -> list[dict[str, object]]:
        return [{"markdown": {"text": "safe"}}]


def client() -> TestClient:
    module = load_vl_app_module()
    settings = Settings(
        auth_enabled=False,
        vl_api_key="vl-secret",
        vl_max_upload_mb=1,
    )
    return TestClient(module.create_app(settings=settings, pipeline=FakePipeline()))


def test_vl_endpoint_requires_authentication() -> None:
    response = client().post(
        "/layout-parsing",
        json={"file": base64.b64encode(b"content").decode(), "fileType": 1},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_vl_endpoint_rejects_url_even_when_authenticated() -> None:
    response = client().post(
        "/layout-parsing",
        headers={"X-API-Key": "vl-secret"},
        json={"file": "https://example.com/a.png", "fileType": 1},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "url_input_forbidden"
