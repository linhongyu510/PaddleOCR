# OCR API 测试工具

这个文件夹包含了用于测试OCR API接口的完整工具集。

## 📁 文件说明

### 测试脚本
- `test_ocr_api.py` - 综合API测试脚本，测试所有支持的语言编码
- `quick_test.py` - 快速测试脚本，测试主要语言
- `generate_test_images.py` - 生成多语言测试图片

### 测试图片
- `test_images/` - 自动生成的测试图片目录
- 各种语言的测试图片文件

## 🚀 使用方法

### 1. 启动OCR服务
```bash
cd /root/lhy/paddleocr
python main.py
```

### 2. 生成测试图片
```bash
cd /root/lhy/paddleocr/api_test
python generate_test_images.py
```

### 3. 运行快速测试
```bash
python quick_test.py
```

### 4. 运行综合测试
```bash
python test_ocr_api.py
```

## 🔧 测试内容

### 支持的语言编码测试
- **中文**: `zh`, `ch`, `chinese`, `简体中文`, `繁体中文`
- **英文**: `en`, `english`
- **日文**: `ja`, `japanese`, `jp`
- **韩文**: `ko`, `korean`, `kr`
- **俄文**: `ru`, `russian`
- **泰文**: `th`, `thai`
- **希腊文**: `el`, `greek`
- **阿拉伯文**: `ar`
- **法文**: `fr`, `french`
- **德文**: `de`, `german`
- **西班牙文**: `es`, `spanish`
- **意大利文**: `it`, `italian`
- **葡萄牙文**: `pt`, `portuguese`
- **印地文**: `hi`
- **孟加拉文**: `bn`

### API接口测试
- **健康检查**: `GET /health`
- **获取支持语言**: `GET /v1/languages`
- **PaddleOCR语言**: `GET /v1/languages/paddleocr`
- **OCR识别**: `POST /v1/ocr`

## 📊 测试报告

测试完成后会生成：
- 控制台输出结果
- `test_report.json` - 详细的JSON格式测试报告

## 🛠️ 自定义测试

### 修改测试参数
在脚本中修改以下参数：
```python
base_url = "http://localhost:5000"  # API服务地址
api_key = "test_key"                 # API密钥
```

### 添加新的测试语言
在 `test_cases` 列表中添加新的语言测试：
```python
test_cases = [
    ("语言代码", "测试文本", "描述"),
    # 添加更多测试用例
]
```

## 📝 注意事项

1. 确保OCR服务正在运行
2. 检查API密钥是否正确
3. 测试图片会自动生成，无需手动准备
4. 建议在测试前先运行健康检查

## 🔍 故障排除

### 常见问题
1. **连接失败**: 检查服务是否启动
2. **认证失败**: 检查API密钥
3. **语言不支持**: 查看支持的语言列表
4. **图片格式错误**: 确保图片格式正确

### 调试方法
```bash
# 检查服务状态
curl http://localhost:5000/health

# 查看支持的语言
curl http://localhost:5000/v1/languages
```
