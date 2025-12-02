#!/bin/bash
# OCR准确率测试启动脚本

echo "=========================================="
echo "OCR准确率测试系统"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 检查依赖包
echo "检查依赖包..."
python3 -c "import requests, PIL, matplotlib, pandas, seaborn, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装依赖包..."
    pip3 install requests pillow matplotlib pandas seaborn numpy
fi

# 检查OCR API服务
echo "检查OCR API服务..."
if ! curl -s http://localhost:16110/v1/health > /dev/null; then
    echo "警告: OCR API服务未运行，请先启动API服务"
    echo "运行命令: cd /root/lhy/paddleocr && python main.py"
    echo ""
    read -p "是否继续测试? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 运行测试
echo "开始运行OCR准确率测试..."
python3 run_test.py

echo "=========================================="
echo "测试完成!"
echo "查看报告: reports/ 目录"
echo "=========================================="



