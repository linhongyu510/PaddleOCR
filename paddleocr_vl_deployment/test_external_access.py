#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PaddleOCR-VL外部访问
"""

import requests
import json
import base64
from pathlib import Path

def test_external_access():
    """测试外部访问"""
    server_ip = "183.250.90.218"
    port = 8080
    base_url = f"http://{server_ip}:{port}"
    
    print(f"测试服务器: {base_url}")
    
    # 测试健康检查
    try:
        health_url = f"{base_url}/health"
        print(f"\n1. 测试健康检查: {health_url}")
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 健康检查成功: {health_data}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 测试根路径
    try:
        root_url = f"{base_url}/"
        print(f"\n2. 测试根路径: {root_url}")
        response = requests.get(root_url, timeout=10)
        if response.status_code == 200:
            if 'text/html' in response.headers.get('content-type', ''):
                print("✅ 前端页面可访问")
            else:
                root_data = response.json()
                print(f"✅ 根路径访问成功: {root_data}")
        else:
            print(f"❌ 根路径访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 根路径访问异常: {e}")
    
    # 测试API信息
    try:
        api_url = f"{base_url}/api/info"
        print(f"\n2.1 测试API信息: {api_url}")
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            api_data = response.json()
            print(f"✅ API信息获取成功: {api_data}")
        else:
            print(f"❌ API信息获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ API信息获取异常: {e}")
    
    # 测试API文档
    try:
        docs_url = f"{base_url}/docs"
        print(f"\n3. 测试API文档: {docs_url}")
        response = requests.get(docs_url, timeout=10)
        if response.status_code == 200:
            print("✅ API文档可访问")
        else:
            print(f"❌ API文档访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ API文档访问异常: {e}")
    
    print(f"\n🎉 服务部署成功！")
    print(f"📡 服务器地址: {base_url}")
    print(f"📚 API文档: {base_url}/docs")
    print(f"🔍 健康检查: {base_url}/health")
    print(f"📋 版面解析: {base_url}/layout-parsing")
    
    return True

if __name__ == "__main__":
    print("PaddleOCR-VL 外部访问测试")
    print("=" * 50)
    test_external_access()
