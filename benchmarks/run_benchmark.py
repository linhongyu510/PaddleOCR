#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调用服务的 /v1/ocr 接口对各语言数据进行批量测试（默认 http://localhost:8000，可用 --server 覆盖）。
确保所有 I/O 使用 UTF-8，避免编码问题。
"""

import os
import json
import time
import argparse
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent

def load_manifest(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def call_ocr(server: str, img_path: Path, language: str, score: float, api_key: str):
    data = {
        'language': language,
        'score_threshold': str(score)
    }
    headers = { 'Authorization': f'Bearer {api_key}' }
    with open(img_path, 'rb') as handle:
        files = { 'file': (img_path.name, handle, 'image/jpeg') }
        resp = requests.post(f"{server}/v1/ocr", files=files, data=data, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--server', default='http://localhost:8000')
    ap.add_argument('--score', type=float, default=0.5)
    ap.add_argument('--api_key', default=os.getenv('POLYOCR_API_KEY', ''))
    ap.add_argument('--datasets', default=str((ROOT / 'benchmarks' / 'datasets' / 'manifest.json')))
    ap.add_argument('--out', default=str((ROOT / 'benchmarks' / 'results')))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(Path(args.datasets))
    summary = {}
    for lang, files in manifest.items():
        results = []
        lang_dir = out_dir / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        for fp in files:
            img = Path(fp)
            try:
                start = time.time()
                res = call_ocr(args.server, img, lang, args.score, args.api_key)
                elapsed = time.time() - start
                item = {
                    'image': str(img),
                    'elapsed': round(elapsed, 3),
                    'response': res
                }
                results.append(item)
            except Exception as e:
                results.append({'image': str(img), 'error': str(e)})
        with open(lang_dir / 'results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        summary[lang] = {'count': len(results)}

    with open(out_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print('✅ 基准测试完成，结果已写入', out_dir)

if __name__ == '__main__':
    main()

