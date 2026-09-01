"""Public service errors and FastAPI exception handlers."""

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@dataclass
class ServiceError(Exception):
    code: str
    message: str
    status_code: int = 400

    def __post_init__(self) -> None:
        super().__init__(self.message)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": _request_id(request),
            }
        },
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
        return _response(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _response(request, 422, "validation_error", "Request validation failed.")

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code = "unauthorized" if exc.status_code == 401 else "http_error"
        message = "Missing or invalid API key." if exc.status_code == 401 else str(exc.detail)
        response = _response(request, exc.status_code, code, message)
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _response(
            request,
            500,
            "internal_error",
            "The service could not process the request.",
        )


def error_schema() -> dict[str, Any]:
    return {
        "model": None,
        "description": "Unified error response.",
    }
