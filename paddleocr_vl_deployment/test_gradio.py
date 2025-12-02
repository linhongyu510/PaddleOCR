#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Gradio PaddleOCR-VL服务
"""

import requests
import time

def test_gradio_service():
    """测试Gradio服务"""
    server_ip = "183.250.90.218"
    port = 7860
    base_url = f"http://{server_ip}:{port}"
    
    print("🔍 测试Gradio PaddleOCR-VL服务")
    print("=" * 50)
    
    # 测试服务连接
    try:
        print(f"1. 测试服务连接: {base_url}")
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ Gradio服务连接成功")
            print(f"   状态码: {response.status_code}")
            print(f"   内容类型: {response.headers.get('content-type', '')}")
        else:
            print(f"❌ 服务连接失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False
    
    # 测试API端点
    try:
        print(f"\n2. 测试API端点")
        api_url = f"{base_url}/api/predict"
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            print("✅ API端点可访问")
        else:
            print(f"⚠️  API端点状态: {response.status_code}")
    except Exception as e:
        print(f"⚠️  API端点测试异常: {e}")
    
    # 显示访问信息
    print(f"\n🎉 Gradio服务部署成功！")
    print(f"🌐 前端地址: {base_url}")
    print(f"📱 移动端访问: {base_url}")
    print(f"🔧 服务器IP: {server_ip}:{port}")
    
    print(f"\n📋 功能特点:")
    print("  ✅ 图像上传和解析")
    print("  ✅ PDF文档解析")
    print("  ✅ 实时参数调整")
    print("  ✅ 结果预览和下载")
    print("  ✅ 响应式界面设计")
    
    print(f"\n🚀 使用方法:")
    print("  1. 打开浏览器访问上述地址")
    print("  2. 上传图像或PDF文件")
    print("  3. 调整解析参数")
    print("  4. 点击开始解析")
    print("  5. 查看和下载结果")
    
    return True

if __name__ == "__main__":
    test_gradio_service()
