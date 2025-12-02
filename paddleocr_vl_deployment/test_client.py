#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR-VL 客户端测试脚本
"""

import base64
import requests
import json
import pathlib
from pathlib import Path

# 服务器配置
SERVER_IP = "183.250.90.218"
SERVER_PORT = 8080
API_URL = f"http://{SERVER_IP}:{SERVER_PORT}/layout-parsing"

def test_image_parsing(image_path: str):
    """测试图像版面解析"""
    print(f"测试图像: {image_path}")
    
    # 读取图像文件
    with open(image_path, "rb") as file:
        image_bytes = file.read()
        image_data = base64.b64encode(image_bytes).decode("ascii")
    
    # 构建请求
    payload = {
        "file": image_data,
        "fileType": 1,  # 图像文件
        "visualize": True,
        "prettifyMarkdown": True,
        "showFormulaNumber": False
    }
    
    try:
        # 发送请求
        print("发送请求到服务器...")
        response = requests.post(API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print("请求成功!")
            print(f"错误码: {result['errorCode']}")
            print(f"错误信息: {result['errorMsg']}")
            
            # 保存结果
            if result['errorCode'] == 0:
                save_results(result, image_path)
            else:
                print(f"处理失败: {result['errorMsg']}")
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("请求超时，请检查服务器状态")
    except requests.exceptions.ConnectionError:
        print(f"连接失败，请检查服务器 {SERVER_IP}:{SERVER_PORT} 是否运行")
    except Exception as e:
        print(f"请求异常: {e}")

def save_results(result, input_path):
    """保存解析结果"""
    output_dir = Path("output") / Path(input_path).stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, res in enumerate(result["result"]["layoutParsingResults"]):
        # 保存Markdown
        md_file = output_dir / f"page_{i}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(res["markdown"]["text"])
        print(f"Markdown保存到: {md_file}")
        
        # 保存图像
        if res["markdown"]["images"]:
            for img_path, img_data in res["markdown"]["images"].items():
                img_file = output_dir / img_path
                img_file.parent.mkdir(parents=True, exist_ok=True)
                with open(img_file, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"图像保存到: {img_file}")
        
        # 保存输出图像
        if res["outputImages"]:
            for img_name, img_data in res["outputImages"].items():
                img_file = output_dir / f"{img_name}_{i}.jpg"
                with open(img_file, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"输出图像保存到: {img_file}")
    
    # 保存完整结果JSON
    json_file = output_dir / "result.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"完整结果保存到: {json_file}")

def test_server_health():
    """测试服务器健康状态"""
    try:
        health_url = f"http://{SERVER_IP}:{SERVER_PORT}/health"
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"服务器状态: {health_data}")
            return health_data.get('status') == 'healthy'
        else:
            print(f"健康检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"健康检查异常: {e}")
        return False

if __name__ == "__main__":
    print("PaddleOCR-VL 客户端测试")
    print(f"服务器地址: {SERVER_IP}:{SERVER_PORT}")
    
    # 测试服务器健康状态
    print("\n1. 测试服务器健康状态...")
    if not test_server_health():
        print("服务器不可用，请检查服务是否启动")
        exit(1)
    
    # 测试图像解析
    print("\n2. 测试图像版面解析...")
    test_image_path = "test_image.jpg"  # 请替换为实际的测试图像路径
    
    if Path(test_image_path).exists():
        test_image_parsing(test_image_path)
    else:
        print(f"测试图像 {test_image_path} 不存在，请提供有效的图像文件")
        print("使用方法: python3 test_client.py")
        print("请将测试图像命名为 test_image.jpg 并放在当前目录")
