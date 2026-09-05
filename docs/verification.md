# PolyOCR Service verification

## Round 4 — robustness measurement and the `preprocess` flag (2026-09-05)

Host: macOS arm64, Python 3.12.14, paddleocr 3.7.0, paddlepaddle 3.3.1.

### A parameter that did nothing

`POST /v1/ocr` accepted `preprocess`, advertised it in the OpenAPI schema, returned
HTTP 200, and then dropped it:

```python
preprocess: Annotated[bool, Form()] = False,
...
del preprocess
```

Verified by instrumenting the backend: the identical array reaches the model with
`preprocess=false` and `preprocess=true`. Three scripts under `benchmarks/` were
sending `preprocess=true`, so this was a live misuse, not a hypothetical one.

### Measured before deciding

Rather than implement preprocessing on the assumption it helps, 17 degradations were
measured across `en, fr, ru, zh`. Rotation, compression, brightness and contrast turned
out to cost ≤0.03 exact against the clean reference of 0.975. Only two degradations
break recognition:

| Degradation | exact | cer | empty |
| --- | --- | --- | --- |
| blur σ4 | 0.125 | 0.795 | 4 |
| blur σ6 | 0.000 | 1.000 | 2 |
| 25% scale | 0.550 | 0.365 | 2 |
| 15% scale | 0.000 | 0.980 | 5 |
| blur σ3 + JPEG 10 | 0.375 | 0.530 | 2 |

Four preprocessing pipelines were then scored on those failing cases. Improvements
above 0.01 exact: upscale 4/10, sharpen 2/10, autocontrast 1/10, combined 1/10 — and
each came with regressions elsewhere:

| Case | off | upscale | autocontrast | combined |
| --- | --- | --- | --- | --- |
| JPEG 5 | 0.950 | −0.058 | **−0.225** | **−0.308** |
| 25% scale | 0.550 | **−0.183** | −0.175 | −0.217 |
| rotate 15° | 0.958 | +0.042 | **−0.308** | +0.017 |
| blur σ3 + JPEG 10 | 0.375 | **−0.250** | **−0.375** | **−0.375** |

Where a pipeline helped, the case was already unusable (blur σ4: 0.125 → 0.250). Where
it hurt, it damaged cases that were working. So `preprocess` is not implemented, and
`preprocess=true` now returns `400 preprocess_unsupported` rather than a misleading 200.
Full data in [`docs/robustness.md`](robustness.md).

### Verification

| Check | Result |
| --- | --- |
| `ruff format --check .` / `ruff check .` | Passed, 37 files |
| `pytest -m "not integration"` | Passed, **133 tests** (was 125) |
| Robustness benchmark, packaged tool | Reproduced the findings independently |

Against real models over HTTP with authentication enabled:

| Request | Result |
| --- | --- |
| `preprocess` omitted | 200 — `Bonjour \| Test français \| Reconnaissance OCR` |
| `preprocess=false` | 200 — identical text |
| `preprocess=true` | 400 `preprocess_unsupported` |

### Caveat

Degradations are synthetic and applied programmatically. Real capture blur is
directional rather than Gaussian, and photographs add perspective rather than pure
rotation. These numbers bound the failure envelope on controlled inputs and support
the preprocessing decision; they do not replace evaluation on real photographed
documents. The conclusion is tied to paddleocr 3.7.0, which is why the benchmark
ships with the repository.

---

## Round 3 — per-language accuracy benchmark (2026-09-05)

Host: macOS arm64, Python 3.12.14, paddleocr 3.7.0, paddlepaddle 3.3.1.

### Why this round exists

Round 2 proved each language *loads a model* and returns HTTP 200. That is not the
same as recognising text correctly. A benchmark scoring real images against known
text was added, and it immediately found a defect the earlier checks had missed.

### Fixtures recovered

`main` carried 70 labelled images across 34 languages under `accuracy_test/`, with
expected text for 64 of them. The refactor branch deleted that directory along with
its one-off run reports. The reports were genuinely disposable; the labelled images
were not — they are the only ground truth in the repository, and they cover exactly
the Latin and Cyrillic languages whose mapping was broken.

They now live in `benchmarks/accuracy_dataset/` with image references rewritten from
absolute `/root/lhy/paddleocr/...` paths to names relative to `images/`. The `latin`
entry was dropped: it is a model prefix, not a language.

### A defect the benchmark found

Serbian failed on **both** images with `422 unsupported_language`. The round 2
catalogue defined `sr-Latn` and `sr-Cyrl` but no bare `sr`, so callers using the
plain ISO code were rejected even though PaddleOCR ships both Serbian models.
PaddleOCR has no bare `sr` either, so it needed an explicit mapping: `sr` now
resolves to `rs_latin`, the more common written form, with `sr-Cyrl` still
available. Serbian scores 0.90 exact / 0.005 CER after the fix.

### A defect in the measurement itself

The first scorer reported `exact=1.00` alongside `cer≈0.6` for Greek and Dutch —
self-contradictory. The cause was in the benchmark, not the service: it joined all
lines and compared them positionally, so output that was perfectly correct but
returned bottom-to-top was charged a large error rate. Detection order is not part
of the API contract. The scorer now pairs each expected line with its closest
recognised line before measuring; both languages score CER 0.000. Seventeen unit
tests in `tests/unit/test_accuracy_scorer.py` pin this, including the exact Greek
and Dutch sequences.

### Results: 32 languages, 64 images, 0 failures

Every language returns text. Perfect scores (`exact` 1.00, CER 0.000) for: af, be,
cs, cy, de, el, en, es, et, fr, ga, it, lt, nl, oc, pl, pt, sk, sq, sw, uz, zh.

Remaining variance, all traced to character confusions in the recogniser rather
than to service behaviour:

| Language | exact | CER | Cause |
| --- | --- | --- | --- |
| hr, hu, ru, sl, sr, th | 0.90 | ≤0.010 | one confusable character |
| ja, ko | 0.80 | ≤0.033 | line segmentation on the denser image |
| is | 0.73 | 0.022 | `þ` read as `p` |
| uk | 0.73 | 0.024 | Cyrillic `О`/`С` read as Latin `O`/`C` |

The Russian case is representative: `OCR распознавание` comes back with a Cyrillic
`С` in place of the Latin `C`. One character, so `exact` drops to 0.80 while CER
stays at 0.006 — which is why both metrics are reported.

Languages that previously returned 503 for every request now score:

| Language | exact | CER |
| --- | --- | --- |
| fr | 1.00 | 0.000 |
| de | 1.00 | 0.000 |
| es | 1.00 | 0.000 |
| pt | 1.00 | 0.000 |
| it | 1.00 | 0.000 |
| nl | 1.00 | 0.000 |
| ru | 0.90 | 0.006 |
| be | 1.00 | 0.000 |
| uk | 0.73 | 0.024 |

### Fast checks

| Command | Result |
| --- | --- |
| `ruff format --check .` | Passed, 37 files |
| `ruff check .` | Passed |
| `pytest -m "not integration"` | Passed, **125 tests** |
| Language catalogue vs installed PaddleOCR | 78/78 resolve |

### Caveat on these numbers

The fixtures are synthetic and cleanly rendered, so the scores are an upper bound.
They confirm each language is served end to end and will catch a regression in the
language mapping; they say nothing about photographed documents, skew, handwriting
or low resolution.

---

## Round 2 — language mapping fix and packaging (2026-09-05)

Host: macOS arm64 (Apple Silicon), Python 3.12.14, Docker server 29.7.2.
Runtime under test: paddleocr 3.7.0, paddlepaddle 3.3.1.

### The defect that was found and fixed

The previous revision mapped several caller languages onto **recognition-model
prefixes** rather than PaddleOCR language codes:

| Request language | Previous `lang` passed to PaddleOCR | Result |
| --- | --- | --- |
| `fr`, `de`, `es`, `pt`, `it`, `nl`, … | `latin` | always failed |
| `ru`, `be`, `uk` | `cyrillic` | always failed |

`PaddleOCR(lang=...)` expects a language code. `latin` and `cyrillic` are derived
internally from that code and are not accepted as input. Reproduced against the
installed build:

```text
latin:    ValueError: No models are available for lang='latin' and ocr_version=None.
cyrillic: ValueError: No models are available for lang='cyrillic' and ocr_version=None.
```

Every request for those languages therefore returned `503 model_unavailable`. Only
`zh`, `zh-Hant`, `en`, `ja`, `ko`, `th` and `la` ever worked.

After the fix, the same languages resolve and load real models:

```text
fr -> 'fr': model loaded OK   (PP-OCRv6_medium_det / PP-OCRv6_medium_rec)
ru -> 'ru': model loaded OK   (PP-OCRv5_server_det / eslav_PP-OCRv5_mobile_rec)
```

The catalogue went from 12 to 78 languages. All 78 `paddle_code` values were
checked against the installed PaddleOCR: **0 unresolvable**.

An unknown language is now rejected at the request boundary with
`422 unsupported_language` instead of surfacing later as a `503`, and a bad
`POLYOCR_DEFAULT_LANGUAGE` fails at application startup.

### Fast checks

| Command | Result |
| --- | --- |
| `python -m ruff format --check .` | Passed, 35 files |
| `python -m ruff check .` | Passed |
| `python -m pytest -m "not integration"` | Passed, 98 tests (was 28) |
| `python -m build` | Passed, sdist + wheel |
| `python -m twine check dist/*` | Passed for both distributions |

Fast tests use fake OCR and translation backends: no model downloads, no network.

### Language catalogue against real PaddleOCR

`pytest tests/integration/test_language_catalogue.py -m integration` passed (2 tests).
It confirms every declared `paddle_code` resolves to a detection/recognition model
pair, and that the model prefixes still do *not* resolve — which is the assumption
the fix depends on. It reads PaddleOCR metadata only and downloads no weights.

### Real OCR over HTTP

Authentication enabled, real models, `TestClient` against the app factory:

| Fixture | Language | Status | Recognised text |
| --- | --- | --- | --- |
| `benchmarks/simple_dataset/en.jpg` | `en` | 200 | `Hello World | OCR Test | English Text Recognition` |
| `benchmarks/simple_dataset/zh.jpg` | `zh` | 200 | `中文文字识别 | OCR准确率测试 | 多语言支持` |
| `benchmarks/simple_dataset/ja.jpg` | `ja` | 200 | `こんにちは | 日本語テスト | OCR認識テスト` |

Boundary behaviour in the same run:

| Case | Status | Error code |
| --- | --- | --- |
| No API key | 401 | `unauthorized` |
| Corrupt image bytes | 422 | `invalid_image` |
| Unknown language | 422 | `unsupported_language` |

`GET /v1/health` then reported `models_loaded: ['ch', 'en', 'japan']`, confirming the
cache is keyed by resolved PaddleOCR code.

### Packaging

The wheel was installed into a clean virtual environment and inspected:

| Check | Result |
| --- | --- |
| `License-Expression` metadata | `Apache-2.0` |
| `LICENSE` and `NOTICE` in `dist-info/licenses/` | Present |
| `polyocr/py.typed` packaged | Present |
| `polyocr/web/*.html` packaged | Present |
| `polyocr-service` console script | Registered and `--help` runs |
| `polyocr.__version__` vs distribution metadata | Both `0.3.0` |

The version is now read from distribution metadata, so `pyproject.toml` is the only
place it is declared.

### Container

**Not rebuilt in this environment.** Docker Hub was unreachable from this host
(`registry-1.docker.io` timed out after 25s while PyPI returned HTTP 200), so
`docker build` could not resolve the base image. The base image is therefore left at
the tag verified in round 1, `python:3.10.16-slim-bookworm`.

One container change was still required and was verified without Docker. Because
`pyproject.toml` now declares `license-files = ["LICENSE", "NOTICE"]`, those files
must exist in the build context. Building the same project with and without them:

| Build context | Outcome |
| --- | --- |
| With `LICENSE` and `NOTICE` | Wheel contains `dist-info/licenses/LICENSE` and `NOTICE` |
| Without them | Build **succeeds** with only `Pattern 'LICENSE' did not match any files.`; wheel contains no license files at all |

The failure mode is silent, not fatal: the image would install a distribution with
`License-Expression: Apache-2.0` but no license or attribution text, which does not
satisfy Apache-2.0 section 4(d). `COPY` in the Dockerfile was extended accordingly,
and `tests/test_container_contract.py` now fails if a file declared in
`license-files` is not copied into the image.

The container build and its `/v1/health` check still need to be run where Docker Hub
is reachable; CI performs both.

### Not covered in this environment

Docker Hub was unreachable, so the container image was not rebuilt (see above); CI
covers the build and a `/v1/health` smoke check. No GPU was available, so PaddleOCR-VL
inference was not executed; only its authentication, URL-rejection and upload-limit
boundaries are covered by fast tests. No throughput or accuracy benchmark was run.

---

## Round 1 — initial engineering pass (2026-09-01)

Verified implementation revision: `a5cec61` plus that record.
Host: macOS arm64, Python 3.10.20, Docker server 29.7.2, container Linux arm64 with
Python 3.10.16.

| Command | Result |
| --- | --- |
| `python3 -m ruff format --check .` | Passed, 31 files already formatted |
| `python3 -m ruff check .` | Passed |
| `python3 -m pytest -m "not integration" -q` | Passed, 28 tests; 1 integration test deselected |
| `python3 -m build` | Passed; sdist and wheel include both Web HTML assets |
| Application factory import with `POLYOCR_AUTH_ENABLED=false` | Passed |

`docker build` passed after adding the runtime libraries required by OpenCV. That image
used PaddlePaddle 3.2.2 and PaddleOCR 3.7.0. The first fixed-image run failed because
OpenCV could not load `libGL.so.1`; a failing container contract test was added,
`libgl1` and `libglib2.0-0` were installed, and the image was rebuilt. The container
then processed `benchmarks/simple_dataset/en.jpg` and printed:

```text
hello world ocr test english text recognition
```

A container startup check exposed port 8000 and `/v1/health` returned:

```json
{"status":"ok","service":"PolyOCR Service","models_loaded":[]}
```

No performance benchmark or PaddleOCR-VL GPU inference was run in that environment.
