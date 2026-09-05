#!/usr/bin/env python3
"""Per-language OCR accuracy benchmark.

Runs the OCR pipeline over `benchmarks/accuracy_dataset` and scores the result
against the ground truth shipped with those images. Unlike the throughput
scripts in this directory, this one measures *correctness*, so it is what proves
a language is genuinely served rather than merely returning HTTP 200.

Two modes:

  --mode direct  (default)  call the OCR service in-process; no server needed
  --mode http    --server URL   exercise a running deployment over HTTP

Reported per language:

  exact      fraction of expected lines matched exactly after normalisation
  cer        character error rate over the joined text (lower is better)
  status     ok | no_text | error

Model weights are downloaded on first use for each language, so a full run over
all languages takes a while and needs network access. Scope it with --languages.

Examples:
  python benchmarks/run_accuracy_benchmark.py --languages fr,de,ru
  python benchmarks/run_accuracy_benchmark.py --mode http --server http://localhost:8000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATASET = BASE / "accuracy_dataset"
IMAGES = DATASET / "images"
GROUND_TRUTH = DATASET / "ground_truth.json"


def normalize(text: str) -> str:
    """Casefold, strip accents-preserving NFC, and collapse whitespace.

    OCR line breaks and spacing vary between models, so comparison is done on
    normalised text. Characters are preserved: no accent or script stripping,
    which would flatter non-Latin scripts.
    """
    folded = unicodedata.normalize("NFC", text).casefold()
    return " ".join(folded.split())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (ca != cb),
                )
            )
        previous = current
    return previous[-1]


def character_error_rate(expected: str, actual: str) -> float:
    reference = normalize(expected).replace(" ", "")
    hypothesis = normalize(actual).replace(" ", "")
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return min(1.0, levenshtein(reference, hypothesis) / len(reference))


def _best_pairing(expected_lines: list[str], recognised: list[str]) -> list[tuple[str, str]]:
    """Greedily pair each expected line with its closest unused recognised line.

    Detection order is not part of the contract: PaddleOCR may return regions
    bottom-to-top, and a caller reading `items` gets whatever order detection
    produced. Comparing joined text positionally would therefore charge a huge
    error rate to output that is perfectly correct but ordered differently, which
    is exactly what happened for `el` and `nl` before this pairing was added.
    """
    unused = list(recognised)
    pairs: list[tuple[str, str]] = []
    for line in expected_lines:
        if not unused:
            pairs.append((line, ""))
            continue
        target = normalize(line)
        best = min(unused, key=lambda candidate: levenshtein(target, normalize(candidate)))
        unused.remove(best)
        pairs.append((line, best))
    # Anything left over is spurious output and still counts against the score.
    pairs.extend(("", leftover) for leftover in unused)
    return pairs


def score(expected_lines: list[str], recognised: list[str]) -> dict[str, float]:
    """Exact per-line match plus order-independent CER."""
    remaining = [normalize(line) for line in recognised]
    exact = 0
    for line in expected_lines:
        target = normalize(line)
        if target in remaining:
            remaining.remove(target)
            exact += 1

    pairs = _best_pairing(expected_lines, recognised)
    reference_length = sum(len(normalize(e).replace(" ", "")) for e, _ in pairs)
    distance = sum(
        levenshtein(normalize(e).replace(" ", ""), normalize(a).replace(" ", ""))
        for e, a in pairs
    )
    cer = 0.0 if reference_length == 0 else min(1.0, distance / reference_length)

    return {
        "expected_lines": len(expected_lines),
        "recognised_lines": len(recognised),
        "exact_matches": exact,
        "exact": round(exact / len(expected_lines), 4) if expected_lines else 0.0,
        "cer": round(cer, 4),
    }


def load_ground_truth(languages: list[str] | None) -> dict[str, dict]:
    if not GROUND_TRUTH.exists():
        raise SystemExit(f"ground truth not found: {GROUND_TRUTH}")
    data = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
    if languages:
        missing = [lang for lang in languages if lang not in data]
        if missing:
            raise SystemExit(
                f"no ground truth for: {', '.join(missing)}. "
                f"available: {', '.join(sorted(data))}"
            )
        data = {lang: data[lang] for lang in languages}
    return data


def recognise_direct(image: Path, language: str, threshold: float) -> list[str]:
    from polyocr.services.model_manager import ModelManager
    from polyocr.services.ocr import OCRService, create_paddle_backend

    service = getattr(recognise_direct, "_service", None)
    if service is None:
        manager = ModelManager(create_paddle_backend)
        service = OCRService(manager.get, max_concurrency=1, workers=1)
        recognise_direct._service = service
    items = asyncio.run(
        service.recognize(
            image.read_bytes(),
            language,
            threshold,
            max_bytes=50 * 1024 * 1024,
            max_pixels=50_000_000,
        )
    )
    return [item.text for item in items]


def recognise_http(image: Path, language: str, threshold: float, server: str, key: str) -> list[str]:
    import requests

    headers = {"X-API-Key": key} if key else {}
    with image.open("rb") as handle:
        response = requests.post(
            f"{server.rstrip('/')}/v1/ocr",
            files={"file": (image.name, handle, "image/jpeg")},
            data={"language": language, "score_threshold": str(threshold)},
            headers=headers,
            timeout=180,
        )
    response.raise_for_status()
    return [item["text"] for item in response.json().get("items", [])]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("direct", "http"), default="direct")
    parser.add_argument("--server", default="http://localhost:8000")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--score", type=float, default=0.3)
    parser.add_argument(
        "--languages",
        default="",
        help="Comma-separated subset, e.g. fr,de,ru. Default: every language with ground truth.",
    )
    parser.add_argument("--out", default=str(BASE / "results" / "accuracy_report.json"))
    args = parser.parse_args()

    requested = [lang.strip() for lang in args.languages.split(",") if lang.strip()]
    ground_truth = load_ground_truth(requested or None)

    report: dict[str, dict] = {}
    for language, config in ground_truth.items():
        per_image = []
        for name, expected in sorted(config["expected_texts"].items()):
            image = IMAGES / name
            if not image.exists():
                per_image.append({"image": name, "status": "missing"})
                continue
            started = time.perf_counter()
            try:
                if args.mode == "direct":
                    recognised = recognise_direct(image, language, args.score)
                else:
                    recognised = recognise_http(
                        image, language, args.score, args.server, args.api_key
                    )
            except Exception as exc:  # noqa: BLE001 - reported per image
                per_image.append(
                    {"image": name, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
                )
                print(f"  {language:8} {name:28} ERROR {type(exc).__name__}: {exc}")
                continue
            elapsed = round(time.perf_counter() - started, 3)
            metrics = score(expected, recognised)
            status = "ok" if recognised else "no_text"
            per_image.append(
                {
                    "image": name,
                    "status": status,
                    "elapsed": elapsed,
                    "expected": expected,
                    "recognised": recognised,
                    **metrics,
                }
            )
            print(
                f"  {language:8} {name:28} exact={metrics['exact']:.2f} "
                f"cer={metrics['cer']:.3f} lines={metrics['recognised_lines']} {elapsed}s"
            )

        scored = [item for item in per_image if item.get("status") in {"ok", "no_text"}]
        errors = [item for item in per_image if item.get("status") == "error"]
        report[language] = {
            "images": per_image,
            "images_scored": len(scored),
            "images_failed": len(errors),
            "exact": round(sum(i["exact"] for i in scored) / len(scored), 4) if scored else 0.0,
            "cer": round(sum(i["cer"] for i in scored) / len(scored), 4) if scored else 1.0,
            "status": "ok" if scored and not errors else ("partial" if scored else "error"),
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )

    print()
    print(f"{'language':10} {'exact':>7} {'cer':>7} {'scored':>7} {'failed':>7}  status")
    for language, summary in sorted(report.items()):
        print(
            f"{language:10} {summary['exact']:>7.2f} {summary['cer']:>7.3f} "
            f"{summary['images_scored']:>7} {summary['images_failed']:>7}  {summary['status']}"
        )
    failed = [lang for lang, summary in report.items() if summary["status"] != "ok"]
    print()
    print(f"report written to {out_path}")
    if failed:
        print(f"languages not fully served: {', '.join(sorted(failed))}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
