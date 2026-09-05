# Changelog

All notable changes to this project are documented here. This project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **`preprocess` was accepted and silently discarded.** `POST /v1/ocr` advertised a
  `preprocess` flag in its OpenAPI schema, returned HTTP 200, then dropped it with
  `del preprocess`. Callers had no way to tell that nothing happened, and three
  scripts in `benchmarks/` sent `preprocess=true`. It now returns
  `400 preprocess_unsupported` pointing at `docs/robustness.md`; `preprocess=false`
  and omitting the field behave as before.
- `benchmarks/run_benchmark.py` leaked a file handle per request by passing an
  unclosed `open()` into `requests.post`.

### Added

- **Robustness benchmark** (`benchmarks/run_robustness_benchmark.py`) measuring
  accuracy under 17 controlled degradations, with `--compare-preprocess` to score
  candidate preprocessing pipelines. Findings in `docs/robustness.md`.
- `docs/robustness.md`: measured failure profile and the evidence behind not
  implementing `preprocess`. Rotation, JPEG compression, brightness and contrast cost
  ≤0.03 exact against the clean reference; only blur beyond ~σ2 and downscaling past
  ~25% break recognition, and both fail by returning no text rather than wrong text.
  Of four preprocessing pipelines across ten degradations, none was a net win —
  autocontrast dropped quality-5 JPEG from 0.950 to 0.725 exact, and upscaling dropped
  25%-scale text from 0.550 to 0.367.

## [0.3.0] - 2026-09-05

### Fixed

- **OCR failed for every Latin and Cyrillic language.** `fr`, `de`, `es`, `pt`, `it`,
  `nl`, `ru`, `be` and `uk` were mapped to `latin` / `cyrillic` and passed to
  `PaddleOCR(lang=...)`. Those are recognition-model prefixes, not language codes, so
  PaddleOCR raised `ValueError: No models are available for lang='latin'` and the API
  returned `503 model_unavailable` for every such request. All languages are now mapped
  to codes PaddleOCR accepts, verified against the installed build.
- **Serbian was unreachable by its ISO code.** The catalogue defined `sr-Latn` and
  `sr-Cyrl` but no bare `sr`, so `language=sr` returned `422`. PaddleOCR has no bare
  `sr` either, so it is now mapped explicitly to `rs_latin`, with `sr-Cyrl` still
  available for Cyrillic Serbian. Found by the new accuracy benchmark.
- An unknown `language` now returns `422 unsupported_language` at the request boundary
  instead of failing later during model loading.
- A misconfigured `POLYOCR_DEFAULT_LANGUAGE` now fails at startup instead of making
  every request that omits `language` fail.
- `benchmarks/evaluate_results.py` read `response["data"]`, which the API no longer
  returns, so it reported zero recognised text for every image. It now reads `items`
  and still accepts the older `data` shape.
- The Dockerfile did not copy `LICENSE` / `NOTICE`, which `pyproject.toml` declares as
  `license-files`. The image silently installed a distribution with no license or
  attribution text.

### Added

- Apache-2.0 `LICENSE` matching upstream PaddleOCR, plus a `NOTICE` file carrying the
  upstream attribution required by section 4(d). The repository previously shipped no
  license at all, which left redistribution rights undefined.
- Language coverage expanded from 12 to 78 languages across the Han, Japanese, Hangul,
  Latin, Cyrillic, Arabic, Devanagari, Thai, Greek, Georgian, Tamil and Telugu scripts.
- Language aliases: `fr`, `french` and `法文` all resolve to French. `GET /v1/languages`
  now returns each language's PaddleOCR code, script and accepted aliases.
- **Per-language accuracy benchmark** (`benchmarks/run_accuracy_benchmark.py`) scoring
  recognition against ground truth, reporting exact line match and character error
  rate independently of detection order. Runs in-process or over HTTP against a
  deployment. Current results: 32 languages, 64 images, 0 failures.
- 64 labelled images across 32 languages in `benchmarks/accuracy_dataset/`, recovered
  from `accuracy_test/` on `main` with portable relative paths. The dated one-off run
  reports that accompanied them were not carried over.
- `polyocr-service` console entry point, so an installed distribution can be started
  without the `--factory` uvicorn invocation.
- `py.typed` marker, so downstream type checkers use the package's annotations.
- Packaging metadata: license expression, keywords, trove classifiers and project URLs.
- 97 new tests (28 to 125), covering the language contract, boundary validation, the
  packaging contract, the container's license handling and the benchmark scorer. A new
  integration test checks the language catalogue against real PaddleOCR metadata
  without downloading model weights.
- CI: `twine check` on built distributions, an offline language-catalogue job, and a
  container smoke test that asserts `/v1/health` responds.

### Changed

- `__version__` is read from distribution metadata, making `pyproject.toml` the single
  source of truth. It was previously duplicated in three files.
- Removed the unused `error_schema()` helper and the `log_level` setting that nothing
  read. Log level is now a `polyocr-service --log-level` option.

## [0.2.0] - 2026-09-01

### Fixed

- Removed hardcoded API keys and translation credentials from the source tree.
- Replaced the wildcard CORS policy, which was unsafe with credentialed requests.
- Replaced silent `except` blocks that turned failures into empty successful responses.
- Added the OpenCV runtime libraries the image needs (`libgl1`, `libglib2.0-0`).

### Changed

- Restructured a flat script layout into the `src/polyocr` package with an installable
  `pyproject.toml`, split into API, core, services and schema layers.
- Unified all failures onto a single `error` response shape with a request ID.
- Moved blocking inference into a worker pool behind a concurrency semaphore.
- Added byte-size, pixel-count and image-validity limits ahead of inference.
- Rendered browser results with `textContent` instead of `innerHTML`.
