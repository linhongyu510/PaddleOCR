#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio服务诊断脚本
"""

import requests
import socket
import time
import subprocess
import os

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

def check_process():
    """检查进程状态"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        gradio_processes = [line for line in lines if 'gradio' in line.lower() or 'python3 gradio_app.py' in line]
        return gradio_processes
    except Exception as e:
        return [f"进程检查失败: {e}"]

def check_logs():
    """检查日志"""
    log_file = "/home/meiya/lhy/paddleocr/paddleocr_vl_deployment/gradio.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                return lines[-10:]  # 返回最后10行
        except Exception as e:
            return [f"日志读取失败: {e}"]
    else:
        return ["日志文件不存在"]

def diagnose_gradio():
    """诊断Gradio服务"""
    server_ip = "183.250.90.218"
    port = 7860
    base_url = f"http://{server_ip}:{port}"
    
    print("🔍 Gradio PaddleOCR-VL 服务诊断")
    print("=" * 60)
    
    # 1. 检查进程
    print(f"\n1. 检查服务进程:")
    processes = check_process()
    if processes:
        for proc in processes:
            if 'python3 gradio_app.py' in proc:
                print("✅ Gradio进程正在运行")
                print(f"   进程信息: {proc.strip()}")
            else:
                print(f"   其他进程: {proc.strip()}")
    else:
        print("❌ 未找到Gradio进程")
    
    # 2. 测试TCP连接
    print(f"\n2. 测试TCP连接: {server_ip}:{port}")
    if test_connection(server_ip, port):
        print("✅ TCP连接正常")
    else:
        print("❌ TCP连接失败")
        print("可能原因:")
        print("  - 服务未启动")
        print("  - 防火墙阻止")
        print("  - 网络路由问题")
        return False
    
    # 3. 测试HTTP请求
    print(f"\n3. 测试HTTP请求: {base_url}")
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
    
    # 4. 检查日志
    print(f"\n4. 检查服务日志:")
    log_lines = check_logs()
    for line in log_lines:
        print(f"   {line.strip()}")
    
    # 5. 提供解决方案
    print(f"\n5. 故障排除建议:")
    print("如果仍然无法访问，请尝试:")
    print("1. 等待模型加载完成（可能需要几分钟）")
    print("2. 清除浏览器缓存 (Ctrl+F5)")
    print("3. 尝试不同的浏览器")
    print("4. 检查网络防火墙设置")
    print("5. 尝试使用手机热点网络")
    print("6. 重启服务: pkill -f gradio_app.py && cd /home/meiya/lhy/paddleocr/paddleocr_vl_deployment && nohup python3 gradio_app.py > gradio.log 2>&1 &")
    
    # 6. 显示访问信息
    print(f"\n6. 访问信息:")
    print(f"🌐 前端地址: {base_url}")
    print(f"📱 移动端: {base_url}")
    print(f"🔧 服务器: {server_ip}:{port}")
    
    return True

if __name__ == "__main__":
    diagnose_gradio()
