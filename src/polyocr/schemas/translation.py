"""Translation request and response schemas."""

from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    source_language: str | None = None
    target_language: str = Field(min_length=1, max_length=64)


class TranslationResponse(BaseModel):
    code: int = 0
    message: str = "Translation succeeded."
    request_id: str
    translations: list[str]
