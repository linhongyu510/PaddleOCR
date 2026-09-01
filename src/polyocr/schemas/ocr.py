"""OCR response schemas."""

from pydantic import BaseModel, Field


class OCRItem(BaseModel):
    text: str
    score: float = Field(ge=0, le=1)
    bbox: list[int] = Field(default_factory=list)


class OCRResponse(BaseModel):
    code: int = 0
    message: str = "Recognition succeeded."
    request_id: str
    cost_ms: float
    language: str
    items: list[OCRItem]
