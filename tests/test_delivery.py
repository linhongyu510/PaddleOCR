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


def test_readmes_state_the_apache_license_and_no_longer_claim_it_is_missing() -> None:
    for name in ("README.md", "README_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Apache License 2.0" in text
        assert "LICENSE" in text
        assert "NOTICE" in text
        assert "no license file" not in text.casefold()
        assert "未包含许可证文件" not in text


def test_readmes_document_the_language_contract() -> None:
    """The language fix is user-visible, so it must be documented."""
    for name in ("README.md", "README_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "/v1/languages" in text
        assert "unsupported_language" in text
        assert "78" in text


def test_readmes_document_the_console_entry_point() -> None:
    for name in ("README.md", "README_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "polyocr-service --host" in text


def test_robustness_findings_are_documented() -> None:
    """The preprocess rejection points callers at this document, so it must exist."""
    doc = (ROOT / "docs" / "robustness.md").read_text(encoding="utf-8")
    assert "preprocess" in doc
    # The decision must be backed by numbers, not an assertion.
    assert "autocontrast" in doc
    assert "upscale" in doc
    assert "0.950" in doc
    assert "caveat" in doc.casefold()


def test_readmes_document_the_robustness_benchmark_and_preprocess_decision() -> None:
    for name in ("README.md", "README_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "run_robustness_benchmark.py" in text
        assert "preprocess_unsupported" in text
        assert "docs/robustness.md" in text


def test_no_benchmark_script_sends_the_unsupported_preprocess_field() -> None:
    """These scripts sent preprocess=true, which now returns 400."""
    for script in (ROOT / "benchmarks").glob("*.py"):
        source = script.read_text(encoding="utf-8")
        assert "'preprocess'" not in source, f"{script.name} still sends preprocess"
        assert '"preprocess"' not in source, f"{script.name} still sends preprocess"
