#!/bin/bash

# PaddleOCR服务状态检查脚本

echo "🔍 检查PaddleOCR服务状态..."
echo "服务器IP: 43.137.12.144"
echo "========================================"

# 检查进程
echo "📋 进程状态:"
ps aux | grep -E "(frontend_server|start_backend)" | grep -v grep | while read line; do
    echo "  $line"
done

echo ""
echo "🌐 端口监听状态:"
netstat -tlnp | grep -E ":8000|:16110" | while read line; do
    echo "  $line"
done

echo ""
echo "🔗 公网访问测试:"

# 测试前端服务
echo -n "  🌐 Web界面 (8000): "
if curl -s --connect-timeout 5 http://43.137.12.144:8000/ > /dev/null; then
    echo "✅ 可访问"
else
    echo "❌ 无法访问"
fi

# 测试后端API
echo -n "  🔧 API接口 (16110): "
if curl -s --connect-timeout 5 http://43.137.12.144:16110/v1/health > /dev/null; then
    echo "✅ 可访问"
else
    echo "❌ 无法访问"
fi

# 测试API健康状态
echo ""
echo "📊 API详细状态:"
curl -s --connect-timeout 5 http://43.137.12.144:16110/v1/health | jq . 2>/dev/null || echo "  ❌ 无法获取API状态"

echo ""
echo "📝 日志文件:"
echo "  后端日志: logs/backend.log"
echo "  前端日志: logs/frontend.log"

echo ""
echo "🔧 管理命令:"
echo "  重启服务: ./deploy_production.sh"
echo "  停止服务: pkill -f 'python3.*start_backend.py' && pkill -f 'python3.*frontend_server.py'"
