"""Authenticated, upload-only PaddleOCR-VL application factory."""

import os
import tempfile
import uuid
from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field

from polyocr import __version__
from polyocr.api.errors import ServiceError, install_error_handlers
from polyocr.core.config import Settings
from polyocr.core.security import require_explicit_api_key
from polyocr.vl import decode_vl_input


class LayoutParsingRequest(BaseModel):
    file: str = Field(min_length=1)
    fileType: int = Field(default=1, ge=0, le=1)
    useDocUnwarping: bool | None = None
    useLayoutDetection: bool | None = None
    useChartRecognition: bool | None = None


def _default_pipeline() -> Any:
    try:
        from paddleocr import PaddleOCRVL
    except ImportError as exc:
        raise RuntimeError("Install the PaddleOCR-VL deployment dependencies.") from exc
    return PaddleOCRVL()


def _result_mapping(result: Any) -> Mapping[str, Any]:
    if isinstance(result, Mapping):
        return result
    json_value = getattr(result, "json", None)
    if json_value is not None:
        value = json_value() if callable(json_value) else json_value
        if isinstance(value, Mapping):
            return value
    return {
        "layout": getattr(result, "layout", []),
        "text": getattr(result, "text", ""),
        "markdown": getattr(result, "markdown", {}),
    }


def create_app(
    settings: Settings | None = None,
    pipeline: Any | None = None,
    pipeline_factory: Callable[[], Any] = _default_pipeline,
) -> FastAPI:
    active_settings = settings or Settings(auth_enabled=False)
    if not active_settings.vl_api_key:
        raise RuntimeError("POLYOCR_VL_API_KEY is required for the VL service")
    active_pipeline = pipeline

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        nonlocal active_pipeline
        if active_pipeline is None:
            active_pipeline = pipeline_factory()
        yield

    app = FastAPI(title="PolyOCR-VL Service", version=__version__, lifespan=lifespan)
    install_error_handlers(app)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    def authenticated(request: Request) -> None:
        require_explicit_api_key(request, active_settings.vl_api_key)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "pipeline_ready": active_pipeline is not None}

    @app.post("/layout-parsing")
    async def layout_parsing(
        payload: LayoutParsingRequest,
        _: None = Depends(authenticated),
    ) -> dict[str, Any]:
        data = decode_vl_input(payload.file, max_bytes=active_settings.vl_max_upload_bytes)
        if payload.fileType == 0 and not data.startswith(b"%PDF"):
            raise ServiceError("invalid_file", "PDF input has an invalid signature.", 422)
        suffix = ".pdf" if payload.fileType == 0 else ".img"
        path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
                temporary.write(data)
                path = temporary.name
            if active_pipeline is None:
                raise ServiceError("model_unavailable", "VL pipeline is not ready.", 503)
            output = list(active_pipeline.predict(path))
            return {
                "logId": f"req_{uuid.uuid4().hex}",
                "errorCode": 0,
                "errorMsg": "Success",
                "result": {
                    "layoutParsingResults": [dict(_result_mapping(result)) for result in output],
                    "dataInfo": {
                        "inputType": "pdf" if payload.fileType == 0 else "image",
                        "totalPages": len(output),
                    },
                },
            }
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                "vl_inference_failed",
                "The VL service could not process the document.",
                502,
            ) from exc
        finally:
            if path:
                Path(path).unlink(missing_ok=True)

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:create_app",
        factory=True,
        host=os.getenv("POLYOCR_VL_HOST", "0.0.0.0"),
        port=int(os.getenv("POLYOCR_VL_PORT", "8080")),
    )
