#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程OCR API测试客户端
用于从其他计算机测试OCR服务
"""

import requests
import json
import time
from remote_test_config import SERVER_CONFIG, TEST_CONFIG

class RemoteOCRClient:
    def __init__(self):
        self.base_url = SERVER_CONFIG["base_url"]
        self.api_key = SERVER_CONFIG["api_key"]
        self.timeout = TEST_CONFIG["timeout"]
    
    def test_connection(self):
        """测试连接"""
        print("🔍 测试服务器连接...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ 服务器连接正常")
                print(f"📊 响应: {response.json()}")
                return True
            else:
                print(f"❌ 服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def test_supported_languages(self):
        """测试获取支持的语言"""
        print("\n🌍 测试获取支持的语言...")
        try:
            response = requests.get(f"{self.base_url}/v1/languages", timeout=10)
            if response.status_code == 200:
                print("✅ 获取支持的语言成功")
                languages = response.json()
                print(f"📊 支持的语言模型: {len(languages.get('data', {}))}")
                return languages
            else:
                print(f"❌ 获取语言失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def test_ocr_with_image(self, image_path, language="zh"):
        """测试OCR识别"""
        print(f"\n🔍 测试OCR识别 (语言: {language})...")
        
        try:
            files = {
                'file': (image_path, open(image_path, 'rb'), 'image/jpeg')
            }
            
            data = {
                'language': language,
                'preprocess': 'true',
                'score': '0.5'
            }
            
            headers = {
                'X-API-Key': self.api_key
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/v1/ocr",
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OCR识别成功 - 耗时: {end_time - start_time:.2f}s")
                if result.get('data'):
                    texts = [item.get('text', '') for item in result['data']]
                    print(f"📊 识别结果: {texts}")
                return result
            else:
                print(f"❌ OCR识别失败 - 状态码: {response.status_code}")
                print(f"📄 错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ OCR识别异常: {e}")
            return None
        finally:
            if 'file' in files:
                files['file'][1].close()
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始远程OCR API综合测试")
        print("=" * 50)
        
        # 1. 测试连接
        if not self.test_connection():
            print("❌ 无法连接到服务器，测试终止")
            return
        
        # 2. 测试获取支持的语言
        languages = self.test_supported_languages()
        if not languages:
            print("❌ 无法获取支持的语言，测试终止")
            return
        
        # 3. 测试OCR识别（如果有测试图片）
        print("\n📝 注意: 要测试OCR识别，请提供测试图片路径")
        print("   例如: client.test_ocr_with_image('test.jpg', 'zh')")
        
        print("\n🎉 基础连接测试完成！")

def main():
    """主函数"""
    print("🌐 远程OCR API测试客户端")
    print("=" * 50)
    
    # 显示连接信息
    from remote_test_config import print_connection_info
    print_connection_info()
    
    # 创建客户端
    client = RemoteOCRClient()
    
    # 运行测试
    client.run_comprehensive_test()
    
    print("\n📋 使用示例:")
    print("```python")
    print("from remote_test_client import RemoteOCRClient")
    print("client = RemoteOCRClient()")
    print("client.test_connection()")
    print("client.test_supported_languages()")
    print("client.test_ocr_with_image('test.jpg', 'zh')")
    print("```")

if __name__ == "__main__":
    main()
