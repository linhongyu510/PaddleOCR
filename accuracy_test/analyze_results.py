#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR测试结果分析工具
用于分析测试结果并生成详细报告
"""

import json
import os
import argparse
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

class OCRResultAnalyzer:
    """OCR测试结果分析器"""
    
    def __init__(self, results_file: str):
        """
        初始化分析器
        
        Args:
            results_file: 测试结果文件路径
        """
        self.results_file = results_file
        self.results_data = None
        self.load_results()
    
    def load_results(self):
        """加载测试结果数据"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                self.results_data = json.load(f)
            print(f"成功加载测试结果: {self.results_file}")
        except Exception as e:
            print(f"加载测试结果失败: {e}")
            raise
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """生成总结报告"""
        if not self.results_data:
            return {}
        
        test_info = self.results_data.get('test_info', {})
        language_results = self.results_data.get('language_results', {})
        
        summary = {
            'test_overview': {
                'timestamp': test_info.get('timestamp'),
                'api_url': test_info.get('api_base_url'),
                'total_languages': test_info.get('total_languages_tested', 0),
                'total_images': test_info.get('total_images_tested', 0),
                'successful_tests': test_info.get('total_successful_tests', 0),
                'overall_success_rate': test_info.get('overall_success_rate', 0),
                'total_cost_time': test_info.get('total_cost_time', 0),
                'avg_cost_time': test_info.get('avg_cost_time_per_image', 0)
            },
            'language_performance': {},
            'performance_ranking': [],
            'recommendations': []
        }
        
        # 分析各语言性能
        language_stats = []
        for lang, result in language_results.items():
            if result.get('successful_tests', 0) > 0:
                lang_perf = {
                    'language': lang,
                    'success_rate': result.get('success_rate', 0),
                    'avg_precision': result.get('avg_precision', 0),
                    'avg_recall': result.get('avg_recall', 0),
                    'avg_f1_score': result.get('avg_f1_score', 0),
                    'avg_exact_match': result.get('avg_exact_match', 0),
                    'avg_character_accuracy': result.get('avg_character_accuracy', 0),
                    'avg_cost_time': result.get('avg_cost_time', 0),
                    'total_images': result.get('total_images', 0),
                    'successful_tests': result.get('successful_tests', 0)
                }
                language_stats.append(lang_perf)
                summary['language_performance'][lang] = lang_perf
        
        # 按F1分数排序
        language_stats.sort(key=lambda x: x['avg_f1_score'], reverse=True)
        summary['performance_ranking'] = language_stats
        
        # 生成建议
        recommendations = self.generate_recommendations(language_stats)
        summary['recommendations'] = recommendations
        
        return summary
    
    def generate_recommendations(self, language_stats: List[Dict]) -> List[str]:
        """生成性能改进建议"""
        recommendations = []
        
        if not language_stats:
            return ["没有可分析的语言数据"]
        
        # 找出表现最好和最差的语言
        best_lang = language_stats[0]
        worst_lang = language_stats[-1]
        
        recommendations.append(f"表现最佳语言: {best_lang['language']} (F1分数: {best_lang['avg_f1_score']:.2%})")
        recommendations.append(f"表现最差语言: {worst_lang['language']} (F1分数: {worst_lang['avg_f1_score']:.2%})")
        
        # 分析需要改进的语言
        low_performance_langs = [lang for lang in language_stats if lang['avg_f1_score'] < 0.5]
        if low_performance_langs:
            recommendations.append(f"需要改进的语言: {', '.join([lang['language'] for lang in low_performance_langs])}")
        
        # 分析速度问题
        slow_langs = [lang for lang in language_stats if lang['avg_cost_time'] > 2.0]
        if slow_langs:
            recommendations.append(f"处理速度较慢的语言: {', '.join([lang['language'] for lang in slow_langs])}")
        
        # 分析成功率问题
        low_success_langs = [lang for lang in language_stats if lang['success_rate'] < 0.8]
        if low_success_langs:
            recommendations.append(f"成功率较低的语言: {', '.join([lang['language'] for lang in low_success_langs])}")
        
        return recommendations
    
    def setup_chinese_font(self):
        """设置中文字体"""
        import matplotlib.font_manager as fm
        from matplotlib.font_manager import FontProperties
        
        # 直接使用字体文件路径
        font_paths = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
        ]
        
        self.chinese_font = None
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    self.chinese_font = FontProperties(fname=font_path)
                    print(f"使用中文字体: {font_path}")
                    break
            except Exception as e:
                print(f"字体加载失败 {font_path}: {e}")
                continue
        
        if self.chinese_font is None:
            print("未找到可用的中文字体，使用默认字体")
            self.chinese_font = FontProperties()
        
        # 设置matplotlib全局字体
        plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.family'] = 'sans-serif'

    def create_performance_charts(self, output_dir: str = None):
        """创建性能图表"""
        if not self.results_data:
            print("没有数据可分析")
            return
        
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(self.results_file), 'charts')
        
        os.makedirs(output_dir, exist_ok=True)
        
        language_results = self.results_data.get('language_results', {})
        
        # 准备数据
        languages = []
        success_rates = []
        f1_scores = []
        precision_scores = []
        recall_scores = []
        exact_match_scores = []
        character_accuracies = []
        cost_times = []
        
        for lang, result in language_results.items():
            if result.get('successful_tests', 0) > 0:
                languages.append(lang)
                success_rates.append(result.get('success_rate', 0))
                f1_scores.append(result.get('avg_f1_score', 0))
                precision_scores.append(result.get('avg_precision', 0))
                recall_scores.append(result.get('avg_recall', 0))
                exact_match_scores.append(result.get('avg_exact_match', 0))
                character_accuracies.append(result.get('avg_character_accuracy', 0))
                cost_times.append(result.get('avg_cost_time', 0))
        
        if not languages:
            print("没有可用的语言数据")
            return
        
        # 设置中文字体
        self.setup_chinese_font()
        
        # 1. 成功率对比图
        plt.figure(figsize=(12, 6))
        plt.bar(languages, success_rates, color='skyblue', alpha=0.7)
        plt.title('各语言OCR识别成功率对比', fontsize=14, fontweight='bold', fontproperties=self.chinese_font)
        plt.xlabel('语言', fontsize=12, fontproperties=self.chinese_font)
        plt.ylabel('成功率', fontsize=12, fontproperties=self.chinese_font)
        plt.xticks(rotation=45)
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'success_rate_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 准确率指标对比图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # F1分数
        axes[0, 0].bar(languages, f1_scores, color='lightgreen', alpha=0.7)
        axes[0, 0].set_title('F1分数对比', fontweight='bold', fontproperties=self.chinese_font)
        axes[0, 0].set_ylabel('F1分数', fontproperties=self.chinese_font)
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(True, alpha=0.3)
        
        # 精确率
        axes[0, 1].bar(languages, precision_scores, color='lightcoral', alpha=0.7)
        axes[0, 1].set_title('精确率对比', fontweight='bold', fontproperties=self.chinese_font)
        axes[0, 1].set_ylabel('精确率', fontproperties=self.chinese_font)
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(True, alpha=0.3)
        
        # 召回率
        axes[1, 0].bar(languages, recall_scores, color='lightblue', alpha=0.7)
        axes[1, 0].set_title('召回率对比', fontweight='bold', fontproperties=self.chinese_font)
        axes[1, 0].set_ylabel('召回率', fontproperties=self.chinese_font)
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].grid(True, alpha=0.3)
        
        # 字符准确率
        axes[1, 1].bar(languages, character_accuracies, color='lightyellow', alpha=0.7)
        axes[1, 1].set_title('字符准确率对比', fontweight='bold', fontproperties=self.chinese_font)
        axes[1, 1].set_ylabel('字符准确率', fontproperties=self.chinese_font)
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'accuracy_metrics_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 处理时间对比图
        plt.figure(figsize=(12, 6))
        plt.bar(languages, cost_times, color='orange', alpha=0.7)
        plt.title('各语言OCR处理时间对比', fontsize=14, fontweight='bold', fontproperties=self.chinese_font)
        plt.xlabel('语言', fontsize=12, fontproperties=self.chinese_font)
        plt.ylabel('平均处理时间 (秒)', fontsize=12, fontproperties=self.chinese_font)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'processing_time_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. 综合性能雷达图
        if len(languages) >= 3:  # 至少需要3个语言才能画雷达图
            self.create_radar_chart(languages, f1_scores, precision_scores, recall_scores, output_dir)
        
        print(f"性能图表已保存到: {output_dir}")
    
    def create_radar_chart(self, languages: List[str], f1_scores: List[float], 
                          precision_scores: List[float], recall_scores: List[float], 
                          output_dir: str):
        """创建雷达图"""
        import numpy as np
        
        # 选择前5个语言进行雷达图展示
        top_languages = languages[:5]
        top_f1 = f1_scores[:5]
        top_precision = precision_scores[:5]
        top_recall = recall_scores[:5]
        
        # 设置角度
        angles = np.linspace(0, 2 * np.pi, 3, endpoint=False).tolist()
        angles += angles[:1]  # 闭合
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, (lang, f1, prec, rec) in enumerate(zip(top_languages, top_f1, top_precision, top_recall)):
            values = [f1, prec, rec]
            values += values[:1]  # 闭合
            
            ax.plot(angles, values, 'o-', linewidth=2, label=lang, color=colors[i % len(colors)])
            ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(['F1分数', '精确率', '召回率'])
        ax.set_ylim(0, 1)
        ax.set_title('语言性能雷达图', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'performance_radar.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_detailed_report(self, output_file: str = None) -> str:
        """生成详细报告"""
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(self.results_file), 'reports')
        
        os.makedirs(output_dir, exist_ok=True)
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(output_dir, f'ocr_analysis_report_{timestamp}.html')
        
        summary = self.generate_summary_report()
        
        # 生成HTML报告
        html_content = self.create_html_report(summary)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"详细报告已保存到: {output_file}")
        return output_file
    
    def create_html_report(self, summary: Dict[str, Any]) -> str:
        """创建HTML格式的报告"""
        test_overview = summary.get('test_overview', {})
        language_performance = summary.get('language_performance', {})
        performance_ranking = summary.get('performance_ranking', [])
        recommendations = summary.get('recommendations', [])
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR准确率测试分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        .overview {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 15px;
            background: #3498db;
            color: white;
            border-radius: 5px;
            font-weight: bold;
        }}
        .language-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .language-table th, .language-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .language-table th {{
            background-color: #3498db;
            color: white;
        }}
        .language-table tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .recommendations {{
            background: #e8f5e8;
            padding: 20px;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .recommendations li {{
            margin: 8px 0;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OCR准确率测试分析报告</h1>
        
        <div class="overview">
            <h2>测试概览</h2>
            <div class="metric">测试时间: {test_overview.get('timestamp', 'N/A')}</div>
            <div class="metric">API地址: {test_overview.get('api_url', 'N/A')}</div>
            <div class="metric">测试语言数: {test_overview.get('total_languages', 0)}</div>
            <div class="metric">测试图片数: {test_overview.get('total_images', 0)}</div>
            <div class="metric">成功测试数: {test_overview.get('successful_tests', 0)}</div>
            <div class="metric">总体成功率: {test_overview.get('overall_success_rate', 0):.2%}</div>
            <div class="metric">总耗时: {test_overview.get('total_cost_time', 0):.3f}秒</div>
            <div class="metric">平均耗时: {test_overview.get('avg_cost_time', 0):.3f}秒/图片</div>
        </div>
        
        <h2>各语言性能对比</h2>
        <table class="language-table">
            <thead>
                <tr>
                    <th>语言</th>
                    <th>成功率</th>
                    <th>F1分数</th>
                    <th>精确率</th>
                    <th>召回率</th>
                    <th>精确匹配</th>
                    <th>字符准确率</th>
                    <th>平均耗时(秒)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for lang_perf in performance_ranking:
            html += f"""
                <tr>
                    <td>{lang_perf['language']}</td>
                    <td>{lang_perf['success_rate']:.2%}</td>
                    <td>{lang_perf['avg_f1_score']:.2%}</td>
                    <td>{lang_perf['avg_precision']:.2%}</td>
                    <td>{lang_perf['avg_recall']:.2%}</td>
                    <td>{lang_perf['avg_exact_match']:.2%}</td>
                    <td>{lang_perf['avg_character_accuracy']:.2%}</td>
                    <td>{lang_perf['avg_cost_time']:.3f}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <h2>性能改进建议</h2>
        <div class="recommendations">
            <ul>
"""
        
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        
        html += """
            </ul>
        </div>
        
        <h2>性能图表</h2>
        <div class="chart-container">
            <p>图表文件已保存到 charts/ 目录中，包括：</p>
            <ul>
                <li>成功率对比图</li>
                <li>准确率指标对比图</li>
                <li>处理时间对比图</li>
                <li>性能雷达图</li>
            </ul>
        </div>
        
        <footer style="margin-top: 50px; text-align: center; color: #7f8c8d;">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OCR测试结果分析工具')
    parser.add_argument('results_file', help='测试结果JSON文件路径')
    parser.add_argument('--output-dir', help='输出目录路径')
    parser.add_argument('--charts', action='store_true', help='生成性能图表')
    parser.add_argument('--report', action='store_true', help='生成详细报告')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results_file):
        print(f"错误: 结果文件不存在: {args.results_file}")
        return
    
    # 创建分析器
    analyzer = OCRResultAnalyzer(args.results_file)
    
    # 生成总结报告
    summary = analyzer.generate_summary_report()
    
    print("\n" + "=" * 60)
    print("OCR测试结果分析报告")
    print("=" * 60)
    print(f"测试时间: {summary['test_overview']['timestamp']}")
    print(f"测试语言数: {summary['test_overview']['total_languages']}")
    print(f"测试图片数: {summary['test_overview']['total_images']}")
    print(f"成功测试数: {summary['test_overview']['successful_tests']}")
    print(f"总体成功率: {summary['test_overview']['overall_success_rate']:.2%}")
    print(f"总耗时: {summary['test_overview']['total_cost_time']:.3f}秒")
    print(f"平均耗时: {summary['test_overview']['avg_cost_time']:.3f}秒/图片")
    
    print("\n各语言性能排名:")
    for i, lang_perf in enumerate(summary['performance_ranking'], 1):
        print(f"{i}. {lang_perf['language']}: F1={lang_perf['avg_f1_score']:.2%}, "
              f"成功率={lang_perf['success_rate']:.2%}, 耗时={lang_perf['avg_cost_time']:.3f}s")
    
    print("\n改进建议:")
    for rec in summary['recommendations']:
        print(f"- {rec}")
    
    # 生成图表
    if args.charts:
        analyzer.create_performance_charts(args.output_dir)
    
    # 生成详细报告
    if args.report:
        analyzer.generate_detailed_report()

if __name__ == "__main__":
    main()
