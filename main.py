#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR服务接口 - FastAPI后端
支持多语言OCR识别，基于PaddleOCR
"""

import os
import time
import uuid
import math
from typing import Optional, Dict, Any
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import paddleocr
from paddleocr import PaddleOCR
import cv2 # 图像处理
import numpy as np # 数值计算 
from PIL import Image # 图像操作
import io
import base64

# 导入翻译模块
from translation import (
    translate_texts_endpoint,
    v2_translate_texts_endpoint,
    update_translation_config,
    get_translation_config,
    health_check_translation,
    get_supported_languages_endpoint
)

# 导入认证模块
from auth import auth_required

# 创建FastAPI应用
app = FastAPI(
    title="OCR识别服务",
    description="基于PaddleOCR的多语言OCR识别服务",
    version="1.0.0"
)

# 添加CORS中间件(允许跨域请求，支持前端调用)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务(挂载static目录，提供前端资源)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模型缓存
model_cache: Dict[str, PaddleOCR] = {}

# 语言到模型的映射关系
LANGUAGE_MODEL_MAPPING = {
    # PP-OCRv5_server_rec: 简体中文、繁体中文、英文、日文
    "PP-OCRv5_server_rec": [
        # 中文相关
        "zh", "ch", "chinese", "zh-cn", "zh-tw", "traditional", "simplified", "简体中文", "繁体中文", "中文",
        # 英文
        "en", "english", "英文",
        # 日文
        "ja", "japanese", "jp", "日文", "日语"
    ],
    
    # PP-OCRv5_mobile_rec: 简体中文、繁体中文、英文、日文
    "PP-OCRv5_mobile_rec": [
        # 中文相关
        "zh", "ch", "chinese", "zh-cn", "zh-tw", "traditional", "simplified", "简体中文", "繁体中文", "中文",
        # 英文
        "en", "english", "英文",
        # 日文
        "ja", "japanese", "jp", "日文", "日语"
    ],
    
    # korean_PP-OCRv5_mobile_rec: 韩文、英文
    "korean_PP-OCRv5_mobile_rec": [
        # 韩文
        "ko", "korean", "kr", "韩文", "韩语", "한국어",
        # 英文
        "en", "english", "英文"
    ],
    
    # latin_PP-OCRv5_mobile_rec: 拉丁语系语言
    "latin_PP-OCRv5_mobile_rec": [
        # 英文
        "en", "english", "英文",
        # 法文
        "fr", "french", "法文", "法语", "français",
        # 德文
        "de", "german", "德文", "德语", "deutsch",
        # 南非荷兰文
        "af", "afrikaans", "南非荷兰文", "南非荷兰语",
        # 意大利文
        "it", "italian", "意大利文", "意大利语", "italiano",
        # 西班牙文
        "es", "spanish", "西班牙文", "西班牙语", "español",
        # 波斯尼亚文
        "bs", "bosnian", "波斯尼亚文", "波斯尼亚语", "bosanski",
        # 葡萄牙文
        "pt", "portuguese", "葡萄牙文", "葡萄牙语", "português",
        # 捷克文
        "cs", "czech", "捷克文", "捷克语", "čeština",
        # 威尔士文
        "cy", "welsh", "威尔士文", "威尔士语", "cymraeg",
        # 丹麦文
        "da", "danish", "丹麦文", "丹麦语", "dansk",
        # 爱沙尼亚文
        "et", "estonian", "爱沙尼亚文", "爱沙尼亚语", "eesti",
        # 爱尔兰文
        "ga", "irish", "爱尔兰文", "爱尔兰语", "gaeilge",
        # 克罗地亚文
        "hr", "croatian", "克罗地亚文", "克罗地亚语", "hrvatski",
        # 乌兹别克文
        "uz", "uzbek", "乌兹别克文", "乌兹别克语", "o'zbek",
        # 匈牙利文
        "hu", "hungarian", "匈牙利文", "匈牙利语", "magyar",
        # 塞尔维亚文（latin）
        "sr", "serbian", "塞尔维亚文", "塞尔维亚语", "српски",
        # 印度尼西亚文
        "id", "indonesian", "印度尼西亚文", "印度尼西亚语", "bahasa indonesia",
        # 欧西坦文
        "oc", "occitan", "欧西坦文", "欧西坦语", "occitan",
        # 冰岛文
        "is", "icelandic", "冰岛文", "冰岛语", "íslenska",
        # 立陶宛文
        "lt", "lithuanian", "立陶宛文", "立陶宛语", "lietuvių",
        # 毛利文
        "mi", "maori", "毛利文", "毛利语", "te reo māori",
        # 马来文
        "ms", "malay", "马来文", "马来语", "bahasa melayu",
        # 荷兰文
        "nl", "dutch", "荷兰文", "荷兰语", "nederlands",
        # 挪威文
        "no", "norwegian", "挪威文", "挪威语", "norsk",
        # 波兰文
        "pl", "polish", "波兰文", "波兰语", "polski",
        # 斯洛伐克文
        "sk", "slovak", "斯洛伐克文", "斯洛伐克语", "slovenčina",
        # 斯洛文尼亚文
        "sl", "slovenian", "斯洛文尼亚文", "斯洛文尼亚语", "slovenščina",
        # 阿尔巴尼亚文
        "sq", "albanian", "阿尔巴尼亚文", "阿尔巴尼亚语", "shqip",
        # 瑞典文
        "sv", "swedish", "瑞典文", "瑞典语", "svenska",
        # 西瓦希里文
        "sw", "swahili", "西瓦希里文", "西瓦希里语", "kiswahili",
        # 塔加洛文
        "tl", "tagalog", "塔加洛文", "塔加洛语", "tagalog",
        # 土耳其文
        "tr", "turkish", "土耳其文", "土耳其语", "türkçe",
        # 拉丁文
        "la", "latin", "拉丁文", "拉丁语", "latina"
    ],
    
    # eslav_PP-OCRv5_mobile_rec: 斯拉夫语系
    "eslav_PP-OCRv5_mobile_rec": [
        # 俄罗斯文
        "ru", "russian", "俄文", "俄语", "русский",
        # 白俄罗斯文
        "be", "belarusian", "白俄罗斯文", "白俄罗斯语", "беларуская",
        # 乌克兰文
        "uk", "ukrainian", "乌克兰文", "乌克兰语", "українська",
        # 英文
        "en", "english", "英文"
    ],
    
    # th_PP-OCRv5_mobile_rec: 泰文
    "th_PP-OCRv5_mobile_rec": [
        # 泰文
        "th", "thai", "泰文", "泰语", "ไทย",
        # 英文
        "en", "english", "英文"
    ],
    
    # el_PP-OCRv5_mobile_rec: 希腊文
    "el_PP-OCRv5_mobile_rec": [
        # 希腊文
        "el", "greek", "希腊文", "希腊语", "ελληνικά",
        # 英文
        "en", "english", "英文"
    ],
    
    # en_PP-OCRv5_mobile_rec: 英文
    "en_PP-OCRv5_mobile_rec": [
        # 英文
        "en", "english", "英文"
    ]
}

def get_model_for_language(lang: str) -> str:
    """
    根据语言参数获取对应的模型名称
    
    Args:
        lang: 用户指定的语言
        
    Returns:
        对应的模型名称
        
    Raises:
        ValueError: 当语言不支持时
    """
    lang = lang.lower().strip()
    
    for model_name, supported_langs in LANGUAGE_MODEL_MAPPING.items():
        if lang in supported_langs:
            return model_name
    
    raise ValueError(f"不支持的语言: {lang}")

def load_model(model_name: str) -> PaddleOCR:
    """
    加载PaddleOCR模型，支持缓存
    
    Args:
        model_name: 模型名称
        
    Returns:
        PaddleOCR实例
    """
    if model_name in model_cache:
        return model_cache[model_name]
    
    print(f"正在加载模型: {model_name}")
    
    # 根据模型名称设置参数
    if model_name == "PP-OCRv5_server_rec":
        ocr = PaddleOCR(lang='ch')
    elif model_name == "PP-OCRv5_mobile_rec":
        ocr = PaddleOCR(lang='ch')
    elif model_name == "korean_PP-OCRv5_mobile_rec":
        ocr = PaddleOCR(lang='korean')
    elif model_name == "latin_PP-OCRv5_mobile_rec":
        ocr = PaddleOCR(lang='latin')
    elif model_name == "eslav_PP-OCRv5_mobile_rec":
        ocr = PaddleOCR(lang='eslav')
    elif model_name == "th_PP-OCRv5_mobile_rec":
        ocr = PaddleOCR(lang='th')
    elif model_name == "el_PP-OCRv5_mobile_rec":
        ocr = PaddleOCR(lang='el')
    elif model_name == "en_PP-OCRv5_mobile_rec":
        ocr = PaddleOCR(lang='en')
    else:
        # 默认使用中文模型
        ocr = PaddleOCR(lang='ch')
    
    # 缓存模型
    model_cache[model_name] = ocr
    print(f"模型 {model_name} 加载完成")
    
    return ocr

def load_model_by_language(lang: str) -> PaddleOCR:
    """
    根据语言代码直接加载对应的PaddleOCR模型
    
    Args:
        lang: 语言代码
        
    Returns:
        PaddleOCR实例
    """
    # 首先尝试从缓存中获取
    model_name = get_model_for_language(lang)
    if model_name in model_cache:
        return model_cache[model_name]
    
    print(f"正在为语言 '{lang}' 加载模型: {model_name}")
    
    # 根据语言代码直接创建PaddleOCR实例
    try:
        # 使用PaddleOCR支持的语言代码
        ocr = PaddleOCR(lang=lang)
        
        # 缓存模型（使用语言代码作为键）
        model_cache[lang] = ocr
        print(f"语言 '{lang}' 的模型加载完成")
        
        return ocr
    except Exception as e:
        print(f"加载语言 '{lang}' 的模型失败: {e}")
        # 如果失败，回退到中文模型
        return load_model("PP-OCRv5_server_rec")

def get_supported_paddleocr_languages():
    """
    获取PaddleOCR支持的所有语言列表
    
    Returns:
        支持的语言列表
    """
    # PaddleOCR支持的语言列表（根据官方文档）
    supported_languages = [
        'ch',      # 中文
        'en',      # 英文
        'korean',  # 韩文
        'japan',   # 日文
        'ta',      # 泰文
        'te',      # 泰卢固文
        'ka',      # 格鲁吉亚文
        'chinese_cht',  # 繁体中文
        'hi',      # 印地文
        'mr',      # 马拉地文
        'ne',      # 尼泊尔文
        'ur',      # 乌尔都文
        'fa',      # 波斯文
        'ug',      # 维吾尔文
        'kk',      # 哈萨克文
        'ky',      # 吉尔吉斯文
        'tk',      # 土库曼文
        'az',      # 阿塞拜疆文
        'be',      # 白俄罗斯文
        'bg',      # 保加利亚文
        'uk',      # 乌克兰文
        'ru',      # 俄文
        'sr',      # 塞尔维亚文
        'mk',      # 马其顿文
        'mn',      # 蒙古文
        'ab',      # 阿布哈兹文
        'ru_mold', # 摩尔多瓦俄文
        'oc',      # 欧西坦文
        'rs_cyrillic',  # 塞尔维亚文（西里尔字母）
        'rs_latin',     # 塞尔维亚文（拉丁字母）
        'bg',      # 保加利亚文
        'uk',      # 乌克兰文
        'be',      # 白俄罗斯文
        'te',      # 泰卢固文
        'kn',      # 卡纳达文
        'ml',      # 马拉雅拉姆文
        'ta',      # 泰米尔文
        'si',      # 僧伽罗文
        'my',      # 缅甸文
        'km',      # 高棉文
        'lo',      # 老挝文
        'vi',      # 越南文
        'th',      # 泰文
        'ar',      # 阿拉伯文
        'fa',      # 波斯文
        'ur',      # 乌尔都文
        'hi',      # 印地文
        'bn',      # 孟加拉文
        'gu',      # 古吉拉特文
        'pa',      # 旁遮普文
        'or',      # 奥里亚文
        'as',      # 阿萨姆文
        'ne',      # 尼泊尔文
        'mr',      # 马拉地文
        'kn',      # 卡纳达文
        'ml',      # 马拉雅拉姆文
        'te',      # 泰卢固文
        'ta',      # 泰米尔文
        'si',      # 僧伽罗文
        'my',      # 缅甸文
        'km',      # 高棉文
        'lo',      # 老挝文
        'vi',      # 越南文
        'th',      # 泰文
        'ko',      # 韩文
        'ja',      # 日文
        'zh',      # 中文
        'ch',      # 中文（别名）
        'chinese_cht',  # 繁体中文
        'latin',   # 拉丁语系
        'eslav',   # 斯拉夫语系
        'el',      # 希腊文
        'en',      # 英文
    ]
    
    return supported_languages

def process_image(image_data: bytes) -> np.ndarray:
    """
    处理图片数据，转换为OpenCV格式
    
    Args:
        image_data: 图片字节数据
        
    Returns:
        OpenCV格式的图片数组
    """
    # 使用PIL读取图片
    image = Image.open(io.BytesIO(image_data))
    
    # 转换为RGB格式
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 转换为numpy数组
    img_array = np.array(image)
    
    # 转换为OpenCV格式 (BGR)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    return img_cv

def extract_text_from_ocr_result(result: list, score_threshold: float = 0.5) -> tuple:
    """
    从OCR结果中提取文本和置信度
    
    Args:
        result: OCR识别结果
        score_threshold: 置信度阈值
        
    Returns:
        (texts, scores): 文本列表和置信度列表
    """
    texts = []
    scores = []
    
    if result and len(result) > 0:
        page_result = result[0]
        
        # 检查是否是OCRResult对象（新版本PaddleOCR）
        if hasattr(page_result, 'rec_texts') and hasattr(page_result, 'rec_scores'):
            # 新版本PaddleOCR结果结构 - OCRResult对象
            rec_texts = page_result.rec_texts
            rec_scores = page_result.rec_scores
            for text, score in zip(rec_texts, rec_scores):
                if score >= score_threshold:  # 根据阈值过滤
                    texts.append(text)
                    scores.append(score)
        elif isinstance(page_result, dict) and 'rec_texts' in page_result and 'rec_scores' in page_result:
            # OCRResult对象实际上是字典格式
            rec_texts = page_result['rec_texts']
            rec_scores = page_result['rec_scores']
            for text, score in zip(rec_texts, rec_scores):
                if score >= score_threshold:  # 根据阈值过滤
                    texts.append(text)
                    scores.append(score)
        elif isinstance(page_result, dict):
            # 字典格式的结果
            if 'rec_texts' in page_result and 'rec_scores' in page_result:
                rec_texts = page_result['rec_texts']
                rec_scores = page_result['rec_scores']
                for text, score in zip(rec_texts, rec_scores):
                    if score >= score_threshold:  # 根据阈值过滤
                        texts.append(text)
                        scores.append(score)
            # 如果没有rec_texts，尝试其他字段
            elif 'text' in page_result:
                texts.append(page_result['text'])
                scores.append(1.0)
        # 旧版本的PaddleOCR结果结构
        elif isinstance(page_result, list):
            for line in page_result:
                if line and len(line) >= 2:
                    # line[1] 是 [text, confidence] 的格式
                    if isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                        text = line[1][0]  # 提取识别的文本
                        confidence = line[1][1]  # 提取置信度
                        if confidence >= score_threshold:  # 根据阈值过滤
                            texts.append(text)
                            scores.append(confidence)
    
    return texts, scores

def extract_detailed_ocr_result(result: list, score_threshold: float = 0.5) -> dict:
    """
    从OCR结果中提取详细的结构化数据
    
    Args:
        result: OCR识别结果
        score_threshold: 置信度阈值
        
    Returns:
        包含检测框、多边形、方向、阈值等详细信息的字典
    """
    detailed_result = {
        "bbox": [],             # 检测框多边形坐标
        "texts": [],            # 识别文本
        "scores": []            # 置信度
    }
    
    if result and len(result) > 0:
        page_result = result[0]
        
        # 检查是否是OCRResult对象（新版本PaddleOCR）
        if hasattr(page_result, 'rec_texts') and hasattr(page_result, 'rec_scores'):
            # 新版本PaddleOCR结果结构 - OCRResult对象
            rec_texts = page_result.rec_texts
            rec_scores = page_result.rec_scores
            
            # 检查是否有检测框信息
            if hasattr(page_result, 'dt_polys'):
                det_polys = page_result.dt_polys
                for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                    if score >= score_threshold:
                        detailed_result["texts"].append(text)
                        detailed_result["scores"].append(score)
                        if i < len(det_polys):
                            # 转换numpy数组为Python列表
                            poly_data = det_polys[i].tolist() if hasattr(det_polys[i], 'tolist') else det_polys[i]
                            detailed_result["bbox"].append(poly_data)
                        else:
                            detailed_result["bbox"].append([])
        elif isinstance(page_result, dict) and 'rec_texts' in page_result and 'rec_scores' in page_result:
            # OCRResult对象实际上是字典格式
            rec_texts = page_result['rec_texts']
            rec_scores = page_result['rec_scores']
            
            # 检查是否有检测框信息
            if 'dt_polys' in page_result:
                det_polys = page_result['dt_polys']
                for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                    if score >= score_threshold:
                        detailed_result["texts"].append(text)
                        detailed_result["scores"].append(score)
                        if i < len(det_polys):
                            # 转换numpy数组为Python列表
                            poly_data = det_polys[i].tolist() if hasattr(det_polys[i], 'tolist') else det_polys[i]
                            detailed_result["bbox"].append(poly_data)
                        else:
                            detailed_result["bbox"].append([])
        elif isinstance(page_result, dict):
            # 字典格式的结果
            if 'rec_texts' in page_result and 'rec_scores' in page_result:
                rec_texts = page_result['rec_texts']
                rec_scores = page_result['rec_scores']
                
                # 检查是否有检测框信息
                if 'det_polys' in page_result:
                    det_polys = page_result['det_polys']
                    for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                        if score >= score_threshold:
                            detailed_result["texts"].append(text)
                            detailed_result["scores"].append(score)
                            if i < len(det_polys):
                                detailed_result["bbox"].append(det_polys[i])
                            else:
                                detailed_result["bbox"].append([])
        elif isinstance(page_result, list):
            # 旧版本PaddleOCR结果结构
            for line in page_result:
                if line and len(line) >= 2:
                    if isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        if confidence >= score_threshold:
                            detailed_result["texts"].append(text)
                            detailed_result["scores"].append(confidence)
                            
                            # 检测框信息 - line[0] 是检测框坐标
                            if len(line) >= 1 and isinstance(line[0], list):
                                poly = line[0]
                                detailed_result["bbox"].append(poly)
                            else:
                                detailed_result["bbox"].append([])
    
    return detailed_result

def extract_ocr_result_for_json(result: list, score_threshold: float = 0.5) -> list:
    """
    从OCR结果中提取用于JSON格式的数据
    
    Args:
        result: OCR识别结果
        score_threshold: 置信度阈值
        
    Returns:
        包含text和bbox的字典列表
    """
    ocr_items = []
    
    if result and len(result) > 0:
        page_result = result[0]
        
        # 检查是否是OCRResult对象（新版本PaddleOCR）
        if hasattr(page_result, 'rec_texts') and hasattr(page_result, 'rec_scores'):
            # 新版本PaddleOCR结果结构 - OCRResult对象
            rec_texts = page_result.rec_texts
            rec_scores = page_result.rec_scores
            
            # 检查是否有检测框信息
            if hasattr(page_result, 'dt_polys'):
                det_polys = page_result.dt_polys
                for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                    if score >= score_threshold:
                        if i < len(det_polys):
                            # 转换numpy数组为Python列表
                            poly_data = det_polys[i].tolist() if hasattr(det_polys[i], 'tolist') else det_polys[i]
                            # 简化bbox为[x1, y1, x2, y2]格式
                            if len(poly_data) >= 4:
                                x_coords = [point[0] for point in poly_data]
                                y_coords = [point[1] for point in poly_data]
                                bbox = [int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords))]
                            else:
                                bbox = poly_data
                        else:
                            bbox = []
                        
                        ocr_items.append({
                            "text": text,
                            "bbox": bbox
                        })
        elif isinstance(page_result, dict) and 'rec_texts' in page_result and 'rec_scores' in page_result:
            # OCRResult对象实际上是字典格式
            rec_texts = page_result['rec_texts']
            rec_scores = page_result['rec_scores']
            
            # 检查是否有检测框信息
            if 'dt_polys' in page_result:
                det_polys = page_result['dt_polys']
                for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                    if score >= score_threshold:
                        if i < len(det_polys):
                            poly_data = det_polys[i].tolist() if hasattr(det_polys[i], 'tolist') else det_polys[i]
                            # 简化bbox为[x1, y1, x2, y2]格式
                            if len(poly_data) >= 4:
                                x_coords = [point[0] for point in poly_data]
                                y_coords = [point[1] for point in poly_data]
                                bbox = [int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords))]
                            else:
                                bbox = poly_data
                        else:
                            bbox = []
                        
                        ocr_items.append({
                            "text": text,
                            "bbox": bbox
                        })
        elif isinstance(page_result, list):
            # 旧版本PaddleOCR结果结构
            for line in page_result:
                if line and len(line) >= 2:
                    if isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        if confidence >= score_threshold:
                            # 检测框信息 - line[0] 是检测框坐标
                            if len(line) >= 1 and isinstance(line[0], list):
                                poly = line[0]
                                # 简化bbox为[x1, y1, x2, y2]格式
                                if len(poly) >= 4:
                                    x_coords = [point[0] for point in poly]
                                    y_coords = [point[1] for point in poly]
                                    bbox = [int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords))]
                                else:
                                    bbox = poly
                            else:
                                bbox = []
                            
                            ocr_items.append({
                                "text": text,
                                "bbox": bbox
                            })
    
    return ocr_items

def draw_ocr_result_on_image(img_cv, detailed_result, score_threshold=0.5):
    """
    在图片上绘制OCR检测结果
    
    Args:
        img_cv: OpenCV格式的图片
        detailed_result: 详细的OCR结果
        score_threshold: 置信度阈值
        
    Returns:
        绘制了检测框的图片（base64编码）
    """
    import cv2
    import base64
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    
    # 复制图片
    img_with_boxes = img_cv.copy()
    
    # 转换为PIL格式以支持中文显示
    img_pil = Image.fromarray(cv2.cvtColor(img_with_boxes, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # 尝试加载中文字体，如果失败则使用默认字体
    try:
        # 尝试使用系统中文字体
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            font = ImageFont.load_default()
    
    # 绘制检测框和文本
    for i, (bbox, text, score) in enumerate(zip(detailed_result["bbox"], 
                                               detailed_result["texts"], 
                                               detailed_result["scores"])):
        if score >= score_threshold and bbox:
            # 绘制检测框
            x1, y1, x2, y2 = map(int, bbox)
            draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=2)
            
            # 计算文本位置
            text_x = x1
            text_y = y1 - 25 if y1 - 25 > 10 else y1 + 25
            
            # 绘制文本背景
            text_display = f"{text} ({score:.2f})"
            bbox_text = draw.textbbox((text_x, text_y), text_display, font=font)
            draw.rectangle(bbox_text, fill=(0, 0, 0))
            
            # 绘制文本
            draw.text((text_x, text_y), text_display, fill=(0, 255, 0), font=font)
    
    # 转换回OpenCV格式
    img_with_boxes = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    # 转换为base64
    _, buffer = cv2.imencode('.png', img_with_boxes)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"

@app.get("/")
async def root():
    """API服务根路径"""
    return {"message": "PolyOCR API Service", "version": "1.0.0", "docs": "/docs"}

@app.post("/v1/ocr")
async def ocr_recognize(
    file: UploadFile = File(..., description="上传的图片文件"),
    language: str = Form(None, description="图片语言，参见附录一：OCR语言代码表"),
    preprocess: bool = Form(False, description="是否启用图像预处理"),
    score: float = Form(0.0, description="置信度阈值"),
    api_key: str = Depends(auth_required)
):
    """
    OCR识别接口
    
    Args:
        file: 上传的图片文件
        lang: 用户指定语言
        
    Returns:
        JSON格式的识别结果
    """
    start_time = time.time()
    task_id = str(uuid.uuid4())
    
    try:
        # 验证文件类型
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.tif', '.tiff'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": f"不支持的文件格式: {file_extension}",
                    "cost": time.time() - start_time,
                    "tid": task_id,
                    "data": ""
                }
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 处理图片
        img_cv = process_image(file_content)
        
        # 获取对应的模型
        try:
            if language:
                # 首先尝试使用预定义的模型映射
                model_name = get_model_for_language(language)
                ocr = load_model(model_name)
            else:
                # 如果没有指定语言，使用默认的中文模型
                ocr = load_model("ch")
        except ValueError:
            # 如果预定义映射中没有，尝试直接使用语言代码
            try:
                if language:
                    ocr = load_model_by_language(language)
                else:
                    ocr = load_model("ch")
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={
                        "code": 1,
                        "msg": f"不支持的语言: {language}",
                        "cost": time.time() - start_time,
                        "tid": task_id,
                        "data": []
                    }
                )
        
        # 执行OCR识别
        result = ocr.ocr(img_cv)
        
        # 计算耗时
        cost_time = time.time() - start_time
        
        # 返回OCR识别结果，符合新的API规范
        if result and len(result) > 0 and result[0]:
            ocr_items = extract_ocr_result_for_json(result, score)  # 使用传入的置信度阈值
        else:
            ocr_items = []
        
        return JSONResponse(
            content={
                "code": 0,
                "msg": "识别成功",
                "cost": round(cost_time, 3),
                "tid": task_id,
                "data": ocr_items
            }
        )
        
    except Exception as e:
        cost_time = time.time() - start_time
        return JSONResponse(
            status_code=500,
            content={
                "code": 10001,
                "msg": "请求内部错误",
                "cost": round(cost_time, 3),
                "tid": task_id,
                "data": None
            }
        )

@app.get("/v1/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "models_loaded": list(model_cache.keys())}

@app.get("/v1/languages")
async def get_supported_languages():
    """获取支持的语言列表"""
    languages = {}
    for model_name, langs in LANGUAGE_MODEL_MAPPING.items():
        languages[model_name] = langs
    
    return {
        "code": 0,
        "msg": "获取成功",
        "data": languages
    }

@app.get("/v1/languages/paddleocr")
async def get_paddleocr_languages():
    """获取PaddleOCR支持的所有语言列表"""
    paddleocr_languages = get_supported_paddleocr_languages()
    
    return {
        "code": 0,
        "msg": "获取成功",
        "data": {
            "languages": paddleocr_languages,
            "count": len(paddleocr_languages),
            "description": "PaddleOCR官方支持的语言代码列表"
        }
    }

# 翻译相关路由
@app.post("/v1/translation/translate")
async def translate_texts(
    texts: list = Form(...),
    source_language: str = Form("中文"),
    target_language: str = Form("英文"),
    api_key: str = Form(None),
    model_name: str = Form(None),
    base_url: str = Form(None),
    auth_key: str = Depends(auth_required)
):
    """翻译文本接口"""
    return await translate_texts_endpoint(
        texts, source_language, target_language, 
        api_key, model_name, base_url
    )

@app.post("/v1/translation/config")
async def update_config(
    api_key: str = Form(...),
    model_name: str = Form("gpt-3.5-turbo"),
    base_url: str = Form("https://api.openai.com/v1"),
    prompt_template: str = Form(None)
):
    """更新翻译配置"""
    return await update_translation_config(
        api_key, model_name, base_url, prompt_template
    )

@app.get("/v1/translation/config")
async def get_config():
    """获取翻译配置"""
    return await get_translation_config()

@app.get("/v1/translation/health")
async def translation_health():
    """翻译服务健康检查"""
    return await health_check_translation()

@app.get("/v1/translation/languages")
async def get_translation_languages():
    """获取翻译支持的语言列表"""
    return await get_supported_languages_endpoint()

@app.post("/v2/translate")
async def v2_translate(
    request: dict,
    api_key: str = Depends(auth_required)
):
    """v2翻译接口 - 支持JSON格式"""
    from translation import V2TranslationRequest
    v2_request = V2TranslationRequest(**request)
    return await v2_translate_texts_endpoint(v2_request)

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs("static", exist_ok=True)
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=16110,
        reload=True,
        log_level="info"
    )
