# PaddleOCR-VL 部署指南

本项目提供了PaddleOCR-VL的完整部署方案，支持图像和PDF文档的版面解析。

## 服务器信息
- **服务器IP**: 183.250.90.218
- **服务端口**: 8080
- **API文档**: http://183.250.90.218:8080/docs

## 快速开始

### 1. 环境安装
```bash
# 给安装脚本执行权限
chmod +x install.sh

# 运行安装脚本
./install.sh
```

### 2. 启动服务
```bash
# 给启动脚本执行权限
chmod +x start_server.sh

# 启动服务
./start_server.sh
```

### 3. 测试服务
```bash
# 运行客户端测试
python3 test_client.py
```

## 配置说明

### 服务器配置 (config.yaml)
```yaml
server:
  host: "0.0.0.0"          # 服务监听地址
  port: 8080              # 服务端口
  server_ip: "183.250.90.218"  # 服务器IP

model:
  use_doc_orientation_classify: true   # 文档方向分类
  use_doc_unwarping: true              # 文本图像矫正
  use_layout_detection: true           # 版面区域检测
  use_chart_recognition: true          # 图表识别

inference:
  backend: "vllm-server"               # 推理后端
  server_url: "http://183.250.90.218:8118/v1"  # VLM服务地址
  max_concurrency: 4                   # 最大并发数
```

## API接口

### 版面解析接口
- **URL**: `POST /layout-parsing`
- **功能**: 对图像或PDF进行版面解析
- **参数**:
  - `file`: Base64编码的文件内容或URL
  - `fileType`: 文件类型 (0=PDF, 1=图像)
  - `visualize`: 是否返回可视化结果
  - `prettifyMarkdown`: 是否美化Markdown输出

### 文件上传接口
- **URL**: `POST /upload`
- **功能**: 上传文件并获取Base64编码

### 健康检查接口
- **URL**: `GET /health`
- **功能**: 检查服务状态

## 使用示例

### Python客户端
```python
import requests
import base64

# 读取图像文件
with open("test_image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# 发送请求
payload = {
    "file": image_data,
    "fileType": 1,
    "visualize": True
}

response = requests.post(
    "http://183.250.90.218:8080/layout-parsing",
    json=payload
)

result = response.json()
print(result)
```

### cURL命令
```bash
curl -X POST "http://183.250.90.218:8080/layout-parsing" \
  -H "Content-Type: application/json" \
  -d '{
    "file": "base64_encoded_image_data",
    "fileType": 1,
    "visualize": true
  }'
```

## 性能优化

### GPU要求
- **PaddlePaddle**: Compute Capability ≥ 8.5
- **vLLM**: Compute Capability ≥ 8
- **推荐硬件**: RTX 3060, RTX 5070, A10, A100

### 性能调优参数
```yaml
performance:
  gpu_memory_utilization: 0.8    # GPU内存使用率
  max_num_seqs: 128             # 最大序列数
  temperature: 0.1              # 生成温度
  top_p: 0.9                    # Top-p采样
  repetition_penalty: 1.0       # 重复惩罚
```

## 故障排除

### 常见问题
1. **服务启动失败**: 检查GPU驱动和CUDA环境
2. **内存不足**: 调整`gpu_memory_utilization`参数
3. **连接超时**: 检查网络连接和防火墙设置
4. **模型加载失败**: 确保有足够的磁盘空间和网络连接

### 日志查看
```bash
# 查看服务日志
tail -f app.log

# 查看系统日志
journalctl -u paddleocr-vl
```

## 部署架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户端        │    │   PaddleOCR-VL  │    │   VLM推理服务   │
│                │────│   服务 (8080)   │────│   (8118)        │
│  - 图像上传     │    │                │    │                │
│  - 结果处理     │    │  - 版面解析     │    │  - vLLM/SGLang  │
│                │    │  - 结果返回     │    │  - 模型推理     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 联系信息
- 服务器IP: 183.250.90.218
- 服务端口: 8080
- API文档: http://183.250.90.218:8080/docs
