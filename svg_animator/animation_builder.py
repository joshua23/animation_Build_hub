#!/usr/bin/env python3
"""
SVG动画构建器 - 专注于SVG到Lottie的转换功能
适用于Python 3.13环境
"""
import os
import sys
import argparse
from pathlib import Path
import time
import json

# 导入自定义模块
from svg_parser import SVGParser
from svg_to_lottie_converter import SVGToLottieConverter, LOTTIE_AVAILABLE

class AnimationBuilder:
    """SVG到Lottie动画构建器"""
    
    def __init__(self, verbose=True):
        """初始化构建器"""
        self.verbose = verbose
        self.parser = SVGParser(verbose=verbose)
        
        # 检查lottie库是否可用
        if not LOTTIE_AVAILABLE:
            raise ImportError("错误: Lottie库不可用，请安装: pip install lottie")
        
        # 初始化Lottie转换器
        self.lottie_converter = SVGToLottieConverter(verbose=verbose)
    
    def log(self, message):
        """输出日志信息"""
        if self.verbose:
            print(message)
    
    def process_svg(self, svg_path, output_path=None, animation_config=None):
        """
        处理SVG文件并构建Lottie动画
        
        Args:
            svg_path (str): SVG文件路径
            output_path (str, optional): 输出文件路径
            animation_config (dict, optional): 动画配置
        
        Returns:
            dict: 包含处理结果的字典
        """
        result = {
            "success": False,
            "input_file": svg_path,
            "output_files": [],
            "format": "lottie",
            "messages": []
        }
        
        # 确认输入文件存在
        if not os.path.exists(svg_path):
            result["messages"].append(f"错误: 输入文件不存在: {svg_path}")
            return result
        
        # 确定输出路径
        if output_path is None:
            output_path = str(Path(svg_path).with_suffix('.json'))
        
        # 步骤1: 解析SVG
        self.log(f"[1/3] 解析SVG: {svg_path}")
        if not self.parser.load_svg(svg_path):
            result["messages"].append(f"错误: 无法加载SVG文件: {svg_path}")
            return result
        
        # 步骤2: 分析SVG结构
        self.log(f"[2/3] 分析SVG结构")
        is_flat = self.parser.analyze_structure()
        element_groups = self.parser.get_element_groups()
        svg_width, svg_height = self.parser.get_svg_size()
        
        # 记录结构信息
        structure_info = {
            "is_flat": is_flat,
            "groups": len(element_groups['groups']),
            "paths": len(element_groups['paths']),
            "shapes": len(element_groups['shapes']),
            "dimensions": f"{svg_width}x{svg_height}"
        }
        result["structure_info"] = structure_info
        
        # 步骤3: 构建Lottie动画
        self.log(f"[3/3] 构建Lottie动画")
        
        # 确保有合适的配置
        if animation_config is None:
            animation_config = {}
        
        # 添加宽高信息（如果未指定）
        if "width" not in animation_config:
            animation_config["width"] = svg_width
        if "height" not in animation_config:
            animation_config["height"] = svg_height
        
        # 执行转换
        json_path = self.lottie_converter.convert_svg_to_lottie(
            svg_path, 
            output_path, 
            animation_config
        )
        
        if json_path:
            result["success"] = True
            result["output_files"].append(json_path)
            
            # 创建HTML预览
            html_path = self.lottie_converter.create_lottie_preview_html(json_path)
            if html_path:
                result["output_files"].append(html_path)
                result["messages"].append(f"创建了Lottie预览: {html_path}")
        else:
            result["messages"].append("转换为Lottie格式失败")
        
        return result
    
    def batch_process(self, input_dir, output_dir=None, animation_config=None):
        """
        批量处理目录中的SVG文件
        
        Args:
            input_dir (str): 输入目录
            output_dir (str, optional): 输出目录
            animation_config (dict, optional): 动画配置
            
        Returns:
            dict: 包含批处理结果的字典
        """
        result = {
            "success": True,
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "input_dir": input_dir,
            "output_dir": output_dir,
            "results": []
        }
        
        # 确定输出目录
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(input_dir), "lottie_animations")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        result["output_dir"] = output_dir
        
        # 获取所有SVG文件
        svg_files = []
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith('.svg'):
                    svg_files.append(os.path.join(root, file))
        
        result["total_files"] = len(svg_files)
        self.log(f"找到 {len(svg_files)} 个SVG文件")
        
        # 处理每个文件
        for i, svg_file in enumerate(svg_files):
            self.log(f"处理文件 {i+1}/{len(svg_files)}: {svg_file}")
            
            # 确定输出路径
            rel_path = os.path.relpath(svg_file, input_dir)
            filename = os.path.basename(rel_path)
            basename = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{basename}.json")
            
            # 处理单个文件
            file_result = self.process_svg(
                svg_file,
                output_path=output_path,
                animation_config=animation_config
            )
            
            # 记录结果
            result["results"].append(file_result)
            if file_result["success"]:
                result["processed_files"] += 1
            else:
                result["failed_files"] += 1
                result["success"] = False
        
        return result

def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description="SVG到Lottie动画构建器")
    parser.add_argument("input", help="输入SVG文件或目录")
    parser.add_argument("--output", "-o", help="输出文件或目录")
    parser.add_argument("--config", "-c", help="动画配置JSON文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出详细日志")
    
    args = parser.parse_args()
    
    # 加载配置文件
    animation_config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                animation_config = json.load(f)
        except Exception as e:
            print(f"错误: 无法加载配置文件: {e}")
            sys.exit(1)
    
    try:
        # 初始化构建器
        builder = AnimationBuilder(verbose=args.verbose)
        
        # 确定是文件还是目录
        if os.path.isfile(args.input):
            # 处理单个文件
            result = builder.process_svg(
                args.input,
                output_path=args.output,
                animation_config=animation_config
            )
            
            # 输出结果
            if result["success"]:
                print(f"成功！输出文件:")
                for output_file in result["output_files"]:
                    print(f"  - {output_file}")
            else:
                print("处理失败:")
                for message in result["messages"]:
                    print(f"  - {message}")
                sys.exit(1)
        
        elif os.path.isdir(args.input):
            # 批量处理目录
            result = builder.batch_process(
                args.input,
                output_dir=args.output,
                animation_config=animation_config
            )
            
            # 输出结果
            print(f"批处理完成: 总共 {result['total_files']} 个文件，"
                f"成功 {result['processed_files']} 个，"
                f"失败 {result['failed_files']} 个")
            
            if result["failed_files"] > 0:
                print("失败文件:")
                for file_result in result["results"]:
                    if not file_result["success"]:
                        print(f"  - {file_result['input_file']}")
                        for message in file_result["messages"]:
                            print(f"    {message}")
                sys.exit(1)
        
        else:
            print(f"错误: 输入路径不存在: {args.input}")
            sys.exit(1)
    
    except ImportError as e:
        print(str(e))
        print("请安装必要的依赖: pip install lottie")
        sys.exit(1)

if __name__ == "__main__":
    main() 