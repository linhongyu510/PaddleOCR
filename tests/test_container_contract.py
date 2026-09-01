from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_container_is_non_root_and_has_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER polyocr" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "libgl1" in dockerfile
    assert "polyocr.main:create_app" in dockerfile
    assert "--factory" in dockerfile


def test_compose_does_not_embed_api_key() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "POLYOCR_API_KEY=${POLYOCR_API_KEY:?set POLYOCR_API_KEY}" in compose
