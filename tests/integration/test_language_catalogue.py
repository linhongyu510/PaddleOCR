"""Checks the language catalogue against the installed PaddleOCR build.

The fast unit tests pin `paddle_code` values against a copy of PaddleOCR's
language tables. This test verifies that copy is still true for the PaddleOCR
actually installed, so an upstream change cannot silently invalidate it. It needs
the `ocr` extra but downloads no model: `_get_ocr_model_names` only maps a
language code to model names.
"""

import pytest

from polyocr.services.languages import supported_languages

pytestmark = pytest.mark.integration

paddleocr = pytest.importorskip("paddleocr", reason="requires the 'ocr' extra")


def test_every_paddle_code_resolves_in_installed_paddleocr() -> None:
    resolver = paddleocr.PaddleOCR.__new__(paddleocr.PaddleOCR)
    unresolved: list[tuple[str, str]] = []
    for language in supported_languages():
        detection, recognition = resolver._get_ocr_model_names(language.paddle_code, None)
        if not detection or not recognition:
            unresolved.append((language.code, language.paddle_code))
    assert not unresolved, f"languages PaddleOCR cannot serve: {unresolved}"


def test_model_prefixes_still_fail_upstream() -> None:
    """Guards the assumption behind the fix: prefixes are not valid lang values."""
    resolver = paddleocr.PaddleOCR.__new__(paddleocr.PaddleOCR)
    for prefix in ("latin", "cyrillic", "eslav", "arabic", "devanagari"):
        detection, recognition = resolver._get_ocr_model_names(prefix, None)
        assert detection is None and recognition is None, (
            f"{prefix!r} now resolves upstream; revisit the language mapping"
        )
