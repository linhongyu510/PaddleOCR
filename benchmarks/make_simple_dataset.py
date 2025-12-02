#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从现有示例拷贝每种语言 1 张图片到同一文件夹 benchmarks/simple_dataset。
确保文件名与语言对应，生成 simple_manifest.json（UTF-8）。
"""

import shutil
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'accuracy_test' / 'test_images'
DST = ROOT / 'benchmarks' / 'simple_dataset'
DST.mkdir(parents=True, exist_ok=True)

LANG_TO_FILE = {
    'zh': 'test_zh_3texts.jpg',
    'en': 'test_en_3texts.jpg',
    'ja': 'test_ja_3texts.jpg',
    'ko': 'test_ko_3texts.jpg',
    'th': 'test_th_3texts.jpg'
}

def main():
    manifest = []
    for lang, fname in LANG_TO_FILE.items():
        src = SRC / fname
        if not src.exists():
            continue
        dst = DST / f'{lang}.jpg'
        shutil.copyfile(src, dst)
        manifest.append({'language': lang, 'path': str(dst)})
    out = DST / 'simple_manifest.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print('✅ 简洁数据集就绪:', out)

if __name__ == '__main__':
    main()


