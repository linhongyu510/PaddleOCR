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


def _declared_version() -> str:
    """Read the version from pyproject without needing tomllib.

    tomllib is stdlib only from 3.11, and this project supports 3.10, so parsing
    the single `version = "..."` line in `[project]` keeps the test portable
    rather than adding a tomli dependency just to read one field.
    """
    import re

    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project = text.split("[project]", 1)[1]
    match = re.search(r'^version\s*=\s*"([^"]+)"', project, re.MULTILINE)
    assert match, "no version found under [project] in pyproject.toml"
    return match.group(1)


def test_declared_version_matches_installed_metadata() -> None:
    assert _declared_version() == metadata("polyocr-service")["Version"]


def test_packaged_version_has_a_changelog_entry() -> None:
    """A released version must be documented.

    Guards against tagging a release whose notes are still sitting under
    `[Unreleased]`, which is how 0.3.0 shipped untagged.
    """
    version = _declared_version()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{version}]" in changelog, (
        f"version {version} has no CHANGELOG entry; it is probably still under [Unreleased]"
    )


def test_changelog_versions_are_ordered_newest_first() -> None:
    import re

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    found = re.findall(r"^## \[(\d+)\.(\d+)\.(\d+)\]", changelog, re.MULTILINE)
    versions = [tuple(int(part) for part in item) for item in found]
    assert versions, "no released versions in CHANGELOG"
    assert versions == sorted(versions, reverse=True), f"out of order: {versions}"


def test_no_source_file_imports_a_module_newer_than_the_supported_floor() -> None:
    """Guard the declared `requires-python` floor.

    `tomllib` is stdlib only from 3.11 but the project supports 3.10, so importing
    it passed locally on 3.12 and broke the 3.10 CI job.

    Uses the AST rather than a text search so that a module name appearing in a
    docstring or a data literal is not mistaken for an import, and so that only the
    exact module is matched -- `asyncio.taskgroups` is 3.11, but plain `asyncio` is
    not, and reducing one to the other flags every async file in the tree.
    """
    import ast
    import re

    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    floor_match = re.search(r'requires-python\s*=\s*">=(\d+)\.(\d+)', text)
    assert floor_match, "pyproject must declare a requires-python floor"
    floor = (int(floor_match.group(1)), int(floor_match.group(2)))

    # Importable stdlib modules and the Python version that introduced them.
    added_in = {"tomllib": (3, 11), "asyncio.taskgroups": (3, 11), "graphlib": (3, 9)}
    too_new = {name for name, since in added_in.items() if since > floor}

    def imported_modules(tree: ast.Module) -> set[str]:
        found: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module)
                found.update(f"{node.module}.{alias.name}" for alias in node.names)
        return found

    offenders: list[str] = []
    for path in list((ROOT / "src").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")):
        modules = imported_modules(ast.parse(path.read_text(encoding="utf-8")))
        for name in sorted(too_new & modules):
            offenders.append(f"{path.relative_to(ROOT)} imports {name}")
    assert not offenders, f"requires-python is >={floor[0]}.{floor[1]}: {offenders}"
