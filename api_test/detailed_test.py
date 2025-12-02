#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR API详细测试脚本
测试所有支持的语言编码
"""

import requests
import time
import json
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
        response = requests.post(f"{base_url}/v1/ocr", files=files, data=data, headers=headers, timeout=60)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功 - 耗时: {response_time:.2f}s")
            if result.get('data'):
                texts = [item.get('text', '') for item in result['data']]
                print(f"📊 识别结果: {texts}")
                return {
                    'status': 'success',
                    'response_time': response_time,
                    'result': texts,
                    'confidence': [item.get('confidence', 0) for item in result.get('data', [])]
                }
            else:
                print("📊 无识别结果")
                return {
                    'status': 'success',
                    'response_time': response_time,
                    'result': [],
                    'confidence': []
                }
        else:
            print(f"❌ 失败 - 状态码: {response.status_code}")
            print(f"📄 错误: {response.text}")
            return {
                'status': 'error',
                'status_code': response.status_code,
                'error': response.text,
                'response_time': response_time
            }
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return {
            'status': 'exception',
            'error': str(e),
            'response_time': 0
        }
    finally:
        # 关闭文件
        if 'file' in files:
            files['file'][1].close()

def main():
    """主函数"""
    print("🚀 OCR API详细测试")
    print("=" * 50)
    
    # 测试所有支持的语言编码
    test_cases = [
        # 中文相关
        ("zh", "你好世界", "中文测试"),
        ("ch", "OCR识别测试", "中文别名测试"),
        ("chinese", "多语言支持", "中文全名测试"),
        ("简体中文", "简体中文测试", "中文描述测试"),
        
        # 英文相关
        ("en", "Hello World", "英文测试"),
        ("english", "OCR Recognition Test", "英文全名测试"),
        
        # 日文相关
        ("ja", "こんにちは", "日文测试"),
        ("japanese", "OCR認識テスト", "日文全名测试"),
        ("jp", "日本語テスト", "日文别名测试"),
        
        # 韩文相关
        ("ko", "안녕하세요", "韩文测试"),
        ("korean", "OCR 인식 테스트", "韩文全名测试"),
        ("kr", "한국어 테스트", "韩文别名测试"),
        
        # 俄文相关
        ("ru", "Привет мир", "俄文测试"),
        ("russian", "OCR распознавание", "俄文全名测试"),
        
        # 泰文相关
        ("th", "สวัสดี", "泰文测试"),
        ("thai", "การทดสอบ OCR", "泰文全名测试"),
        
        # 希腊文相关
        ("el", "Γεια σας", "希腊文测试"),
        ("greek", "OCR αναγνώριση", "希腊文全名测试"),
        
        # 拉丁语系
        ("fr", "Bonjour", "法文测试"),
        ("french", "Test de reconnaissance", "法文全名测试"),
        ("de", "Hallo Welt", "德文测试"),
        ("german", "OCR Erkennungstest", "德文全名测试"),
        ("es", "Hola mundo", "西班牙文测试"),
        ("spanish", "Prueba de reconocimiento", "西班牙文全名测试"),
        ("it", "Ciao mondo", "意大利文测试"),
        ("italian", "Test di riconoscimento", "意大利文全名测试"),
        ("pt", "Olá mundo", "葡萄牙文测试"),
        ("portuguese", "Teste de reconhecimento", "葡萄牙文全名测试"),
    ]
    
    results = {}
    success_count = 0
    total_count = len(test_cases)
    
    print(f"📋 开始测试 {total_count} 种语言编码")
    print("=" * 50)
    
    for language, text, description in test_cases:
        result = test_ocr_language(language, text)
        results[f"{language}_{description}"] = result
        
        if result['status'] == 'success':
            success_count += 1
        
        time.sleep(2)  # 避免请求过于频繁
    
    # 生成测试报告
    print(f"\n📊 测试报告")
    print("=" * 50)
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    # 按状态分类显示结果
    print(f"\n📋 详细结果:")
    success_cases = []
    error_cases = []
    exception_cases = []
    
    for test_name, result in results.items():
        if result['status'] == 'success':
            success_cases.append((test_name, result))
        elif result['status'] == 'error':
            error_cases.append((test_name, result))
        else:
            exception_cases.append((test_name, result))
    
    if success_cases:
        print(f"\n✅ 成功案例 ({len(success_cases)}):")
        for test_name, result in success_cases:
            print(f"  - {test_name}: {result['response_time']:.2f}s")
            if result.get('result'):
                print(f"    识别结果: {result['result']}")
    
    if error_cases:
        print(f"\n❌ 错误案例 ({len(error_cases)}):")
        for test_name, result in error_cases:
            print(f"  - {test_name}: {result.get('error', 'Unknown error')}")
    
    if exception_cases:
        print(f"\n⚠️ 异常案例 ({len(exception_cases)}):")
        for test_name, result in exception_cases:
            print(f"  - {test_name}: {result.get('error', 'Unknown exception')}")
    
    # 保存详细报告
    report_path = "/root/lhy/paddleocr/api_test/detailed_test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 详细报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
