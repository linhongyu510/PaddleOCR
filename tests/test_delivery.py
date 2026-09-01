from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_ci_covers_supported_python_versions() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for version in ("3.10", "3.11", "3.12"):
        assert version in workflow
    assert "3.13" not in workflow


def test_bilingual_readmes_document_limits_and_verification() -> None:
    for name in ("README.md", "README_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "POLYOCR_MAX_UPLOAD_MB" in text
        assert "POLYOCR_MAX_IMAGE_PIXELS" in text
        assert "POLYOCR_MAX_CONCURRENCY" in text
        assert "POLYOCR_MAX_TRANSLATION_ITEMS" in text
        assert "verification" in text.casefold() or "验证" in text
