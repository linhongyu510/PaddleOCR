# PaddleOCR-VL optional deployment

This GPU-oriented service is separate from the base CPU OCR API.

1. Install this directory's requirements in a compatible PaddlePaddle GPU environment.
2. Set `POLYOCR_VL_API_KEY` and optionally `POLYOCR_VL_MAX_UPLOAD_MB`.
3. From the repository root, run:

```bash
PYTHONPATH=src uvicorn app:create_app \
  --factory \
  --app-dir deployment/paddleocr-vl \
  --host 0.0.0.0 \
  --port 8080
```

`POST /layout-parsing` requires either `X-API-Key` or `Authorization: Bearer`.
The `file` field must contain base64-encoded local file bytes. Remote URL input is rejected
to prevent server-side request forgery. Uploads larger than `POLYOCR_VL_MAX_UPLOAD_MB` are
rejected before inference.

PaddleOCR-VL, its selected backend, GPU drivers, CUDA runtime, and model assets must be
compatible with one another. This repository does not claim support for an untested GPU
combination.
