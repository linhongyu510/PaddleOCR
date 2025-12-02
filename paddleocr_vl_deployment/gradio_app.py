#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR-VL Gradio 前端应用
"""

import os
import json
import base64
import tempfile
import gradio as gr
import numpy as np
from PIL import Image
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCRVL
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR未安装，将使用模拟模式")

# 全局变量
pipeline = None

def init_paddleocr():
    """初始化PaddleOCR-VL"""
    global pipeline
    if not PADDLEOCR_AVAILABLE:
        return False, "PaddleOCR未安装"
    
    try:
        # 设置PaddlePaddle数据类型和环境变量
        import paddle
        import os
        os.environ['PADDLE_DTYPE'] = 'float32'
        paddle.set_default_dtype('float32')
        
        # 尝试使用更简单的初始化方式
        pipeline = PaddleOCRVL(
            use_doc_orientation_classify=False,  # 先关闭这些功能
            use_doc_unwarping=False,
            use_layout_detection=False,
            use_chart_recognition=False
        )
        return True, "PaddleOCR-VL初始化成功"
    except Exception as e:
        # 如果失败，尝试最基本的初始化
        try:
            print(f"第一次初始化失败: {e}")
            # 尝试最基本的初始化，不设置任何参数
            pipeline = PaddleOCRVL()
            return True, "PaddleOCR-VL初始化成功（基本配置）"
        except Exception as e2:
            print(f"第二次初始化也失败: {e2}")
            return False, f"PaddleOCR-VL初始化失败: {str(e2)}"

def process_image(image, use_doc_orientation_classify, use_doc_unwarping, use_layout_detection, use_chart_recognition):
    """处理图像"""
    if pipeline is None:
        return "❌ PaddleOCR-VL未初始化", None, None
    
    try:
        # 保存临时图像
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            image.save(tmp_file.name)
            temp_path = tmp_file.name
        
        # 执行推理
        output = pipeline.predict(temp_path)
        
        # 处理结果
        results = []
        markdown_texts = []
        
        for i, res in enumerate(output):
            result_info = {
                "page": i + 1,
                "layout": res.layout if hasattr(res, 'layout') else [],
                "text": res.text if hasattr(res, 'text') else "",
                "markdown": res.markdown if hasattr(res, 'markdown') else {}
            }
            results.append(result_info)
            
            if hasattr(res, 'markdown') and res.markdown:
                markdown_texts.append(res.markdown.get('text', ''))
        
        # 清理临时文件
        os.unlink(temp_path)
        
        # 格式化输出
        output_text = f"📄 解析完成，共处理 {len(results)} 页\n\n"
        
        for result in results:
            output_text += f"=== 第 {result['page']} 页 ===\n"
            if result['text']:
                output_text += f"文本内容:\n{result['text']}\n\n"
            if result['markdown'] and result['markdown'].get('text'):
                output_text += f"Markdown:\n{result['markdown']['text']}\n\n"
        
        # 合并所有页面的Markdown
        full_markdown = "\n\n---\n\n".join(markdown_texts) if markdown_texts else "无Markdown内容"
        
        return output_text, full_markdown, results
        
    except Exception as e:
        logger.error(f"处理图像失败: {e}")
        return f"❌ 处理失败: {str(e)}", None, None

def process_pdf(file_path, use_doc_orientation_classify, use_doc_unwarping, use_layout_detection, use_chart_recognition):
    """处理PDF文件"""
    if pipeline is None:
        return "❌ PaddleOCR-VL未初始化", None, None
    
    try:
        # 执行推理
        output = pipeline.predict(file_path)
        
        # 处理结果
        results = []
        markdown_texts = []
        
        for i, res in enumerate(output):
            result_info = {
                "page": i + 1,
                "layout": res.layout if hasattr(res, 'layout') else [],
                "text": res.text if hasattr(res, 'text') else "",
                "markdown": res.markdown if hasattr(res, 'markdown') else {}
            }
            results.append(result_info)
            
            if hasattr(res, 'markdown') and res.markdown:
                markdown_texts.append(res.markdown.get('text', ''))
        
        # 格式化输出
        output_text = f"📄 PDF解析完成，共处理 {len(results)} 页\n\n"
        
        for result in results:
            output_text += f"=== 第 {result['page']} 页 ===\n"
            if result['text']:
                output_text += f"文本内容:\n{result['text']}\n\n"
            if result['markdown'] and result['markdown'].get('text'):
                output_text += f"Markdown:\n{result['markdown']['text']}\n\n"
        
        # 合并所有页面的Markdown
        full_markdown = "\n\n---\n\n".join(markdown_texts) if markdown_texts else "无Markdown内容"
        
        return output_text, full_markdown, results
        
    except Exception as e:
        logger.error(f"处理PDF失败: {e}")
        return f"❌ 处理失败: {str(e)}", None, None

def create_gradio_interface():
    """创建Gradio界面"""
    
    # 初始化PaddleOCR
    init_success, init_message = init_paddleocr()
    
    with gr.Blocks(
        title="PaddleOCR-VL 版面解析服务",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
            margin: auto !important;
        }
        .main-header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        """
    ) as demo:
        
        # 主标题
        gr.HTML("""
        <div class="main-header">
            <h1>🔍 PaddleOCR-VL 版面解析服务</h1>
            <p>智能文档版面解析与OCR识别</p>
            <p>服务器: 183.250.90.218:7860</p>
        </div>
        """)
        
        # 状态显示
        status_text = gr.Textbox(
            value=f"初始化状态: {init_message}",
            label="系统状态",
            interactive=False,
            visible=True
        )
        
        with gr.Tabs():
            # 图像处理标签页
            with gr.Tab("🖼️ 图像解析"):
                with gr.Row():
                    with gr.Column(scale=1):
                        image_input = gr.Image(
                            label="上传图像",
                            type="pil",
                            height=400
                        )
                        
                        with gr.Row():
                            use_doc_orientation_classify = gr.Checkbox(
                                label="文档方向分类",
                                value=True
                            )
                            use_doc_unwarping = gr.Checkbox(
                                label="文本图像矫正",
                                value=True
                            )
                        
                        with gr.Row():
                            use_layout_detection = gr.Checkbox(
                                label="版面区域检测",
                                value=True
                            )
                            use_chart_recognition = gr.Checkbox(
                                label="图表识别",
                                value=True
                            )
                        
                        process_btn = gr.Button(
                            "🚀 开始解析",
                            variant="primary",
                            size="lg"
                        )
                    
                    with gr.Column(scale=2):
                        output_text = gr.Textbox(
                            label="解析结果",
                            lines=15,
                            max_lines=20,
                            show_copy_button=True
                        )
                        
                        markdown_output = gr.Textbox(
                            label="Markdown格式",
                            lines=10,
                            max_lines=15,
                            show_copy_button=True
                        )
                
                # 绑定事件
                process_btn.click(
                    fn=process_image,
                    inputs=[
                        image_input,
                        use_doc_orientation_classify,
                        use_doc_unwarping,
                        use_layout_detection,
                        use_chart_recognition
                    ],
                    outputs=[output_text, markdown_output, gr.State()]
                )
            
            # PDF处理标签页
            with gr.Tab("📄 PDF解析"):
                with gr.Row():
                    with gr.Column(scale=1):
                        pdf_input = gr.File(
                            label="上传PDF文件",
                            file_types=[".pdf"]
                        )
                        
                        with gr.Row():
                            pdf_use_doc_orientation_classify = gr.Checkbox(
                                label="文档方向分类",
                                value=True
                            )
                            pdf_use_doc_unwarping = gr.Checkbox(
                                label="文本图像矫正",
                                value=True
                            )
                        
                        with gr.Row():
                            pdf_use_layout_detection = gr.Checkbox(
                                label="版面区域检测",
                                value=True
                            )
                            pdf_use_chart_recognition = gr.Checkbox(
                                label="图表识别",
                                value=True
                            )
                        
                        pdf_process_btn = gr.Button(
                            "🚀 开始解析PDF",
                            variant="primary",
                            size="lg"
                        )
                    
                    with gr.Column(scale=2):
                        pdf_output_text = gr.Textbox(
                            label="PDF解析结果",
                            lines=15,
                            max_lines=20,
                            show_copy_button=True
                        )
                        
                        pdf_markdown_output = gr.Textbox(
                            label="PDF Markdown格式",
                            lines=10,
                            max_lines=15,
                            show_copy_button=True
                        )
                
                # 绑定事件
                pdf_process_btn.click(
                    fn=process_pdf,
                    inputs=[
                        pdf_input,
                        pdf_use_doc_orientation_classify,
                        pdf_use_doc_unwarping,
                        pdf_use_layout_detection,
                        pdf_use_chart_recognition
                    ],
                    outputs=[pdf_output_text, pdf_markdown_output, gr.State()]
                )
            
            # 使用说明标签页
            with gr.Tab("📖 使用说明"):
                gr.Markdown("""
                ## PaddleOCR-VL 使用说明
                
                ### 🎯 功能特点
                - **智能版面解析**: 自动识别文档的版面结构
                - **OCR文字识别**: 高精度文字识别
                - **图表识别**: 支持表格、图表等复杂元素识别
                - **文档矫正**: 自动矫正倾斜的文档图像
                - **方向分类**: 自动识别文档方向
                
                ### 📝 使用方法
                1. **图像解析**: 上传图像文件，选择处理选项，点击"开始解析"
                2. **PDF解析**: 上传PDF文件，选择处理选项，点击"开始解析PDF"
                3. **结果查看**: 查看解析结果和Markdown格式输出
                
                ### ⚙️ 参数说明
                - **文档方向分类**: 自动识别文档的旋转方向
                - **文本图像矫正**: 矫正弯曲或倾斜的文本
                - **版面区域检测**: 检测文档中的不同区域（标题、正文、表格等）
                - **图表识别**: 识别和解析表格、图表等结构化内容
                
                ### 🔧 支持格式
                - **图像格式**: JPG, PNG, BMP, TIFF等
                - **文档格式**: PDF
                - **输出格式**: 文本、Markdown、结构化数据
                
                ### 📞 技术支持
                - 服务器地址: 183.250.90.218:7860
                - 如遇问题，请检查网络连接和服务状态
                """)
        
        # 页脚
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #666;">
            <p>PaddleOCR-VL 版面解析服务 | 服务器: 183.250.90.218:7860</p>
            <p>支持图像和PDF文档的智能版面解析</p>
        </div>
        """)
    
    return demo

if __name__ == "__main__":
    # 创建Gradio界面
    demo = create_gradio_interface()
    
    # 启动服务
    demo.launch(
        server_name="0.0.0.0",
        server_port=8080,  # 使用8080端口
        share=False,
        show_error=True,
        quiet=False
    )
