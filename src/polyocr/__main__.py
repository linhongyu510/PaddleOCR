"""Console entry point: ``polyocr-service``.

Thin wrapper over uvicorn so an installed distribution can be started without
remembering the ``--factory`` invocation. Host, port and worker count come from
``POLYOCR_HOST`` / ``POLYOCR_PORT`` / ``POLYOCR_WEB_CONCURRENCY`` and can be
overridden on the command line.
"""

import argparse
import os
import sys
from collections.abc import Sequence


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(f"{name} must be an integer, got {raw!r}") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polyocr-service",
        description="Run the PolyOCR OCR and translation API.",
    )
    parser.add_argument("--host", default=os.getenv("POLYOCR_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=_int_env("POLYOCR_PORT", 8000))
    parser.add_argument(
        "--workers",
        type=int,
        default=_int_env("POLYOCR_WEB_CONCURRENCY", 1),
        help="Number of worker processes. Each worker keeps its own model cache.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("POLYOCR_LOG_LEVEL", "info"),
        choices=("critical", "error", "warning", "info", "debug", "trace"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        import uvicorn
    except ImportError:  # pragma: no cover - uvicorn is a runtime dependency
        raise SystemExit("uvicorn is required to run the service") from None

    uvicorn.run(
        "polyocr.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        workers=args.workers if args.workers > 1 else None,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
