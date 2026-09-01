import asyncio
import os
from pathlib import Path

import pytest

from polyocr.services.model_manager import ModelManager
from polyocr.services.ocr import OCRService, create_paddle_backend

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("POLYOCR_RUN_OCR_E2E") != "1",
    reason="set POLYOCR_RUN_OCR_E2E=1 to download models and run real OCR",
)
def test_fixed_english_image_end_to_end() -> None:
    image = (Path(__file__).parents[2] / "benchmarks" / "simple_dataset" / "en.jpg").read_bytes()
    manager = ModelManager(create_paddle_backend)
    service = OCRService(manager.get, max_concurrency=1, workers=1)
    try:
        items = asyncio.run(service.recognize(image, "en", 0.2))
    finally:
        service.close()
    recognized = " ".join(item.text for item in items).casefold()
    assert "hello" in recognized
    assert "ocr" in recognized
