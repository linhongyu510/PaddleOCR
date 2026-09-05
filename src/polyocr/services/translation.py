"""Bounded translation service and OpenAI-compatible provider."""

import json
from typing import Protocol

import httpx

from polyocr.api.errors import ServiceError
from polyocr.core.config import Settings


class TranslationProvider(Protocol):
    async def translate(
        self,
        texts: list[str],
        source_language: str | None,
        target_language: str,
    ) -> list[str]: ...


def validate_translation_result(
    translations: list[str],
    *,
    expected_count: int,
) -> list[str]:
    if len(translations) != expected_count:
        raise ServiceError(
            "translation_result_mismatch",
            "Translation provider returned a different number of results.",
            502,
        )
    if not all(isinstance(item, str) for item in translations):
        raise ServiceError(
            "translation_provider_error",
            "Translation provider returned an invalid result.",
            502,
        )
    return translations


class TranslationService:
    def __init__(self, provider: TranslationProvider, settings: Settings) -> None:
        self._provider = provider
        self._settings = settings

    async def translate(
        self,
        texts: list[str],
        source_language: str | None,
        target_language: str,
    ) -> list[str]:
        if not texts:
            raise ServiceError("validation_error", "At least one text is required.", 422)
        if len(texts) > self._settings.max_translation_items:
            raise ServiceError(
                "translation_input_too_large",
                "Too many translation items.",
                422,
            )
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ServiceError(
                "validation_error",
                "Translation texts must be non-empty strings.",
                422,
            )
        if sum(len(text) for text in texts) > self._settings.max_translation_chars:
            raise ServiceError(
                "translation_input_too_large",
                "Translation text exceeds the character limit.",
                422,
            )
        translations = await self._provider.translate(
            texts,
            source_language,
            target_language,
        )
        return validate_translation_result(translations, expected_count=len(texts))


class OpenAITranslationProvider:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self._settings = settings
        self._transport = transport

    async def translate(
        self,
        texts: list[str],
        source_language: str | None,
        target_language: str,
    ) -> list[str]:
        if not self._settings.translation_api_key:
            raise ServiceError(
                "translation_not_configured",
                "Translation is not configured.",
                503,
            )
        source = source_language or "auto-detected language"
        prompt = (
            f"Translate each JSON array item from {source} to {target_language}. "
            "Return only a JSON array with exactly the same number and order of strings."
        )
        payload = {
            "model": self._settings.translation_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(texts, ensure_ascii=False)},
            ],
            "temperature": 0,
        }
        timeout = httpx.Timeout(30, connect=5)
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    f"{str(self._settings.translation_base_url).rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self._settings.translation_api_key}"},
                    json=payload,
                )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            translated = json.loads(content)
            if not isinstance(translated, list):
                raise TypeError("provider content is not a list")
            return translated
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ServiceError(
                "translation_provider_error",
                "Translation provider request failed.",
                502,
            ) from exc
