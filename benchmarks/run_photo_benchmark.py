#!/usr/bin/env python3
"""Real-photograph benchmark: accuracy on genuine camera captures.

Every other benchmark here uses synthetic fixtures with programmatic degradation.
Those bound the failure envelope but cannot answer the question that matters for a
deployed service: how does it do on photographs people actually take? This one
downloads real photographed receipts and scores against human word annotations.

Dataset: CORD-v2 (naver-clova-ix/cord-v2, CC-BY-4.0) -- 100 photographed Indonesian
receipts with word-level transcriptions. Real phone captures: hand shadows, creases,
curled thermal paper, dark backgrounds, off-axis framing, held-in-hand shots.

Images are downloaded at runtime into a gitignored directory, never committed. They
are photographs of real receipts belonging to real people, and this repository is
Apache-2.0; redistributing them here would be inappropriate regardless of the
dataset's own permissive licence. Attribution stays with the upstream dataset.

Scoring is order-independent word recall, not the line-based `exact` used by
run_accuracy_benchmark.py. CORD annotates individual words with quads and groups them
by semantic role, so neither line order nor line grouping is a meaningful contract to
compare against. Recall answers the useful question: what fraction of the annotated
words did the service actually read?

Requires `pyarrow` and network access on first run. ~234 MB download, cached.

Examples:
  python benchmarks/run_photo_benchmark.py
  python benchmarks/run_photo_benchmark.py --limit 15 --compare-preprocess
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / "photo_dataset"
IMAGES = CACHE / "images"
MANIFEST = CACHE / "manifest.json"
PARQUET = CACHE / "cord-v2-test.parquet"

PARQUET_URL = (
    "https://huggingface.co/datasets/naver-clova-ix/cord-v2/resolve/main/"
    "data/test-00000-of-00001-9c204eb3f4e11791.parquet"
)

_spec = importlib.util.spec_from_file_location("_robustness", BASE / "run_robustness_benchmark.py")
assert _spec and _spec.loader
_robustness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_robustness)
PREPROCESSORS = _robustness.PREPROCESSORS


def normalise(token: str) -> str:
    """Compare on alphanumerics only.

    Receipt annotations and OCR output disagree constantly on punctuation and
    thousands separators (`100,000` vs `100.000` vs `100 000`) in ways that say
    nothing about whether the text was read. Case and separators are dropped so the
    score reflects recognition rather than formatting convention.
    """
    return re.sub(r"[^0-9a-z]", "", token.lower())


def word_recall(expected: list[str], lines: list[str]) -> tuple[float, int, int]:
    """Fraction of annotated words that appear anywhere in the output."""
    produced: set[str] = set()
    for line in lines:
        for token in line.split():
            cleaned = normalise(token)
            if cleaned:
                produced.add(cleaned)
    wanted = [cleaned for cleaned in (normalise(word) for word in expected) if cleaned]
    if not wanted:
        return 1.0, 0, 0
    hits = sum(1 for word in wanted if word in produced)
    return hits / len(wanted), len(wanted), hits


def download_parquet() -> None:
    if PARQUET.exists():
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"downloading CORD-v2 test split -> {PARQUET.name} (~234 MB, one time)")
    temporary = PARQUET.with_suffix(".part")
    with urllib.request.urlopen(PARQUET_URL, timeout=600) as response:
        total = int(response.headers.get("Content-Length", 0))
        done = 0
        with temporary.open("wb") as handle:
            while chunk := response.read(1 << 20):
                handle.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done / 1e6:6.1f} / {total / 1e6:.0f} MB", end="")
    print()
    temporary.replace(PARQUET)


def extract(limit: int) -> dict[str, dict]:
    """Materialise `limit` images plus their word annotations."""
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if len(manifest) >= limit and all((IMAGES / name).exists() for name in manifest):
            return {name: manifest[name] for name in sorted(manifest)[:limit]}

    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise SystemExit("pyarrow is required: pip install pyarrow") from None
    from PIL import Image

    download_parquet()
    IMAGES.mkdir(parents=True, exist_ok=True)
    table = pq.read_table(PARQUET)
    manifest: dict[str, dict] = {}
    for index in range(min(limit, table.num_rows)):
        row = table.slice(index, 1).to_pylist()[0]
        image = Image.open(io.BytesIO(row["image"]["bytes"])).convert("RGB")
        name = f"cord_{index:02d}.png"
        image.save(IMAGES / name)
        truth = json.loads(row["ground_truth"])
        words = [
            text
            for line in truth.get("valid_line", [])
            for word in line.get("words", [])
            if (text := (word.get("text") or "").strip())
        ]
        manifest[name] = {"words": words, "size": list(image.size)}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def build_recognizer(mode: str, server: str, api_key: str, threshold: float):
    if mode == "http":
        import requests

        def over_http(payload: bytes) -> list[str]:
            response = requests.post(
                f"{server.rstrip('/')}/v1/ocr",
                files={"file": ("image.png", io.BytesIO(payload), "image/png")},
                data={"language": "en", "score_threshold": str(threshold)},
                headers={"X-API-Key": api_key} if api_key else {},
                timeout=300,
            )
            response.raise_for_status()
            return [item["text"] for item in response.json().get("items", [])]

        return over_http

    from polyocr.services.model_manager import ModelManager
    from polyocr.services.ocr import OCRService, create_paddle_backend

    service = OCRService(ModelManager(create_paddle_backend).get, max_concurrency=1, workers=1)

    def in_process(payload: bytes) -> list[str]:
        items = asyncio.run(
            service.recognize(
                payload,
                "en",
                threshold,
                max_bytes=80 * 1024 * 1024,
                max_pixels=80_000_000,
            )
        )
        return [item.text for item in items]

    return in_process


def bootstrap_interval(deltas: list[float], iterations: int = 20000) -> tuple[float, float, float]:
    """Percentile CI and two-sided p for the mean, so small n is not over-read.

    With 15 images a mean shift of a few points is easy to produce by chance; without
    an interval it would be tempting to read one as a real effect.
    """
    import numpy as np

    sample = np.asarray(deltas, dtype=np.float64)
    generator = np.random.default_rng(0)
    means = np.array(
        [generator.choice(sample, sample.size, replace=True).mean() for _ in range(iterations)]
    )
    low, high = np.percentile(means, [2.5, 97.5])
    p = 2 * min(float((means <= 0).mean()), float((means >= 0).mean()))
    return float(low), float(high), min(1.0, p)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("direct", "http"), default="direct")
    parser.add_argument("--server", default="http://localhost:8000")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--score", type=float, default=0.3)
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--compare-preprocess", action="store_true")
    parser.add_argument("--out", default=str(BASE / "results" / "photo_report.json"))
    args = parser.parse_args()

    manifest = extract(args.limit)
    recognize = build_recognizer(args.mode, args.server, args.api_key, args.score)

    def encode(image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    from PIL import Image

    print(f"real photographs: {len(manifest)}")
    print()
    print(f"{'image':14} {'size':13} {'words':>6} {'read':>5} {'recall':>7}")

    baseline: list[float] = []
    report: dict[str, dict] = {}
    for name in sorted(manifest):
        image = Image.open(IMAGES / name).convert("RGB")
        recall, wanted, hits = word_recall(manifest[name]["words"], recognize(encode(image)))
        baseline.append(recall)
        report[name] = {"recall": round(recall, 4), "words": wanted, "read": hits}
        size = str(tuple(manifest[name]["size"]))
        print(f"{name:14} {size:13} {wanted:>6} {hits:>5} {recall:>7.3f}")

    mean_recall = sum(baseline) / len(baseline)
    print()
    print(f"mean word recall: {mean_recall:.3f}")
    report["_summary"] = {"mean_recall": round(mean_recall, 4), "images": len(baseline)}

    if args.compare_preprocess:
        print()
        print("Candidate preprocessing on real photographs:")
        print(f"{'pipeline':14} {'mean':>7} {'delta':>8} {'95% CI':>18} {'p':>6} {'+':>3} {'-':>3}")
        comparison: dict[str, dict] = {}
        for label, preprocessor in PREPROCESSORS.items():
            scores: list[float] = []
            for name in sorted(manifest):
                image = Image.open(IMAGES / name).convert("RGB")
                try:
                    processed = encode(preprocessor(image))
                    recall, _, _ = word_recall(manifest[name]["words"], recognize(processed))
                except Exception:  # noqa: BLE001 - counted as a zero, not silenced
                    recall = 0.0
                scores.append(recall)
            deltas = [after - before for after, before in zip(scores, baseline, strict=True)]
            mean_after = sum(scores) / len(scores)
            delta = mean_after - mean_recall
            low, high, p = bootstrap_interval(deltas)
            helped = sum(1 for d in deltas if d > 0.01)
            harmed = sum(1 for d in deltas if d < -0.01)
            comparison[label] = {
                "mean": round(mean_after, 4),
                "delta": round(delta, 4),
                "ci": [round(low, 4), round(high, 4)],
                "p": round(p, 4),
                "helped": helped,
                "harmed": harmed,
            }
            interval = f"[{low:+.3f},{high:+.3f}]"
            print(
                f"{label:14} {mean_after:>7.3f} {delta:>+8.3f} {interval:>18} "
                f"{p:>6.3f} {helped:>3} {harmed:>3}"
            )
        report["_preprocess"] = comparison

        significant = [
            label for label, entry in comparison.items() if entry["p"] < 0.05 and entry["delta"] > 0
        ]
        print()
        if significant:
            print(f"significant improvement (p<0.05): {', '.join(significant)}")
        else:
            print("no pipeline shows a significant improvement; every CI includes zero")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"report written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
