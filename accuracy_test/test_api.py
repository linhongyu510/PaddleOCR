#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR API准确率测试脚本
支持多种语言的OCR识别准确率验证
"""

import os
import json
import time
import requests
import base64
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse
from datetime import datetime
import statistics

class OCRAccuracyTester:
    """OCR准确率测试器"""
    
    def __init__(self, api_base_url: str = "http://localhost:16110", api_key: str = None):
        """
        初始化测试器
        
        Args:
            api_base_url: API服务地址
            api_key: API密钥
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.test_results = []
        self.session = requests.Session()
        
        # 设置请求头
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def test_single_image(self, image_path: str, language: str = None, 
                         expected_texts: List[str] = None, 
                         score_threshold: float = 0.5) -> Dict[str, Any]:
        """
        测试单张图片的OCR识别
        
        Args:
            image_path: 图片路径
            language: 指定语言
            expected_texts: 期望识别的文本列表
            score_threshold: 置信度阈值
            
        Returns:
            测试结果字典
        """
        start_time = time.time()
        
        try:
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': f'图片文件不存在: {image_path}',
                    'cost_time': 0,
                    'language': language,
                    'image_path': image_path
                }
            
            # 准备请求数据
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                data = {}
                
                if language:
                    data['language'] = language
                if score_threshold > 0:
                    data['score'] = score_threshold
                
                # 发送请求
                response = self.session.post(
                    f"{self.api_base_url}/v1/ocr",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            cost_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # 提取识别的文本
                recognized_texts = []
                if result.get('code') == 0 and result.get('data'):
                    for item in result['data']:
                        if 'text' in item:
                            recognized_texts.append(item['text'])
                
                # 计算准确率
                accuracy = self.calculate_accuracy(recognized_texts, expected_texts)
                
                return {
                    'success': True,
                    'cost_time': cost_time,
                    'language': language,
                    'image_path': image_path,
                    'recognized_texts': recognized_texts,
                    'expected_texts': expected_texts,
                    'accuracy': accuracy,
                    'api_response': result,
                    'score_threshold': score_threshold
                }
            else:
                return {
                    'success': False,
                    'error': f'API请求失败: {response.status_code} - {response.text}',
                    'cost_time': cost_time,
                    'language': language,
                    'image_path': image_path
                }
                
        except Exception as e:
            cost_time = time.time() - start_time
            return {
                'success': False,
                'error': f'测试异常: {str(e)}',
                'cost_time': cost_time,
                'language': language,
                'image_path': image_path
            }
    
    def calculate_accuracy(self, recognized_texts: List[str], 
                          expected_texts: List[str]) -> Dict[str, float]:
        """
        计算识别准确率
        
        Args:
            recognized_texts: 识别出的文本列表
            expected_texts: 期望的文本列表
            
        Returns:
            准确率统计字典
        """
        if not expected_texts:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'exact_match': 0.0,
                'character_accuracy': 0.0
            }
        
        # 转换为小写进行比较
        recognized_lower = [text.lower().strip() for text in recognized_texts]
        expected_lower = [text.lower().strip() for text in expected_texts]
        
        # 精确匹配
        exact_matches = 0
        for expected in expected_lower:
            if expected in recognized_lower:
                exact_matches += 1
        
        exact_match_rate = exact_matches / len(expected_lower) if expected_lower else 0
        
        # 字符级准确率
        recognized_chars = ''.join(recognized_lower)
        expected_chars = ''.join(expected_lower)
        
        if expected_chars:
            # 计算最长公共子序列
            lcs_length = self.lcs_length(recognized_chars, expected_chars)
            character_accuracy = lcs_length / len(expected_chars)
        else:
            character_accuracy = 0.0
        
        # 计算Precision和Recall
        true_positives = exact_matches
        false_positives = len(recognized_lower) - true_positives
        false_negatives = len(expected_lower) - true_positives
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'exact_match': exact_match_rate,
            'character_accuracy': character_accuracy
        }
    
    def lcs_length(self, s1: str, s2: str) -> int:
        """计算最长公共子序列长度"""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def test_language_batch(self, language: str, test_images: List[str], 
                           expected_texts_map: Dict[str, List[str]] = None,
                           score_threshold: float = 0.5) -> Dict[str, Any]:
        """
        批量测试某种语言
        
        Args:
            language: 语言代码
            test_images: 测试图片路径列表
            expected_texts_map: 图片路径到期望文本的映射
            score_threshold: 置信度阈值
            
        Returns:
            批量测试结果
        """
        print(f"\n开始测试语言: {language}")
        print("=" * 50)
        
        batch_results = []
        total_cost_time = 0
        successful_tests = 0
        
        for i, image_path in enumerate(test_images, 1):
            print(f"测试图片 {i}/{len(test_images)}: {os.path.basename(image_path)}")
            
            expected_texts = expected_texts_map.get(image_path, []) if expected_texts_map else []
            
            result = self.test_single_image(
                image_path=image_path,
                language=language,
                expected_texts=expected_texts,
                score_threshold=score_threshold
            )
            
            batch_results.append(result)
            total_cost_time += result.get('cost_time', 0)
            
            if result.get('success'):
                successful_tests += 1
                accuracy = result.get('accuracy', {})
                print(f"  ✓ 成功 - 耗时: {result['cost_time']:.3f}s")
                print(f"    识别文本: {result.get('recognized_texts', [])}")
                print(f"    准确率: {accuracy.get('exact_match', 0):.2%}")
            else:
                print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        
        # 计算统计信息
        accuracies = [r.get('accuracy', {}) for r in batch_results if r.get('success')]
        
        if accuracies:
            avg_precision = statistics.mean([a.get('precision', 0) for a in accuracies])
            avg_recall = statistics.mean([a.get('recall', 0) for a in accuracies])
            avg_f1 = statistics.mean([a.get('f1_score', 0) for a in accuracies])
            avg_exact_match = statistics.mean([a.get('exact_match', 0) for a in accuracies])
            avg_character_accuracy = statistics.mean([a.get('character_accuracy', 0) for a in accuracies])
        else:
            avg_precision = avg_recall = avg_f1 = avg_exact_match = avg_character_accuracy = 0
        
        batch_summary = {
            'language': language,
            'total_images': len(test_images),
            'successful_tests': successful_tests,
            'success_rate': successful_tests / len(test_images) if test_images else 0,
            'total_cost_time': total_cost_time,
            'avg_cost_time': total_cost_time / len(test_images) if test_images else 0,
            'avg_precision': avg_precision,
            'avg_recall': avg_recall,
            'avg_f1_score': avg_f1,
            'avg_exact_match': avg_exact_match,
            'avg_character_accuracy': avg_character_accuracy,
            'results': batch_results
        }
        
        print(f"\n语言 {language} 测试完成:")
        print(f"  总图片数: {len(test_images)}")
        print(f"  成功测试: {successful_tests}")
        print(f"  成功率: {batch_summary['success_rate']:.2%}")
        print(f"  平均耗时: {batch_summary['avg_cost_time']:.3f}s")
        print(f"  平均精确率: {avg_precision:.2%}")
        print(f"  平均召回率: {avg_recall:.2%}")
        print(f"  平均F1分数: {avg_f1:.2%}")
        print(f"  平均精确匹配: {avg_exact_match:.2%}")
        print(f"  平均字符准确率: {avg_character_accuracy:.2%}")
        
        return batch_summary
    
    def run_comprehensive_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行综合测试
        
        Args:
            test_config: 测试配置字典
            
        Returns:
            综合测试结果
        """
        print("开始OCR准确率综合测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API地址: {self.api_base_url}")
        print("=" * 60)
        
        all_results = {}
        overall_stats = {
            'total_languages': 0,
            'total_images': 0,
            'total_successful': 0,
            'total_cost_time': 0,
            'language_stats': {}
        }
        
        for language, config in test_config.items():
            if 'images' not in config:
                print(f"跳过语言 {language}: 未找到图片配置")
                continue
            
            test_images = config['images']
            expected_texts_map = config.get('expected_texts', {})
            score_threshold = config.get('score_threshold', 0.5)
            
            # 检查图片文件是否存在
            valid_images = []
            for img_path in test_images:
                if os.path.exists(img_path):
                    valid_images.append(img_path)
                else:
                    print(f"警告: 图片文件不存在: {img_path}")
            
            if not valid_images:
                print(f"跳过语言 {language}: 没有有效的测试图片")
                continue
            
            # 运行测试
            batch_result = self.test_language_batch(
                language=language,
                test_images=valid_images,
                expected_texts_map=expected_texts_map,
                score_threshold=score_threshold
            )
            
            all_results[language] = batch_result
            
            # 更新总体统计
            overall_stats['total_languages'] += 1
            overall_stats['total_images'] += batch_result['total_images']
            overall_stats['total_successful'] += batch_result['successful_tests']
            overall_stats['total_cost_time'] += batch_result['total_cost_time']
            overall_stats['language_stats'][language] = {
                'success_rate': batch_result['success_rate'],
                'avg_precision': batch_result['avg_precision'],
                'avg_recall': batch_result['avg_recall'],
                'avg_f1_score': batch_result['avg_f1_score'],
                'avg_exact_match': batch_result['avg_exact_match'],
                'avg_character_accuracy': batch_result['avg_character_accuracy']
            }
        
        # 计算总体统计
        if overall_stats['total_images'] > 0:
            overall_stats['overall_success_rate'] = overall_stats['total_successful'] / overall_stats['total_images']
            overall_stats['avg_cost_time'] = overall_stats['total_cost_time'] / overall_stats['total_images']
        else:
            overall_stats['overall_success_rate'] = 0
            overall_stats['avg_cost_time'] = 0
        
        # 生成最终报告
        final_report = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'api_base_url': self.api_base_url,
                'total_languages_tested': overall_stats['total_languages'],
                'total_images_tested': overall_stats['total_images'],
                'total_successful_tests': overall_stats['total_successful'],
                'overall_success_rate': overall_stats['overall_success_rate'],
                'total_cost_time': overall_stats['total_cost_time'],
                'avg_cost_time_per_image': overall_stats['avg_cost_time']
            },
            'language_results': all_results,
            'overall_statistics': overall_stats
        }
        
        return final_report
    
    def save_results(self, results: Dict[str, Any], output_path: str = None):
        """
        保存测试结果到文件
        
        Args:
            results: 测试结果
            output_path: 输出文件路径
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"/root/lhy/paddleocr/accuracy_test/results/ocr_test_results_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试结果已保存到: {output_path}")
        return output_path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OCR API准确率测试工具')
    parser.add_argument('--api-url', default='http://localhost:16110', 
                       help='API服务地址 (默认: http://localhost:16110)')
    parser.add_argument('--api-key', help='API密钥')
    parser.add_argument('--config', default='test_config.json',
                       help='测试配置文件路径 (默认: test_config.json)')
    parser.add_argument('--output', help='结果输出文件路径')
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = OCRAccuracyTester(api_base_url=args.api_url, api_key=args.api_key)
    
    # 加载测试配置
    config_path = os.path.join(os.path.dirname(__file__), args.config)
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        print("请先创建测试配置文件")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        test_config = json.load(f)
    
    # 运行测试
    results = tester.run_comprehensive_test(test_config)
    
    # 保存结果
    output_path = tester.save_results(results, args.output)
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"测试语言数: {results['test_info']['total_languages_tested']}")
    print(f"测试图片数: {results['test_info']['total_images_tested']}")
    print(f"成功测试数: {results['test_info']['total_successful_tests']}")
    print(f"总体成功率: {results['test_info']['overall_success_rate']:.2%}")
    print(f"总耗时: {results['test_info']['total_cost_time']:.3f}s")
    print(f"平均耗时: {results['test_info']['avg_cost_time_per_image']:.3f}s/图片")
    print("=" * 60)

if __name__ == "__main__":
    main()



