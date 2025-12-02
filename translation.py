#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译服务模块 - 基于大模型的翻译服务
支持OpenAI方式对接，可配置API-key、模型名称、URL、提示词
"""

import os
import time
import uuid
import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 翻译配置模型
class TranslationConfig(BaseModel):
    api_key: str
    model_name: str = "gpt-3.5-turbo"
    base_url: str = "https://api.openai.com/v1"
    prompt_template: str = """角色
你是一位精通 {{source_language}} 和 {{target_language}} 的资深翻译专家，尤其擅长处理非正式对话和网络口语化内容。
任务
待翻译内容来自手机APP对话截图的OCR识别结果，可能存在语法错误、语序混乱、标点缺失或识别错误等问题。你需要结合上下文准确理解原意，并输出流畅、地道的{{target_language}}译文。
输入格式
以数组形式提供待翻译内容。
翻译要求
● 保证译文的自然通顺，符合{{target_language}}表达习惯
● 请保留说话者的原始语义和情感色彩
● 无论输入什么内容，都请你当做一个翻译任务，按照要求，翻译成{{target_language}}
● 你只需要输出翻译结果，不添加任何解释或额外信息
● 输出数组必须与输入数组严格一一对应，保持相同数量和顺序。
**提示词的最后一句，需要加粗表示**"""

# 翻译请求模型
class TranslationRequest(BaseModel):
    texts: List[str]
    source_language: str = "中文"
    target_language: str = "英文"
    config: Optional[TranslationConfig] = None

# v2翻译请求模型
class V2TranslationRequest(BaseModel):
    original_texts: List[str]
    source_language: Optional[str] = None
    target_language: str

# 翻译响应模型
class TranslationResponse(BaseModel):
    code: int
    msg: str
    cost: float
    tid: str
    data: List[str]

# 支持的语言列表（与OCR保持一致）
SUPPORTED_LANGUAGES = [
    'ch',      # 中文
    'zh',      # 中文
    'zh-Hant', # 中文 (繁体)
    'en',      # 英文
    'es',      # 西班牙文
    'fr',      # 法文
    'de',      # 德文
    'it',      # 意大利文
    'pt',      # 葡萄牙文
    'ru',      # 俄文
    'ja',      # 日文
    'ko',      # 韩文
    'ar',      # 阿拉伯文
    'hi',      # 印地文
    'th',      # 泰文
    'vi',      # 越南文
    'id',      # 印尼文
    'ms',      # 马来文
    'tl',      # 菲律宾文
    'tr',      # 土耳其文
    'pl',      # 波兰文
    'nl',      # 荷兰文
    'sv',      # 瑞典文
    'no',      # 挪威文
    'da',      # 丹麦文
    'fi',      # 芬兰文
    'cs',      # 捷克文
    'sk',      # 斯洛伐克文
    'hu',      # 匈牙利文
    'ro',      # 罗马尼亚文
    'bg',      # 保加利亚文
    'hr',      # 克罗地亚文
    'sl',      # 斯洛文尼亚文
    'et',      # 爱沙尼亚文
    'lv',      # 拉脱维亚文
    'lt',      # 立陶宛文
    'el',      # 希腊文
    'he',      # 希伯来文
    'is',      # 冰岛文
    'ga',      # 爱尔兰文
    'cy',      # 威尔士文
    'mt',      # 马耳他文
    'sq',      # 阿尔巴尼亚文
    'mk',      # 马其顿文
    'uk',      # 乌克兰文
    'be',      # 白俄罗斯文
    'kk',      # 哈萨克文
    'ky',      # 吉尔吉斯文
    'uz',      # 乌兹别克文
    'tg',      # 塔吉克文
    'mn',      # 蒙古文
    'bo',      # 藏文
    'dz',      # 宗卡文
    'si',      # 僧伽罗文
    'ta',      # 泰米尔文
    'te',      # 泰卢固文
    'kn',      # 卡纳达文
    'ml',      # 马拉雅拉姆文
    'gu',      # 古吉拉特文
    'pa',      # 旁遮普文
    'or',      # 奥里亚文
    'as',      # 阿萨姆文
    'bn',      # 孟加拉文
    'ur',      # 乌尔都文
    'ne',      # 尼泊尔文
    'mr',      # 马拉地文
    'sa',      # 梵文
    'sd',      # 信德文
    'ps',      # 普什图文
    'fa',      # 波斯文
    'ku',      # 库尔德文
    'my',      # 缅甸文
    'km',      # 高棉文
    'lo',      # 老挝文
    'am',      # 阿姆哈拉文
    'ti',      # 提格雷尼亚文
    'om',      # 奥罗莫文
    'so',      # 索马里文
    'sw',      # 斯瓦希里文
    'yo',      # 约鲁巴文
    'ig',      # 伊博文
    'ha',      # 豪萨文
    'zu',      # 祖鲁文
    'xh',      # 科萨文
    'af',      # 南非荷兰文
    'st',      # 塞索托文
    'tn',      # 茨瓦纳文
    'ss',      # 斯威士文
    've',      # 文达文
    'ts',      # 聪加文
    'nr',      # 南恩德贝勒文
    'nso',     # 北索托文
    'tk',      # 土库曼文
    'az',      # 阿塞拜疆文
    'ab',      # 阿布哈兹文
    'ru_mold', # 摩尔多瓦俄文
    'oc',      # 欧西坦文
    'rs_cyrillic',  # 塞尔维亚文（西里尔字母）
    'rs_latin',     # 塞尔维亚文（拉丁字母）
    'sr',      # 塞尔维亚文
    'latin',   # 拉丁语系
    'eslav',   # 斯拉夫语系
    'chinese_cht',  # 繁体中文
    'korean',  # 韩文
    'japan',   # 日文
    'ug',      # 维吾尔文
    
    # 新增的语言编码
    'eu',      # 巴斯克语
    'fy',      # 弗里斯兰语
    'eo',      # 世界语
    'gd',      # 苏格兰盖尔语
    'tt',      # 鞑靼语
    'ceb',     # 宿务语
    'la',      # 拉丁语
    'sh',      # 塞尔维亚-克罗地亚语
    'nn',      # 新挪威语
    'hy',      # 亚美尼亚语
    'yi',      # 意第绪语
    'lb',      # 卢森堡语
    'bcl',     # 中比科尔语
    'hsb',     # 上索布语
    'lmo',     # 伦巴第语
    'bs',      # 波斯尼亚语
    'war',     # 瓦瑞语
    'cv',      # 楚瓦什语
    'ckb',     # 中库尔德语
    'arz',     # 埃及阿拉伯语
    'pnb',     # 西旁遮普语
    'ht',      # 海地克里奥尔语
    'dv',      # 迪维希语
    'ast',     # 阿斯图里亚斯语
    'mg',      # 马达加斯加语
    'jv',      # 爪哇语
    'nds',     # 低地德语
    'su',      # 巽他语
    'ca',      # 加泰罗尼亚语
    'gl',      # 加利西亚语
]

# 语言代码到中文名称的映射
LANGUAGE_NAMES = {
    # 主要语言
    'ch': '中文',
    'zh': '中文',
    'zh-Hant': '中文 (繁体)',
    'chinese_cht': '繁体中文',
    'en': '英语',
    'es': '西班牙语',
    'fr': '法语',
    'de': '德语',
    'it': '意大利语',
    'pt': '葡萄牙语',
    'ru': '俄语',
    'ja': '日语',
    'ko': '韩语',
    'ar': '阿拉伯语',
    'hi': '印地语',
    'th': '泰语',
    'vi': '越南语',
    'id': '印尼语',
    'ms': '马来语',
    'tl': '菲律宾语',
    'tr': '土耳其语',
    
    # 欧洲语言
    'pl': '波兰语',
    'nl': '荷兰语',
    'sv': '瑞典语',
    'no': '挪威语',
    'da': '丹麦语',
    'fi': '芬兰语',
    'cs': '捷克语',
    'sk': '斯洛伐克语',
    'hu': '匈牙利语',
    'ro': '罗马尼亚语',
    'bg': '保加利亚语',
    'hr': '克罗地亚语',
    'sl': '斯洛文尼亚语',
    'et': '爱沙尼亚语',
    'lv': '拉脱维亚语',
    'lt': '立陶宛语',
    'el': '希腊语',
    'he': '希伯来语',
    'is': '冰岛语',
    'ga': '爱尔兰语',
    'cy': '威尔士语',
    'mt': '马耳他语',
    'sq': '阿尔巴尼亚语',
    'mk': '马其顿语',
    'uk': '乌克兰语',
    'be': '白俄罗斯语',
    
    # 亚洲语言
    'kk': '哈萨克语',
    'ky': '吉尔吉斯语',
    'uz': '乌兹别克语',
    'tg': '塔吉克语',
    'mn': '蒙古语',
    'bo': '藏语',
    'dz': '宗卡语',
    'si': '僧伽罗语',
    'ta': '泰米尔语',
    'te': '泰卢固语',
    'kn': '卡纳达语',
    'ml': '马拉雅拉姆语',
    'gu': '古吉拉特语',
    'pa': '旁遮普语',
    'or': '奥里亚语',
    'as': '阿萨姆语',
    'bn': '孟加拉语',
    'ur': '乌尔都语',
    'ne': '尼泊尔语',
    'mr': '马拉地语',
    'sa': '梵语',
    'sd': '信德语',
    'ps': '普什图语',
    'fa': '波斯语',
    'ku': '库尔德语',
    'my': '缅甸语',
    'km': '高棉语',
    'lo': '老挝语',
    
    # 非洲语言
    'am': '阿姆哈拉语',
    'ti': '提格雷尼亚语',
    'om': '奥罗莫语',
    'so': '索马里语',
    'sw': '斯瓦希里语',
    'yo': '约鲁巴语',
    'ig': '伊博语',
    'ha': '豪萨语',
    'zu': '祖鲁语',
    'xh': '科萨语',
    'af': '南非荷兰语',
    'st': '塞索托语',
    'tn': '茨瓦纳语',
    'ss': '斯威士语',
    've': '文达语',
    'ts': '聪加语',
    'nr': '南恩德贝勒语',
    'nso': '北索托语',
    
    # 其他语言
    'tk': '土库曼语',
    'az': '阿塞拜疆语',
    'ab': '阿布哈兹语',
    'ru_mold': '摩尔多瓦俄语',
    'oc': '欧西坦语',
    'rs_cyrillic': '塞尔维亚语（西里尔字母）',
    'rs_latin': '塞尔维亚语（拉丁字母）',
    'sr': '塞尔维亚语',
    'latin': '拉丁语系',
    'eslav': '斯拉夫语系',
    
    # 新增的语言编码映射
    'eu': '巴斯克语',
    'fy': '弗里斯兰语',
    'eo': '世界语',
    'gd': '苏格兰盖尔语',
    'tt': '鞑靼语',
    'ceb': '宿务语',
    'la': '拉丁语',
    'sh': '塞尔维亚-克罗地亚语',
    'nn': '新挪威语',
    'hy': '亚美尼亚语',
    'yi': '意第绪语',
    'lb': '卢森堡语',
    'bcl': '中比科尔语',
    'hsb': '上索布语',
    'lmo': '伦巴第语',
    'bs': '波斯尼亚语',
    'war': '瓦瑞语',
    'cv': '楚瓦什语',
    'ckb': '中库尔德语',
    'arz': '埃及阿拉伯语',
    'pnb': '西旁遮普语',
    'ht': '海地克里奥尔语',
    'dv': '迪维希语',
    'ast': '阿斯图里亚斯语',
    'mg': '马达加斯加语',
    'jv': '爪哇语',
    'nds': '低地德语',
    'su': '巽他语',
    'ug': '维吾尔语',
    'ca': '加泰罗尼亚语',
    'gl': '加利西亚语',
}

# 中文名称到语言代码的反向映射
LANGUAGE_CODES = {v: k for k, v in LANGUAGE_NAMES.items()}

def get_supported_languages():
    """获取支持的语言列表"""
    return SUPPORTED_LANGUAGES

def get_language_name(lang_code: str) -> str:
    """获取语言代码对应的中文名称"""
    return LANGUAGE_NAMES.get(lang_code, lang_code)

def validate_language(lang_code: str) -> bool:
    """验证语言代码是否支持"""
    return lang_code in SUPPORTED_LANGUAGES

def normalize_language_input(language_input: str) -> tuple[str, str]:
    """
    标准化语言输入，支持编码和中文名称两种方式
    
    Args:
        language_input: 用户输入的语言参数（可以是编码或中文名称）
        
    Returns:
        tuple: (语言代码, 中文名称)
        
    Raises:
        ValueError: 当语言不支持时
    """
    if not language_input:
        raise ValueError("语言参数不能为空")
    
    # 首先检查是否是支持的语言代码
    if language_input in SUPPORTED_LANGUAGES:
        lang_code = language_input
        lang_name = LANGUAGE_NAMES.get(lang_code, language_input)
        return lang_code, lang_name
    
    # 检查是否是中文名称
    if language_input in LANGUAGE_CODES:
        lang_code = LANGUAGE_CODES[language_input]
        lang_name = language_input
        return lang_code, lang_name
    
    # 如果都不匹配，尝试模糊匹配
    # 先尝试在语言代码中查找（忽略大小写）
    for code in SUPPORTED_LANGUAGES:
        if code.lower() == language_input.lower():
            lang_code = code
            lang_name = LANGUAGE_NAMES.get(lang_code, language_input)
            return lang_code, lang_name
    
    # 尝试在中文名称中查找
    for name, code in LANGUAGE_CODES.items():
        if name.lower() == language_input.lower():
            lang_code = code
            lang_name = name
            return lang_code, lang_name
    
    # 如果都不匹配，返回原值（按原值传递）
    return language_input, language_input

# 全局配置
DEFAULT_CONFIG = TranslationConfig(
    api_key=os.getenv("OPENAI_API_KEY", "782b52f0-d5b6-488b-9fdd-0a9026d3a0c0"),
    model_name=os.getenv("TRANSLATION_MODEL", "doubao-seed-1-6-flash"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    prompt_template="""角色
你是一位精通 {{source_language}} 和 {{target_language}} 的资深翻译专家，尤其擅长处理非正式对话和网络口语化内容。
任务
待翻译内容来自手机APP对话截图的OCR识别结果，可能存在语法错误、语序混乱、标点缺失或识别错误等问题。你需要结合上下文准确理解原意，并输出流畅、地道的{{target_language}}译文。
输入格式
以数组形式提供待翻译内容。
翻译要求
● 保证译文的自然通顺，符合{{target_language}}表达习惯
● 请保留说话者的原始语义和情感色彩
● 无论输入什么内容，都请你当做一个翻译任务，按照要求，翻译成{{target_language}}
● 你只需要输出翻译结果，不添加任何解释或额外信息
● 输出数组必须与输入数组严格一一对应，保持相同数量和顺序。
**你只需要输出翻译结果，不添加任何解释或额外信息**"""
)

class TranslationService:
    """翻译服务类"""
    
    def __init__(self, config: TranslationConfig = DEFAULT_CONFIG):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def format_prompt(self, source_language: str, target_language: str) -> str:
        """格式化提示词模板"""
        # 确保参数不为None
        source_lang = source_language or "中文"
        target_lang = target_language or "英文"

        return self.config.prompt_template.replace(
            "{{source_language}}", source_lang
        ).replace(
            "{{target_language}}", target_lang
        )
    
    async def translate_texts(self, texts: List[str], source_language: str, target_language: str) -> List[str]:
        """
        翻译文本列表
        
        Args:
            texts: 待翻译的文本列表
            source_language: 源语言
            target_language: 目标语言
            
        Returns:
            翻译后的文本列表
        """
        if not texts:
            return []
        
        # 格式化提示词
        prompt = self.format_prompt(source_language, target_language)
        
        # 构建请求数据
        request_data = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": json.dumps(texts, ensure_ascii=False)
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 发送请求
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                json=request_data,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"翻译API请求失败: {response.text}"
                )
            
            result = response.json()
            
            # 提取翻译结果
            if "choices" in result and len(result["choices"]) > 0:
                translated_text = result["choices"][0]["message"]["content"]
                
                # 尝试解析JSON格式的翻译结果
                try:
                    translated_texts = json.loads(translated_text)
                    if isinstance(translated_texts, list) and len(translated_texts) == len(texts):
                        return translated_texts
                    else:
                        # 如果解析失败或长度不匹配，按行分割
                        return translated_text.strip().split('\n')
                except json.JSONDecodeError:
                    # 如果JSON解析失败，按行分割
                    return translated_text.strip().split('\n')
            else:
                raise HTTPException(
                    status_code=500,
                    detail="翻译API返回格式错误"
                )
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408,
                detail="翻译请求超时"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"翻译请求失败: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"翻译处理失败: {str(e)}"
            )
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

# 全局翻译服务实例
translation_service = TranslationService()

async def translate_texts_endpoint(
    texts: List[str] = Form(...),
    source_language: str = Form("中文"),
    target_language: str = Form("英文"),
    api_key: Optional[str] = Form(None),
    model_name: Optional[str] = Form(None),
    base_url: Optional[str] = Form(None)
):
    """
    翻译文本接口
    
    Args:
        texts: 待翻译的文本列表
        source_language: 源语言
        target_language: 目标语言
        api_key: API密钥（可选，覆盖默认配置）
        model_name: 模型名称（可选，覆盖默认配置）
        base_url: API基础URL（可选，覆盖默认配置）
        
    Returns:
        翻译结果
    """
    start_time = time.time()
    task_id = str(uuid.uuid4())
    
    try:
        # 标准化语言输入，支持编码和中文名称两种方式
        try:
            source_lang_code, source_lang_name = normalize_language_input(source_language)
            target_lang_code, target_lang_name = normalize_language_input(target_language)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
        # 验证语言代码是否在支持列表中
        if source_lang_code not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的源语言: {source_language}。支持的语言: {', '.join(SUPPORTED_LANGUAGES[:10])}..."
            )
        
        if target_lang_code not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的目标语言: {target_language}。支持的语言: {', '.join(SUPPORTED_LANGUAGES[:10])}..."
            )
        # 创建临时配置（如果提供了覆盖参数）
        config = translation_service.config
        if api_key or model_name or base_url:
            config = TranslationConfig(
                api_key=api_key or translation_service.config.api_key,
                model_name=model_name or translation_service.config.model_name,
                base_url=base_url or translation_service.config.base_url,
                prompt_template=translation_service.config.prompt_template
            )
        
        # 创建临时翻译服务实例
        temp_service = TranslationService(config)
        
        try:
            # 执行翻译（使用中文名称）
            translated_texts = await temp_service.translate_texts(
                texts, source_lang_name, target_lang_name
            )
            
            # 计算耗时
            cost_time = time.time() - start_time
            
            return JSONResponse(
                content={
                    "code": 0,
                    "msg": "翻译成功",
                    "cost": round(cost_time, 3),
                    "tid": task_id,
                    "data": translated_texts
                }
            )
            
        finally:
            # 关闭临时服务
            await temp_service.close()
            
    except HTTPException as e:
        cost_time = time.time() - start_time
        return JSONResponse(
            status_code=e.status_code,
            content={
                "code": 1,
                "msg": f"翻译失败: {e.detail}",
                "cost": round(cost_time, 3),
                "tid": task_id,
                "data": []
            }
        )
    except Exception as e:
        cost_time = time.time() - start_time
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"翻译失败: {str(e)}",
                "cost": round(cost_time, 3),
                "tid": task_id,
                "data": []
            }
        )

async def update_translation_config(
    api_key: str = Form(...),
    model_name: str = Form("gpt-3.5-turbo"),
    base_url: str = Form("https://api.openai.com/v1"),
    prompt_template: Optional[str] = Form(None)
):
    """
    更新翻译配置
    
    Args:
        api_key: API密钥
        model_name: 模型名称
        base_url: API基础URL
        prompt_template: 提示词模板（可选）
        
    Returns:
        配置更新结果
    """
    try:
        # 更新全局配置
        translation_service.config.api_key = api_key
        translation_service.config.model_name = model_name
        translation_service.config.base_url = base_url
        
        if prompt_template:
            translation_service.config.prompt_template = prompt_template
        
        return JSONResponse(
            content={
                "code": 0,
                "msg": "配置更新成功",
                "data": {
                    "api_key": api_key[:10] + "..." if len(api_key) > 10 else api_key,
                    "model_name": model_name,
                    "base_url": base_url,
                    "prompt_template": prompt_template[:100] + "..." if prompt_template and len(prompt_template) > 100 else prompt_template
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"配置更新失败: {str(e)}",
                "data": None
            }
        )

async def get_translation_config():
    """
    获取当前翻译配置
    
    Returns:
        当前配置信息
    """
    try:
        return JSONResponse(
            content={
                "code": 0,
                "msg": "获取配置成功",
                "data": {
                    "api_key": translation_service.config.api_key[:10] + "..." if len(translation_service.config.api_key) > 10 else translation_service.config.api_key,
                    "model_name": translation_service.config.model_name,
                    "base_url": translation_service.config.base_url,
                    "prompt_template": translation_service.config.prompt_template
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"获取配置失败: {str(e)}",
                "data": None
            }
        )

async def v2_translate_texts_endpoint(request: V2TranslationRequest):
    """
    v2翻译文本接口 - 支持JSON格式请求
    
    Args:
        request: v2翻译请求对象
        
    Returns:
        翻译结果
    """
    start_time = time.time()
    task_id = str(uuid.uuid4())
    
    try:
        # 标准化语言输入，支持编码和中文名称两种方式
        try:
            # 如果没有指定源语言，默认使用中文
            source_lang_input = request.source_language or "zh"
            source_lang_code, source_lang_name = normalize_language_input(source_lang_input)
            target_lang_code, target_lang_name = normalize_language_input(request.target_language)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
        # 验证语言代码是否在支持列表中
        if source_lang_code and source_lang_code not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的源语言: {request.source_language}"
            )
        
        if target_lang_code not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的目标语言: {request.target_language}"
            )
        
        # 创建临时翻译服务实例
        temp_service = TranslationService()
        
        try:
            # 执行翻译
            translated_texts = await temp_service.translate_texts(
                request.original_texts, source_lang_name, target_lang_name
            )
            
            # 计算耗时
            cost_time = time.time() - start_time
            
            return JSONResponse(
                content={
                    "code": 0,
                    "msg": "翻译成功",
                    "cost": round(cost_time, 3),
                    "tid": task_id,
                    "data": translated_texts
                }
            )
            
        finally:
            # 关闭临时服务
            await temp_service.close()
            
    except HTTPException as e:
        cost_time = time.time() - start_time
        return JSONResponse(
            status_code=e.status_code,
            content={
                "code": 1,
                "msg": f"翻译失败: {e.detail}",
                "cost": round(cost_time, 3),
                "tid": task_id,
                "data": []
            }
        )
    except Exception as e:
        cost_time = time.time() - start_time
        return JSONResponse(
            status_code=500,
            content={
                "code": 10001,
                "msg": f"请求内部错误: {str(e)}",
                "cost": round(cost_time, 3),
                "tid": task_id,
                "data": None
            }
        )

async def get_supported_languages_endpoint():
    """
    获取支持的语言列表
    
    Returns:
        支持的语言列表
    """
    try:
        languages = []
        for lang_code in SUPPORTED_LANGUAGES:
            languages.append({
                "code": lang_code,
                "name": get_language_name(lang_code)
            })
        
        return JSONResponse(
            content={
                "code": 0,
                "msg": "获取语言列表成功",
                "data": {
                    "languages": languages,
                    "total": len(languages)
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"获取语言列表失败: {str(e)}",
                "data": None
            }
        )

async def health_check_translation():
    """
    翻译服务健康检查
    
    Returns:
        服务状态
    """
    try:
        # 简单的配置检查
        config = translation_service.config
        return JSONResponse(
            content={
                "code": 0,
                "msg": "翻译服务正常",
                "data": {
                    "api_key_configured": bool(config.api_key),
                    "model_name": config.model_name,
                    "base_url": config.base_url,
                    "status": "healthy"
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"翻译服务异常: {str(e)}",
                "data": None
            }
        )
