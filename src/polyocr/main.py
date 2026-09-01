"""FastAPI application factory for PolyOCR Service."""

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from polyocr.api.errors import ServiceError, install_error_handlers
from polyocr.core.config import Settings
from polyocr.core.security import require_api_key
from polyocr.schemas.ocr import OCRResponse
from polyocr.schemas.translation import TranslationRequest, TranslationResponse
from polyocr.services.languages import supported_languages
from polyocr.services.model_manager import ModelManager
from polyocr.services.ocr import OCRService, create_paddle_backend
from polyocr.services.translation import OpenAITranslationProvider, TranslationService


def create_app(
    settings: Settings | None = None,
    ocr_service: OCRService | None = None,
    translation_service: TranslationService | None = None,
) -> FastAPI:
    active_settings = settings or Settings()
    manager: ModelManager | None = None
    if ocr_service is None:
        manager = ModelManager(create_paddle_backend)
        ocr_service = OCRService(
            manager.get,
            max_bytes=active_settings.max_upload_bytes,
            max_pixels=active_settings.max_image_pixels,
            max_concurrency=active_settings.max_concurrency,
            workers=active_settings.ocr_workers,
        )
    if translation_service is None:
        translation_service = TranslationService(
            OpenAITranslationProvider(active_settings),
            active_settings,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        ocr_service.close()

    app = FastAPI(
        title="PolyOCR Service",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.state.ocr_service = ocr_service
    app.state.translation_service = translation_service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origin_list,
        allow_credentials=active_settings.cors_allow_credentials,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    )
    install_error_handlers(app)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    def authenticated(request: Request) -> None:
        require_api_key(request, active_settings)

    @app.get("/")
    async def root() -> Any:
        web_file = Path(__file__).parents[2] / "web" / "index.html"
        if web_file.exists():
            return FileResponse(web_file)
        return {"service": "PolyOCR Service", "docs": "/docs"}

    @app.get("/v1/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "PolyOCR Service",
            "models_loaded": list(manager.loaded_languages) if manager else [],
        }

    @app.get("/v1/languages")
    async def languages() -> dict[str, Any]:
        return {
            "languages": [
                {
                    "code": language.code,
                    "paddle_code": language.paddle_code,
                    "name": language.name,
                }
                for language in supported_languages()
            ]
        }

    @app.post("/v1/ocr", response_model=OCRResponse)
    async def recognize(
        request: Request,
        file: Annotated[UploadFile, File()],
        language: Annotated[str | None, Form()] = None,
        preprocess: Annotated[bool, Form()] = False,
        score_threshold: Annotated[float, Form(ge=0, le=1)] = 0.5,
        _: Annotated[None, Depends(authenticated)] = None,
    ) -> OCRResponse:
        del preprocess
        allowed_types = {"image/jpeg", "image/png", "image/webp", "image/tiff", "image/gif"}
        if file.content_type not in allowed_types:
            raise ServiceError(
                "invalid_image_type",
                "Uploaded file is not a supported image.",
                415,
            )
        data = await file.read(active_settings.max_upload_bytes + 1)
        started = time.perf_counter()
        selected_language = language or active_settings.default_language
        items = await ocr_service.recognize(
            data,
            selected_language,
            score_threshold,
            max_bytes=active_settings.max_upload_bytes,
            max_pixels=active_settings.max_image_pixels,
        )
        return OCRResponse(
            request_id=request.state.request_id,
            cost_ms=round((time.perf_counter() - started) * 1000, 3),
            language=selected_language,
            items=items,
        )

    async def run_translation(
        payload: TranslationRequest,
        request: Request,
    ) -> TranslationResponse:
        translations = await translation_service.translate(
            payload.texts,
            payload.source_language,
            payload.target_language,
        )
        return TranslationResponse(
            request_id=request.state.request_id,
            translations=translations,
        )

    @app.post("/v2/translate", response_model=TranslationResponse)
    async def translate_v2(
        payload: TranslationRequest,
        request: Request,
        _: Annotated[None, Depends(authenticated)] = None,
    ) -> TranslationResponse:
        return await run_translation(payload, request)

    @app.post("/v1/translation/translate", response_model=TranslationResponse)
    async def translate_compatible(
        payload: TranslationRequest,
        request: Request,
        _: Annotated[None, Depends(authenticated)] = None,
    ) -> TranslationResponse:
        return await run_translation(payload, request)

    @app.get("/v1/translation/health")
    async def translation_health() -> dict[str, Any]:
        return {
            "status": "ok" if active_settings.translation_enabled else "not_configured",
            "configured": active_settings.translation_enabled,
        }

    return app
