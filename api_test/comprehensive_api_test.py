#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合API测试 - 根据文档测试所有功能
"""

import requests
import json
import time
from PIL import Image, ImageDraw, ImageFont

class ComprehensiveAPITester:
    def __init__(self, base_url="http://43.137.12.144:16110", api_key="PolyNex-PolyOCR-2025xm"):
        self.base_url = base_url
        self.api_key = api_key
        self.test_results = {}
    
    def create_test_image(self, text, filename):
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
    
    def test_ocr_language(self, language, test_text, description):
        """测试OCR接口 - 特定语言"""
        print(f"\n🔍 测试OCR - {description} ({language})")
        print(f"📝 测试文本: {test_text}")
        
        # 创建测试图片
        filename = f"test_{language}.jpg"
        image_path = self.create_test_image(test_text, filename)
        
        files = {
            'file': (filename, open(image_path, 'rb'), 'image/jpeg')
        }
        
        data = {
            'language': language,
            'preprocess': 'false'
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/v1/ocr",
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
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
            if 'file' in files:
                files['file'][1].close()
    
    def test_translate_language(self, original_texts, source_lang, target_lang, description):
        """测试翻译接口 - 特定语言对"""
        print(f"\n🔍 测试翻译 - {description}")
        print(f"📝 原文: {original_texts}")
        print(f"🌍 {source_lang} → {target_lang}")
        
        data = {
            "original_texts": original_texts,
            "source_language": source_lang,
            "target_language": target_lang
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/v2/translate",
                json=data,
                headers=headers,
                timeout=30
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功 - 耗时: {response_time:.2f}s")
                if result.get('data'):
                    print(f"📊 翻译结果: {result['data']}")
                    return {
                        'status': 'success',
                        'response_time': response_time,
                        'result': result['data']
                    }
                else:
                    print("📊 无翻译结果")
                    return {
                        'status': 'success',
                        'response_time': response_time,
                        'result': []
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
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始综合API测试")
        print("=" * 60)
        print(f"📍 服务器地址: {self.base_url}")
        print(f"🔑 API密钥: {self.api_key}")
        print("=" * 60)
        
        # OCR测试用例
        ocr_test_cases = [
            ("en", "Hello World", "英文测试"),
            ("zh", "你好世界", "中文测试"),
            ("ja", "こんにちは", "日文测试"),
            ("ko", "안녕하세요", "韩文测试"),
            ("ru", "Привет", "俄文测试"),
            ("th", "สวัสดี", "泰文测试"),
            ("fr", "Bonjour", "法文测试"),
            ("de", "Hallo", "德文测试"),
            ("es", "Hola", "西班牙文测试"),
        ]
        
        # 翻译测试用例
        translate_test_cases = [
            (["Good morning!", "How are you?"], "英语", "中文", "英译中"),
            (["你好", "再见"], "中文", "英语", "中译英"),
            (["こんにちは", "ありがとう"], "日语", "中文", "日译中"),
            (["안녕하세요", "감사합니다"], "韩语", "中文", "韩译中"),
            (["Привет", "Спасибо"], "俄语", "中文", "俄译中"),
            (["Bonjour", "Merci"], "法语", "中文", "法译中"),
            (["Hallo", "Danke"], "德语", "中文", "德译中"),
            (["Hola", "Gracias"], "西班牙语", "中文", "西译中"),
        ]
        
        print(f"\n📋 开始OCR测试 ({len(ocr_test_cases)} 种语言)")
        print("-" * 60)
        
        ocr_results = {}
        for language, text, description in ocr_test_cases:
            result = self.test_ocr_language(language, text, description)
            ocr_results[f"{language}_{description}"] = result
            time.sleep(2)  # 避免请求过于频繁
        
        print(f"\n📋 开始翻译测试 ({len(translate_test_cases)} 种语言对)")
        print("-" * 60)
        
        translate_results = {}
        for original_texts, source_lang, target_lang, description in translate_test_cases:
            result = self.test_translate_language(original_texts, source_lang, target_lang, description)
            translate_results[f"{description}"] = result
            time.sleep(1)  # 避免请求过于频繁
        
        # 生成测试报告
        self.generate_test_report(ocr_results, translate_results)
    
    def generate_test_report(self, ocr_results, translate_results):
        """生成测试报告"""
        print(f"\n📊 综合测试报告")
        print("=" * 60)
        
        # OCR测试统计
        ocr_total = len(ocr_results)
        ocr_success = sum(1 for r in ocr_results.values() if r['status'] == 'success')
        ocr_success_rate = ocr_success / ocr_total * 100 if ocr_total > 0 else 0
        
        # 翻译测试统计
        translate_total = len(translate_results)
        translate_success = sum(1 for r in translate_results.values() if r['status'] == 'success')
        translate_success_rate = translate_success / translate_total * 100 if translate_total > 0 else 0
        
        print(f"🔍 OCR接口测试:")
        print(f"  总测试数: {ocr_total}")
        print(f"  成功: {ocr_success}")
        print(f"  失败: {ocr_total - ocr_success}")
        print(f"  成功率: {ocr_success_rate:.1f}%")
        
        print(f"\n🌍 翻译接口测试:")
        print(f"  总测试数: {translate_total}")
        print(f"  成功: {translate_success}")
        print(f"  失败: {translate_total - translate_success}")
        print(f"  成功率: {translate_success_rate:.1f}%")
        
        # 详细结果
        print(f"\n📋 OCR详细结果:")
        for test_name, result in ocr_results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"  {status_icon} {test_name}: {result['status']} ({result.get('response_time', 0):.2f}s)")
        
        print(f"\n📋 翻译详细结果:")
        for test_name, result in translate_results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"  {status_icon} {test_name}: {result['status']} ({result.get('response_time', 0):.2f}s)")
        
        # 保存报告
        full_report = {
            'ocr_results': ocr_results,
            'translate_results': translate_results,
            'summary': {
                'ocr_total': ocr_total,
                'ocr_success': ocr_success,
                'ocr_success_rate': ocr_success_rate,
                'translate_total': translate_total,
                'translate_success': translate_success,
                'translate_success_rate': translate_success_rate
            }
        }
        
        report_path = "/root/lhy/paddleocr/api_test/comprehensive_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到: {report_path}")

def main():
    """主函数"""
    tester = ComprehensiveAPITester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
