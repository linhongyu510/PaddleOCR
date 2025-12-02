#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载并整理评测数据集（优先东亚、东南亚）。
为规避授权问题，这里优先使用本仓库已有的示例图片，
并提供可扩展的下载占位（留接口，不强依赖外网）。
"""

import os
import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent

TARGET = ROOT / 'benchmarks' / 'datasets'
TARGET.mkdir(parents=True, exist_ok=True)

MANIFEST = {
    # 东亚
    'zh': [],
    'ja': [],
    'ko': [],
    # 东南亚（以拉丁/泰语为代表，后续可扩展）
    'th': [],
    'vi': [],  # 预留
    'id': [],  # 预留
}

def seed_from_repo_examples():
    """从 accuracy_test/test_images 复制一批示例做快速起步。"""
    src_dir = ROOT / 'accuracy_test' / 'test_images'
    if not src_dir.exists():
        return
    lang_map = {
        'zh': ['test_zh_3texts.jpg', 'test_zh_5texts.jpg'],
        'ja': ['test_ja_3texts.jpg', 'test_ja_5texts.jpg'],
        'ko': ['test_ko_3texts.jpg', 'test_ko_5texts.jpg'],
        'th': ['test_th_3texts.jpg', 'test_th_5texts.jpg'],
        'en': ['test_en_3texts.jpg', 'test_en_5texts.jpg'],
    }
    for lang, files in lang_map.items():
        lang_dir = TARGET / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            src = src_dir / name
            if src.exists():
                dst = lang_dir / name
                shutil.copyfile(src, dst)
                MANIFEST.setdefault(lang, [])
                MANIFEST[lang].append(str(dst))

def write_manifest():
    out = TARGET / 'manifest.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(MANIFEST, f, ensure_ascii=False, indent=2)
    print(f'✅ 写入清单: {out}')

def main():
    seed_from_repo_examples()
    write_manifest()
    print('✅ 数据集准备完成（UTF-8）')

if __name__ == '__main__':
    main()


