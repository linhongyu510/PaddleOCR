#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time
from pathlib import Path
import argparse
import requests


def call(server, img_path: Path, language: str, api_key: str, score: float):
    files = {
        'file': (img_path.name, open(img_path, 'rb'), 'image/png')
    }
    data = {
        'language': language,
        'preprocess': 'true',
        'score_threshold': str(score)
    }
    headers = { 'Authorization': f'Bearer {api_key}' }
    r = requests.post(f"{server}/v1/ocr", files=files, data=data, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--server', default='http://localhost:8000')
    ap.add_argument('--api_key', default=os.getenv('POLYOCR_API_KEY', ''))
    ap.add_argument('--manifest', default='benchmarks/synthetic/manifest.json')
    ap.add_argument('--out', default='benchmarks/synthetic_results.json')
    ap.add_argument('--score', type=float, default=0.5)
    args = ap.parse_args()

    with open(args.manifest, 'r', encoding='utf-8') as f:
        items = json.load(f)

    per_lang = {}
    detailed = []
    for it in items:
        lang = it['language']
        path = Path(it['path'])
        start = time.time()
        res = call(args.server, path, lang, args.api_key, args.score)
        elapsed = time.time() - start
        data = res.get('items', []) if isinstance(res, dict) else []
        texts = [d.get('text', '') for d in data if isinstance(d, dict)]
        non_empty = any(t.strip() for t in texts)
        detailed.append({
            'language': lang,
            'image': str(path),
            'elapsed': round(elapsed, 3),
            'non_empty': bool(non_empty),
            'texts': texts,
        })
        s = per_lang.setdefault(lang, {'total': 0, 'ok': 0, 'elapsed_sum': 0.0})
        s['total'] += 1
        s['elapsed_sum'] += elapsed
        s['ok'] += 1 if non_empty else 0

    summary = {}
    overall_total = 0
    overall_ok = 0
    overall_elapsed = 0.0
    for lang, s in per_lang.items():
        summary[lang] = {
            'total': s['total'],
            'non_empty_rate': round(s['ok'] / max(s['total'], 1), 4),
            'avg_elapsed': round(s['elapsed_sum'] / max(s['total'], 1), 3)
        }
        overall_total += s['total']
        overall_ok += s['ok']
        overall_elapsed += s['elapsed_sum']

    overall = {
        'total': overall_total,
        'non_empty_rate': round(overall_ok / max(overall_total, 1), 4),
        'avg_elapsed': round(overall_elapsed / max(overall_total, 1), 3)
    }

    out = Path(args.out)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'summary': overall, 'per_language': summary, 'details': detailed}, f, ensure_ascii=False, indent=2)
    print('✅ 合成集评测完成，结果写入', out)


if __name__ == '__main__':
    main()
