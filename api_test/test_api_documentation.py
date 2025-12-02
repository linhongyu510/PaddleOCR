#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据API文档测试OCR和翻译接口
"""

import requests
import json
import time
from PIL import Image, ImageDraw, ImageFont

class APITester:
    def __init__(self, base_url="http://43.137.12.144:16110", api_key="PolyNex-PolyOCR-2025xm"):
        self.base_url = base_url
        self.api_key = api_key
    
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
    
    def test_connection(self):
        """测试基础连接"""
        print("🔍 测试基础连接...")
        try:
            # 测试根路径
            response = requests.get(f"{self.base_url}/", timeout=10)
            print(f"✅ 根路径响应: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def test_ocr_api(self):
        """测试OCR接口 - 根据文档格式"""
        print("\n🔍 测试OCR接口...")
        
        # 创建测试图片
        image_path = self.create_test_image("Hello World", "test_ocr.jpg")
        
        # 根据文档使用multipart/form-data
        files = {
            'file': ('test_ocr.jpg', open(image_path, 'rb'), 'image/jpeg')
        }
        
        data = {
            'language': 'en',  # 使用英文
            'preprocess': 'false'
        }
        
        # 根据文档使用Authorization Bearer
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
            
            print(f"📊 状态码: {response.status_code}")
            print(f"⏱️ 响应时间: {end_time - start_time:.2f}秒")
            print(f"📄 响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OCR接口测试成功")
                if result.get('data'):
                    print(f"📝 识别结果: {[item.get('text', '') for item in result['data']]}")
                return True
            else:
                print("❌ OCR接口测试失败")
                return False
                
        except Exception as e:
            print(f"❌ OCR接口异常: {e}")
            return False
        finally:
            if 'file' in files:
                files['file'][1].close()
    
    def test_translate_api(self):
        """测试翻译接口 - 根据文档格式"""
        print("\n🔍 测试翻译接口...")
        
        # 根据文档使用JSON格式
        data = {
            "original_texts": [
                "Good morning!",
                "How are you today?",
                "See you tomorrow."
            ],
            "source_language": "英语",
            "target_language": "中文"
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
            
            print(f"📊 状态码: {response.status_code}")
            print(f"⏱️ 响应时间: {end_time - start_time:.2f}秒")
            print(f"📄 响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 翻译接口测试成功")
                if result.get('data'):
                    print(f"📝 翻译结果: {result['data']}")
                return True
            else:
                print("❌ 翻译接口测试失败")
                return False
                
        except Exception as e:
            print(f"❌ 翻译接口异常: {e}")
            return False
    
    def test_alternative_auth(self):
        """测试替代认证方式"""
        print("\n🔍 测试替代认证方式...")
        
        # 测试X-API-Key方式
        headers = {
            'X-API-Key': self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/", headers=headers, timeout=10)
            print(f"📊 X-API-Key认证状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
        except Exception as e:
            print(f"❌ X-API-Key认证失败: {e}")
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始API文档测试")
        print("=" * 50)
        print(f"📍 服务器地址: {self.base_url}")
        print(f"🔑 API密钥: {self.api_key}")
        print("=" * 50)
        
        # 1. 测试基础连接
        if not self.test_connection():
            print("❌ 基础连接失败，测试终止")
            return
        
        # 2. 测试替代认证
        self.test_alternative_auth()
        
        # 3. 测试OCR接口
        ocr_success = self.test_ocr_api()
        
        # 4. 测试翻译接口
        translate_success = self.test_translate_api()
        
        # 总结
        print(f"\n📊 测试总结:")
        print(f"OCR接口: {'✅ 成功' if ocr_success else '❌ 失败'}")
        print(f"翻译接口: {'✅ 成功' if translate_success else '❌ 失败'}")

def main():
    """主函数"""
    tester = APITester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
