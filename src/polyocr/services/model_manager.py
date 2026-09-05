"""Thread-safe PaddleOCR model cache."""

import threading
from collections.abc import Callable
from typing import Any

from polyocr.api.errors import ServiceError
from polyocr.services.languages import normalize_language


class ModelManager:
    def __init__(self, factory: Callable[[str], Any]) -> None:
        self._factory = factory
        self._models: dict[str, Any] = {}
        self._lock = threading.RLock()

    def get(self, language: str) -> Any:
        paddle_code = normalize_language(language)
        with self._lock:
            if paddle_code in self._models:
                return self._models[paddle_code]
            try:
                model = self._factory(paddle_code)
            except Exception as exc:
                raise ServiceError(
                    "model_unavailable",
                    f"The OCR model for {paddle_code!r} could not be loaded.",
                    503,
                ) from exc
            self._models[paddle_code] = model
            return model

    @property
    def loaded_languages(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._models))
