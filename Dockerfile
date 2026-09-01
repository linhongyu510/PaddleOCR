FROM python:3.10.16-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 polyocr

COPY pyproject.toml README.md ./
COPY src ./src
COPY benchmarks/simple_dataset/en.jpg ./tests/fixtures/en.jpg

RUN python -m pip install --upgrade pip \
    && python -m pip install ".[ocr]"

USER polyocr

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/v1/health', timeout=3)"

CMD ["uvicorn", "polyocr.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
