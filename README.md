# PolyOCR Service

[English](README_EN.md)

基于 PaddleOCR 3.x 的多语言 OCR、可选翻译和独立 PaddleOCR-VL 服务。此仓库是社区项目，
并非 PaddleOCR 官方组件。

## 能力与边界

- 基础 OCR 使用 PaddleOCR 3.x `predict()`，兼容 3.x 映射/对象结果和旧列表结果。
- 支持 78 种语言，覆盖汉字、日文、韩文、拉丁、西里尔、阿拉伯、天城文、泰文、希腊文等
  文字系统，并接受语种码、英文名和中文名三类别名（如 `fr` / `french` / `法文`）。
- 语言在请求边界完成校验：未知语言返回 `422 unsupported_language`，不会延迟到加载模型
  时才失败。
- 图片在推理前接受字节数、解码结果、像素数和置信度阈值校验。
- 同步模型推理在线程池执行，并由信号量限制并发。
- 翻译输入限制条目数和总字符数；供应商返回数量必须与输入一致。
- HTTP、认证、请求校验和领域错误使用统一 `error` 响应。
- PaddleOCR-VL 只接受上传内容，拒绝 URL，要求独立 API Key 并限制上传大小。
- 浏览器页面使用 `textContent` 渲染服务端结果，不把返回内容解释为 HTML。

快速单元测试不下载模型，也不访问公网。真实 OCR 会下载模型，仅在显式启用的集成测试中
运行。PaddleOCR-VL 需要单独准备兼容的 GPU、驱动、CUDA 和推理依赖。

## 安装

支持并由 CI 检查 Python 3.10、3.11 和 3.12。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,ocr]"
cp .env.example .env
```

修改 `.env` 中的 API Key 后启动：

```bash
uvicorn polyocr.main:create_app --factory --host 0.0.0.0 --port 8000
```

安装后也可以直接使用命令行入口（默认监听 `127.0.0.1:8000`）：

```bash
polyocr-service --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/` 使用 Web 页面，API 文档位于 `/docs`。

## API

健康检查不要求认证：

```bash
curl http://localhost:8000/v1/health
```

查询支持的语言（返回语种码、PaddleOCR 语言码、文字系统和可用别名）：

```bash
curl http://localhost:8000/v1/languages
```

OCR 请求支持 `X-API-Key` 或 Bearer Token：

```bash
curl -X POST http://localhost:8000/v1/ocr \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -F "file=@benchmarks/simple_dataset/en.jpg" \
  -F "language=en" \
  -F "score_threshold=0.5"
```

`language` 接受语种码、英文名或中文名，响应中的 `language` 始终回显规范语种码：

```bash
curl -X POST http://localhost:8000/v1/ocr \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -F "file=@image.jpg" \
  -F "language=法文"      # 等价于 fr / french
```

成功响应：

```json
{
  "code": 0,
  "message": "Recognition succeeded.",
  "request_id": "...",
  "cost_ms": 412.7,
  "language": "fr",
  "items": [{"text": "Bonjour", "score": 0.99, "bbox": [12, 8, 96, 34]}]
}
```

翻译：

```bash
curl -X POST http://localhost:8000/v2/translate \
  -H "X-API-Key: $POLYOCR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts":["Hello"],"target_language":"zh"}'
```

失败响应统一为：

```json
{
  "error": {
    "code": "invalid_image",
    "message": "Uploaded file could not be decoded as an image.",
    "request_id": "..."
  }
}
```

## 配置

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `POLYOCR_AUTH_ENABLED` | `true` | 基础业务接口是否启用认证 |
| `POLYOCR_API_KEY` | 无 | 认证启用时必填 |
| `POLYOCR_CORS_ORIGINS` | `http://localhost:8000` | 逗号分隔的允许来源 |
| `POLYOCR_MAX_UPLOAD_MB` | `10` | OCR 上传字节上限 |
| `POLYOCR_MAX_IMAGE_PIXELS` | `25000000` | 解码后像素上限 |
| `POLYOCR_MAX_CONCURRENCY` | `2` | 同时运行的 OCR 推理数 |
| `POLYOCR_OCR_WORKERS` | `2` | OCR 工作线程数 |
| `POLYOCR_MAX_TRANSLATION_ITEMS` | `50` | 单次翻译条目上限 |
| `POLYOCR_MAX_TRANSLATION_CHARS` | `20000` | 单次翻译总字符上限 |
| `TRANSLATION_API_KEY` | 无 | OpenAI 兼容翻译服务密钥 |
| `TRANSLATION_BASE_URL` | OpenAI API | 翻译服务基址 |
| `TRANSLATION_MODEL` | `gpt-4o-mini` | 翻译模型 |
| `POLYOCR_VL_API_KEY` | 无 | 独立 VL 服务必填密钥 |
| `POLYOCR_VL_MAX_UPLOAD_MB` | `20` | VL 上传上限 |

项目会自动读取当前目录的 `.env`。不要提交 `.env` 或真实密钥。认证开启而
`POLYOCR_API_KEY` 为空时，基础服务拒绝启动；VL 服务始终要求 `POLYOCR_VL_API_KEY`。
带凭据的 CORS 配置不允许通配来源。

## Docker

```bash
export POLYOCR_API_KEY='replace-with-a-secret'
docker compose up --build
```

镜像固定 Python 3.10 基线，以非 root 用户运行并提供健康检查。首次 OCR 会下载模型，
模型缓存保存在 Compose volume。

## PaddleOCR-VL

可选部署说明见
[`deployment/paddleocr-vl/README.md`](deployment/paddleocr-vl/README.md)。
VL 接口不抓取远程 URL，调用者必须上传 base64 文件并携带独立认证信息。

## 测试与验证

```bash
python -m ruff format --check .
python -m ruff check .
python -m pytest -m "not integration"
python -m build
```

固定图片真实 OCR E2E：

```bash
POLYOCR_RUN_OCR_E2E=1 python -m pytest tests/integration/test_real_ocr.py -q
```

该命令可能下载模型。容器验证命令和本次实际结果记录在
[`docs/verification.md`](docs/verification.md)。CI 只运行不下载模型的快速测试，并在
Python 3.10–3.12 上执行。

## 许可证

采用 [Apache License 2.0](LICENSE)，与上游 PaddleOCR 保持一致；第三方署名记录在
[`NOTICE`](NOTICE)。

本仓库是基于 PaddleOCR 构建的独立社区服务，并非 PaddleOCR 官方组件。PaddleOCR 模型在运行
时从其原始分发方下载，并受各自许可证与使用条款约束。
