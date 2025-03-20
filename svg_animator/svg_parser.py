#!/usr/bin/env python3
"""
SVG解析器 - 解析SVG文件并识别元素组
兼容Python 3.13环境
"""
import re
from pathlib import Path
from xml.dom import minidom
from collections import defaultdict
import sys
import importlib
import importlib.util

# 更健壮的库依赖检查
def check_module_available(module_name):
    """检查模块是否可用"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ModuleNotFoundError:
        return False

# 提前声明SVG组件类型，避免linter错误
Group = Path = Circle = Rect = None

# 检查svgelements库
SVGELEMENTS_AVAILABLE = check_module_available("svgelements")
if SVGELEMENTS_AVAILABLE:
    try:
        from svgelements import SVG, Group, Path, Circle, Rect
    except ImportError:
        SVGELEMENTS_AVAILABLE = False
        print("警告: svgelements库导入出错，将使用备用解析方法")

if not SVGELEMENTS_AVAILABLE:
    print("提示: svgelements库不可用，某些功能将受限。您可以安装：pip install svgelements")

class SVGParser:
    """解析SVG文件并识别组件结构"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.svg = None
        self.svg_doc = None
        self.element_groups = {
            'groups': [], 
            'paths': [], 
            'shapes': [],
            'original_elements': {}  # 存储原始元素内容
        }
        self.structure_map = {}
        
    def log(self, message):
        """输出日志信息"""
        if self.verbose:
            print(message)
    
    def load_svg(self, svg_path):
        """从文件加载SVG"""
        self.log(f"加载SVG: {svg_path}")
        self.svg = None
        self.svg_doc = None
        
        # 尝试使用svgelements解析
        if SVGELEMENTS_AVAILABLE:
            try:
                self.svg = SVG.parse(svg_path)
                self.log("使用svgelements成功解析")
                return True
            except Exception as e:
                self.log(f"svgelements解析出错: {e}")
        
        # 回退到minidom
        try:
            self.svg_doc = minidom.parse(svg_path)
            self.log("使用minidom成功解析")
            return True
        except Exception as e:
            self.log(f"解析SVG出错: {e}")
            return False
    
    def analyze_structure(self):
        """分析SVG结构并识别组件"""
        self.element_groups = {
            'groups': [], 
            'paths': [], 
            'shapes': [],
            'original_elements': {}  # 重置原始元素内容
        }
        
        if self.svg is not None:
            self._analyze_with_svgelements()
        else:
            self._analyze_with_minidom()
            
        self.log(f"找到 {len(self.element_groups['groups'])} 个组, "
                f"{len(self.element_groups['paths'])} 个路径, "
                f"{len(self.element_groups['shapes'])} 个形状")
        
        # 检查是否为扁平结构
        return len(self.element_groups['groups']) < 3 and len(self.element_groups['paths']) > 20
    
    def _analyze_with_svgelements(self):
        """使用svgelements分析SVG结构"""
        def process_element(element, parent_id=None):
            element_id = getattr(element, 'id', f"element_{len(self.structure_map)}")
            
            # 记录元素信息
            self.structure_map[element_id] = {
                'type': element.__class__.__name__,
                'parent': parent_id
            }
            
            # 保存原始元素信息
            self._save_element_content(element_id, element)
            
            # 分类元素
            if SVGELEMENTS_AVAILABLE and isinstance(element, Group):
                self.element_groups['groups'].append(element_id)
                # 递归处理子元素
                for child in element:
                    process_element(child, element_id)
            elif SVGELEMENTS_AVAILABLE and isinstance(element, Path):
                self.element_groups['paths'].append(element_id)
            elif SVGELEMENTS_AVAILABLE and isinstance(element, (Circle, Rect)):
                self.element_groups['shapes'].append(element_id)
        
        # 从根元素开始分析
        try:
            process_element(self.svg)
        except Exception as e:
            self.log(f"svgelements分析过程出错: {e}")
            # 尝试降级到minidom
            if self.svg_doc is None:
                try:
                    self.svg_doc = minidom.parseString(self.svg.tostring())
                    self._analyze_with_minidom()
                except Exception as e2:
                    self.log(f"降级到minidom也失败: {e2}")
    
    def _analyze_with_minidom(self):
        """使用minidom分析SVG结构"""
        def process_node(node, parent_id=None):
            if node.nodeType != node.ELEMENT_NODE:
                return
            
            element_id = node.getAttribute('id') or f"element_{len(self.structure_map)}"
            
            # 记录元素信息
            self.structure_map[element_id] = {
                'type': node.tagName,
                'parent': parent_id
            }
            
            # 保存原始元素内容
            self._save_node_content(element_id, node)
            
            # 分类元素
            if node.tagName == 'g':
                self.element_groups['groups'].append(element_id)
            elif node.tagName == 'path':
                self.element_groups['paths'].append(element_id)
            elif node.tagName in ('circle', 'rect', 'ellipse', 'polygon', 'polyline'):
                self.element_groups['shapes'].append(element_id)
            
            # 递归处理子元素
            for child in node.childNodes:
                process_node(child, element_id)
        
        # 从根元素开始分析
        try:
            process_node(self.svg_doc.documentElement)
        except Exception as e:
            self.log(f"minidom分析过程出错: {e}")
    
    def _save_element_content(self, element_id, element):
        """保存svgelements元素的内容信息"""
        try:
            if hasattr(element, 'id') and element.id:
                elements = []
                
                # 处理不同类型的元素
                if SVGELEMENTS_AVAILABLE and isinstance(element, Circle):
                    elements.append({
                        'type': 'circle',
                        'cx': element.cx,
                        'cy': element.cy,
                        'r': element.r,
                        'fill': element.fill
                    })
                elif SVGELEMENTS_AVAILABLE and isinstance(element, Rect):
                    elements.append({
                        'type': 'rect',
                        'x': element.x,
                        'y': element.y,
                        'width': element.width,
                        'height': element.height,
                        'fill': element.fill
                    })
                elif SVGELEMENTS_AVAILABLE and isinstance(element, Path):
                    elements.append({
                        'type': 'path',
                        'd': element.d(),
                        'fill': element.fill
                    })
                
                if elements:
                    self.element_groups['original_elements'][element_id] = elements
        except Exception as e:
            self.log(f"保存元素内容出错 ({element_id}): {e}")
    
    def _save_node_content(self, element_id, node):
        """保存minidom节点的内容信息"""
        try:
            elements = []
            
            # 处理不同类型的元素
            if node.tagName == 'circle':
                elements.append({
                    'type': 'circle',
                    'cx': float(node.getAttribute('cx') or 0),
                    'cy': float(node.getAttribute('cy') or 0),
                    'r': float(node.getAttribute('r') or 5),
                    'fill': node.getAttribute('fill') or 'black'
                })
            elif node.tagName == 'rect':
                elements.append({
                    'type': 'rect',
                    'x': float(node.getAttribute('x') or 0),
                    'y': float(node.getAttribute('y') or 0),
                    'width': float(node.getAttribute('width') or 10),
                    'height': float(node.getAttribute('height') or 10),
                    'fill': node.getAttribute('fill') or 'black'
                })
            elif node.tagName == 'path':
                elements.append({
                    'type': 'path',
                    'd': node.getAttribute('d') or 'M0,0',
                    'fill': node.getAttribute('fill') or 'none'
                })
            elif node.tagName in ('polygon', 'polyline'):
                elements.append({
                    'type': node.tagName,
                    'points': node.getAttribute('points') or '',
                    'fill': node.getAttribute('fill') or 'none'
                })
            # 对于组，保存所有子元素
            elif node.tagName == 'g':
                for child in node.childNodes:
                    if child.nodeType == child.ELEMENT_NODE:
                        child_elements = self._extract_node_elements(child)
                        if child_elements:
                            elements.extend(child_elements)
            
            if elements:
                self.element_groups['original_elements'][element_id] = elements
        except Exception as e:
            self.log(f"保存节点内容出错 ({element_id}): {e}")
    
    def _extract_node_elements(self, node):
        """提取节点中的元素信息"""
        elements = []
        
        if node.nodeType != node.ELEMENT_NODE:
            return elements
        
        try:    
            if node.tagName == 'circle':
                elements.append({
                    'type': 'circle',
                    'cx': float(node.getAttribute('cx') or 0),
                    'cy': float(node.getAttribute('cy') or 0),
                    'r': float(node.getAttribute('r') or 5),
                    'fill': node.getAttribute('fill') or 'black'
                })
            elif node.tagName == 'rect':
                elements.append({
                    'type': 'rect',
                    'x': float(node.getAttribute('x') or 0),
                    'y': float(node.getAttribute('y') or 0),
                    'width': float(node.getAttribute('width') or 10),
                    'height': float(node.getAttribute('height') or 10),
                    'fill': node.getAttribute('fill') or 'black'
                })
            elif node.tagName == 'path':
                elements.append({
                    'type': 'path',
                    'd': node.getAttribute('d') or 'M0,0',
                    'fill': node.getAttribute('fill') or 'none'
                })
            elif node.tagName in ('polygon', 'polyline'):
                elements.append({
                    'type': node.tagName,
                    'points': node.getAttribute('points') or '',
                    'fill': node.getAttribute('fill') or 'none'
                })
            elif node.tagName == 'g':
                for child in node.childNodes:
                    if child.nodeType == child.ELEMENT_NODE:
                        child_elements = self._extract_node_elements(child)
                        if child_elements:
                            elements.extend(child_elements)
        except Exception as e:
            pass  # 忽略单个元素的解析错误
        
        return elements
    
    def get_element_groups(self):
        """获取分组结果"""
        return self.element_groups
    
    def get_element_by_id(self, element_id):
        """根据ID获取元素"""
        if element_id in self.element_groups['original_elements']:
            return self.element_groups['original_elements'][element_id]
        return None
    
    def get_svg_size(self):
        """获取SVG尺寸"""
        try:
            if self.svg is not None:
                return self.svg.width, self.svg.height
            else:
                root = self.svg_doc.documentElement
                width = root.getAttribute('width') or '800'
                height = root.getAttribute('height') or '600'
                # 移除单位（如px）
                width = re.sub(r'[^0-9.]', '', width)
                height = re.sub(r'[^0-9.]', '', height)
                return float(width), float(height)
        except Exception as e:
            self.log(f"获取SVG尺寸出错: {e}")
            return 800.0, 600.0  # 返回默认值
    
    def get_elements_by_type(self, element_type):
        """根据元素类型获取元素列表"""
        if element_type == 'path':
            return self.element_groups['paths']
        elif element_type in ('rect', 'circle', 'ellipse', 'polygon', 'polyline'):
            return [eid for eid in self.element_groups['shapes'] 
                   if self.structure_map.get(eid, {}).get('type', '').lower() == element_type.lower()]
        elif element_type == 'group':
            return self.element_groups['groups']
        return []