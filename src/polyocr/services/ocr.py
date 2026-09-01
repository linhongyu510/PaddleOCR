"""Bounded OCR execution and PaddleOCR result compatibility."""

import asyncio
import io
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError

from polyocr.api.errors import ServiceError
from polyocr.schemas.ocr import OCRItem


def validate_score_threshold(value: float) -> float:
    if not 0 <= value <= 1:
        raise ServiceError(
            "invalid_score_threshold",
            "score_threshold must be between 0 and 1.",
            422,
        )
    return value


def decode_image(data: bytes, *, max_bytes: int, max_pixels: int) -> np.ndarray:
    if not data:
        raise ServiceError("invalid_image", "Uploaded image is empty.", 422)
    if len(data) > max_bytes:
        raise ServiceError("file_too_large", "Uploaded image exceeds the byte limit.", 413)
    try:
        with Image.open(io.BytesIO(data)) as source:
            width, height = source.size
            if width <= 0 or height <= 0:
                raise ServiceError("invalid_image", "Uploaded image has invalid dimensions.", 422)
            if width * height > max_pixels:
                raise ServiceError(
                    "image_too_large",
                    "Decoded image exceeds the pixel limit.",
                    413,
                )
            source.verify()
        with Image.open(io.BytesIO(data)) as source:
            return np.asarray(source.convert("RGB"))
    except ServiceError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ServiceError(
            "invalid_image",
            "Uploaded file could not be decoded as an image.",
            422,
        ) from exc


def _plain(value: Any) -> Any:
    converter = getattr(value, "tolist", None)
    return converter() if callable(converter) else value


def _bbox(poly: Any) -> list[int]:
    points = _plain(poly) if poly is not None else []
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)):
        return []
    valid_points = [
        _plain(point)
        for point in points
        if isinstance(_plain(point), Sequence)
        and not isinstance(_plain(point), (str, bytes))
        and len(_plain(point)) >= 2
    ]
    if not valid_points:
        return []
    return [
        int(min(point[0] for point in valid_points)),
        int(min(point[1] for point in valid_points)),
        int(max(point[0] for point in valid_points)),
        int(max(point[1] for point in valid_points)),
    ]


def _unwrap_page(page: Any) -> Any:
    json_value = getattr(page, "json", None)
    if json_value is not None:
        page = json_value() if callable(json_value) else json_value
    if isinstance(page, Mapping) and isinstance(page.get("res"), Mapping):
        page = page["res"]
    return page


def _mapping_items(page: Any, threshold: float) -> list[OCRItem] | None:
    if isinstance(page, Mapping):
        texts = page.get("rec_texts")
        scores = page.get("rec_scores")
        polys = page.get("dt_polys", page.get("rec_polys", []))
    else:
        texts = getattr(page, "rec_texts", None)
        scores = getattr(page, "rec_scores", None)
        polys = getattr(page, "dt_polys", getattr(page, "rec_polys", []))
    if texts is None and scores is None:
        return None
    if not isinstance(texts, Iterable) or not isinstance(scores, Iterable):
        raise ServiceError("invalid_ocr_result", "OCR result has an invalid structure.", 502)
    text_list = list(texts)
    score_list = list(scores)
    poly_list = list(polys) if isinstance(polys, Iterable) else []
    if len(text_list) != len(score_list):
        raise ServiceError("invalid_ocr_result", "OCR text and score counts differ.", 502)
    return [
        OCRItem(
            text=str(text),
            score=float(score),
            bbox=_bbox(poly_list[index]) if index < len(poly_list) else [],
        )
        for index, (text, score) in enumerate(zip(text_list, score_list, strict=True))
        if float(score) >= threshold
    ]


def _looks_like_legacy_line(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) >= 2
        and isinstance(value[1], (list, tuple))
        and len(value[1]) >= 2
        and isinstance(value[1][0], str)
        and isinstance(value[1][1], (int, float))
    )


def _legacy_items(value: Any, threshold: float) -> list[OCRItem]:
    if _looks_like_legacy_line(value):
        score = float(value[1][1])
        if score >= threshold:
            return [OCRItem(text=value[1][0], score=score, bbox=_bbox(value[0]))]
        return []
    if isinstance(value, (list, tuple)):
        items: list[OCRItem] = []
        for child in value:
            items.extend(_legacy_items(child, threshold))
        return items
    return []


def normalize_ocr_result(result: Any, score_threshold: float = 0.5) -> list[OCRItem]:
    threshold = validate_score_threshold(score_threshold)
    pages = list(result) if not isinstance(result, (list, tuple)) else result
    items: list[OCRItem] = []
    for raw_page in pages:
        page = _unwrap_page(raw_page)
        mapped = _mapping_items(page, threshold)
        items.extend(mapped if mapped is not None else _legacy_items(page, threshold))
    return items


class OCRService:
    def __init__(
        self,
        backend_provider: Callable[[str], Any],
        *,
        max_bytes: int = 10 * 1024 * 1024,
        max_pixels: int = 25_000_000,
        max_concurrency: int = 2,
        workers: int = 2,
    ) -> None:
        self._backend_provider = backend_provider
        self._max_bytes = max_bytes
        self._max_pixels = max_pixels
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="polyocr")

    def _predict(self, language: str, image: np.ndarray) -> Any:
        backend = self._backend_provider(language)
        predict = getattr(backend, "predict", None)
        if not callable(predict):
            raise ServiceError("model_unavailable", "OCR backend does not support predict().", 503)
        return predict(image)

    async def recognize(
        self,
        data: bytes,
        language: str,
        score_threshold: float,
        *,
        max_bytes: int | None = None,
        max_pixels: int | None = None,
    ) -> list[OCRItem]:
        threshold = validate_score_threshold(score_threshold)
        image = decode_image(
            data,
            max_bytes=max_bytes or self._max_bytes,
            max_pixels=max_pixels or self._max_pixels,
        )
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._predict,
                language,
                image,
            )
        return normalize_ocr_result(result, threshold)

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)


def create_paddle_backend(language: str) -> Any:
    from paddleocr import PaddleOCR

    return PaddleOCR(lang=language)
