from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_web_uses_text_content_for_remote_results() -> None:
    paths = (
        ROOT / "src/polyocr/web/index.html",
        ROOT / "src/polyocr/web/translation.html",
        ROOT / "deployment/paddleocr-vl/static/index.html",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "textContent" in text
        assert "innerHTML" not in text


def test_legacy_entrypoints_do_not_contain_credentials_or_runtime_config_api() -> None:
    forbidden = (
        "PolyNex-" + "PolyOCR-" + "2025xm",
        "782b52f0-" + "d5b6-" + "488b-" + "9fdd-" + "0a9026d3a0c0",
        "183." + "250.90.218",
        "43." + "137.12.144",
        "10." + "206.0.6",
    )
    paths = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "tests" not in path.parts
        and path.suffix in {".html", ".json", ".md", ".py", ".sh", ".yaml", ".yml"}
    ]
    combined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)
    for value in forbidden:
        assert value not in combined
    assert "/v1/translation/config" not in combined
    assert "update_translation_config" not in combined
    assert not (ROOT / "index.html").exists()
    assert not (ROOT / "translation.html").exists()
    assert not (ROOT / "frontend_server.py").exists()
