#!/usr/bin/env python3
"""
前端服务器 - 运行在8080端口，提供静态页面服务
API调用转发到16110端口的后端服务
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 创建前端应用
app = FastAPI(title="PolyOCR Frontend", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 根路径 - OCR主页面
@app.get("/")
async def index():
    """OCR主页面"""
    return FileResponse("index.html")

# 翻译页面
@app.get("/translation")
async def translation():
    """翻译页面"""
    return FileResponse("translation.html")

# 简单测试页面
@app.get("/simple-test")
async def simple_test():
    """简单测试页面"""
    return FileResponse("simple_test.html")

# 翻译调试页面
@app.get("/debug-translation")
async def debug_translation():
    """翻译调试页面"""
    return FileResponse("debug_translation.html")

# 测试翻译页面
@app.get("/test-translation")
async def test_translation():
    """测试翻译页面"""
    return FileResponse("test_translation_page.html")

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs("static", exist_ok=True)
    
    # 启动前端服务
    uvicorn.run(
        "frontend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
