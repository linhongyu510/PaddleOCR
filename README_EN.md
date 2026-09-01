# PolyOCR Service

[简体中文](README.md)

A multilingual OCR API powered by PaddleOCR 3.x, with optional translation and a separate
PaddleOCR-VL deployment. This is a community project, not an official PaddleOCR component.

## Capabilities and boundaries

- Base OCR calls PaddleOCR 3.x `predict()` and normalizes both 3.x mapping/object results and
  legacy list results.
- Byte size, decoded pixel count, image validity, and score thresholds are checked before
  inference.
- Blocking inference runs in a worker pool behind a concurrency semaphore.
- Translation requests have item and total-character limits; provider output must preserve
  the input count.
- HTTP, authentication, validation, and domain failures share one `error` response shape.
- PaddleOCR-VL accepts uploaded content only, rejects URLs, requires a separate API key, and
  enforces an upload limit.
- Browser pages render remote results with `textContent`, never as executable HTML.

Fast tests neither download models nor access the public network. Real OCR downloads model
assets and runs only when its integration test is explicitly enabled. PaddleOCR-VL requires
a separately prepared, mutually compatible GPU, driver, CUDA, and inference stack.

## Installation

CI covers Python 3.10, 3.11, and 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,ocr]"
cp .env.example .env
```

Replace the sample API keys in `.env`, then start the service:

```bash
uvicorn polyocr.main:create_app --factory --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/` for the web client or `/docs` for the API documentation.

## API

The health endpoint does not require authentication:

```bash
curl http://localhost:8000/v1/health
```

OCR accepts either `X-API-Key` or a Bearer token:

```bash
curl -X POST http://localhost:8000/v1/ocr \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -F "file=@benchmarks/simple_dataset/en.jpg" \
  -F "language=en" \
  -F "score_threshold=0.5"
```

Translation:

```bash
curl -X POST http://localhost:8000/v2/translate \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts":["Hello"],"target_language":"zh"}'
```

All failures use the same envelope:

```json
{
  "error": {
    "code": "invalid_image",
    "message": "Uploaded file could not be decoded as an image.",
    "request_id": "..."
  }
}
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `POLYOCR_AUTH_ENABLED` | `true` | Enables authentication for base business endpoints |
| `POLYOCR_API_KEY` | none | Required when base authentication is enabled |
| `POLYOCR_CORS_ORIGINS` | `http://localhost:8000` | Comma-separated allowed origins |
| `POLYOCR_MAX_UPLOAD_MB` | `10` | OCR upload byte limit |
| `POLYOCR_MAX_IMAGE_PIXELS` | `25000000` | Decoded image pixel limit |
| `POLYOCR_MAX_CONCURRENCY` | `2` | Concurrent OCR inference limit |
| `POLYOCR_OCR_WORKERS` | `2` | OCR worker thread count |
| `POLYOCR_MAX_TRANSLATION_ITEMS` | `50` | Translation item limit |
| `POLYOCR_MAX_TRANSLATION_CHARS` | `20000` | Translation total-character limit |
| `TRANSLATION_API_KEY` | none | OpenAI-compatible provider key |
| `TRANSLATION_BASE_URL` | OpenAI API | Translation provider base URL |
| `TRANSLATION_MODEL` | `gpt-4o-mini` | Translation model |
| `POLYOCR_VL_API_KEY` | none | Required key for the separate VL service |
| `POLYOCR_VL_MAX_UPLOAD_MB` | `20` | VL upload limit |

The application automatically reads `.env` from its current directory. Never commit `.env`
or real secrets. The base service refuses to start when authentication is enabled without
`POLYOCR_API_KEY`; the VL service always requires `POLYOCR_VL_API_KEY`. Credentialed CORS
cannot use a wildcard origin.

## Docker

```bash
export POLYOCR_API_KEY='replace-with-a-secret'
docker compose up --build
```

The image pins a Python 3.10 baseline, runs as a non-root user, and includes a health check.
The first OCR request downloads model assets into the Compose cache volume.

## PaddleOCR-VL

See [`deployment/paddleocr-vl/README.md`](deployment/paddleocr-vl/README.md).
The VL endpoint does not fetch remote URLs. Clients upload a base64 file and provide the
separate VL credential.

## Tests and verification

```bash
python -m ruff format --check .
python -m ruff check .
python -m pytest -m "not integration"
python -m build
```

Run the fixed-image real OCR E2E explicitly:

```bash
POLYOCR_RUN_OCR_E2E=1 python -m pytest tests/integration/test_real_ocr.py -q
```

This command may download model assets. Container commands and observed results for this
revision are recorded in [`docs/verification.md`](docs/verification.md). CI runs only fast,
offline tests across Python 3.10–3.12.

## License

The repository currently has no license file. The repository owner must choose one before
release.
