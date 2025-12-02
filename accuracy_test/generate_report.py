#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成器
用于生成OCR测试的详细报告
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, results_file: str):
        """
        初始化报告生成器
        
        Args:
            results_file: 测试结果文件路径
        """
        self.results_file = results_file
        self.results_data = None
        self.load_results()
    
    def load_results(self):
        """加载测试结果"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                self.results_data = json.load(f)
            print(f"成功加载测试结果: {self.results_file}")
        except Exception as e:
            print(f"加载测试结果失败: {e}")
            raise
    
    def generate_comprehensive_report(self, output_dir: str = None) -> str:
        """
        生成综合测试报告
        
        Args:
            output_dir: 输出目录
            
        Returns:
            报告文件路径
        """
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(self.results_file), 'reports')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成HTML报告
        html_report = self.create_html_report()
        html_path = os.path.join(output_dir, f'ocr_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # 生成图表
        charts_dir = os.path.join(output_dir, 'charts')
        self.create_performance_charts(charts_dir)
        
        # 生成CSV数据
        csv_path = os.path.join(output_dir, f'ocr_test_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        self.export_to_csv(csv_path)
        
        print(f"综合报告已生成:")
        print(f"  HTML报告: {html_path}")
        print(f"  图表目录: {charts_dir}")
        print(f"  CSV数据: {csv_path}")
        
        return html_path
    
    def create_html_report(self) -> str:
        """创建HTML格式的详细报告"""
        test_info = self.results_data.get('test_info', {})
        language_results = self.results_data.get('language_results', {})
        
        # 计算统计信息
        total_languages = len(language_results)
        total_images = sum(result.get('total_images', 0) for result in language_results.values())
        total_successful = sum(result.get('successful_tests', 0) for result in language_results.values())
        overall_success_rate = total_successful / total_images if total_images > 0 else 0
        
        # 按性能排序
        performance_data = []
        for lang, result in language_results.items():
            if result.get('successful_tests', 0) > 0:
                performance_data.append({
                    'language': lang,
                    'success_rate': result.get('success_rate', 0),
                    'avg_f1_score': result.get('avg_f1_score', 0),
                    'avg_precision': result.get('avg_precision', 0),
                    'avg_recall': result.get('avg_recall', 0),
                    'avg_exact_match': result.get('avg_exact_match', 0),
                    'avg_character_accuracy': result.get('avg_character_accuracy', 0),
                    'avg_cost_time': result.get('avg_cost_time', 0),
                    'total_images': result.get('total_images', 0),
                    'successful_tests': result.get('successful_tests', 0)
                })
        
        performance_data.sort(key=lambda x: x['avg_f1_score'], reverse=True)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR准确率测试综合报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
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
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
        }}
        .overview {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .performance-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .performance-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}
        .performance-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .performance-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .performance-table tr:hover {{
            background-color: #e3f2fd;
        }}
        .rank-1 {{ background-color: #d4edda !important; }}
        .rank-2 {{ background-color: #fff3cd !important; }}
        .rank-3 {{ background-color: #f8d7da !important; }}
        .chart-container {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 10px;
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-card h4 {{
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .language-details {{
            margin: 20px 0;
        }}
        .language-card {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .language-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .language-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .language-rank {{
            background: #3498db;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.3s ease;
        }}
        .recommendations {{
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .recommendations li {{
            margin: 10px 0;
            font-size: 1.1em;
        }}
        .footer {{
            margin-top: 50px;
            text-align: center;
            color: #7f8c8d;
            border-top: 1px solid #ecf0f1;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OCR准确率测试综合报告</h1>
        
        <div class="overview">
            <h2>测试概览</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{test_info.get('timestamp', 'N/A')[:10]}</div>
                    <div class="metric-label">测试日期</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_languages}</div>
                    <div class="metric-label">测试语言数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_images}</div>
                    <div class="metric-label">测试图片数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_successful}</div>
                    <div class="metric-label">成功测试数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{overall_success_rate:.1%}</div>
                    <div class="metric-label">总体成功率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{test_info.get('total_cost_time', 0):.1f}s</div>
                    <div class="metric-label">总耗时</div>
                </div>
            </div>
        </div>
        
        <h2>语言性能排名</h2>
        <table class="performance-table">
            <thead>
                <tr>
                    <th>排名</th>
                    <th>语言</th>
                    <th>成功率</th>
                    <th>F1分数</th>
                    <th>精确率</th>
                    <th>召回率</th>
                    <th>精确匹配</th>
                    <th>字符准确率</th>
                    <th>平均耗时</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for i, data in enumerate(performance_data, 1):
            rank_class = ""
            if i == 1:
                rank_class = "rank-1"
            elif i == 2:
                rank_class = "rank-2"
            elif i == 3:
                rank_class = "rank-3"
            
            html += f"""
                <tr class="{rank_class}">
                    <td><strong>#{i}</strong></td>
                    <td><strong>{data['language']}</strong></td>
                    <td>{data['success_rate']:.1%}</td>
                    <td>{data['avg_f1_score']:.1%}</td>
                    <td>{data['avg_precision']:.1%}</td>
                    <td>{data['avg_recall']:.1%}</td>
                    <td>{data['avg_exact_match']:.1%}</td>
                    <td>{data['avg_character_accuracy']:.1%}</td>
                    <td>{data['avg_cost_time']:.3f}s</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <h2>详细语言分析</h2>
        <div class="language-details">
"""
        
        for i, data in enumerate(performance_data, 1):
            html += f"""
            <div class="language-card">
                <div class="language-header">
                    <div class="language-name">{data['language']} 语言</div>
                    <div class="language-rank">排名 #{i}</div>
                </div>
                
                <h4>性能指标</h4>
                <div class="summary-stats">
                    <div class="stat-card">
                        <h4>准确率指标</h4>
                        <p><strong>F1分数:</strong> {data['avg_f1_score']:.1%}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['avg_f1_score']*100:.1f}%"></div>
                        </div>
                        <p><strong>精确率:</strong> {data['avg_precision']:.1%}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['avg_precision']*100:.1f}%"></div>
                        </div>
                        <p><strong>召回率:</strong> {data['avg_recall']:.1%}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['avg_recall']*100:.1f}%"></div>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <h4>匹配指标</h4>
                        <p><strong>精确匹配:</strong> {data['avg_exact_match']:.1%}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['avg_exact_match']*100:.1f}%"></div>
                        </div>
                        <p><strong>字符准确率:</strong> {data['avg_character_accuracy']:.1%}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['avg_character_accuracy']*100:.1f}%"></div>
                        </div>
                        <p><strong>成功率:</strong> {data['success_rate']:.1%}</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {data['success_rate']*100:.1f}%"></div>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <h4>性能指标</h4>
                        <p><strong>测试图片数:</strong> {data['total_images']}</p>
                        <p><strong>成功测试数:</strong> {data['successful_tests']}</p>
                        <p><strong>平均耗时:</strong> {data['avg_cost_time']:.3f}秒</p>
                        <p><strong>总耗时:</strong> {data['avg_cost_time'] * data['total_images']:.3f}秒</p>
                    </div>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <h2>性能图表</h2>
        <div class="chart-container">
            <p>以下图表展示了各语言的性能对比：</p>
            <ul>
                <li><strong>成功率对比图:</strong> 显示各语言的识别成功率</li>
                <li><strong>准确率指标对比图:</strong> 展示F1分数、精确率、召回率等指标</li>
                <li><strong>处理时间对比图:</strong> 比较各语言的处理速度</li>
                <li><strong>性能雷达图:</strong> 综合展示多维度性能指标</li>
            </ul>
            <p>图表文件保存在 charts/ 目录中。</p>
        </div>
        
        <div class="recommendations">
            <h2>性能改进建议</h2>
            <ul>
"""
        
        # 生成建议
        if performance_data:
            best_lang = performance_data[0]
            worst_lang = performance_data[-1]
            
            html += f"<li><strong>最佳表现语言:</strong> {best_lang['language']} (F1分数: {best_lang['avg_f1_score']:.1%})</li>"
            html += f"<li><strong>需要改进语言:</strong> {worst_lang['language']} (F1分数: {worst_lang['avg_f1_score']:.1%})</li>"
            
            # 分析需要改进的语言
            low_performance = [lang for lang in performance_data if lang['avg_f1_score'] < 0.5]
            if low_performance:
                low_langs = ', '.join([lang['language'] for lang in low_performance])
                html += f"<li><strong>低性能语言:</strong> {low_langs} 需要重点关注和改进</li>"
            
            # 分析速度问题
            slow_langs = [lang for lang in performance_data if lang['avg_cost_time'] > 2.0]
            if slow_langs:
                slow_lang_names = ', '.join([lang['language'] for lang in slow_langs])
                html += f"<li><strong>处理速度较慢:</strong> {slow_lang_names} 建议优化处理速度</li>"
        
        html += """
            </ul>
        </div>
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>OCR测试系统 - 准确率验证报告</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
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

    def create_performance_charts(self, output_dir: str):
        """创建性能图表"""
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
        plt.figure(figsize=(14, 8))
        bars = plt.bar(languages, success_rates, color='skyblue', alpha=0.8, edgecolor='navy', linewidth=1)
        plt.title('各语言OCR识别成功率对比', fontsize=16, fontweight='bold', pad=20, fontproperties=self.chinese_font)
        plt.xlabel('语言', fontsize=14, fontproperties=self.chinese_font)
        plt.ylabel('成功率', fontsize=14, fontproperties=self.chinese_font)
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, rate in zip(bars, success_rates):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{rate:.1%}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'success_rate_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 准确率指标对比图
        self.setup_chinese_font()  # 重新设置字体
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('各语言准确率指标对比', fontsize=16, fontweight='bold', fontproperties=self.chinese_font)
        
        # F1分数
        bars1 = axes[0, 0].bar(languages, f1_scores, color='lightgreen', alpha=0.8)
        axes[0, 0].set_title('F1分数对比', fontweight='bold', fontsize=14, fontproperties=self.chinese_font)
        axes[0, 0].set_ylabel('F1分数', fontsize=12, fontproperties=self.chinese_font)
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        axes[0, 0].set_ylim(0, 1)
        for bar, score in zip(bars1, f1_scores):
            axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                           f'{score:.1%}', ha='center', va='bottom', fontsize=10)
        
        # 精确率
        bars2 = axes[0, 1].bar(languages, precision_scores, color='lightcoral', alpha=0.8)
        axes[0, 1].set_title('精确率对比', fontweight='bold', fontsize=14, fontproperties=self.chinese_font)
        axes[0, 1].set_ylabel('精确率', fontsize=12, fontproperties=self.chinese_font)
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        axes[0, 1].set_ylim(0, 1)
        for bar, score in zip(bars2, precision_scores):
            axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                         f'{score:.1%}', ha='center', va='bottom', fontsize=10)
        
        # 召回率
        bars3 = axes[1, 0].bar(languages, recall_scores, color='lightblue', alpha=0.8)
        axes[1, 0].set_title('召回率对比', fontweight='bold', fontsize=14, fontproperties=self.chinese_font)
        axes[1, 0].set_ylabel('召回率', fontsize=12, fontproperties=self.chinese_font)
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        axes[1, 0].set_ylim(0, 1)
        for bar, score in zip(bars3, recall_scores):
            axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                           f'{score:.1%}', ha='center', va='bottom', fontsize=10)
        
        # 字符准确率
        bars4 = axes[1, 1].bar(languages, character_accuracies, color='lightyellow', alpha=0.8)
        axes[1, 1].set_title('字符准确率对比', fontweight='bold', fontsize=14, fontproperties=self.chinese_font)
        axes[1, 1].set_ylabel('字符准确率', fontsize=12, fontproperties=self.chinese_font)
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        axes[1, 1].set_ylim(0, 1)
        for bar, score in zip(bars4, character_accuracies):
            axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                           f'{score:.1%}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'accuracy_metrics_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 处理时间对比图
        self.setup_chinese_font()  # 重新设置字体
        plt.figure(figsize=(14, 8))
        bars = plt.bar(languages, cost_times, color='orange', alpha=0.8, edgecolor='darkorange', linewidth=1)
        plt.title('各语言OCR处理时间对比', fontsize=16, fontweight='bold', pad=20, fontproperties=self.chinese_font)
        plt.xlabel('语言', fontsize=14, fontproperties=self.chinese_font)
        plt.ylabel('平均处理时间 (秒)', fontsize=14, fontproperties=self.chinese_font)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, time_val in zip(bars, cost_times):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{time_val:.3f}s', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'processing_time_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. 综合性能雷达图
        if len(languages) >= 3:
            self.setup_chinese_font()  # 重新设置字体
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
        
        fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, (lang, f1, prec, rec) in enumerate(zip(top_languages, top_f1, top_precision, top_recall)):
            values = [f1, prec, rec]
            values += values[:1]  # 闭合
            
            ax.plot(angles, values, 'o-', linewidth=3, label=lang, color=colors[i % len(colors)], markersize=8)
            ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(['F1分数', '精确率', '召回率'], fontsize=12, fontproperties=self.chinese_font)
        ax.set_ylim(0, 1)
        ax.set_title('语言性能雷达图', size=18, fontweight='bold', pad=30, fontproperties=self.chinese_font)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'performance_radar.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def export_to_csv(self, csv_path: str):
        """导出数据到CSV文件"""
        language_results = self.results_data.get('language_results', {})
        
        # 准备数据
        data = []
        for lang, result in language_results.items():
            if result.get('successful_tests', 0) > 0:
                data.append({
                    'language': lang,
                    'success_rate': result.get('success_rate', 0),
                    'avg_f1_score': result.get('avg_f1_score', 0),
                    'avg_precision': result.get('avg_precision', 0),
                    'avg_recall': result.get('avg_recall', 0),
                    'avg_exact_match': result.get('avg_exact_match', 0),
                    'avg_character_accuracy': result.get('avg_character_accuracy', 0),
                    'avg_cost_time': result.get('avg_cost_time', 0),
                    'total_images': result.get('total_images', 0),
                    'successful_tests': result.get('successful_tests', 0)
                })
        
        # 创建DataFrame并保存
        df = pd.DataFrame(data)
        if not df.empty and 'avg_f1_score' in df.columns:
            df = df.sort_values('avg_f1_score', ascending=False)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"CSV数据已导出到: {csv_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OCR测试报告生成器')
    parser.add_argument('results_file', help='测试结果JSON文件路径')
    parser.add_argument('--output-dir', help='输出目录路径')
    parser.add_argument('--charts-only', action='store_true', help='仅生成图表')
    parser.add_argument('--csv-only', action='store_true', help='仅导出CSV数据')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results_file):
        print(f"错误: 结果文件不存在: {args.results_file}")
        return
    
    # 创建报告生成器
    generator = TestReportGenerator(args.results_file)
    
    if args.csv_only:
        # 仅导出CSV
        csv_path = os.path.join(args.output_dir or os.path.dirname(args.results_file), 
                               f'ocr_test_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        generator.export_to_csv(csv_path)
    elif args.charts_only:
        # 仅生成图表
        charts_dir = args.output_dir or os.path.join(os.path.dirname(args.results_file), 'charts')
        generator.create_performance_charts(charts_dir)
    else:
        # 生成综合报告
        generator.generate_comprehensive_report(args.output_dir)

if __name__ == "__main__":
    main()
