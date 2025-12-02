#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
读取 benchmarks/results 下的语言结果，做简单评估：
- 成功率（code==0 的比例）
- 平均耗时
- 文本长度均值（粗略衡量识别量）
所有 I/O 均为 UTF-8，避免编码问题。
"""

import os
import json
from pathlib import Path
import argparse

def stat_lang(dir_path: Path):
    fp = dir_path / 'results.json'
    if not fp.exists():
        return None
    with open(fp, 'r', encoding='utf-8') as f:
        items = json.load(f)
    total = len(items)
    success = 0
    elapsed_sum = 0.0
    text_len_sum = 0
    for it in items:
        res = it.get('response')
        if isinstance(res, dict) and res.get('code') == 0:
            success += 1
            elapsed_sum += float(it.get('elapsed', 0.0))
            data = res.get('data', [])
            # data 为列表，每项含 text
            if isinstance(data, list):
                texts = [d.get('text', '') for d in data if isinstance(d, dict)]
                text_len_sum += sum(len(t) for t in texts)
    if total == 0:
        return None
    return {
        'total': total,
        'success': success,
        'success_rate': round(success / total, 4),
        'avg_elapsed': round(elapsed_sum / max(success, 1), 3),
        'avg_text_len': round(text_len_sum / max(success, 1), 1)
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default='benchmarks/results')
    args = ap.parse_args()

    root = Path(args.results)
    report = {}
    for lang_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        s = stat_lang(lang_dir)
        if s:
            report[lang_dir.name] = s

    out = root / 'report.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('✅ 评估完成，报告写入', out)

if __name__ == '__main__':
    main()


