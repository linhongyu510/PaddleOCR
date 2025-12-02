# 远程测试OCR API指南

## 📋 连接信息

### 服务器信息
- **服务器IP地址**: `10.206.0.6`
- **OCR服务端口**: `16110`
- **完整服务地址**: `http://10.206.0.6:16110`

### API认证信息
- **API密钥**: `PolyNex-PolyOCR-2025xm`
- **API密钥头**: `X-API-Key: PolyNex-PolyOCR-2025xm`

## 🔧 测试方法

### 1. 健康检查
```bash
curl http://10.206.0.6:16110/health
```

### 2. 获取支持的语言
```bash
curl http://10.206.0.6:16110/v1/languages
```

### 3. OCR识别测试
```bash
curl -X POST http://10.206.0.6:16110/v1/ocr \
  -H "X-API-Key: PolyNex-PolyOCR-2025xm" \
  -F "file=@test_image.jpg" \
  -F "language=zh" \
  -F "preprocess=true" \
  -F "score=0.5"
```

## 🐍 Python测试代码

### 基础连接测试
```python
import requests

# 测试连接
response = requests.get("http://10.206.0.6:16110/health")
print(response.json())

# 获取支持的语言
response = requests.get("http://10.206.0.6:16110/v1/languages")
print(response.json())
```

### OCR识别测试
```python
import requests

# 准备测试图片
files = {
    'file': ('test.jpg', open('test.jpg', 'rb'), 'image/jpeg')
}

data = {
    'language': 'zh',
    'preprocess': 'true',
    'score': '0.5'
}

headers = {
    'X-API-Key': 'PolyNex-PolyOCR-2025xm'
}

# 发送请求
response = requests.post(
    "http://10.206.0.6:16110/v1/ocr",
    files=files,
    data=data,
    headers=headers,
    timeout=60
)

print(response.json())
```

## 📦 使用测试工具

### 下载测试工具
将以下文件复制到您的测试机器：
- `remote_test_config.py` - 配置文件
- `remote_test_client.py` - 测试客户端

### 运行测试
```bash
# 基础连接测试
python3 remote_test_client.py

# 在Python中使用
from remote_test_client import RemoteOCRClient
client = RemoteOCRClient()
client.test_connection()
```

## 🌍 支持的语言

### 主要语言编码
- **中文**: `zh`, `ch`, `chinese`, `简体中文`, `繁体中文`
- **英文**: `en`, `english`
- **日文**: `ja`, `japanese`, `jp`
- **韩文**: `ko`, `korean`, `kr`
- **俄文**: `ru`, `russian`
- **泰文**: `th`, `thai`
- **希腊文**: `el`, `greek`
- **法文**: `fr`, `french`
- **德文**: `de`, `german`
- **西班牙文**: `es`, `spanish`

### 完整语言列表
通过API获取: `GET http://10.206.0.6:16110/v1/languages`

## 🔍 故障排除

### 常见问题
1. **连接超时**: 检查网络连接和防火墙设置
2. **认证失败**: 确认API密钥正确
3. **端口不通**: 检查服务器端口16110是否开放

### 网络检查
```bash
# 检查端口连通性
telnet 10.206.0.6 16110

# 或使用nc
nc -zv 10.206.0.6 16110
```

### 防火墙设置
确保服务器防火墙允许16110端口访问：
```bash
# Ubuntu/Debian
sudo ufw allow 16110

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=16110/tcp
sudo firewall-cmd --reload
```

## 📊 性能参考
- **平均响应时间**: 4-24秒
- **支持并发**: 根据服务器配置
- **超时设置**: 建议60秒

## 🛡️ 安全说明
- API密钥请妥善保管
- 建议在生产环境中使用HTTPS
- 定期更换API密钥
