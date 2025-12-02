#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成多语言测试图片
用于OCR API测试
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_multilingual_test_images():
    """创建多语言测试图片"""
    
    # 测试文本配置
    test_texts = {
        'zh': "你好世界\nOCR识别测试\n多语言支持",
        'en': "Hello World\nOCR Recognition Test\nMulti-language Support",
        'ja': "こんにちは\nOCR認識テスト\n多言語対応",
        'ko': "안녕하세요\nOCR 인식 테스트\n다국어 지원",
        'ru': "Привет мир\nOCR распознавание\nМногоязычная поддержка",
        'th': "สวัสดี\nการทดสอบ OCR\nการสนับสนุนหลายภาษา",
        'ar': "مرحبا بالعالم\nاختبار التعرف على النص\nدعم متعدد اللغات",
        'fr': "Bonjour le monde\nTest de reconnaissance OCR\nSupport multilingue",
        'de': "Hallo Welt\nOCR-Erkennungstest\nMehrsprachige Unterstützung",
        'es': "Hola mundo\nPrueba de reconocimiento OCR\nSoporte multilingüe",
        'it': "Ciao mondo\nTest di riconoscimento OCR\nSupporto multilingue",
        'pt': "Olá mundo\nTeste de reconhecimento OCR\nSuporte multilíngue",
        'el': "Γεια σας κόσμος\nOCR αναγνώριση\nΠολυγλωσσική υποστήριξη",
        'hi': "नमस्ते दुनिया\nOCR पहचान परीक्षण\nबहुभाषी समर्थन",
        'bn': "হ্যালো বিশ্ব\nOCR স্বীকৃতি পরীক্ষা\nবহুভাষিক সমর্থন"
    }
    
    # 创建输出目录
    output_dir = "/root/lhy/paddleocr/api_test/test_images"
    os.makedirs(output_dir, exist_ok=True)
    
    print("🎨 生成多语言测试图片...")
    
    for lang_code, text in test_texts.items():
        try:
            # 创建图片
            img = Image.new('RGB', (600, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # 尝试使用合适的字体
            font_size = 24
            try:
                if lang_code in ['zh', 'ja', 'ko']:
                    # 中日韩语言使用CJK字体
                    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", font_size)
                elif lang_code in ['ar', 'hi', 'bn']:
                    # 阿拉伯文、印地文等使用Noto Sans
                    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf", font_size)
                else:
                    # 其他语言使用DejaVu Sans
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # 绘制文字
            lines = text.split('\n')
            y_offset = 30
            for line in lines:
                draw.text((20, y_offset), line, fill='black', font=font)
                y_offset += 40
            
            # 保存图片
            filename = f"{lang_code}_test.jpg"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath)
            print(f"✅ 生成: {filename}")
            
        except Exception as e:
            print(f"❌ 生成 {lang_code} 失败: {e}")
    
    print(f"\n📁 测试图片已保存到: {output_dir}")
    return output_dir

def create_mixed_language_image():
    """创建混合语言测试图片"""
    print("\n🌍 生成混合语言测试图片...")
    
    # 混合语言文本
    mixed_text = """Multi-language OCR Test
多语言OCR测试
こんにちは世界
안녕하세요 세계
Привет мир
مرحبا بالعالم
Bonjour le monde
Hallo Welt
Hola mundo"""
    
    try:
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # 使用默认字体
        font = ImageFont.load_default()
        
        # 绘制混合语言文本
        lines = mixed_text.split('\n')
        y_offset = 30
        for line in lines:
            draw.text((20, y_offset), line, fill='black', font=font)
            y_offset += 35
        
        # 保存图片
        output_dir = "/root/lhy/paddleocr/api_test/test_images"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, "mixed_language_test.jpg")
        img.save(filepath)
        print(f"✅ 生成混合语言图片: mixed_language_test.jpg")
        
    except Exception as e:
        print(f"❌ 生成混合语言图片失败: {e}")

def main():
    """主函数"""
    print("🎨 多语言测试图片生成器")
    print("=" * 40)
    
    # 生成单语言测试图片
    create_multilingual_test_images()
    
    # 生成混合语言测试图片
    create_mixed_language_image()
    
    print("\n🎉 所有测试图片生成完成！")

if __name__ == "__main__":
    main()
