"""API-key authentication shared by the base and VL services."""

import secrets

from fastapi import HTTPException, Request

from polyocr.core.config import Settings


def verify_api_key(candidate: str | None, expected: str) -> bool:
    if candidate is None:
        return False
    return secrets.compare_digest(candidate.encode(), expected.encode())


def extract_api_key(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    return request.headers.get("X-API-Key")


def require_api_key(request: Request, settings: Settings) -> None:
    if not settings.auth_enabled:
        return
    if not verify_api_key(extract_api_key(request), settings.api_key):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_explicit_api_key(request: Request, expected: str | None) -> None:
    if not expected or not verify_api_key(extract_api_key(request), expected):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
