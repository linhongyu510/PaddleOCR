# OCR准确率测试系统

这是一个完整的OCR识别准确率验证测试系统，支持多种语言的OCR API测试和性能分析。

## 功能特性

- 🌍 **多语言支持**: 支持中文、英文、日文、韩文、泰文、俄文、阿拉伯文、印地文等
- 📊 **全面测试**: 成功率、精确率、召回率、F1分数、字符准确率等多维度评估
- 📈 **可视化报告**: 自动生成HTML报告和性能图表
- 🔧 **灵活配置**: 支持自定义测试图片和期望结果
- ⚡ **批量测试**: 支持批量测试多种语言
- 📋 **详细分析**: 提供性能排名和改进建议

## 目录结构

```
accuracy_test/
├── test_images/              # 测试图片目录
├── results/                  # 测试结果目录
├── reports/                  # 测试报告目录
├── test_api.py              # API测试脚本
├── analyze_results.py       # 结果分析工具
├── generate_report.py       # 报告生成器
├── prepare_test_images.py   # 图片准备工具
├── run_test.py              # 主测试脚本
├── test_config.json         # 测试配置文件
└── README.md                # 说明文档
```

## 快速开始

### 1. 环境准备

确保已安装必要的依赖包：

```bash
pip install requests pillow matplotlib pandas seaborn numpy
```

### 2. 启动OCR API服务

确保OCR API服务正在运行（默认端口16110）：

```bash
cd /root/lhy/paddleocr
python main.py
```

### 3. 运行测试

#### 一键测试（推荐）

```bash
cd /root/lhy/paddleocr/accuracy_test
python run_test.py
```

#### 分步测试

1. **准备测试图片**：
```bash
python prepare_test_images.py --update-config
```

2. **运行API测试**：
```bash
python test_api.py --api-url http://localhost:16110 --config test_config.json
```

3. **生成测试报告**：
```bash
python generate_report.py results/ocr_test_results_*.json
```

## 详细使用说明

### 测试配置

编辑 `test_config.json` 文件来配置测试参数：

```json
{
  "zh": {
    "images": ["/path/to/chinese_test.jpg"],
    "expected_texts": {
      "/path/to/chinese_test.jpg": ["期望识别的文本1", "期望识别的文本2"]
    },
    "score_threshold": 0.5,
    "description": "中文OCR测试"
  }
}
```

### 自定义测试图片

使用 `prepare_test_images.py` 生成测试图片：

```bash
# 生成所有语言的测试图片
python prepare_test_images.py

# 生成混合语言测试图片
python prepare_test_images.py --mixed zh en ja

# 指定输出目录
python prepare_test_images.py --output-dir /path/to/output
```

### API测试参数

`test_api.py` 支持以下参数：

```bash
python test_api.py \
  --api-url http://localhost:16110 \
  --api-key your_api_key \
  --config test_config.json \
  --output results.json
```

### 结果分析

`analyze_results.py` 提供详细的结果分析：

```bash
# 生成分析报告
python analyze_results.py results.json --report --charts

# 仅生成图表
python analyze_results.py results.json --charts

# 仅生成报告
python analyze_results.py results.json --report
```

### 报告生成

`generate_report.py` 生成综合测试报告：

```bash
# 生成完整报告
python generate_report.py results.json

# 仅生成图表
python generate_report.py results.json --charts-only

# 仅导出CSV数据
python generate_report.py results.json --csv-only
```

## 测试指标说明

### 准确率指标

- **成功率**: 测试图片成功识别的比例
- **精确率 (Precision)**: 识别结果中正确文本的比例
- **召回率 (Recall)**: 期望文本中被正确识别的比例
- **F1分数**: 精确率和召回率的调和平均数
- **精确匹配**: 完全匹配期望文本的比例
- **字符准确率**: 字符级别的识别准确率

### 性能指标

- **处理时间**: 单张图片的平均处理时间
- **总耗时**: 所有测试的总处理时间
- **吞吐量**: 单位时间内处理的图片数量

## 报告内容

生成的测试报告包含：

1. **测试概览**: 总体测试统计信息
2. **语言性能排名**: 各语言按性能排序
3. **详细语言分析**: 每种语言的详细指标
4. **性能图表**: 可视化性能对比
5. **改进建议**: 基于测试结果的优化建议

## 支持的语言

- 中文 (zh)
- 英文 (en)
- 日文 (ja)
- 韩文 (ko)
- 泰文 (th)
- 俄文 (ru)
- 阿拉伯文 (ar)
- 印地文 (hi)

## 故障排除

### 常见问题

1. **API连接失败**
   - 检查OCR API服务是否正在运行
   - 确认API地址和端口正确
   - 检查防火墙设置

2. **依赖包缺失**
   ```bash
   pip install requests pillow matplotlib pandas seaborn numpy
   ```

3. **测试图片生成失败**
   - 检查字体文件是否存在
   - 确认输出目录权限
   - 尝试使用默认字体

4. **报告生成失败**
   - 检查测试结果文件是否存在
   - 确认输出目录权限
   - 检查matplotlib后端设置

### 调试模式

启用详细日志输出：

```bash
python test_api.py --api-url http://localhost:16110 --config test_config.json 2>&1 | tee test.log
```

## 扩展功能

### 添加新语言

1. 在 `test_config.json` 中添加新语言配置
2. 在 `prepare_test_images.py` 中添加测试文本
3. 运行测试验证

### 自定义测试图片

1. 将测试图片放入 `test_images/` 目录
2. 更新 `test_config.json` 中的图片路径
3. 设置期望的识别文本

### 性能优化

1. 调整置信度阈值 (`score_threshold`)
2. 优化测试图片质量
3. 使用更合适的语言模型

## 贡献

欢迎提交问题和改进建议！

## 许可证

本项目采用MIT许可证。



