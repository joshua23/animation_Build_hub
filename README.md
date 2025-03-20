# ElephantDash - SVG到Lottie动画转换器

将静态SVG图像转换为Lottie动画格式，适用于网页和移动应用。

## 概述

ElephantDash SVG到Lottie动画转换器是一个专注于将SVG矢量图转换为Lottie JSON动画格式的工具。Lottie是一种高性能的、可在多平台使用的动画格式，被广泛应用于网页和移动应用程序。

该工具能够解析复杂的SVG图像，识别元素组，并创建流畅的Lottie动画。

## 特性

- 自动解析和分析SVG结构
- 高效生成Lottie JSON动画
- 批量处理功能
- 自适应不同SVG复杂度
- HTML预览生成
- 全面的Python 3.13支持
- 模块化架构便于扩展

## 安装

```bash
# 克隆仓库
git clone https://github.com/joshua23/animation_Build_hub.git
cd animation_Build_hub

# 安装依赖
pip install -r svg_animator/requirements.txt
```

## 快速开始

### 基本用法

```bash
# 将SVG转换为Lottie JSON
python svg_animator/animation_builder.py your_image.svg
```

### 批量处理

```bash
python svg_animator/animation_builder.py input_directory/ --output output_directory/
```

### 自定义配置

```bash
python svg_animator/animation_builder.py input.svg --config custom_config.json
```

## 配置示例

`custom_config.json`:

```json
{
  "n_frames": 120,
  "framerate": 30,
  "width": 800,
  "height": 600,
  "background_color": "#ffffff"
}
```

## 文档

详细文档请参阅 [svg_animator/README.md](svg_animator/README.md)。

## 系统要求

- Python 3.13
- 必需依赖：
  - lottie
  - svgelements
  - svgwrite
  - numpy
  - pillow

## 贡献

欢迎贡献！请随时提交问题报告、功能请求或拉取请求。

## 许可

详见 [LICENSE](svg_animator/LICENSE) 文件。 