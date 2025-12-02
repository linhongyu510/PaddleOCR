#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR-VL 服务诊断脚本
"""

import requests
import socket
import time
from urllib.parse import urlparse

def test_connection(host, port):
    """测试TCP连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"连接测试异常: {e}")
        return False

def test_http_request(url):
    """测试HTTP请求"""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code, response.headers.get('content-type', ''), len(response.content)
    except Exception as e:
        return None, str(e), 0

def diagnose_service():
    """诊断服务"""
    server_ip = "183.250.90.218"
    port = 8080
    base_url = f"http://{server_ip}:{port}"
    
    print("🔍 PaddleOCR-VL 服务诊断")
    print("=" * 50)
    
    # 1. 测试TCP连接
    print(f"\n1. 测试TCP连接: {server_ip}:{port}")
    if test_connection(server_ip, port):
        print("✅ TCP连接正常")
    else:
        print("❌ TCP连接失败")
        print("可能原因:")
        print("  - 服务器防火墙阻止了连接")
        print("  - 网络路由问题")
        print("  - 服务器未启动")
        return False
    
    # 2. 测试HTTP请求
    print(f"\n2. 测试HTTP请求: {base_url}")
    status, content_type, content_length = test_http_request(base_url)
    
    if status == 200:
        print("✅ HTTP请求成功")
        print(f"   状态码: {status}")
        print(f"   内容类型: {content_type}")
        print(f"   内容长度: {content_length} 字节")
        
        if 'text/html' in content_type:
            print("✅ 返回HTML页面")
        else:
            print("⚠️  返回非HTML内容")
    else:
        print(f"❌ HTTP请求失败: {status}")
        if content_type:
            print(f"   错误信息: {content_type}")
        return False
    
    # 3. 测试其他端点
    endpoints = [
        ("/health", "健康检查"),
        ("/api/info", "API信息"),
        ("/docs", "API文档")
    ]
    
    print(f"\n3. 测试其他端点")
    for endpoint, description in endpoints:
        url = f"{base_url}{endpoint}"
        status, content_type, content_length = test_http_request(url)
        if status == 200:
            print(f"✅ {description}: {endpoint}")
        else:
            print(f"❌ {description}: {endpoint} (状态码: {status})")
    
    # 4. 提供访问建议
    print(f"\n4. 访问建议")
    print(f"🌐 前端页面: {base_url}")
    print(f"📚 API文档: {base_url}/docs")
    print(f"🔍 健康检查: {base_url}/health")
    
    print(f"\n5. 故障排除")
    print("如果仍然无法访问，请尝试:")
    print("1. 清除浏览器缓存 (Ctrl+F5)")
    print("2. 尝试不同的浏览器")
    print("3. 检查网络防火墙设置")
    print("4. 尝试使用手机热点网络")
    print("5. 联系网络管理员检查端口8080是否开放")
    
    return True

if __name__ == "__main__":
    diagnose_service()
