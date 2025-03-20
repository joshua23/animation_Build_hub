#!/usr/bin/env python3
"""
导出器 - 将SVG转换为HTML格式
"""
import os
from pathlib import Path

class Exporter:
    """将SVG转换为不同格式的工具"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    def log(self, message):
        """输出日志信息"""
        if self.verbose:
            print(message)
    
    def to_html(self, svg_path, output_path=None, title=None):
        """将SVG文件转换为HTML文件"""
        # 读取SVG文件
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except Exception as e:
            self.log(f"读取SVG文件时出错: {e}")
            return None
        
        # 确定输出路径
        if output_path is None:
            svg_path_obj = Path(svg_path)
            output_path = svg_path_obj.with_suffix('.html')
        
        # 确定标题
        if title is None:
            title = Path(svg_path).stem
        
        # 创建HTML内容
        html_content = self._create_html_template(svg_content, title)
        
        # 保存HTML文件
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.log(f"HTML文件已保存到: {output_path}")
            return output_path
        except Exception as e:
            self.log(f"保存HTML文件时出错: {e}")
            return None
    
    def _create_html_template(self, svg_content, title):
        """创建HTML模板"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f5f5f5;
            font-family: 'Arial', sans-serif;
        }}
        .container {{
            max-width: 90vw;
            max-height: 90vh;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            background-color: white;
            padding: 20px;
            border-radius: 5px;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        svg {{
            max-width: 100%;
            max-height: 70vh;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="svg-container">
            {svg_content}
        </div>
    </div>
</body>
</html>
""" 