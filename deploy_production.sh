#!/bin/bash

# PaddleOCR 生产环境部署脚本
# 服务器IP: 43.137.12.144
# 前端端口: 8000
# 后端端口: 16110

echo "🚀 开始部署PaddleOCR生产环境服务..."

# 检查Python环境
echo "📋 检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ 错误: Python3未安装"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖包..."
pip3 list | grep -E "(fastapi|uvicorn|paddleocr)" > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  安装依赖包..."
    pip3 install -r requirements.txt
fi

# 停止现有服务
echo "🛑 停止现有服务..."
pkill -f "python3.*frontend_server.py" 2>/dev/null || true
pkill -f "python3.*start_backend.py" 2>/dev/null || true
sleep 2

# 创建日志目录
mkdir -p logs

# 检查端口是否被占用
echo "🔍 检查端口占用情况..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  端口8000已被占用，尝试释放..."
    fuser -k 8000/tcp 2>/dev/null || true
    sleep 1
fi

if lsof -Pi :16110 -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  端口16110已被占用，尝试释放..."
    fuser -k 16110/tcp 2>/dev/null || true
    sleep 1
fi

# 启动后端服务
echo "🔧 启动OCR后端API服务 (端口: 16110)..."
cd /root/paddleocr
nohup python3 /root/start_backend.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端服务启动
sleep 5

# 检查后端服务状态
if curl -s --connect-timeout 5 http://localhost:16110/v1/health > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败，检查日志: logs/backend.log"
    exit 1
fi

# 启动前端服务
echo "🌐 启动前端Web服务 (端口: 8000)..."
cd /root/paddleocr
nohup python3 frontend_server.py > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# 等待前端服务启动
sleep 3

# 检查前端服务状态
if curl -s --connect-timeout 5 http://localhost:8000/ > /dev/null; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败，检查日志: logs/frontend.log"
    exit 1
fi

echo ""
echo "🎉 PaddleOCR服务部署完成！"
echo ""
echo "📍 公网访问地址:"
echo "   🌐 Web界面: http://43.137.12.144:8000"
echo "   🔧 API接口: http://43.137.12.144:16110"
echo ""
echo "📋 服务信息:"
echo "   前端进程ID: $FRONTEND_PID"
echo "   后端进程ID: $BACKEND_PID"
echo ""
echo "🔧 管理命令:"
echo "   查看后端日志: tail -f logs/backend.log"
echo "   查看前端日志: tail -f logs/frontend.log"
echo "   重启服务: ./deploy_production.sh"
echo "   停止服务: pkill -f 'python3.*start_backend.py' && pkill -f 'python3.*frontend_server.py'"
echo ""
echo "🔑 API认证:"
echo "   X-API-Key: PolyNex-PolyOCR-2025xm"
echo "   或 Authorization: Bearer PolyNex-PolyOCR-2025xm"
