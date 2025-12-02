#!/bin/bash

# OCR服务部署脚本
# 服务器IP: 43.137.12.144
# 端口: 8000

echo "开始部署OCR服务..."

# 检查Python环境
echo "检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: Python3未安装，请先安装Python3"
    exit 1
fi

# 检查依赖
echo "检查依赖包..."
pip3 list | grep -E "(fastapi|uvicorn|paddleocr|opencv-python|Pillow|numpy)" > /dev/null
if [ $? -ne 0 ]; then
    echo "安装依赖包..."
    pip3 install -r requirements.txt
fi

# 检查端口是否被占用
echo "检查端口8000..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "警告: 端口8000已被占用，正在停止现有服务..."
    pkill -f "python3 main.py"
    sleep 2
fi

# 创建日志目录
mkdir -p logs

# 启动服务
echo "启动OCR服务..."
nohup python3 main.py > logs/ocr_service.log 2>&1 &

# 等待服务启动
sleep 5

# 检查服务状态
echo "检查服务状态..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "OCR服务启动成功！"
    echo "服务地址: http://43.137.12.144:8000"
    echo "服务状态: 运行中"
    echo "日志文件: logs/ocr_service.log"
    
    # 显示进程信息
    echo "进程信息:"
    ps aux | grep "python3 main.py" | grep -v grep
    
    # 显示端口信息
    echo "端口信息:"
    netstat -tlnp | grep :8000
    
    echo ""
    echo "部署完成！"
    echo "其他设备可以通过以下地址访问:"
    echo "   http://43.137.12.144:8000"
    echo ""
    echo "管理命令:"
    echo "   查看日志: tail -f logs/ocr_service.log"
    echo "   停止服务: pkill -f 'python3 main.py'"
    echo "   重启服务: ./deploy.sh"
    
else
    echo "错误: OCR服务启动失败，请检查日志:"
    tail -20 logs/ocr_service.log
    exit 1
fi
