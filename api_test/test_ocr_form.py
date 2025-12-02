#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR API表单测试脚本
使用multipart/form-data格式测试
"""

import requests
import time
from PIL import Image, ImageDraw, ImageFont

def create_test_image(text, filename):
    """创建测试图片"""
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 30), text, fill='black', font=font)
    img.save(f"/root/lhy/paddleocr/api_test/{filename}")
    return f"/root/lhy/paddleocr/api_test/{filename}"

def test_ocr_language(language, test_text, base_url="http://localhost:16110"):
    """测试单个语言的OCR"""
    print(f"\n🔍 测试语言: {language}")
    print(f"📝 测试文本: {test_text}")
    
    # 创建测试图片
    filename = f"test_{language}.jpg"
    image_path = create_test_image(test_text, filename)
    
    # 准备multipart/form-data请求
    files = {
        'file': (filename, open(image_path, 'rb'), 'image/jpeg')
    }
    
    data = {
        'language': language,
        'preprocess': 'true',
        'score': '0.5'
    }
    
    headers = {
        'X-API-Key': 'PolyNex-PolyOCR-2025xm'
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/v1/ocr", files=files, data=data, headers=headers, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功 - 耗时: {end_time - start_time:.2f}s")
            if result.get('data'):
                print(f"📊 识别结果: {[item.get('text', '') for item in result['data']]}")
            return True
        else:
            print(f"❌ 失败 - 状态码: {response.status_code}")
            print(f"📄 错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False
    finally:
        # 关闭文件
        if 'file' in files:
            files['file'][1].close()

def test_supported_languages(base_url="http://localhost:16110"):
    """测试获取支持的语言"""
    print("\n🌍 测试获取支持的语言")
    
    try:
        # 测试项目支持的语言
        response = requests.get(f"{base_url}/v1/languages", timeout=10)
        if response.status_code == 200:
            print("✅ 项目支持的语言:")
            languages = response.json()
            print(f"📊 响应: {languages}")
        else:
            print(f"❌ 获取项目语言失败: {response.status_code}")
        
        # 测试PaddleOCR支持的语言
        response = requests.get(f"{base_url}/v1/languages/paddleocr", timeout=10)
        if response.status_code == 200:
            print("\n✅ PaddleOCR支持的语言:")
            paddleocr_languages = response.json()
            print(f"📊 响应: {paddleocr_languages}")
        else:
            print(f"❌ 获取PaddleOCR语言失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    """主函数"""
    print("🚀 OCR API表单测试")
    print("=" * 40)
    
    # 测试获取支持的语言
    test_supported_languages()
    
    # 测试主要语言
    test_cases = [
        ("zh", "你好世界"),
        ("en", "Hello World"),
        ("ja", "こんにちは"),
        ("ko", "안녕하세요"),
        ("ru", "Привет"),
        ("th", "สวัสดี"),
        ("ar", "مرحبا"),
        ("fr", "Bonjour"),
        ("de", "Hallo"),
        ("es", "Hola")
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for language, text in test_cases:
        if test_ocr_language(language, text):
            success_count += 1
        time.sleep(1)
    
    print(f"\n📊 测试结果: {success_count}/{total_count} 成功")
    print(f"🎯 成功率: {success_count/total_count*100:.1f}%")

if __name__ == "__main__":
    main()
