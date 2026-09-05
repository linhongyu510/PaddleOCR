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

## Real photographs

Everything above uses synthetic fixtures. This section uses genuine phone captures:
15 photographed receipts from [CORD-v2](https://huggingface.co/datasets/naver-clova-ix/cord-v2)
(CC-BY-4.0) with human word-level transcriptions — hand shadows, creases, curled
thermal paper, dark backgrounds, off-axis framing, resolutions from 432×648 to
2304×4096.

```bash
python benchmarks/run_photo_benchmark.py --limit 15 --compare-preprocess
```

Scoring is order-independent **word recall**, not the line-based `exact` used
elsewhere: CORD annotates individual words grouped by semantic role, so neither line
order nor line grouping is a contract worth comparing against. Punctuation and
thousands separators are normalised away, because `100,000` vs `100.000` says nothing
about whether the text was read.

| Metric | Synthetic | Real photographs |
| --- | --- | --- |
| mean score | 0.975 exact | **0.841 word recall** |

**The synthetic numbers are optimistic by roughly 13 points.** This confirms in
measurement what the earlier caveat only asserted. Per-image recall:

| Image | Resolution | Words | Read | Recall |
| --- | --- | --- | --- | --- |
| cord_11 / cord_12 / cord_03 / cord_01 | various | 12–23 | all | 1.000 |
| cord_06 | 864×1296 | 19 | 18 | 0.947 |
| cord_08 | 864×1296 | 28 | 26 | 0.929 |
| cord_00 / cord_04 | — | 23 | 21 | 0.913 |
| cord_13 | 864×1296 | 24 | 21 | 0.875 |
| cord_14 | 1836×3264 | 40 | 33 | 0.825 |
| cord_02 | 864×1296 | 23 | 18 | 0.783 |
| cord_10 | 576×864 | 13 | 10 | 0.769 |
| cord_09 | 576×864 | 11 | 8 | 0.727 |
| cord_05 | 2304×4096 | 16 | 11 | 0.688 |
| **cord_07** | 576×864 | 16 | **4** | **0.250** |

Four of fifteen are read perfectly; nine score ≥0.727. One image, `cord_07`, is a
badly faded thermal receipt where recognition largely fails.

### The preprocessing conclusion survives, but the reasoning changes

On synthetic degradation every pipeline was clearly net negative. On real photographs
three of five have a *positive* mean. That looked like it might overturn the decision,
so it was tested rather than eyeballed — bootstrap 95% CI and two-sided p over 20 000
resamples:

| Pipeline | mean | Δ | 95% CI | p | helped | harmed |
| --- | --- | --- | --- | --- | --- | --- |
| (none) | 0.841 | — | — | — | — | — |
| upscale | 0.848 | +0.007 | [−0.017, +0.037] | 0.773 | 1 | 1 |
| sharpen | 0.868 | +0.027 | [−0.028, +0.087] | 0.371 | 6 | 3 |
| autocontrast | 0.829 | −0.012 | [−0.065, +0.050] | 0.668 | 2 | 5 |
| flatten | 0.852 | +0.011 | [−0.039, +0.068] | 0.721 | 4 | 4 |
| combined | 0.870 | +0.029 | [−0.072, +0.152] | 0.656 | 5 | 6 |

**Every confidence interval includes zero; no p is below 0.37.** With 15 images a
few points of mean shift is ordinary sampling noise.

`combined` shows this most clearly. Its +0.029 comes almost entirely from `cord_07`,
where it gains +0.688 on the one image that was already failing. Drop that single
image and `combined` becomes **−0.018** — the apparent benefit was one outlier, not an
effect. It also harmed 6 of 15 images, including −0.357 on `cord_08`, which had been
reading at 0.929.

Two hypotheses for why `cord_07` responds to preprocessing were tested and both
failed: global ink contrast correlates with recall at only **−0.262** (the
*lowest*-contrast image scores 0.947), and local text-to-background contrast at
**+0.027**. Neither explains it, so no mechanism is claimed here — `cord_07` is simply
one hard image.

So the decision stands, on a narrower and more honest basis than before: **on real
photographs no preprocessing pipeline produces a statistically detectable improvement,
and the best-looking candidate is driven by a single outlier while harming 6 of 15
images.** Enabling it by default would trade reliable cases for one unreliable one.

### What this does and does not establish

It establishes that the synthetic estimate is ~13 points optimistic, and that
preprocessing is not a free win on real captures. It does not establish that
preprocessing could never help a *specific* known-bad input class; `cord_07` shows a
faded receipt can respond. A caller who knows their inputs are uniformly degraded in
one way is better served preprocessing on their side, where they can measure it
against their own data, than by a service-wide default chosen from 15 images.

## Caveats

Degradations in the tiers above are applied programmatically to cleanly-rendered
synthetic fixtures. The `capture` tier models photograph and scan artifacts —
directional blur, projective skew, illumination gradients, soft shadows, correlated
paper grain — but simulation is not photography: real lenses vary sharpness across the
frame, real sensors apply denoising and sharpening in the ISP, and real pages have
creases and specular highlights. The **Real photographs** section above measures actual
captures and puts a number on that gap (0.975 synthetic vs 0.841 real).

The real-photograph sample is 15 images of receipts, in English and Indonesian, from a
single dataset. It is enough to detect a ~13 point gap against synthetic fixtures and
to show that no preprocessing pipeline is a significant win, but it is not a
representative sample of document photography in general — no handwriting, no dense
multi-column layouts, no other scripts under capture conditions.

The conclusion is tied to the PaddleOCR version above. Both benchmarks are kept in the
repository so it can be re-run against a future release rather than trusted
indefinitely.

