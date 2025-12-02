#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR API接口测试脚本
测试所有支持的语言编码
"""

import requests
import json
import base64
import time
import os
from pathlib import Path

class OCRAPITester:
    def __init__(self, base_url="http://localhost:16110", api_key="PolyNex-PolyOCR-2025xm"):
        self.base_url = base_url
        self.api_key = api_key
        self.test_results = {}
        
    def create_test_image(self, text, filename, size=(400, 100)):
        """创建测试图片"""
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建图片
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)
        
        # 尝试使用系统字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # 绘制文字
        draw.text((10, 30), text, fill='black', font=font)
        
        # 保存图片
        img_path = f"/root/lhy/paddleocr/api_test/{filename}"
        img.save(img_path)
        return img_path
    
    def encode_image_to_base64(self, image_path):
        """将图片编码为base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def test_ocr_api(self, language, test_text, image_path=None):
        """测试OCR API接口"""
        print(f"\n🔍 测试语言: {language}")
        print(f"📝 测试文本: {test_text}")
        
        # 如果没有提供图片路径，创建测试图片
        if not image_path:
            filename = f"test_{language}.jpg"
            image_path = self.create_test_image(test_text, filename)
        
        # 编码图片
        image_base64 = self.encode_image_to_base64(image_path)
        
        # 准备请求数据
        data = {
            "image": image_base64,
            "language": language,
            "preprocess": True,
            "score": 0.5
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            # 发送请求
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/v1/ocr",
                json=data,
                headers=headers,
                timeout=30
            )
            end_time = time.time()
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功 - 耗时: {end_time - start_time:.2f}s")
                print(f"📊 识别结果: {result.get('data', [])}")
                
                self.test_results[language] = {
                    "status": "success",
                    "response_time": end_time - start_time,
                    "result": result
                }
            else:
                print(f"❌ 失败 - 状态码: {response.status_code}")
                print(f"📄 错误信息: {response.text}")
                
                self.test_results[language] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
            self.test_results[language] = {
                "status": "exception",
                "error": str(e)
            }
    
    def test_supported_languages_api(self):
        """测试获取支持语言的API"""
        print("\n🌍 测试获取支持语言的API")
        
        try:
            # 测试项目支持的语言
            response = requests.get(f"{self.base_url}/v1/languages", timeout=10)
            if response.status_code == 200:
                print("✅ 项目支持的语言:")
                languages = response.json()
                print(json.dumps(languages, indent=2, ensure_ascii=False))
            else:
                print(f"❌ 获取项目语言失败: {response.status_code}")
            
            # 测试PaddleOCR支持的语言
            response = requests.get(f"{self.base_url}/v1/languages/paddleocr", timeout=10)
            if response.status_code == 200:
                print("\n✅ PaddleOCR支持的语言:")
                paddleocr_languages = response.json()
                print(json.dumps(paddleocr_languages, indent=2, ensure_ascii=False))
            else:
                print(f"❌ 获取PaddleOCR语言失败: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
    
    def test_health_check(self):
        """测试健康检查"""
        print("\n🏥 测试健康检查")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ 服务健康")
                print(f"📊 响应: {response.json()}")
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ 健康检查异常: {e}")
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始OCR API综合测试")
        print("=" * 50)
        
        # 测试健康检查
        self.test_health_check()
        
        # 测试获取支持的语言
        self.test_supported_languages_api()
        
        # 定义测试语言和对应的测试文本
        test_cases = [
            # 中文测试
            ("zh", "你好世界", "中文测试"),
            ("ch", "OCR识别测试", "中文别名测试"),
            ("chinese", "多语言支持", "中文全名测试"),
            
            # 英文测试
            ("en", "Hello World", "英文测试"),
            ("english", "OCR Recognition Test", "英文全名测试"),
            
            # 日文测试
            ("ja", "こんにちは", "日文测试"),
            ("japanese", "OCR認識テスト", "日文全名测试"),
            
            # 韩文测试
            ("ko", "안녕하세요", "韩文测试"),
            ("korean", "OCR 인식 테스트", "韩文全名测试"),
            
            # 俄文测试
            ("ru", "Привет мир", "俄文测试"),
            ("russian", "OCR распознавание", "俄文全名测试"),
            
            # 泰文测试
            ("th", "สวัสดี", "泰文测试"),
            ("thai", "การทดสอบ OCR", "泰文全名测试"),
            
            # 希腊文测试
            ("el", "Γεια σας", "希腊文测试"),
            ("greek", "OCR αναγνώριση", "希腊文全名测试"),
            
            # 阿拉伯文测试
            ("ar", "مرحبا", "阿拉伯文测试"),
            
            # 法文测试
            ("fr", "Bonjour", "法文测试"),
            ("french", "Test de reconnaissance", "法文全名测试"),
            
            # 德文测试
            ("de", "Hallo Welt", "德文测试"),
            ("german", "OCR Erkennungstest", "德文全名测试"),
            
            # 西班牙文测试
            ("es", "Hola mundo", "西班牙文测试"),
            ("spanish", "Prueba de reconocimiento", "西班牙文全名测试"),
        ]
        
        print(f"\n📋 开始测试 {len(test_cases)} 种语言编码")
        print("=" * 50)
        
        # 执行测试
        for language, test_text, description in test_cases:
            self.test_ocr_api(language, test_text)
            time.sleep(1)  # 避免请求过于频繁
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n📊 测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["status"] == "success")
        failed_tests = total_tests - successful_tests
        
        print(f"总测试数: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")
        
        print("\n📋 详细结果:")
        for language, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"{status_icon} {language}: {result['status']}")
            if result["status"] == "success":
                print(f"   ⏱️  响应时间: {result['response_time']:.2f}s")
            elif result["status"] == "error":
                print(f"   📄 错误: {result.get('error', 'Unknown error')}")
        
        # 保存报告到文件
        report_path = "/root/lhy/paddleocr/api_test/test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到: {report_path}")

def main():
    """主函数"""
    print("🔧 OCR API接口测试工具")
    print("=" * 50)
    
    # 创建测试器
    tester = OCRAPITester()
    
    # 运行综合测试
    tester.run_comprehensive_test()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
