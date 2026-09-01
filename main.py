"""Compatibility entry point.

New deployments should run ``uvicorn polyocr.main:create_app --factory``.
"""

from polyocr.main import create_app

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("polyocr.main:create_app", factory=True, host="0.0.0.0", port=8000)
