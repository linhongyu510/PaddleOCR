"""PolyOCR Service: a bounded, authenticated OCR and translation API.

``__version__`` is read from the installed distribution metadata so that
``pyproject.toml`` stays the single source of truth.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("polyocr-service")
except PackageNotFoundError:  # pragma: no cover - source tree without install
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
