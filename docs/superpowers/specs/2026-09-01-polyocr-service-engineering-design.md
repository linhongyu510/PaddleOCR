# PolyOCR Service 工程化改造设计

## 背景

当前仓库实现了基于 PaddleOCR 的多语言 OCR API、翻译接口、Web 页面，以及独立的 PaddleOCR-VL 版面解析部署，但所有内容集中在一次初始提交中。根目录缺少项目级 README、许可证、工程配置和自动化质量门禁；业务代码、部署脚本、运行日志、缓存文件、测试图片与测试报告混合存放。

仓库还在 Python、Shell、HTML、YAML 和 Markdown 文件中硬编码了 API Key、Secret、内网地址及公网服务器地址。工程化改造必须先建立安全边界，再整理架构、测试、部署和文档，不能直接把现状包装成已达到生产标准的项目。

## 目标

将仓库整理为名为 **PolyOCR Service** 的开源作品集项目，并明确标注其为社区项目、由 PaddleOCR 驱动，不代表 PaddleOCR 官方项目。

交付目标：

- 保留基础 OCR、语言查询、健康检查和翻译能力。
- 使用标准 Python 包结构拆分配置、API、服务与数据模型。
- 清除仓库当前版本中的硬编码凭据和固定部署地址。
- 提供可复制的本地启动、CPU Docker 启动和测试流程。
- 建立不下载 OCR 模型即可运行的快速测试与 CI 门禁。
- 将 PaddleOCR-VL 作为可选高级部署，与基础服务解耦。
- 提供中文主 README `README.md` 和英文版 `README_EN.md`。
- README 采用“产品展示 + 工程可信度”的混合表达，但只展示可复现或明确限定的能力。

## 非目标

- 不重写 PaddleOCR 推理框架。
- 不承诺所有 PaddleOCR 语言模型在所有硬件上均可用。
- 不把历史测试报告直接当作当前版本性能证明。
- 不在本轮实现用户系统、数据库、计费、任务队列或分布式模型服务。
- 不自动撤销第三方服务中的已泄露凭据，也不默认重写公开 Git 历史。
- 不声称基础 CPU 镜像支持 PaddleOCR-VL 所需的 GPU 推理链路。

## 实施策略

采用渐进式模块化重构，而非在原文件上继续堆叠或全面重写：

1. 建立安全基线和测试支点。
2. 按现有接口契约抽取模块。
3. 迁移前端与部署配置。
4. 建立容器、CI 和文档。
5. 只在验证完成后写入性能和兼容性结论。

迁移期间尽量保留现有公开路径。若旧接口行为存在安全问题或无法形成稳定契约，则以明确的迁移说明代替隐式兼容。

## 目标结构

```text
.
├── src/polyocr/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── errors.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── languages.py
│   │       ├── ocr.py
│   │       └── translation.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── ocr.py
│   │   └── translation.py
│   ├── services/
│   │   ├── languages.py
│   │   ├── model_manager.py
│   │   ├── ocr.py
│   │   └── translation.py
│   ├── __init__.py
│   └── main.py
├── web/
├── tests/
│   ├── api/
│   ├── unit/
│   └── conftest.py
├── benchmarks/
├── deployment/
│   └── paddleocr-vl/
├── docs/
├── .github/workflows/ci.yml
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── README_EN.md
```

`src/polyocr` 是唯一的基础服务运行代码位置。`web` 只存放静态页面及资源；`deployment/paddleocr-vl` 保留高级部署；`benchmarks` 只保留生成器、固定小数据集、执行脚本和经过说明的摘要，不提交批量生成结果。

## 应用架构

### API 层

API 层负责 HTTP 参数解析、认证依赖、响应模型和错误映射，不直接创建 PaddleOCR 模型或调用翻译供应商。计划保留以下端点：

- `GET /`
- `GET /v1/health`
- `GET /v1/languages`
- `GET /v1/languages/paddleocr`
- `POST /v1/ocr`
- `POST /v1/translation/translate`
- `GET /v1/translation/health`
- `GET /v1/translation/languages`
- `POST /v2/translate`

旧的运行时翻译配置读写端点默认不保留，因为它可能暴露或动态覆盖敏感配置。如果确认必须兼容，则只能返回脱敏配置，并要求认证；任何响应都不得包含密钥。

### 服务层

OCR 服务负责图像解码、可选预处理、模型调用和结果归一化。模型管理器按规范化后的模型标识缓存实例，避免当前语言代码与模型名称混用造成缓存失效。

语言服务维护唯一、去重且有测试覆盖的语言别名表。未知语言返回可预测的客户端错误，不再静默回退到中文模型；模型加载失败返回服务错误，并记录不含敏感信息的诊断日志。

翻译服务通过协议接口封装外部 OpenAI 兼容供应商。未配置翻译密钥时，OCR 服务仍可启动，但翻译健康检查显示为未配置，翻译请求返回明确的功能不可用错误。

### Schema 与错误

所有公开接口使用 Pydantic Schema。错误响应至少包含：

```json
{
  "error": {
    "code": "invalid_image",
    "message": "Uploaded file is not a supported image.",
    "request_id": "..."
  }
}
```

错误消息不包含本地路径、密钥、上游完整响应或 Python 堆栈。服务日志通过 `request_id` 与响应关联。

## 配置与安全

配置从环境变量读取，并提供不含真实值的 `.env.example`。核心变量：

- `POLYOCR_API_KEY`
- `POLYOCR_AUTH_ENABLED`
- `POLYOCR_CORS_ORIGINS`
- `POLYOCR_MAX_UPLOAD_MB`
- `POLYOCR_DEFAULT_LANGUAGE`
- `POLYOCR_LOG_LEVEL`
- `TRANSLATION_API_KEY`
- `TRANSLATION_BASE_URL`
- `TRANSLATION_MODEL`

生产模式启用认证时，空 API Key 必须阻止应用启动。API Key 使用 `secrets.compare_digest` 比较。开发者可显式设置 `POLYOCR_AUTH_ENABLED=false` 关闭本地认证，但 Docker 示例默认启用认证并要求用户自行设置密钥。

CORS 来源通过逗号分隔的明确列表配置。启用凭据时不允许通配来源。上传入口先验证声明类型、文件扩展名、文件大小和实际解码结果，再进入模型推理；无法解码、超限或参数越界均返回 `4xx`。

仓库当前暴露的密钥必须由所有者在对应服务侧撤销和轮换。本轮提交移除当前树中的明文，但公开 Git 历史仍可能保留旧值。历史重写属于独立、高影响操作，执行前需确认仓库协作者与分支策略。

## 前端

现有静态页面迁入 `web` 并统一使用 **PolyOCR Service** 品牌。浏览器请求默认使用同源相对路径；需要分离部署时，通过公开的非敏感运行时配置设置 API Base URL。

前端不得嵌入 API Key。需要认证的公开部署应由用户在界面临时输入密钥并仅保存在内存中，或由可信反向代理注入认证；默认实现优先采用临时输入方式。界面展示上传状态、请求失败原因、识别结果和可选翻译结果。

本轮以整理现有页面、去除硬编码地址和保证基础可用为主，不进行全新前端框架迁移。

## PaddleOCR-VL 部署

`paddleocr_vl_deployment` 移至 `deployment/paddleocr-vl`。其配置中的服务器地址、VLM 地址和硬件参数均改为环境变量或示例值。

基础服务的 CPU Docker 镜像不包含 PaddleOCR-VL、vLLM 或 SGLang。高级部署文档必须单独说明 GPU、驱动、CUDA、显存、模型服务和网络依赖，并避免把特定显卡型号写成未经验证的兼容承诺。

## 测试

采用测试优先迁移。快速测试不得下载模型或访问公网，使用依赖注入和假模型覆盖：

- 配置默认值与非法组合。
- API Key 缺失、错误和正确三种路径。
- 常量时间认证比较的调用边界。
- CORS 配置约束。
- 语言别名规范化、去重和未知语言错误。
- 模型缓存键一致性与加载失败传播。
- 新旧 PaddleOCR 结果结构的归一化。
- 文件大小、类型、损坏图片和阈值校验。
- OCR、健康检查和翻译未配置时的 HTTP 契约。
- 错误响应不泄露密钥、路径和堆栈。

可选集成测试允许下载真实 PaddleOCR 模型，并使用固定的小型样本验证端到端推理。它不进入默认 CI，需通过显式标记运行。

## 工具链与 CI

使用 `pyproject.toml` 定义项目元数据、运行依赖、开发依赖、Ruff 和 pytest 配置。目标支持版本在实施阶段依据 PaddlePaddle 与 PaddleOCR 的实际兼容矩阵确定，README 只列出验证过的 Python 版本。

GitHub Actions 快速流程：

1. 安装不包含模型资产的测试环境。
2. 运行 Ruff 格式与静态检查。
3. 运行 pytest 快速测试。
4. 搜索已知硬编码凭据模式和禁止提交的运行产物。
5. 构建 CPU Docker 镜像，至少验证应用模块可导入及健康检查配置。

CI 不把部署端口扫描或历史报告存在视为功能测试通过。

## 容器化

Dockerfile 使用非 root 用户运行服务，明确工作目录、依赖层和健康检查。`docker-compose.yml` 提供基础 OCR 服务示例，通过 `.env` 注入配置，并挂载可选模型缓存目录。

由于 PaddlePaddle 安装包与平台、CPU 指令集及 GPU 环境相关，Docker 构建将选择一个明确验证的 CPU 基线。GPU 与 Apple Silicon 本地安装差异在文档中分别说明，不使用“任意平台一键运行”的表述。

## 仓库清理

删除或停止跟踪：

- `__pycache__`、`.pyc` 和运行日志。
- 带真实地址或凭据的部署脚本与测试配置。
- 重复的临时测试图片。
- 批量生成的测试结果、HTML 报告和中间 CSV。
- 无法追溯生成命令或数据来源的性能图。

保留：

- 少量许可证清晰的示例图片。
- 可复现的数据生成脚本。
- 小型固定基准数据集及清晰的 manifest。
- 生成报告的方法，而不是大量历史产物。

`.gitignore` 覆盖缓存、虚拟环境、日志、`.env`、模型文件、上传目录和生成报告。

## README 设计

`README.md` 使用中文，顶部链接到 `README_EN.md`；英文版保持相同信息结构。

信息层级：

1. 居中的 PolyOCR Service 标题、简短定位、状态徽章和非官方声明。
2. Web 效果图或经过验证的结果预览。
3. 基础 OCR、翻译、Web UI、API、基准工具和可选 VL 部署能力。
4. 架构图，区分基础服务与可选外部翻译、VLM 服务。
5. 本地快速开始和 Docker 快速开始。
6. OCR 与翻译请求示例。
7. 配置表和安全说明。
8. 测试、基准与复现命令。
9. PaddleOCR-VL 高级部署入口。
10. 路线图、贡献方式、许可证及致谢。

README 不展示真实服务器地址或凭据，不声称项目是 PaddleOCR 官方组件。性能数字只有在同一提交、明确硬件、固定数据集和可复现命令下重新测量后才会出现。

## 验收标准

- 仓库当前树中不存在已发现的 API Key、Secret、固定公网 IP 和内网 IP。
- `README.md` 与 `README_EN.md` 中的命令可在支持环境按说明执行。
- 应用可从 `polyocr.main` 的工厂函数或稳定入口启动。
- 快速测试不下载模型、不访问公网并全部通过。
- Ruff 检查通过。
- CPU Docker 镜像构建成功，健康检查可执行。
- 未配置翻译服务时 OCR 能力仍可使用，翻译端点返回明确错误。
- 前端不包含密钥且不绑定特定服务器。
- PaddleOCR-VL 与基础服务的依赖、配置和文档边界清晰。
- README 中的能力与测试证据一致，没有引用无法复现的历史性能结论。

## 风险与缓解

- PaddleOCR 版本间结果结构差异：通过归一化层和多结构契约测试隔离。
- 模型下载导致测试慢或不稳定：默认 CI 使用假模型，真实推理单独标记。
- 大规模移动文件造成回归：先建立关键行为测试，再逐模块迁移。
- 公开密钥已被复制：立即在供应商侧轮换；代码清理不能替代密钥撤销。
- 历史重写破坏协作者分支：本轮不自动执行，另行确认后处理。
- 旧部署脚本依赖特定服务器：改为参数化模板，无法通用化的脚本进入归档或删除。

## 实施顺序

1. 创建独立改造分支并记录安全事件。
2. 添加 `.gitignore`、`.env.example`、项目配置和测试骨架。
3. 先写配置、认证、语言和结果归一化测试。
4. 抽取核心模块并迁移 API。
5. 迁移前端，移除硬编码地址和密钥。
6. 整理 PaddleOCR-VL 部署。
7. 清理生成物、日志和重复资产。
8. 添加 Docker 与 CI。
9. 运行快速测试、静态检查、密钥扫描和容器验证。
10. 基于验证结果编写中英文 README。
