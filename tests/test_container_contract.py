from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_container_is_non_root_and_has_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER polyocr" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "libgl1" in dockerfile
    assert "polyocr.main:create_app" in dockerfile
    assert "--factory" in dockerfile


def test_container_copies_the_declared_license_files() -> None:
    """`license-files` in pyproject only applies if the files are in the context.

    They are otherwise skipped with a warning, producing an installed
    distribution with no LICENSE or NOTICE.
    """
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    copy_lines = [line for line in dockerfile.splitlines() if line.startswith("COPY")]
    copied = " ".join(copy_lines)
    assert "LICENSE" in copied
    assert "NOTICE" in copied

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for declared in ("LICENSE", "NOTICE"):
        if declared in pyproject:
            assert declared in copied, f"{declared} is declared but not copied into the image"


def test_dockerfile_pins_an_explicit_base_image() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    from_lines = [line for line in dockerfile.splitlines() if line.startswith("FROM ")]
    assert from_lines, "Dockerfile has no FROM instruction"
    for line in from_lines:
        assert ":" in line, f"base image is not pinned to a tag: {line}"
        assert ":latest" not in line, f"base image must not use :latest: {line}"


def test_compose_does_not_embed_api_key() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "POLYOCR_API_KEY=${POLYOCR_API_KEY:?set POLYOCR_API_KEY}" in compose
