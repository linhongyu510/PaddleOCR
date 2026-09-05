# Robustness: measured behaviour under image degradation

This records what `benchmarks/run_robustness_benchmark.py` measures, and why the
service does **not** preprocess images before inference.

Measured with paddleocr 3.7.0 / paddlepaddle 3.3.1 on macOS arm64, over
`en, fr, ru, zh` (8 images) from `benchmarks/accuracy_dataset`, `score_threshold=0.3`.
`exact` is the fraction of expected lines matched exactly; `cer` is the character
error rate; `empty` counts images that returned no text at all.

Reproduce with:

```bash
python benchmarks/run_robustness_benchmark.py --languages en,fr,ru,zh --compare-preprocess
```

## What PP-OCR already handles

| Degradation | exact | cer | empty |
| --- | --- | --- | --- |
| none (reference) | 0.975 | 0.002 | 0 |
| rotate 5° | 1.000 | 0.000 | 0 |
| rotate 15° | 0.958 | 0.004 | 0 |
| JPEG quality 20 | 0.975 | 0.003 | 0 |
| JPEG quality 5 | 0.950 | 0.003 | 0 |
| 50% scale | 0.975 | 0.003 | 0 |
| brightness 0.45 | 0.958 | 0.004 | 0 |
| brightness 0.18 | 0.975 | 0.002 | 0 |
| contrast 0.35 | 0.975 | 0.002 | 0 |
| contrast 0.12 | 0.975 | 0.003 | 0 |
| gaussian noise σ25 | 0.933 | 0.005 | 0 |
| gaussian noise σ60 | 0.883 | 0.010 | 0 |

Rotation, compression, lighting and contrast are essentially free: the pipeline
includes document-orientation and text-line-orientation models, and recognition
normalises its input. Even quality-5 JPEG and near-flat contrast stay within
0.03 of the clean reference.

## Where it actually breaks

| Degradation | exact | cer | empty |
| --- | --- | --- | --- |
| gaussian blur σ2 | 0.933 | 0.033 | 0 |
| gaussian blur σ4 | 0.125 | 0.795 | 4 |
| gaussian blur σ6 | 0.000 | 1.000 | 2 |
| 25% scale | 0.550 | 0.365 | 2 |
| 15% scale | 0.000 | 0.980 | 5 |
| blur σ3 + JPEG 10 | 0.375 | 0.530 | 2 |

Only two things matter: **blur beyond about σ2, and downscaling past roughly 25%**.
Both destroy glyph-level detail, and past that point detection returns nothing
rather than returning wrong text — the `empty` column. Failures are visible as
empty results, not as confident nonsense.

Practical implication for callers: keep text at a reasonable pixel height and avoid
out-of-focus captures. Compression, lighting and moderate skew are not worth
worrying about.

## Why `preprocess` is not implemented

`POST /v1/ocr` accepted a `preprocess` flag and discarded it with `del preprocess`.
It was advertised in the OpenAPI schema and returned HTTP 200, so callers could
reasonably believe preprocessing had occurred. Three scripts in `benchmarks/` sent
`preprocess=true`.

Rather than assume preprocessing would help, four pipelines were measured on the
severe tier. Values are the change in `exact` against no preprocessing:

| Degradation | off | upscale | sharpen | autocontrast | combined |
| --- | --- | --- | --- | --- | --- |
| blur σ4 | 0.125 | +0.125 | +0.000 | −0.125 | −0.125 |
| blur σ6 | 0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| JPEG 5 | 0.950 | −0.058 | +0.000 | **−0.225** | **−0.308** |
| 25% scale | 0.550 | **−0.183** | −0.008 | −0.175 | −0.217 |
| 15% scale | 0.000 | +0.042 | +0.000 | +0.000 | +0.000 |
| rotate 15° | 0.958 | +0.042 | +0.017 | **−0.308** | +0.017 |
| noise σ60 | 0.883 | +0.067 | +0.042 | +0.067 | −0.025 |
| brightness 0.18 | 0.975 | −0.042 | +0.000 | +0.000 | −0.150 |
| contrast 0.12 | 0.975 | +0.000 | +0.000 | −0.075 | +0.000 |
| blur σ3 + JPEG 10 | 0.375 | **−0.250** | −0.125 | **−0.375** | **−0.375** |

Improved more than 0.01 `exact`: upscale 4/10, sharpen 2/10, autocontrast 1/10,
combined 1/10.

No pipeline is a net win:

- **autocontrast** is the most damaging. It amplifies compression artifacts and
  rotation-fill edges into structures the detector reads as glyphs.
- **upscale** helps blur σ4 (+0.125), the case it should help, but *hurts* 25%
  scale (−0.183) and the blur+compression combination (−0.250) by interpolating
  artifacts up along with the text. PP-OCR resizes internally, so doing it first
  only adds a lossy step.
- **sharpen** is close to neutral, so it buys nothing for its cost.
- **combined** compounds the harm and is worst overall.

Where a pipeline does help, the case was already failing (blur σ4 at 0.125 → 0.250
is still unusable). Where the pipeline hurts, it damages cases that were working.

So `preprocess=true` now returns `400 preprocess_unsupported` with a pointer to
this document, and `preprocess=false` or omitting the field behaves as before.
Failing loudly is deliberate: a caller who explicitly asks for preprocessing should
not be told the request succeeded.

## Caveats

The fixtures are synthetic, cleanly rendered text, and degradations are applied
programmatically. Real capture blur is directional rather than Gaussian, real scans
carry paper texture and uneven illumination, and photographs add perspective rather
than pure rotation. These numbers bound where the pipeline fails on controlled
inputs and support the preprocessing decision; they are not a substitute for
evaluation on real photographed documents.

The conclusion is tied to the PaddleOCR version above. The benchmark is kept in the
repository so it can be re-run against a future release rather than trusted
indefinitely.
