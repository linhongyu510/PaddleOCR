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
| perspective skew | 0.975 | 0.002 | 0 |
| JPEG quality 20 | 0.975 | 0.003 | 0 |
| JPEG quality 5 | 0.950 | 0.003 | 0 |
| 50% scale | 0.975 | 0.003 | 0 |
| brightness 0.45 | 0.958 | 0.004 | 0 |
| brightness 0.18 | 0.975 | 0.002 | 0 |
| contrast 0.35 | 0.975 | 0.002 | 0 |
| contrast 0.12 | 0.975 | 0.003 | 0 |
| uneven illumination | 1.000 | 0.000 | 0 |
| soft shadow over page | 0.975 | 0.003 | 0 |
| paper texture | 0.975 | 0.003 | 0 |
| gaussian noise σ25 | 0.933 | 0.005 | 0 |
| gaussian noise σ60 | 0.883 | 0.010 | 0 |
| perspective + uneven light + texture + JPEG 30 | 1.000 | 0.000 | 0 |

Rotation, compression, lighting and contrast are essentially free: the pipeline
includes document-orientation and text-line-orientation models, and recognition
normalises its input.

The capture-realistic cases are the more interesting result. Uneven illumination,
soft shadows, paper grain and projective skew — the artifacts that global gaussian
degradation does *not* reproduce — cost nothing at all. The combined "photograph of a
page" case (perspective + gradient + grain + compression) scores **1.000**.

## Where it actually breaks

| Degradation | exact | cer | empty |
| --- | --- | --- | --- |
| gaussian blur σ2 | 0.933 | 0.033 | 0 |
| gaussian blur σ4 | 0.125 | 0.795 | 4 |
| gaussian blur σ6 | 0.000 | 1.000 | 2 |
| **motion blur, 15px horizontal** | **0.000** | **0.786** | 3 |
| **motion blur, 15px diagonal** | **0.000** | **0.756** | 2 |
| 25% scale | 0.550 | 0.365 | 2 |
| 15% scale | 0.000 | 0.980 | 5 |
| blur σ3 + JPEG 10 | 0.375 | 0.530 | 2 |

Only loss of glyph-level detail matters: **blur and downscaling**. Geometry and
lighting do not.

**Directional blur is harsher than its gaussian equivalent.** A 15px motion blur
scores 0.000 while gaussian σ2 still scores 0.933. Its threshold is between 9 and
15 pixels of travel:

| Motion blur | Output |
| --- | --- |
| none | `Hello World` / `OCR Test` / `English Text Recognition` |
| 5px | identical to clean |
| 9px | identical to clean |
| 15px | `Heelco Ncotec` / `COIRTest` / `Engish Teext Re rogmtton` |

**This is the one case that fails unsafely.** Elsewhere, degradation past the limit
returns no text — a caller sees an empty result and knows the image was unusable. At
15px motion blur the service instead returns confidently-scored nonsense that is
structurally plausible. A caller cannot distinguish it from a correct result.

Practical implication: keep text at a reasonable pixel height, and treat camera shake
as the failure to guard against. Compression, lighting, shadows, paper texture and
moderate skew are not worth worrying about.

## Why `preprocess` is not implemented

`POST /v1/ocr` accepted a `preprocess` flag and discarded it with `del preprocess`.
It was advertised in the OpenAPI schema and returned HTTP 200, so callers could
reasonably believe preprocessing had occurred. Three scripts in `benchmarks/` sent
`preprocess=true`.

Rather than assume preprocessing would help, five pipelines were measured across all
17 degradations. Values are the change in `exact` against no preprocessing:

| Degradation | off | upscale | sharpen | autocontrast | flatten | combined |
| --- | --- | --- | --- | --- | --- | --- |
| blur σ4 | 0.125 | +0.125 | +0.000 | −0.125 | −0.083 | −0.125 |
| blur σ6 | 0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| JPEG 5 | 0.950 | −0.058 | +0.000 | **−0.225** | +0.000 | **−0.308** |
| 25% scale | 0.550 | **−0.183** | −0.008 | −0.175 | −0.133 | −0.217 |
| 15% scale | 0.000 | +0.042 | +0.000 | +0.000 | +0.000 | +0.000 |
| rotate 15° | 0.958 | +0.042 | +0.017 | **−0.308** | +0.042 | +0.017 |
| noise σ60 | 0.883 | +0.067 | +0.042 | +0.067 | +0.025 | −0.025 |
| brightness 0.18 | 0.975 | −0.042 | +0.000 | +0.000 | −0.092 | −0.150 |
| contrast 0.12 | 0.975 | +0.000 | +0.000 | −0.075 | −0.025 | +0.000 |
| blur σ3 + JPEG 10 | 0.375 | **−0.250** | −0.125 | **−0.375** | −0.042 | **−0.375** |
| motion 15px horizontal | 0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| motion 15px diagonal | 0.000 | +0.000 | +0.000 | +0.042 | +0.000 | +0.042 |
| uneven illumination | 1.000 | +0.000 | +0.000 | **−0.225** | −0.025 | **−0.708** |
| soft shadow | 0.975 | −0.042 | −0.042 | **−0.517** | −0.042 | −0.042 |
| paper texture | 0.975 | −0.042 | +0.000 | **−0.450** | +0.000 | −0.150 |
| perspective | 0.975 | +0.000 | +0.000 | **−0.300** | +0.000 | +0.000 |
| photo combo | 1.000 | −0.025 | +0.000 | −0.150 | −0.025 | −0.067 |

Net effect over 17 degradations:

| Pipeline | helped | harmed | mean Δexact |
| --- | --- | --- | --- |
| upscale | 4 | 7 | −0.022 |
| sharpen | 2 | 2 | −0.007 |
| autocontrast | 2 | **11** | **−0.166** |
| flatten (local) | 2 | 8 | −0.024 |
| combined | 2 | 10 | −0.124 |

Every pipeline is net negative. In detail:

- **autocontrast** is the most damaging, and it fails hardest exactly where it looks
  most justified: soft shadow −0.517, paper texture −0.450, perspective −0.300,
  uneven illumination −0.225. It stretches artifacts and fill edges into structures
  the detector reads as glyphs.
- **flatten** was included specifically because it is *local* — dividing by a blurred
  background is the standard fix for uneven lighting, and a global operation cannot
  correct a gradient by construction. It still lost (−0.024 net, harmed 8). The
  reason is that PP-OCR was not failing on those cases: uneven light already scored
  1.000, so there was nothing to recover and only detail to lose.
- **upscale** helps blur σ4 (+0.125) but hurts 25% scale (−0.183) and blur+compression
  (−0.250). PP-OCR resizes internally, so doing it first only adds a lossy step.
- **sharpen** is near-neutral, so it buys nothing for its cost.
- **combined** compounds the harm; on uneven illumination it destroys a perfect score
  (−0.708).

Two structural reasons no pipeline can win here:

1. Where a pipeline helps, the case was already unusable. blur σ4 at 0.125 → 0.250 is
   not a recovered result.
2. The cases preprocessing is *designed* for — uneven lighting, shadow, texture, skew
   — are already at 0.975–1.000. There is no headroom, only downside.

So `preprocess=true` returns `400 preprocess_unsupported` with a pointer to this
document, and `preprocess=false` or omitting the field behaves as before. Failing
loudly is deliberate: a caller who explicitly asks for preprocessing should not be
told the request succeeded.

## Caveats

Degradations are applied programmatically to cleanly-rendered synthetic fixtures. The
`capture` tier models photograph and scan artifacts — directional blur, projective
skew, illumination gradients, soft shadows, correlated paper grain — but simulation is
not photography: real lenses vary sharpness across the frame, real sensors apply
denoising and sharpening in the ISP, and real pages have creases and specular
highlights. These numbers bound the failure envelope and support the preprocessing
decision; they do not replace evaluation on genuinely photographed documents.

The conclusion is tied to the PaddleOCR version above. The benchmark is kept in the
repository so it can be re-run against a future release rather than trusted
indefinitely.

