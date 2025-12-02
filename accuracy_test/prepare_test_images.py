#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片准备工具
用于生成不同语言的测试图片
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from typing import List, Tuple, Dict

class TestImageGenerator:
    """测试图片生成器"""
    
    def __init__(self, output_dir: str = "/root/lhy/paddleocr/accuracy_test/test_images"):
        """
        初始化生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 测试文本配置 - 使用对应语言的文字
        self.test_texts = {
            'zh': [
                "中文文字识别",
                "OCR准确率测试",
                "多语言支持",
                "图像文字提取",
                "文本识别技术"
            ],
            'en': [
                "Hello World",
                "OCR Test",
                "English Text Recognition",
                "Multi-language Support",
                "Image Text Extraction"
            ],
            'ja': [
                "こんにちは",
                "日本語テスト",
                "OCR認識テスト",
                "多言語対応",
                "画像文字抽出"
            ],
            'ko': [
                "안녕하세요",
                "한국어 테스트",
                "OCR 인식 테스트",
                "다국어 지원",
                "이미지 텍스트 추출"
            ],
            'th': [
                "Thai Text Recognition",
                "OCR Accuracy Test", 
                "Thai Character Recognition",
                "Multi-language Support Test",
                "Image Text Extraction"
            ],
            'ru': [
                "Привет",
                "Русский тест",
                "OCR распознавание",
                "Многоязычная поддержка",
                "Извлечение текста из изображения"
            ],
            'fr': [
                "Bonjour",
                "Test français",
                "Reconnaissance OCR",
                "Support multilingue",
                "Extraction de texte d'image"
            ],
            'de': [
                "Hallo Welt",
                "Deutscher Test",
                "OCR-Erkennung",
                "Mehrsprachige Unterstützung",
                "Bildtext-Extraktion"
            ],
            'es': [
                "Hola Mundo",
                "Prueba española",
                "Reconocimiento OCR",
                "Soporte multilingüe",
                "Extracción de texto de imagen"
            ],
            'it': [
                "Ciao Mondo",
                "Test italiano",
                "Riconoscimento OCR",
                "Supporto multilingue",
                "Estrazione testo da immagine"
            ],
            'pt': [
                "Olá Mundo",
                "Teste português",
                "Reconhecimento OCR",
                "Suporte multilíngue",
                "Extração de texto de imagem"
            ],
            'nl': [
                "Hallo Wereld",
                "Nederlandse test",
                "OCR herkenning",
                "Meertalige ondersteuning",
                "Tekstextractie uit afbeelding"
            ],
            'pl': [
                "Cześć Świecie",
                "Test polski",
                "Rozpoznawanie OCR",
                "Wsparcie wielojęzyczne",
                "Ekstrakcja tekstu z obrazu"
            ],
            'cs': [
                "Ahoj Světe",
                "Český test",
                "OCR rozpoznávání",
                "Vícejazyčná podpora",
                "Extrakce textu z obrázku"
            ],
            'sk': [
                "Ahoj Svet",
                "Slovenský test",
                "OCR rozpoznávanie",
                "Viacjazyčná podpora",
                "Extrakcia textu z obrázka"
            ],
            'hu': [
                "Helló Világ",
                "Magyar teszt",
                "OCR felismerés",
                "Többnyelvű támogatás",
                "Szöveg kinyerése képből"
            ],
            'hr': [
                "Pozdrav Svijete",
                "Hrvatski test",
                "OCR prepoznavanje",
                "Višejezična podrška",
                "Izdvajanje teksta iz slike"
            ],
            'sl': [
                "Pozdravljen Svet",
                "Slovenski test",
                "OCR prepoznavanje",
                "Večjezična podpora",
                "Izvleček besedila iz slike"
            ],
            'et': [
                "Tere Maailm",
                "Eesti test",
                "OCR tuvastamine",
                "Mitmekeelne tugi",
                "Teksti eraldamine pildist"
            ],
            'lt': [
                "Sveikas Pasauli",
                "Lietuvių testas",
                "OCR atpažinimas",
                "Daugiakalbė palaikymas",
                "Teksto ištraukimas iš paveikslėlio"
            ],
            'el': [
                "Γεια σας Κόσμε",
                "Ελληνικό τεστ",
                "OCR αναγνώριση",
                "Πολύγλωσση υποστήριξη",
                "Εξαγωγή κειμένου από εικόνα"
            ],
            'is': [
                "Halló Heimur",
                "Íslenskt próf",
                "OCR þekking",
                "Fjöltyngd stuðningur",
                "Textaútdráttur úr mynd"
            ],
            'ga': [
                "Dia dhuit Domhan",
                "Tástáil Gaeilge",
                "Aithint OCR",
                "Tacaíocht ilteangach",
                "Aisghabháil téacs ó íomhá"
            ],
            'cy': [
                "Helo Byd",
                "Prawf Cymraeg",
                "Adnabod OCR",
                "Cefnogaeth amlieithog",
                "Echdynnu testun o ddelwedd"
            ],
            'sq': [
                "Përshëndetje Botë",
                "Test shqip",
                "Njohja OCR",
                "Mbështetje shumëgjuhëshe",
                "Nxjerrja e tekstit nga imazhi"
            ],
            'uk': [
                "Привіт Світ",
                "Український тест",
                "OCR розпізнавання",
                "Багатомовна підтримка",
                "Витяг тексту з зображення"
            ],
            'be': [
                "Прывітанне Свет",
                "Беларускі тэст",
                "OCR распазнаванне",
                "Шматмоўная падтрымка",
                "Выцягванне тэксту з выявы"
            ],
            'uz': [
                "Salom Dunyo",
                "O'zbek testi",
                "OCR tan olish",
                "Ko'p tilli qo'llab-quvvatlash",
                "Rasmdan matn chiqarish"
            ],
            'sw': [
                "Hujambo Dunia",
                "Mtihani wa Kiswahili",
                "Utambuzi wa OCR",
                "Msaada wa lugha nyingi",
                "Utoaji wa maandishi kutoka picha"
            ],
            'af': [
                "Hallo Wêreld",
                "Afrikaanse toets",
                "OCR herkenning",
                "Meertalige ondersteuning",
                "Teksonttrekking uit beeld"
            ],
            'oc': [
                "Adieu Mond",
                "Tèst occitan",
                "Reconocença OCR",
                "Supòrt multilengue",
                "Extraccion de tèxte d'imatge"
            ],
            'sr': [
                "Serbian Text Recognition",
                "OCR Accuracy Test",
                "Serbian Character Recognition", 
                "Multi-language Support Test",
                "Image Text Extraction"
            ],
            'latin': [
                "Salve Mundus",
                "Test Latinus",
                "OCR cognitio",
                "Multilingua auxilium",
                "Textus extractio ex imagine"
            ]
        }
    
    def create_test_image(self, texts: List[str], language: str, 
                         image_size: Tuple[int, int] = (800, 600),
                         font_size: int = 24,
                         background_color: str = "white",
                         text_color: str = "black") -> str:
        """
        创建测试图片
        
        Args:
            texts: 要显示的文本列表
            language: 语言代码
            image_size: 图片尺寸
            font_size: 字体大小
            background_color: 背景颜色
            text_color: 文字颜色
            
        Returns:
            生成的图片文件路径
        """
        # 创建图片
        img = Image.new('RGB', image_size, background_color)
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体
        try:
            # 根据语言选择合适的字体
            if language in ['zh', 'ja', 'ko']:
                # 中日韩语言使用CJK字体
                font_paths = [
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                ]
            elif language in ['th', 'ru', 'uk', 'be', 'sr', 'ar', 'he', 'fa', 'ur']:
                # 特殊字符语言使用Noto Sans字体，支持更多Unicode字符
                font_paths = [
                    "/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ]
            else:
                # 其他语言使用标准字体
                font_paths = [
                    "/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ]
            
            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
                
        except:
            font = ImageFont.load_default()
        
        # 计算文本位置
        line_height = font_size + 10
        start_y = 50
        x_margin = 50
        
        # 绘制文本
        for i, text in enumerate(texts):
            y_pos = start_y + i * line_height
            if y_pos + font_size > image_size[1] - 50:
                break  # 避免超出图片边界
            
            try:
                draw.text((x_margin, y_pos), text, fill=text_color, font=font)
            except Exception as e:
                print(f"绘制文本失败: {text}, 错误: {e}")
                # 如果绘制失败，尝试使用默认字体
                try:
                    default_font = ImageFont.load_default()
                    draw.text((x_margin, y_pos), text, fill=text_color, font=default_font)
                except:
                    # 如果还是失败，跳过这个文本
                    continue
        
        # 保存图片
        filename = f"test_{language}_{len(texts)}texts.jpg"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, 'JPEG', quality=95)
        
        return filepath
    
    def generate_all_test_images(self):
        """生成所有语言的测试图片"""
        generated_files = {}
        
        print("开始生成测试图片...")
        print("=" * 50)
        
        for language, texts in self.test_texts.items():
            print(f"生成 {language} 语言测试图片...")
            
            try:
                # 生成不同复杂度的测试图片
                filepaths = []
                
                # 简单测试图片（3个文本）
                simple_texts = texts[:3]
                simple_path = self.create_test_image(
                    simple_texts, language, 
                    image_size=(600, 400), font_size=28
                )
                filepaths.append(simple_path)
                
                # 中等复杂度测试图片（5个文本）
                medium_texts = texts[:5]
                medium_path = self.create_test_image(
                    medium_texts, language,
                    image_size=(800, 600), font_size=24
                )
                filepaths.append(medium_path)
                
                # 复杂测试图片（所有文本）
                complex_path = self.create_test_image(
                    texts, language,
                    image_size=(1000, 800), font_size=20
                )
                filepaths.append(complex_path)
                
                generated_files[language] = filepaths
                print(f"  ✓ 生成了 {len(filepaths)} 张图片")
                
            except Exception as e:
                print(f"  ✗ 生成失败: {e}")
                generated_files[language] = []
        
        print("\n" + "=" * 50)
        print("测试图片生成完成!")
        print(f"输出目录: {self.output_dir}")
        
        # 统计信息
        total_images = sum(len(files) for files in generated_files.values())
        successful_languages = sum(1 for files in generated_files.values() if files)
        
        print(f"成功生成语言数: {successful_languages}/{len(self.test_texts)}")
        print(f"总图片数: {total_images}")
        
        return generated_files
    
    def create_mixed_language_image(self, languages: List[str], 
                                  texts_per_language: int = 2) -> str:
        """
        创建混合语言测试图片
        
        Args:
            languages: 要混合的语言列表
            texts_per_language: 每种语言的文本数量
            
        Returns:
            生成的图片文件路径
        """
        # 收集所有文本
        all_texts = []
        for lang in languages:
            if lang in self.test_texts:
                lang_texts = self.test_texts[lang][:texts_per_language]
                all_texts.extend(lang_texts)
        
        if not all_texts:
            raise ValueError("没有可用的文本")
        
        # 创建图片
        img = Image.new('RGB', (1000, 800), 'white')
        draw = ImageDraw.Draw(img)
        
        # 使用默认字体
        font = ImageFont.load_default()
        
        # 绘制文本
        line_height = 30
        start_y = 50
        x_margin = 50
        
        for i, text in enumerate(all_texts):
            y_pos = start_y + i * line_height
            if y_pos + 25 > 800 - 50:
                break
            
            try:
                draw.text((x_margin, y_pos), text, fill='black', font=font)
            except:
                continue
        
        # 保存图片
        filename = f"test_mixed_{'_'.join(languages)}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, 'JPEG', quality=95)
        
        return filepath
    
    def update_test_config(self, generated_files: Dict[str, List[str]], 
                          config_file: str = None):
        """
        更新测试配置文件
        
        Args:
            generated_files: 生成的文件路径字典
            config_file: 配置文件路径
        """
        if not config_file:
            config_file = os.path.join(os.path.dirname(__file__), 'test_config.json')
        
        import json
        
        # 读取现有配置
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {}
        
        # 更新配置
        for language, filepaths in generated_files.items():
            if filepaths and language in config:
                config[language]['images'] = filepaths
                # 更新期望文本
                if language in self.test_texts:
                    expected_texts = {}
                    for filepath in filepaths:
                        # 根据文件名确定期望的文本
                        if '3texts' in filepath:
                            expected_texts[filepath] = self.test_texts[language][:3]
                        elif '5texts' in filepath:
                            expected_texts[filepath] = self.test_texts[language][:5]
                        else:
                            expected_texts[filepath] = self.test_texts[language]
                    
                    config[language]['expected_texts'] = expected_texts
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"测试配置已更新: {config_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试图片准备工具')
    parser.add_argument('--output-dir', default='/root/lhy/paddleocr/accuracy_test/test_images',
                       help='输出目录路径')
    parser.add_argument('--update-config', action='store_true',
                       help='更新测试配置文件')
    parser.add_argument('--mixed', nargs='+', 
                       help='创建混合语言测试图片，指定语言代码')
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = TestImageGenerator(args.output_dir)
    
    # 生成所有测试图片
    generated_files = generator.generate_all_test_images()
    
    # 创建混合语言图片
    if args.mixed:
        try:
            mixed_path = generator.create_mixed_language_image(args.mixed)
            print(f"混合语言图片已创建: {mixed_path}")
        except Exception as e:
            print(f"创建混合语言图片失败: {e}")
    
    # 更新配置文件
    if args.update_config:
        generator.update_test_config(generated_files)
    
    print("\n测试图片准备完成!")
    print(f"可以使用以下命令开始测试:")
    print(f"python test_api.py --config test_config.json")

if __name__ == "__main__":
    main()
