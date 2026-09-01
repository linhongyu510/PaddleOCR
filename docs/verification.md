# PolyOCR Service verification

Date: 2026-09-01  
Verified revision: `36c6c6730c3cbe93815e3585cb07305ce2cce113` plus this record  
Host: macOS arm64  
Host Python: 3.10.20  
Docker server: 29.7.2  
Container: Linux arm64, Python 3.10.16

## Fast checks

| Command | Result |
| --- | --- |
| `python3 -m ruff format --check .` | Passed, 32 files already formatted |
| `python3 -m ruff check .` | Passed |
| `python3 -m pytest -m "not integration" -q` | Passed, 27 tests; 1 integration test deselected |
| `python3 -m build` | Passed; sdist and wheel built |
| Application factory import with `POLYOCR_AUTH_ENABLED=false` | Passed |

The fast tests used fake OCR and translation backends. They did not download models or call
external translation services.

## Container and fixed-image OCR

`docker build -t polyocr-service:review .` passed after adding the runtime libraries required
by OpenCV. The final image used PaddlePaddle 3.2.2 and PaddleOCR 3.7.0.

The first fixed-image run failed before inference because OpenCV could not load
`libGL.so.1`. A failing container contract test was added, `libgl1` and `libglib2.0-0` were
installed in the image, and the image was rebuilt.

The final container OCR command processed `benchmarks/simple_dataset/en.jpg` through
PaddleOCR 3.x `predict()`. It downloaded the official models and exited successfully with:

```text
hello world ocr test english text recognition
```

A separate container startup check exposed port 8000, called `/v1/health`, and returned:

```json
{"status":"ok","service":"PolyOCR Service","models_loaded":[]}
```

No performance benchmark or PaddleOCR-VL GPU inference was run in this environment.
