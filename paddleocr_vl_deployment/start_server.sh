#!/bin/bash
# PaddleOCR-VL 服务启动脚本

echo "启动 PaddleOCR-VL 服务..."

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate
fi

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "错误: 配置文件 config.yaml 不存在"
    exit 1
fi

# 检查应用文件
if [ ! -f "app.py" ]; then
    echo "错误: 应用文件 app.py 不存在"
    exit 1
fi

# 设置环境变量
export CUDA_VISIBLE_DEVICES=0
export PADDLE_OCR_SERVER_IP=183.250.90.218

# 启动服务
echo "启动服务在端口 8080..."
echo "服务器IP: 183.250.90.218"
echo "访问地址: http://183.250.90.218:8080"
echo "API文档: http://183.250.90.218:8080/docs"

python3 app.py
