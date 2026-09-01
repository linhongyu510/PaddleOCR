from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_web_uses_text_content_for_remote_results() -> None:
    paths = (
        ROOT / "web/index.html",
        ROOT / "web/translation.html",
        ROOT / "deployment/paddleocr-vl/static/index.html",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "textContent" in text
        assert "innerHTML" not in text


def test_legacy_entrypoints_do_not_contain_credentials_or_runtime_config_api() -> None:
    combined = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in ("main.py", "auth.py", "translation.py")
    )
    assert "PolyNex-PolyOCR-2025xm" not in combined
    assert "782b52f0-d5b6-488b-9fdd-0a9026d3a0c0" not in combined
    assert "/v1/translation/config" not in combined
    assert "update_translation_config" not in combined
