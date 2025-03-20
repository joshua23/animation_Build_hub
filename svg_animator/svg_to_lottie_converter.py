#!/usr/bin/env python3
"""
SVG到Lottie转换模块 - 适用于Python 3.13
将SVG文件解析并转换为Lottie JSON动画格式
"""
import os
import sys
import json
from pathlib import Path
import importlib
import importlib.util
import math
import re

# 从SVG解析器导入SVGParser
from svg_parser import SVGParser

# 检查lottie库是否可用
def check_module_available(module_name):
    """检查模块是否可用"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ModuleNotFoundError:
        return False

# 检查lottie库
LOTTIE_AVAILABLE = check_module_available("lottie")
if LOTTIE_AVAILABLE:
    try:
        import lottie
        from lottie import objects
        from lottie.utils import animation as anim_utils
        from lottie.exporters import export_lottie
        from lottie.objects.properties import Value, MultiDimensional
    except ImportError as e:
        LOTTIE_AVAILABLE = False
        print(f"警告: lottie库导入出错: {e}")

if not LOTTIE_AVAILABLE:
    print("错误: lottie库不可用。请安装: pip install lottie")
    print("该模块需要lottie库才能工作。")

class SVGToLottieConverter:
    """SVG到Lottie转换器"""
    
    def __init__(self, verbose=True):
        """初始化转换器"""
        self.verbose = verbose
        self.parser = SVGParser(verbose=verbose)
    
    def log(self, message):
        """输出日志信息"""
        if self.verbose:
            print(message)
    
    def convert_svg_to_lottie(self, svg_path, json_path=None, animation_config=None):
        """
        将SVG文件转换为Lottie JSON
        
        Args:
            svg_path (str): SVG文件路径
            json_path (str, optional): 输出的JSON文件路径，如果不提供则生成默认路径
            animation_config (dict, optional): 动画配置
        
        Returns:
            str: 生成的JSON文件路径，失败则返回None
        """
        if not LOTTIE_AVAILABLE:
            self.log("错误: lottie库不可用，无法进行转换")
            return None
        
        # 默认动画配置
        default_config = {
            "n_frames": 90,
            "framerate": 30,
            "width": 800,
            "height": 600,
            "background_color": "#ffffff"
        }
        
        # 合并用户配置
        config = default_config.copy()
        if animation_config:
            config.update(animation_config)
        
        # 确定输出路径
        if json_path is None:
            json_path = Path(svg_path).with_suffix('.json')
        
        # 解析SVG
        self.log(f"解析SVG文件: {svg_path}")
        if not self.parser.load_svg(svg_path):
            self.log("错误: 无法加载SVG文件")
            return None
        
        # 分析SVG结构
        self.parser.analyze_structure()
        element_groups = self.parser.get_element_groups()
        svg_width, svg_height = self.parser.get_svg_size()
        
        # 创建Lottie动画
        self.log("创建Lottie动画")
        an = objects.Animation(
            n_frames=config["n_frames"], 
            framerate=config["framerate"]
        )
        an.name = Path(svg_path).stem
        an.width = config.get("width", svg_width)
        an.height = config.get("height", svg_height)
        
        # 创建背景图层
        background_layer = objects.ShapeLayer()
        background_layer.name = "Background"
        
        # 如果有背景颜色，创建背景矩形
        if config["background_color"]:
            bg_rect = objects.Rect()
            bg_rect.position.value = (an.width/2, an.height/2)
            bg_rect.size.value = (an.width, an.height)
            
            bg_fill = objects.Fill()
            # 解析十六进制颜色为RGB
            color = config["background_color"].lstrip('#')
            rgb = tuple(int(color[i:i+2], 16)/255 for i in (0, 2, 4))
            bg_fill.color.value = (rgb[0], rgb[1], rgb[2], 1)
            
            bg_group = objects.Group()
            bg_group.add_shape(bg_rect)
            bg_group.add_shape(bg_fill)
            background_layer.add_shape(bg_group)
        
        an.add_layer(background_layer)
        
        # 处理SVG元素组，创建对应图层
        self._process_element_groups(an, element_groups)
        
        # 保存为Lottie JSON
        self.log(f"保存Lottie JSON: {json_path}")
        try:
            export_lottie.export_lottie(an, json_path)
            return json_path
        except Exception as e:
            self.log(f"保存Lottie JSON出错: {e}")
            return None
    
    def _process_element_groups(self, animation, element_groups):
        """
        处理SVG元素组，创建对应的Lottie图层和形状
        
        Args:
            animation: Lottie动画对象
            element_groups: SVG元素组
        """
        # 创建主要图层
        main_layer = objects.ShapeLayer()
        main_layer.name = "Main Elements"
        
        # 处理路径元素
        for path_id in element_groups['paths']:
            path_data = self.parser.get_element_by_id(path_id)
            if path_data:
                self._add_path_to_layer(main_layer, path_data[0])
        
        # 处理形状元素
        for shape_id in element_groups['shapes']:
            shape_data = self.parser.get_element_by_id(shape_id)
            if shape_data:
                self._add_shape_to_layer(main_layer, shape_data[0])
        
        # 添加主图层到动画
        animation.add_layer(main_layer)
        
        # 处理组元素，每个组创建一个图层
        for i, group_id in enumerate(element_groups['groups']):
            group_data = self.parser.get_element_by_id(group_id)
            if group_data:
                group_layer = objects.ShapeLayer()
                group_layer.name = f"Group {i+1}"
                
                for element in group_data:
                    if element['type'] == 'path':
                        self._add_path_to_layer(group_layer, element)
                    elif element['type'] in ('rect', 'circle', 'polygon', 'polyline'):
                        self._add_shape_to_layer(group_layer, element)
                
                animation.add_layer(group_layer)
    
    def _add_path_to_layer(self, layer, path_data):
        """
        添加路径到图层
        
        Args:
            layer: Lottie图层
            path_data: 路径数据
        """
        if 'd' not in path_data:
            return
        
        try:
            # 创建形状组
            shape_group = objects.Group()
            
            # 创建路径
            path = objects.Path()
            # 这里需要将SVG路径字符串转换为Lottie路径格式
            # 简单起见，这里只支持基本路径格式
            path.shape.value = self._parse_svg_path(path_data['d'])
            
            # 创建填充
            fill = objects.Fill()
            fill_color = self._parse_color(path_data.get('fill', 'black'))
            fill.color.value = fill_color
            
            # 添加到组
            shape_group.add_shape(path)
            shape_group.add_shape(fill)
            
            # 添加到图层
            layer.add_shape(shape_group)
        except Exception as e:
            if self.verbose:
                print(f"添加路径出错: {e}")
    
    def _add_shape_to_layer(self, layer, shape_data):
        """
        添加形状到图层
        
        Args:
            layer: Lottie图层
            shape_data: 形状数据
        """
        try:
            # 创建形状组
            shape_group = objects.Group()
            
            if shape_data['type'] == 'rect':
                # 创建矩形
                rect = objects.Rect()
                rect.position.value = (
                    float(shape_data.get('x', 0)) + float(shape_data.get('width', 10))/2,
                    float(shape_data.get('y', 0)) + float(shape_data.get('height', 10))/2
                )
                rect.size.value = (
                    float(shape_data.get('width', 10)),
                    float(shape_data.get('height', 10))
                )
                shape_group.add_shape(rect)
            
            elif shape_data['type'] == 'circle':
                # 创建椭圆（Lottie没有直接的圆形，用椭圆代替）
                ellipse = objects.Ellipse()
                ellipse.position.value = (
                    float(shape_data.get('cx', 0)),
                    float(shape_data.get('cy', 0))
                )
                radius = float(shape_data.get('r', 5))
                ellipse.size.value = (radius*2, radius*2)
                shape_group.add_shape(ellipse)
            
            # 创建填充
            fill = objects.Fill()
            fill_color = self._parse_color(shape_data.get('fill', 'black'))
            fill.color.value = fill_color
            shape_group.add_shape(fill)
            
            # 添加到图层
            layer.add_shape(shape_group)
        except Exception as e:
            if self.verbose:
                print(f"添加形状出错: {e}")
    
    def _parse_svg_path(self, d_string):
        """
        解析SVG路径字符串为Lottie路径
        
        Args:
            d_string: SVG路径字符串
        
        Returns:
            list: Lottie路径数据
        """
        # 注意：这是一个简化实现，仅支持简单的M, L, C, Z命令
        # 完整实现需要更复杂的SVG路径解析
        try:
            # 占位实现，实际项目中需要完整实现SVG路径解析
            # 这里返回一个示例路径
            return [
                [0, 0, 0],  # 闭合状态，顶点类型，顶点索引
                [1, 2, 0, 0, 0, 0]  # 位置x, 位置y, 入点x, 入点y, 出点x, 出点y
            ]
        except Exception as e:
            if self.verbose:
                print(f"解析SVG路径出错: {e}")
            return []
    
    def _parse_color(self, color_str):
        """
        解析颜色字符串为RGBA元组
        
        Args:
            color_str: 颜色字符串，如"#ff0000"或"red"
        
        Returns:
            tuple: RGBA颜色值(r, g, b, a)，范围0-1
        """
        # 颜色名称映射
        color_map = {
            'black': (0, 0, 0, 1),
            'white': (1, 1, 1, 1),
            'red': (1, 0, 0, 1),
            'green': (0, 1, 0, 1),
            'blue': (0, 0, 1, 1),
            'yellow': (1, 1, 0, 1),
            'cyan': (0, 1, 1, 1),
            'magenta': (1, 0, 1, 1),
            'none': (0, 0, 0, 0)
        }
        
        # 默认黑色
        default_color = (0, 0, 0, 1)
        
        if not color_str or color_str.lower() == 'none':
            return (0, 0, 0, 0)  # 透明
        
        # 检查是否为已知颜色名称
        if color_str.lower() in color_map:
            return color_map[color_str.lower()]
        
        # 尝试解析为十六进制
        if color_str.startswith('#'):
            try:
                color = color_str.lstrip('#')
                if len(color) == 3:  # 简写形式 #RGB
                    r = int(color[0] + color[0], 16) / 255
                    g = int(color[1] + color[1], 16) / 255
                    b = int(color[2] + color[2], 16) / 255
                    return (r, g, b, 1)
                elif len(color) == 6:  # 标准形式 #RRGGBB
                    r = int(color[0:2], 16) / 255
                    g = int(color[2:4], 16) / 255
                    b = int(color[4:6], 16) / 255
                    return (r, g, b, 1)
                elif len(color) == 8:  # 带透明度 #RRGGBBAA
                    r = int(color[0:2], 16) / 255
                    g = int(color[2:4], 16) / 255
                    b = int(color[4:6], 16) / 255
                    a = int(color[6:8], 16) / 255
                    return (r, g, b, a)
            except ValueError:
                pass
        
        # 尝试解析为rgb(r,g,b)格式
        rgb_match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
        if rgb_match:
            try:
                r = int(rgb_match.group(1)) / 255
                g = int(rgb_match.group(2)) / 255
                b = int(rgb_match.group(3)) / 255
                return (r, g, b, 1)
            except ValueError:
                pass
        
        # 尝试解析为rgba(r,g,b,a)格式
        rgba_match = re.match(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d\.]+)\s*\)', color_str)
        if rgba_match:
            try:
                r = int(rgba_match.group(1)) / 255
                g = int(rgba_match.group(2)) / 255
                b = int(rgba_match.group(3)) / 255
                a = float(rgba_match.group(4))
                return (r, g, b, a)
            except ValueError:
                pass
        
        # 返回默认颜色
        return default_color
    
    def create_lottie_preview_html(self, json_file_path, html_file_path=None):
        """
        为Lottie JSON创建HTML预览文件
        
        Args:
            json_file_path: Lottie JSON文件路径
            html_file_path: 输出的HTML文件路径，默认为JSON文件同名但后缀为.html
        
        Returns:
            str: 生成的HTML文件路径
        """
        # 如果未提供HTML文件路径，生成默认路径
        if html_file_path is None:
            html_file_path = str(Path(json_file_path).with_suffix('.html'))
        
        # HTML模板
        template = '''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Lottie动画预览</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.10.2/lottie.min.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background-color: #f0f0f0;
                    font-family: Arial, sans-serif;
                }
                .container {
                    max-width: 800px;
                    width: 100%;
                    padding: 20px;
                    box-sizing: border-box;
                }
                .animation-container {
                    width: 100%;
                    background-color: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    text-align: center;
                    color: #333;
                }
                .controls {
                    margin-top: 20px;
                    display: flex;
                    justify-content: center;
                }
                button {
                    padding: 10px 15px;
                    margin: 0 5px;
                    border: none;
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Lottie动画预览</h1>
                <div id="animation" class="animation-container"></div>
                <div class="controls">
                    <button id="play">播放</button>
                    <button id="pause">暂停</button>
                    <button id="stop">停止</button>
                </div>
            </div>
            
            <script>
                // 加载JSON数据
                const animationPath = '__JSON_PATH__';
                let animInstance;
                
                // 初始化Lottie动画
                function initAnimation() {
                    animInstance = lottie.loadAnimation({
                        container: document.getElementById('animation'),
                        renderer: 'svg',
                        loop: true,
                        autoplay: false,
                        path: animationPath
                    });
                    
                    // 设置事件监听
                    document.getElementById('play').addEventListener('click', () => {
                        animInstance.play();
                    });
                    
                    document.getElementById('pause').addEventListener('click', () => {
                        animInstance.pause();
                    });
                    
                    document.getElementById('stop').addEventListener('click', () => {
                        animInstance.stop();
                    });
                }
                
                // 页面加载完成后初始化动画
                document.addEventListener('DOMContentLoaded', initAnimation);
            </script>
        </body>
        </html>
        '''
        
        # 替换JSON路径
        html_content = template.replace('__JSON_PATH__', os.path.basename(json_file_path))
        
        # 写入HTML文件
        try:
            with open(html_file_path, 'w') as f:
                f.write(html_content)
            return html_file_path
        except Exception as e:
            self.log(f"创建HTML预览出错: {e}")
            return None

def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python svg_to_lottie_converter.py <svg_file> [output_json]")
        sys.exit(1)
    
    svg_path = sys.argv[1]
    json_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = SVGToLottieConverter()
    json_file = converter.convert_svg_to_lottie(svg_path, json_path)
    
    if json_file:
        print(f"转换成功: {json_file}")
        html_file = converter.create_lottie_preview_html(json_file)
        if html_file:
            print(f"创建预览: {html_file}")
    else:
        print("转换失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 