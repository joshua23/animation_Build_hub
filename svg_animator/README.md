# SVG动画构建器

将SVG矢量图转换为动画，支持输出为SVG动画或Lottie JSON格式。

## 特性

- 解析复杂SVG图片
- 支持多种动画输出格式
  - SVG SMIL动画
  - Lottie JSON动画（适用于网页和App）
- 批量处理功能
- HTML预览生成

## 系统要求

- Python 3.13
- 下列Python库:
  - svgwrite
  - svgelements
  - lottie
  - numpy
  - pillow

## 安装

1. 克隆仓库
2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 动画构建器 (推荐)

```bash
# 将SVG转换为Lottie JSON
python animation_builder.py input.svg --format lottie --output output.json

# 将SVG转换为动画SVG
python animation_builder.py input.svg --format svg --output output_animated.svg

# 批量处理目录
python animation_builder.py input_dir/ --output output_dir/ --format lottie

# 使用自定义配置
python animation_builder.py input.svg --config animation_config.json
```

### 2. SVG到Lottie转换器

```bash
python svg_to_lottie_converter.py input.svg output.json
```

### 3. 动画配置示例

创建一个`animation_config.json`文件:

```json
{
  "n_frames": 120,
  "framerate": 30,
  "width": 800,
  "height": 600,
  "background_color": "#ffffff"
}
```

## 转换流程

1. **解析SVG**: 使用SVGParser解析SVG文件并识别元素结构
2. **分析结构**: 确定SVG中的组、路径和形状元素
3. **创建动画**: 根据配置生成动画
   - Lottie模式: 生成JSON和HTML预览
   - SVG模式: 生成带SMIL动画的SVG

## 模块说明

- `svg_parser.py`: SVG解析器，支持svgelements和minidom两种解析方式
- `svg_to_lottie_converter.py`: SVG到Lottie转换模块
- `animation_builder.py`: 主要动画构建模块，整合所有功能
- `exporter.py`: 导出工具，支持HTML预览等

## 高级用法

### 自定义动画配置

可以通过JSON配置文件调整动画参数:

- `n_frames`: 总帧数
- `framerate`: 帧率 (fps)
- `width`/`height`: 动画尺寸
- `background_color`: 背景颜色 (十六进制)

## 示例

```bash
# 基本转换
python animation_builder.py examples/input.svg

# 自定义配置
python animation_builder.py examples/complex.svg --config custom_config.json --format lottie
```

## 故障排除

- 如果遇到"SVG解析错误"，尝试使用更简单的SVG文件
- 对于复杂SVG，建议使用Lottie输出格式获得更好的性能
- 如果lottie库不可用，程序将回退到SVG SMIL动画模式

## 许可

详见LICENSE文件 