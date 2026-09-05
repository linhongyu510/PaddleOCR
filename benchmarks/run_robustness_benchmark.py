#!/usr/bin/env python3
"""Robustness benchmark: accuracy under controlled image degradation.

Derives degraded variants from `benchmarks/accuracy_dataset` and scores each one
against the same ground truth, so the effect of blur, compression, rotation,
downscaling, noise and lighting is measured rather than assumed.

This exists to answer a concrete design question: should the service preprocess
images before inference? The answer measured here is no — see `--compare-preprocess`
and `docs/robustness.md`. Keeping the harness in the repository means that
conclusion can be re-checked against a future PaddleOCR release instead of being
taken on trust.

Model weights download on first use per language, so scope runs with --languages.

Examples:
  python benchmarks/run_robustness_benchmark.py --languages en,fr
  python benchmarks/run_robustness_benchmark.py --severity severe
  python benchmarks/run_robustness_benchmark.py --compare-preprocess
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

BASE = Path(__file__).resolve().parent
DATASET = BASE / "accuracy_dataset"
IMAGES = DATASET / "images"
GROUND_TRUTH = DATASET / "ground_truth.json"

_spec = importlib.util.spec_from_file_location("_accuracy", BASE / "run_accuracy_benchmark.py")
assert _spec and _spec.loader
_accuracy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_accuracy)
score = _accuracy.score

NOISE_SEED = 11


def _encode(image: Image.Image, fmt: str = "PNG", **kwargs) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **kwargs)
    return buffer.getvalue()


def _recompress(image: Image.Image, quality: int) -> Image.Image:
    data = _encode(image, "JPEG", quality=quality)
    return Image.open(io.BytesIO(data)).convert("RGB")


def _add_noise(image: Image.Image, sigma: float) -> Image.Image:
    generator = np.random.default_rng(NOISE_SEED)
    array = np.asarray(image).astype(np.float32)
    noisy = array + generator.normal(0, sigma, array.shape)
    return Image.fromarray(np.clip(noisy, 0, 255).astype(np.uint8))


def _rescale(image: Image.Image, factor: float) -> Image.Image:
    width = max(1, round(image.width * factor))
    height = max(1, round(image.height * factor))
    return image.resize((width, height), Image.LANCZOS)


# Two tiers. `moderate` is what a phone photo or a re-saved screenshot looks like;
# `severe` pushes past the point where recognition fails, which is where any
# preprocessing would have to earn its place.
DEGRADATIONS: dict[str, dict[str, Callable[[Image.Image], Image.Image]]] = {
    "moderate": {
        "blur2": lambda im: im.filter(ImageFilter.GaussianBlur(2.0)),
        "jpeg20": lambda im: _recompress(im, 20),
        "rotate5": lambda im: im.rotate(5, resample=Image.BICUBIC, fillcolor=(255, 255, 255), expand=True),
        "scale50": lambda im: _rescale(im, 0.5),
        "noise25": lambda im: _add_noise(im, 25),
        "dark": lambda im: ImageEnhance.Brightness(im).enhance(0.45),
        "lowcontrast": lambda im: ImageEnhance.Contrast(im).enhance(0.35),
    },
    "severe": {
        "blur4": lambda im: im.filter(ImageFilter.GaussianBlur(4.0)),
        "blur6": lambda im: im.filter(ImageFilter.GaussianBlur(6.0)),
        "jpeg5": lambda im: _recompress(im, 5),
        "scale25": lambda im: _rescale(im, 0.25),
        "scale15": lambda im: _rescale(im, 0.15),
        "rotate15": lambda im: im.rotate(15, resample=Image.BICUBIC, fillcolor=(255, 255, 255), expand=True),
        "noise60": lambda im: _add_noise(im, 60),
        "verydark": lambda im: ImageEnhance.Brightness(im).enhance(0.18),
        "flat": lambda im: ImageEnhance.Contrast(im).enhance(0.12),
        "blur3_jpeg10": lambda im: _recompress(im.filter(ImageFilter.GaussianBlur(3.0)), 10),
    },
}

# Candidate preprocessing pipelines, kept only to document that they do not help.
PREPROCESSORS: dict[str, Callable[[Image.Image], Image.Image]] = {
    "upscale": lambda im: _rescale(im, max(1.0, 960 / max(1, min(im.size)))),
    "sharpen": lambda im: im.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=3)),
    "autocontrast": lambda im: ImageOps.autocontrast(im, cutoff=1),
    "combined": lambda im: ImageOps.autocontrast(
        _rescale(im, max(1.0, 960 / max(1, min(im.size)))).filter(
            ImageFilter.UnsharpMask(radius=2, percent=180, threshold=2)
        ),
        cutoff=1,
    ),
}


def build_recognizer(mode: str, server: str, api_key: str):
    if mode == "http":
        import requests

        def http_recognize(payload: bytes, language: str, threshold: float) -> list[str]:
            response = requests.post(
                f"{server.rstrip('/')}/v1/ocr",
                files={"file": ("image.png", io.BytesIO(payload), "image/png")},
                data={"language": language, "score_threshold": str(threshold)},
                headers={"X-API-Key": api_key} if api_key else {},
                timeout=180,
            )
            response.raise_for_status()
            return [item["text"] for item in response.json().get("items", [])]

        return http_recognize

    from polyocr.services.model_manager import ModelManager
    from polyocr.services.ocr import OCRService, create_paddle_backend

    service = OCRService(ModelManager(create_paddle_backend).get, max_concurrency=1, workers=1)

    def direct_recognize(payload: bytes, language: str, threshold: float) -> list[str]:
        items = asyncio.run(
            service.recognize(
                payload,
                language,
                threshold,
                max_bytes=80 * 1024 * 1024,
                max_pixels=80_000_000,
            )
        )
        return [item.text for item in items]

    return direct_recognize


def evaluate(
    recognize,
    cases: list[tuple[str, str, list[str]]],
    transform: Callable[[Image.Image], Image.Image] | None,
    preprocessor: Callable[[Image.Image], Image.Image] | None,
    threshold: float,
) -> dict[str, float]:
    exact_total = cer_total = 0.0
    empty = failures = 0
    for language, name, expected in cases:
        image = Image.open(IMAGES / name).convert("RGB")
        if transform is not None:
            image = transform(image)
        if preprocessor is not None:
            image = preprocessor(image)
        try:
            recognised = recognize(_encode(image), language, threshold)
        except Exception:  # noqa: BLE001 - counted, not silenced
            failures += 1
            recognised = []
        if not recognised:
            empty += 1
        metrics = score(expected, recognised)
        exact_total += metrics["exact"]
        cer_total += metrics["cer"]
    count = len(cases)
    return {
        "exact": round(exact_total / count, 4),
        "cer": round(cer_total / count, 4),
        "empty": empty,
        "errors": failures,
        "cases": count,
    }


def load_cases(languages: list[str]) -> list[tuple[str, str, list[str]]]:
    ground_truth = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
    missing = [language for language in languages if language not in ground_truth]
    if missing:
        raise SystemExit(
            f"no ground truth for: {', '.join(missing)}. "
            f"available: {', '.join(sorted(ground_truth))}"
        )
    cases: list[tuple[str, str, list[str]]] = []
    for language in languages:
        for name, expected in sorted(ground_truth[language]["expected_texts"].items()):
            if (IMAGES / name).exists():
                cases.append((language, name, expected))
    if not cases:
        raise SystemExit("no images matched the requested languages")
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("direct", "http"), default="direct")
    parser.add_argument("--server", default="http://localhost:8000")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--score", type=float, default=0.3)
    parser.add_argument("--languages", default="en,fr,de,ru,zh")
    parser.add_argument("--severity", choices=("moderate", "severe", "all"), default="all")
    parser.add_argument(
        "--compare-preprocess",
        action="store_true",
        help="Also score candidate preprocessing pipelines on the severe tier.",
    )
    parser.add_argument("--out", default=str(BASE / "results" / "robustness_report.json"))
    args = parser.parse_args()

    languages = [item.strip() for item in args.languages.split(",") if item.strip()]
    cases = load_cases(languages)
    recognize = build_recognizer(args.mode, args.server, args.api_key)

    tiers = ["moderate", "severe"] if args.severity == "all" else [args.severity]
    report: dict[str, dict] = {}

    baseline = evaluate(recognize, cases, None, None, args.score)
    report["baseline"] = baseline
    print(f"languages: {', '.join(languages)}   images: {baseline['cases']}")
    print()
    print(f"{'degradation':16} {'exact':>7} {'cer':>7} {'empty':>6} {'err':>4}")
    print(f"{'(none)':16} {baseline['exact']:>7.3f} {baseline['cer']:>7.3f} "
          f"{baseline['empty']:>6} {baseline['errors']:>4}")

    for tier in tiers:
        for name, transform in DEGRADATIONS[tier].items():
            result = evaluate(recognize, cases, transform, None, args.score)
            report[name] = {**result, "tier": tier}
            print(f"{name:16} {result['exact']:>7.3f} {result['cer']:>7.3f} "
                  f"{result['empty']:>6} {result['errors']:>4}")

    if args.compare_preprocess:
        print()
        print("Candidate preprocessing on the severe tier (delta vs no preprocessing):")
        header = f"{'degradation':16} {'off':>7}"
        for label in PREPROCESSORS:
            header += f" {label:>13}"
        print(header)
        comparison: dict[str, dict] = {}
        for name, transform in DEGRADATIONS["severe"].items():
            off = report.get(name) or evaluate(recognize, cases, transform, None, args.score)
            row = f"{name:16} {off['exact']:>7.3f}"
            entry = {"off": off["exact"]}
            for label, preprocessor in PREPROCESSORS.items():
                on = evaluate(recognize, cases, transform, preprocessor, args.score)
                entry[label] = on["exact"]
                row += f" {on['exact'] - off['exact']:>+13.3f}"
            comparison[name] = entry
            print(row)
        report["preprocess_comparison"] = comparison

        improved = {
            label: sum(
                1
                for entry in comparison.values()
                if entry[label] > entry["off"] + 0.01
            )
            for label in PREPROCESSORS
        }
        print()
        print("degradations improved by more than 0.01 exact:")
        for label, count in improved.items():
            print(f"  {label:14} {count}/{len(comparison)}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print()
    print(f"report written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
