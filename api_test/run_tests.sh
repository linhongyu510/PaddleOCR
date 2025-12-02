#!/bin/bash
# OCR API测试启动脚本

echo "🚀 OCR API测试工具"
echo "=================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
python3 -c "import requests, PIL" 2>/dev/null || {
    echo "❌ 缺少依赖，正在安装..."
    pip3 install requests pillow
}

# 创建测试图片目录
mkdir -p /root/lhy/paddleocr/api_test/test_images

echo ""
echo "🎨 生成测试图片..."
python3 generate_test_images.py

echo ""
echo "🔍 运行快速测试..."
python3 quick_test.py

echo ""
echo "📊 运行综合测试..."
python3 test_ocr_api.py

echo ""
echo "🎉 测试完成！"
echo "📁 测试报告保存在: /root/lhy/paddleocr/api_test/test_report.json"
