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


def test_robustness_doc_records_the_capture_tier_and_motion_blur_hazard() -> None:
    """Motion blur returns wrong text rather than nothing; that must stay documented."""
    doc = (ROOT / "docs" / "robustness.md").read_text(encoding="utf-8")
    for term in ("motion blur", "perspective", "uneven illumination", "paper texture"):
        assert term in doc.casefold(), term
    # The unsafe failure mode is the single most important caller-facing finding.
    assert "Heelco Ncotec" in doc, "the observed wrong-text output should be quoted"
    assert "flatten" in doc, "the local illumination pipeline result should be recorded"


def test_robustness_benchmark_exposes_the_capture_tier() -> None:
    source = (ROOT / "benchmarks" / "run_robustness_benchmark.py").read_text(encoding="utf-8")
    assert '"capture"' in source
    for name in ("_motion_blur", "_perspective", "_uneven_illumination", "_shadow"):
        assert f"def {name}" in source, name


def test_robustness_benchmark_does_not_write_into_a_read_only_pil_buffer() -> None:
    """`np.asarray(pil_image)` is read-only; in-place writes raise ValueError.

    Only bare `np.asarray(...)` bound to a name is a hazard — a chained `.astype()`
    copies, so that form is safe and must not be flagged.
    """
    import re

    source = (ROOT / "benchmarks" / "run_robustness_benchmark.py").read_text(encoding="utf-8")
    hazards = [
        line.strip()
        for line in source.splitlines()
        if re.search(r"=\s*np\.asarray\([^)]*\)\s*$", line)
    ]
    assert not hazards, f"assign a writable copy via np.array() instead: {hazards}"


def test_readmes_document_the_robustness_benchmark_and_preprocess_decision() -> None:
    for name in ("README.md", "README_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "run_robustness_benchmark.py" in text
        assert "preprocess_unsupported" in text
        assert "docs/robustness.md" in text


def test_readmes_warn_about_the_motion_blur_failure_mode() -> None:
    for name in ("README.md", "README_EN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Heelco Ncotec" in text, f"{name} should warn about wrong-text output"


def test_no_benchmark_script_sends_the_unsupported_preprocess_field() -> None:
    """These scripts sent preprocess=true, which now returns 400."""
    for script in (ROOT / "benchmarks").glob("*.py"):
        source = script.read_text(encoding="utf-8")
        assert "'preprocess'" not in source, f"{script.name} still sends preprocess"
        assert '"preprocess"' not in source, f"{script.name} still sends preprocess"
