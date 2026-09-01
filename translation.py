"""Deprecated compatibility exports for translation services."""

from polyocr.schemas.translation import TranslationRequest, TranslationResponse
from polyocr.services.translation import (
    OpenAITranslationProvider,
    TranslationService,
    validate_translation_result,
)

__all__ = [
    "OpenAITranslationProvider",
    "TranslationRequest",
    "TranslationResponse",
    "TranslationService",
    "validate_translation_result",
]
