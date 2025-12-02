#!/bin/bash

# 测试PaddleOCR公网访问

echo "🌐 测试PaddleOCR公网访问功能"
echo "服务器: 43.137.12.144"
echo "========================================"

SERVER_IP="43.137.12.144"
API_KEY="PolyNex-PolyOCR-2025xm"

# 测试Web界面
echo "1. 测试Web界面访问..."
if curl -s --connect-timeout 10 http://$SERVER_IP:8000/ | grep -q "PolyOCR"; then
    echo "   ✅ Web界面可正常访问"
else
    echo "   ❌ Web界面访问失败"
fi

# 测试API健康检查
echo "2. 测试API健康检查..."
API_STATUS=$(curl -s --connect-timeout 10 http://$SERVER_IP:16110/v1/health)
if echo "$API_STATUS" | grep -q "healthy"; then
    echo "   ✅ API健康检查正常"
    echo "   📊 加载的模型: $(echo "$API_STATUS" | grep -o '"models_loaded":\[[^]]*\]' | sed 's/.*\[\([^]]*\)\].*/\1/')"
else
    echo "   ❌ API健康检查失败"
fi

# 测试OCR API
echo "3. 测试OCR API调用..."
OCR_RESULT=$(curl -s --connect-timeout 15 -X POST \
    -H "X-API-Key: $API_KEY" \
    -F "file=@test_english.jpg" \
    -F "language=en" \
    http://$SERVER_IP:16110/v1/ocr)

if echo "$OCR_RESULT" | grep -q '"code":0'; then
    echo "   ✅ OCR API调用成功"
    TEXT_COUNT=$(echo "$OCR_RESULT" | grep -o '"text":' | wc -l)
    echo "   📝 识别出 $TEXT_COUNT 个文本块"
else
    echo "   ❌ OCR API调用失败"
fi

echo ""
echo "🎯 总结:"
echo "   🌐 Web界面: http://$SERVER_IP:8000"
echo "   🔧 API接口: http://$SERVER_IP:16110"
echo "   🔑 API密钥: $API_KEY"
echo ""
echo "其他计算机现在可以通过以上地址访问PaddleOCR服务！"
