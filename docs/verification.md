# PolyOCR Service verification

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
