#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR准确率测试主脚本
一键运行完整的测试流程
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

class OCRTestRunner:
    """OCR测试运行器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化测试运行器
        
        Args:
            base_dir: 基础目录路径
        """
        if not base_dir:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = base_dir
        self.test_images_dir = os.path.join(base_dir, 'test_images')
        self.results_dir = os.path.join(base_dir, 'results')
        self.reports_dir = os.path.join(base_dir, 'reports')
        
        # 确保目录存在
        os.makedirs(self.test_images_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def check_dependencies(self):
        """检查依赖项"""
        print("检查依赖项...")
        
        required_packages = [
            'requests', 'PIL', 'matplotlib', 'pandas', 'seaborn', 'numpy'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"缺少依赖包: {', '.join(missing_packages)}")
            print("请运行: pip install " + " ".join(missing_packages))
            return False
        
        print("✓ 依赖项检查通过")
        return True
    
    def prepare_test_images(self, force_regenerate: bool = False):
        """准备测试图片"""
        print("\n准备测试图片...")
        
        # 检查是否已有测试图片
        if not force_regenerate and os.path.exists(self.test_images_dir):
            existing_images = [f for f in os.listdir(self.test_images_dir) if f.endswith('.jpg')]
            if existing_images:
                print(f"✓ 发现 {len(existing_images)} 张现有测试图片")
                return True
        
        # 生成测试图片
        try:
            cmd = [sys.executable, 'prepare_test_images.py', '--update-config']
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ 测试图片准备完成")
                return True
            else:
                print(f"✗ 测试图片准备失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ 测试图片准备异常: {e}")
            return False
    
    def run_api_tests(self, api_url: str = "http://localhost:16110", 
                     api_key: str = None, config_file: str = "test_config.json"):
        """运行API测试"""
        print(f"\n运行API测试 (API: {api_url})...")
        
        # 检查API是否可用
        try:
            import requests
            response = requests.get(f"{api_url}/v1/health", timeout=5)
            if response.status_code != 200:
                print(f"✗ API服务不可用: {api_url}")
                return False
        except Exception as e:
            print(f"✗ 无法连接到API服务: {e}")
            print("请确保OCR API服务正在运行")
            return False
        
        # 运行测试
        try:
            cmd = [sys.executable, 'test_api.py', '--api-url', api_url, '--config', config_file]
            if api_key:
                cmd.extend(['--api-key', api_key])
            
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ API测试完成")
                return True
            else:
                print(f"✗ API测试失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ API测试异常: {e}")
            return False
    
    def generate_reports(self, results_file: str = None):
        """生成测试报告"""
        print("\n生成测试报告...")
        
        # 查找最新的结果文件
        if not results_file:
            results_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
            if not results_files:
                print("✗ 未找到测试结果文件")
                return False
            
            # 按修改时间排序，选择最新的
            results_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.results_dir, x)), reverse=True)
            results_file = os.path.join(self.results_dir, results_files[0])
        
        if not os.path.exists(results_file):
            print(f"✗ 结果文件不存在: {results_file}")
            return False
        
        try:
            # 生成综合报告
            cmd = [sys.executable, 'generate_report.py', results_file, '--output-dir', self.reports_dir]
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ 测试报告生成完成")
                return True
            else:
                print(f"✗ 报告生成失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ 报告生成异常: {e}")
            return False
    
    def run_full_test(self, api_url: str = "http://localhost:16110", 
                     api_key: str = None, force_regenerate: bool = False):
        """运行完整测试流程"""
        print("=" * 60)
        print("OCR准确率测试系统")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API地址: {api_url}")
        print("=" * 60)
        
        # 1. 检查依赖项
        if not self.check_dependencies():
            return False
        
        # 2. 准备测试图片
        if not self.prepare_test_images(force_regenerate):
            return False
        
        # 3. 运行API测试
        if not self.run_api_tests(api_url, api_key):
            return False
        
        # 4. 生成报告
        if not self.generate_reports():
            return False
        
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
        print(f"结果目录: {self.results_dir}")
        print(f"报告目录: {self.reports_dir}")
        print("=" * 60)
        
        return True
    
    def show_test_summary(self):
        """显示测试总结"""
        print("\n测试文件结构:")
        print(f"├── test_images/     # 测试图片")
        print(f"├── results/         # 测试结果")
        print(f"├── reports/         # 测试报告")
        print(f"├── test_api.py      # API测试脚本")
        print(f"├── analyze_results.py # 结果分析工具")
        print(f"├── generate_report.py # 报告生成器")
        print(f"├── prepare_test_images.py # 图片准备工具")
        print(f"└── run_test.py      # 主测试脚本")
        
        print("\n使用方法:")
        print("1. 确保OCR API服务正在运行")
        print("2. 运行: python run_test.py")
        print("3. 查看 reports/ 目录中的报告")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OCR准确率测试主脚本')
    parser.add_argument('--api-url', default='http://localhost:16110',
                       help='API服务地址 (默认: http://localhost:16110)')
    parser.add_argument('--api-key', help='API密钥')
    parser.add_argument('--force-regenerate', action='store_true',
                       help='强制重新生成测试图片')
    parser.add_argument('--prepare-only', action='store_true',
                       help='仅准备测试图片')
    parser.add_argument('--test-only', action='store_true',
                       help='仅运行API测试')
    parser.add_argument('--report-only', action='store_true',
                       help='仅生成报告')
    parser.add_argument('--summary', action='store_true',
                       help='显示测试系统说明')
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = OCRTestRunner()
    
    if args.summary:
        runner.show_test_summary()
        return
    
    if args.prepare_only:
        runner.prepare_test_images(args.force_regenerate)
    elif args.test_only:
        runner.run_api_tests(args.api_url, args.api_key)
    elif args.report_only:
        runner.generate_reports()
    else:
        # 运行完整测试
        runner.run_full_test(args.api_url, args.api_key, args.force_regenerate)

if __name__ == "__main__":
    main()



