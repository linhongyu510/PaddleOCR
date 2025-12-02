#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程测试OCR API配置
用于从其他计算机测试OCR服务
"""

# 服务器信息
SERVER_CONFIG = {
    # 服务器IP地址
    "server_ip": "10.206.0.6",  # 主IP地址
    "server_ips": [
        "10.206.0.6",    # 主IP地址
        "172.17.0.1",    # Docker网络IP
        "172.18.0.1"     # 另一个网络IP
    ],
    
    # OCR服务端口
    "ocr_port": 16110,
    
    # API密钥
    "api_key": "PolyNex-PolyOCR-2025xm",
    "api_secret": "782b52f0-d5b6-488b-9fdd-0a9026d3a0c0",
    
    # 服务端点
    "base_url": "http://10.206.0.6:16110",
    "health_endpoint": "/health",
    "ocr_endpoint": "/v1/ocr",
    "languages_endpoint": "/v1/languages",
    "paddleocr_languages_endpoint": "/v1/languages/paddleocr"
}

# 测试配置
TEST_CONFIG = {
    # 超时设置
    "timeout": 60,
    
    # 重试次数
    "retry_count": 3,
    
    # 测试语言
    "test_languages": [
        "zh", "en", "ja", "ko", "ru", "th", "fr", "de", "es"
    ]
}

def get_server_info():
    """获取服务器信息"""
    return {
        "服务器IP地址": SERVER_CONFIG["server_ip"],
        "所有IP地址": SERVER_CONFIG["server_ips"],
        "OCR服务端口": SERVER_CONFIG["ocr_port"],
        "API密钥": SERVER_CONFIG["api_key"],
        "服务地址": SERVER_CONFIG["base_url"]
    }

def print_connection_info():
    """打印连接信息"""
    print("🌐 远程测试OCR API连接信息")
    print("=" * 50)
    print(f"📍 服务器IP地址: {SERVER_CONFIG['server_ip']}")
    print(f"🔌 OCR服务端口: {SERVER_CONFIG['ocr_port']}")
    print(f"🔑 API密钥: {SERVER_CONFIG['api_key']}")
    print(f"🌍 完整服务地址: {SERVER_CONFIG['base_url']}")
    print()
    print("📋 可用的API端点:")
    print(f"  - 健康检查: {SERVER_CONFIG['base_url']}/health")
    print(f"  - OCR识别: {SERVER_CONFIG['base_url']}/v1/ocr")
    print(f"  - 支持语言: {SERVER_CONFIG['base_url']}/v1/languages")
    print(f"  - PaddleOCR语言: {SERVER_CONFIG['base_url']}/v1/languages/paddleocr")
    print()
    print("🔧 测试方法:")
    print("1. 健康检查:")
    print(f"   curl {SERVER_CONFIG['base_url']}/health")
    print()
    print("2. 获取支持的语言:")
    print(f"   curl {SERVER_CONFIG['base_url']}/v1/languages")
    print()
    print("3. OCR识别测试:")
    print(f"   curl -X POST {SERVER_CONFIG['base_url']}/v1/ocr \\")
    print(f"     -H 'X-API-Key: {SERVER_CONFIG['api_key']}' \\")
    print(f"     -F 'file=@test_image.jpg' \\")
    print(f"     -F 'language=zh'")

if __name__ == "__main__":
    print_connection_info()
