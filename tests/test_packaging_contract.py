"""Packaging contract: license, typing marker, entry point and metadata."""

from importlib.metadata import entry_points, metadata
from importlib.resources import files
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def test_license_and_notice_files_exist() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0" in license_text

    notice_text = (ROOT / "NOTICE").read_text(encoding="utf-8")
    # Apache-2.0 section 4(d) attribution for the upstream project.
    assert "PaddleOCR" in notice_text
    assert "PaddlePaddle Authors" in notice_text


def test_distribution_declares_apache_license() -> None:
    meta = metadata("polyocr-service")
    declared = meta.get("License-Expression") or meta.get("License") or ""
    assert "Apache" in declared


def test_pyproject_declares_license_and_typing_marker() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "Apache-2.0"' in pyproject
    assert "LICENSE" in pyproject
    assert "NOTICE" in pyproject
    assert "py.typed" in pyproject


def test_typing_marker_is_packaged() -> None:
    assert files("polyocr").joinpath("py.typed").is_file()


def test_console_script_is_registered() -> None:
    scripts = [ep for ep in entry_points(group="console_scripts") if ep.name == "polyocr-service"]
    assert scripts, "polyocr-service console script is not registered"
    assert scripts[0].value == "polyocr.__main__:main"


def test_console_script_parses_arguments_without_starting_a_server() -> None:
    from polyocr.__main__ import build_parser

    args = build_parser().parse_args(["--host", "0.0.0.0", "--port", "9001", "--workers", "3"])
    assert (args.host, args.port, args.workers) == ("0.0.0.0", 9001, 3)


def test_console_script_defaults_to_loopback() -> None:
    from polyocr.__main__ import build_parser

    args = build_parser().parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.workers == 1


def test_console_script_rejects_an_unknown_log_level() -> None:
    from polyocr.__main__ import build_parser

    with pytest.raises(SystemExit):
        build_parser().parse_args(["--log-level", "chatty"])


def test_version_is_single_sourced() -> None:
    import polyocr

    assert polyocr.__version__ == metadata("polyocr-service")["Version"]
    # The version must come from distribution metadata, not a second literal.
    init_source = (ROOT / "src/polyocr/__init__.py").read_text(encoding="utf-8")
    assert 'version("polyocr-service")' in init_source
    assert polyocr.__version__ not in init_source


def test_app_reports_the_package_version() -> None:
    import polyocr
    from polyocr.core.config import Settings
    from polyocr.main import create_app
    from polyocr.services.ocr import OCRService

    class Backend:
        def predict(self, image: object) -> list[object]:
            return []

    app = create_app(
        settings=Settings(auth_enabled=False),
        ocr_service=OCRService(lambda _language: Backend()),
    )
    assert app.version == polyocr.__version__
