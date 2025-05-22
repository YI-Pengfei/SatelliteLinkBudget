"""
依赖库 pip install customtkinter openpyxl pandas
打包命令：pyinstaller --onedir --windowed  --hidden-import customtkinter  --hidden-import openpyxl --collect-all customtkinter  "D:\PySimpleGUI.py"
"""
import tkinter as tk
import customtkinter as ctk
from math import sin, cos, tan, log, pi
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment  # Add this import
from tkinter import filedialog, messagebox
from datetime import datetime
import os
import math
from LinkCalculator import LinkCalculator

ctk.set_appearance_mode("System")  # 跟随系统主题
ctk.set_default_color_theme("blue")  # 使用官方主题配色
# ------------------------
# 安全数学函数白名单（全角度制支持）
# ------------------------
# 定义安全的数学函数集合，防止eval执行恶意代码
# 支持角度制（默认）和弧度制（函数名带rad后缀）
SAFE_MATH = {
    'sin': lambda x: math.sin(math.radians(x)),  # 角度制正弦函数
    'cos': lambda x: math.cos(math.radians(x)),  # 角度制余弦函数
    'tan': lambda x: math.tan(math.radians(x)),  # 角度制正切函数
    'arcsin': lambda x: math.degrees(math.asin(x)),  # 反正弦（返回角度）
    'arccos': lambda x: math.degrees(math.acos(x)),  # 反余弦（返回角度）
    'arctan': lambda x: math.degrees(math.atan(x)),  # 反正切（返回角度）
    'sinrad': math.sin,  # 弧度制正弦函数
    'cosrad': math.cos,  # 弧度制余弦函数
    'tanrad': math.tan,  # 弧度制正切函数
    'deg2rad': math.radians,  # 角度转弧度
    'rad2deg': math.degrees,  # 弧度转角度
    'pi': math.pi,  # π常量
    'e': math.e,    # 自然常数e
    'sqrt': math.sqrt,  # 平方根
    'log': math.log10,  # 常用对数（底数10）
    'ln': math.log,     # 自然对数（底数e）
    'inf': math.inf,    # 无穷大
}

def safe_eval(expr):
    """
    安全表达式求值函数
    限制可执行的函数和操作符，防止代码注入风险
    返回表达式计算结果或None（计算失败时）
    """
    try:
        safe_namespace = {
            **SAFE_MATH,
            '__builtins__': None,  # 禁用内置函数
            'abs': abs,  # 绝对值函数
            '+': lambda x, y: x + y,  # 加法
            '-': lambda x, y: x - y,  # 减法
            '*': lambda x, y: x * y,  # 乘法
            '/': lambda x, y: x / y if y != 0 else 0,  # 除法（防止除零）
            '**': lambda x, y: x ** y,  # 幂运算
            '^': lambda x, y: x ** y,  # 幂运算（用^表示）
            '%': lambda x, y: x % y if y != 0 else 0,  # 取模（防止除零）
        }
        return eval(expr, {'__builtins__': {}}, safe_namespace)
    except Exception as e:
        messagebox.showerror("公式错误", f"表达式解析失败: {str(e)}")
        return None

def format_result(value):
    """
    智能格式化结果，最多保留两位小数，去掉多余的0
    例如：
    3.14159 → 3.14
    2.000 → 2
    5 → 5
    """
    if isinstance(value, (int, float)):
        # 将值四舍五入到两位小数
        rounded_value = round(float(value), 2)
        # 转换为字符串并去掉末尾的0和小数点
        s = "{:.2f}".format(rounded_value).rstrip('0').rstrip('.') if "." in "{:.2f}".format(rounded_value) else "{:.2f}".format(rounded_value)
        return s
    return str(value)


# 输入处理类
class InputHandler:
    def __init__(self, parent, default_params):
        self.parent = parent
        self.params = {param: tk.StringVar(value=value) for param, value in default_params.items()}
        self.raw_formulas = {param: "" for param in self.params}
        self.flags = {
            "atmospheric_loss": tk.BooleanVar(value=True),
            "scintillation_loss": tk.BooleanVar(value=True),
            "polarization_loss": tk.BooleanVar(value=True),
            "rain_rate": tk.BooleanVar(value=False),
            "beam_edge_loss": tk.BooleanVar(value=False),
            "scan_loss": tk.BooleanVar(value=False),
            "link_margin": tk.BooleanVar(value=True),
            "interference_psd": tk.BooleanVar(value=False),
        }
        self.defaults = {p: v.get() for p, v in self.params.items()}
        self.entries = {}

    def create_input_form(self, parent):
        title_label = ctk.CTkLabel(
            parent, text="输入参数 (支持公式如sin, cos, tan, log, 幂(^))",
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(pady=(5, 10))

        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollable_frame.grid_columnconfigure(0, weight=1)  # 添加列配置

        group_title_font = ("微软雅黑", 12, "bold")
        group_title_color = "#165DFF"

        # 第一组：频率和带宽
        self.create_group_title(scrollable_frame, "1. 信号参数", group_title_font, group_title_color)
        param_labels = [
            ("frequency", "频率 (GHz):"),
            ("bandwidth", "带宽 (MHz):"),
        ]
        self.create_param_entries(scrollable_frame, param_labels, compact=True)

        # 分隔线
        self.create_separator(scrollable_frame)

        # 第二组：卫星参数
        satellite_params = [
            ("satellite_height", "卫星高度 (km):"),
            ("satellite_scan_angle", "卫星扫描角 (°):")
        ]
        if 'satellite_antenna_gain' in self.params:
            satellite_params.extend([
                ("satellite_antenna_gain", "卫星天线增益 (dBi):"),
                ("satellite_noise_figure", "卫星噪声系数 (dB):"),
                ("satellite_noise_temp", "卫星天线噪声温度 (K):"),
            ])
        if 'satellite_eirp' in self.params:
            satellite_params.append(("satellite_eirp", "卫星EIRP (dBW):"))
        self.create_group_title(scrollable_frame, "2. 卫星参数", group_title_font, group_title_color)
        self.create_param_entries(scrollable_frame, satellite_params, compact=True)

        # 添加卫星G/T值显示框
        if 'satellite_antenna_gain' in self.params:
            self.gt_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            self.gt_frame.pack(fill=tk.X, padx=5, pady=(10, 5))

        # 分隔线
        self.create_separator(scrollable_frame)

        # 第三组：终端参数
        terminal_params = [
        ]
        if 'terminal_eirp' in self.params:
            terminal_params.append(("terminal_eirp", "终端EIRP (dBW):"))
        if 'terminal_noise_figure' in self.params:
            terminal_params.extend([
                ("terminal_noise_figure", "终端噪声系数 (dB):"),
                ("terminal_noise_temp", "终端天线噪声温度 (K):"),
                ("terminal_antenna_gain", "终端天线增益 (dBi):"),
            ])
        self.create_group_title(scrollable_frame, "3. 终端参数", group_title_font, group_title_color)
        self.create_param_entries(scrollable_frame, terminal_params, compact=True)

        # 添加终端G/T值显示框
        if 'terminal_antenna_gain' in self.params:
            self.gt_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            self.gt_frame.pack(fill=tk.X, padx=5, pady=(10, 5))

        # 分隔线
        self.create_separator(scrollable_frame)

        # 第四组：损耗参数
        self.create_group_title(scrollable_frame, "4. 损耗参数", group_title_font, group_title_color)
        param_labels = [
            ("atmospheric_loss", "大气损耗 (dB):"),
            ("scintillation_loss", "闪烁损耗 (dB):"),
            ("polarization_loss", "极化损耗 (dB):"),
            ("beam_edge_loss", "波束边缘损耗 (dB):"),
            ("scan_loss", "扫描损耗 (dB):"),
            ("rain_rate", "降雨率 (mm/h):"),
        ]
        self.create_param_entries(scrollable_frame, param_labels, compact=True, has_checkboxes=True)

        # 分隔线
        self.create_separator(scrollable_frame)

        # 第五组：链路余量
        self.create_group_title(scrollable_frame, "5. 链路余量", group_title_font, group_title_color)
        param_labels = [
            ("link_margin", "链路余量 (dB):"),
        ]
        self.create_param_entries(scrollable_frame, param_labels, compact=True, has_checkboxes=True)

        # 分隔线
        self.create_separator(scrollable_frame)

        # 第六组：干扰
        self.create_group_title(scrollable_frame, "6. 干扰", group_title_font, group_title_color)
        param_labels = [
            ("interference_psd", "干扰信号功率谱密度 (dBm/MHz):"),
        ]
        self.create_param_entries(scrollable_frame, param_labels, compact=True, has_checkboxes=True)

    def create_group_title(self, parent, title, font, color):
        title_label = ctk.CTkLabel(
            parent,  # 直接使用父容器
            text=title, 
            font=font,
            text_color=color,
            anchor="w"
        )
        title_label.pack(fill="x", pady=(5,3))

    def create_separator(self, parent):
        # 统一使用pack布局并优化显示效果
        separator = ctk.CTkFrame(
            parent,
            height=2,
            fg_color="#A0A0A0"
        )
        separator.pack(fill="x", padx=5, pady=3)

    def create_param_entries(self, parent, param_labels, compact=False, has_checkboxes=False):
        for i, label_info in enumerate(param_labels):
            param, label_text = label_info
            if has_checkboxes:
                self.create_param_entry_with_checkbox(parent, param, label_text, compact)
            else:
                self.create_param_entry(parent, param, label_text, compact)

    def create_param_entry(self, parent, param, label_text, compact=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=5, pady=(0, 2) if compact else 3)

        ctk.CTkLabel(frame, text=label_text, width=180 if compact else 200, anchor="w").pack(side=tk.LEFT, padx=5)

        entry = ctk.CTkEntry(frame, textvariable=self.params[param], width=120 if compact else 150)
        entry.pack(side=tk.RIGHT, padx=5)
        self.entries[param] = entry

        entry.bind("<FocusIn>", lambda event, p=param: self.on_entry_focus_in(event, p))
        entry.bind("<FocusOut>", lambda event, p=param: self.on_entry_focus_out(event, p))

    def create_param_entry_with_checkbox(self, parent, param, label_text, compact=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=5, pady=(0, 2) if compact else 3)

        flag_key = {
            "atmospheric_loss": "atmospheric_loss",
            "scintillation_loss": "scintillation_loss",
            "polarization_loss": "polarization_loss",
            "rain_rate": "rain_rate",
            "beam_edge_loss": "beam_edge_loss",
            "scan_loss": "scan_loss",
            "link_margin": "link_margin",
            "interference_psd": "interference_psd",
        }.get(param, None)

        if flag_key:
            flag_var = self.flags[flag_key]

            checkbutton = ctk.CTkCheckBox(
                frame, text="", variable=flag_var,
                command=lambda p=param, f=flag_var: self.toggle_entry_state(p, f),
                border_width=1, width=20
            )
            checkbutton.pack(side=tk.LEFT, padx=(5, 0))
        else:
            placeholder = ctk.CTkLabel(frame, text="", width=20)
            placeholder.pack(side=tk.LEFT, padx=(5, 0))

        ctk.CTkLabel(frame, text=label_text, width=160 if compact else 180, anchor="w").pack(side=tk.LEFT, padx=5)

        entry = ctk.CTkEntry(frame, textvariable=self.params[param], width=120 if compact else 150)
        entry.pack(side=tk.RIGHT, padx=5)
        self.entries[param] = entry

        entry.bind("<FocusIn>", lambda event, p=param: self.on_entry_focus_in(event, p))
        entry.bind("<FocusOut>", lambda event, p=param: self.on_entry_focus_out(event, p))

        if flag_key:
            entry.configure(state="normal" if flag_var.get() else "disabled")

    def on_entry_focus_in(self, event, param):
        if self.raw_formulas[param]:
            self.params[param].set(self.raw_formulas[param])

    def on_entry_focus_out(self, event, param):
        expr = self.params[param].get()
        self.raw_formulas[param] = expr
        try:
            result = safe_eval(expr)
            if result is not None:
                formatted_result = format_result(float(result))
                self.params[param].set(formatted_result)
        except Exception as e:
            pass

    def toggle_entry_state(self, param, flag_var):
        entry = self.entries[param]
        entry.configure(state="normal" if flag_var.get() else "disabled")

    def get_numeric_value(self, param):
        expr = self.params[param].get()
        try:
            return float(expr)
        except ValueError:
            result = safe_eval(expr)
            return float(result) if result is not None else 0

    def reset_params(self):
        for param, value in self.defaults.items():
            self.params[param].set(value)
            self.raw_formulas[param] = ""

        for flag_key, flag_var in self.flags.items():
            if flag_key == "link_margin":
                flag_var.set(True)
            else:
                flag_var.set(False)

        for param, flag_key in {
            "atmospheric_loss": "atmospheric_loss",
            "scintillation_loss": "scintillation_loss",
            "polarization_loss": "polarization_loss",
            "rain_rate": "rain_rate",
            "beam_edge_loss": "beam_edge_loss",
            "scan_loss": "scan_loss",
            "link_margin": "link_margin",
            "interference_psd": "interference_psd",
        }.items():
            if param in self.entries:
                self.entries[param].configure(
                    state="normal" if self.flags[flag_key].get() else "disabled"
                )

    def trigger_all_focus_out(self):
        for entry in self.entries.values():
            entry.event_generate("<FocusOut>")


# 结果显示类
class ResultDisplay:
    def __init__(self):
        self.result_frame = None
        self.result_labels = {}

    def create_result_display(self, parent):
        # 初始化滚动区域（只创建一次）
        self.result_scrollable_frame = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_hover_color="#E5E6EB",
            scrollbar_button_color="#F2F3F5"
        )
        self.result_scrollable_frame.pack(fill=tk.BOTH, expand=True)
        
        # 清空现有内容
        for widget in parent.winfo_children():
            widget.destroy()

        title_label = ctk.CTkLabel(
            parent, text="计算结果",
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(pady=(5, 10))

        # 创建结果显示区域
        self.result_scrollable_frame = ctk.CTkScrollableFrame(parent)
        self.result_scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)  # 增加左右边距

    def update_results(self, results, link_type):
        # 清空现有结果
        if not hasattr(self, 'result_container'):
            self.result_container = ctk.CTkFrame(self.result_scrollable_frame)
            self.result_container.pack(fill=tk.BOTH, expand=True)
        
        # 隐藏所有子元素
        for child in self.result_container.winfo_children():
            child.pack_forget()
    
        # 链路类型标签
        if not hasattr(self, 'link_type_label'):
            self.link_type_label = ctk.CTkLabel(
                self.result_container,
                font=("微软雅黑", 12, "bold"),
                anchor="w"
            )
        self.link_type_label.configure(text=f"链路类型: {link_type}")
        self.link_type_label.pack(pady=(5, 10), anchor="w")
    
        # 结果分类容器
        if not hasattr(self, 'category_frames'):
            self.category_frames = {}
        
        # 遍历每个结果分类
        for category_idx, (category, items) in enumerate(results.items()):
            # 复用或创建分类框架
            if category in self.category_frames:
                category_frame = self.category_frames[category]
            else:
                category_frame = ctk.CTkFrame(self.result_container, fg_color="transparent")
                self.category_frames[category] = category_frame
            
            # 分类标题
            if not hasattr(category_frame, 'title_label'):
                category_frame.title_label = ctk.CTkLabel(
                    category_frame,
                    font=("微软雅黑", 12, "bold"),
                    text_color="#165DFF",
                    anchor="w"
                )
                category_frame.title_label.pack(fill=tk.X, pady=(10,5))
            category_frame.title_label.configure(text=category)
            
            # 结果项容器
            if not hasattr(category_frame, 'item_frames'):
                category_frame.item_frames = []
            
            # 更新或创建结果项
            for item_idx, (label, value, unit) in enumerate(items):
                if item_idx < len(category_frame.item_frames):
                    item_frame = category_frame.item_frames[item_idx]
                else:
                    item_frame = ctk.CTkFrame(category_frame, fg_color="transparent")
                    item_frame.pack(fill=tk.X, pady=2)
                    ctk.CTkLabel(item_frame, width=200, anchor="w").pack(side=tk.LEFT, padx=10)
                    ctk.CTkLabel(item_frame, anchor="e").pack(side=tk.RIGHT, padx=10)
                    category_frame.item_frames.append(item_frame)
                
                # 更新标签内容
                item_labels = item_frame.winfo_children()
                item_labels[0].configure(text=label)
                item_labels[1].configure(text=f"{format_result(value)} {unit}")
            
            # 显示分类框架
            category_frame.pack(fill=tk.X, pady=5)
    
        # 强制刷新界面
        self.result_scrollable_frame._parent_canvas.yview_moveto(0)


# 主应用类
# 常量定义
DEFAULT_FONT = ("微软雅黑", 12)
TITLE_FONT = ("微软雅黑", 14, "bold")
GROUP_TITLE_FONT = ("微软雅黑", 12, "bold")
GROUP_TITLE_COLOR = "#165DFF"
STATUS_BAR_FONT = ("微软雅黑", 10)
STATUS_BAR_BG_COLOR = "#f0f0f0"
STATUS_BAR_TEXT_COLOR = "#333"

class SatelliteLinkBudgetCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("卫星链路预算计算器")
        self.root.geometry("1024x768")  # 设置默认窗口尺寸
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._create_link_type_selector()
        self._init_gt_labels()
        self._create_toolbar()
        self._create_content_frames()
        self._create_status_bar()
        self.change_link_type(self.link_type_var.get())

    def _create_link_type_selector(self):
        """创建链路类型选择器"""
        self.link_type_var = tk.StringVar(value="下行")
        link_type_label = ctk.CTkLabel(self.main_frame, text="选择链路类型:", font=DEFAULT_FONT)
        link_type_label.pack(pady=(5, 0))
        link_type_optionmenu = ctk.CTkOptionMenu(
            self.main_frame,
            variable=self.link_type_var,
            values=["下行", "上行"],
            command=self.change_link_type
        )
        link_type_optionmenu.pack(pady=(0, 5))

    def _init_gt_labels(self):
        """初始化G/T值显示框"""
        self.satellite_gt_label = None
        self.terminal_gt_label = None

    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ctk.CTkFrame(self.main_frame)
        self.toolbar.pack(fill=tk.X, pady=5)

        self._create_left_toolbar_buttons()
        self._create_right_toolbar_buttons()

    def _create_left_toolbar_buttons(self):
        """创建左侧工具栏按钮"""
        self.button_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.button_frame.pack(side=tk.LEFT, padx=5)

        buttons = [
            ("计算", self.calculate, "#165DFF", 100),
            ("重置", self.reset, "#6B7280", 100),
            ("输出计算报告", self.generate_report, "#36B37E", 120),
            ("详细计算公式", self.show_detailed_calculation, "#36B37E", 120),  # 新增按钮
        ]
        for text, command, color, width in buttons:
            button = ctk.CTkButton(
                self.button_frame, text=text, command=command,
                font=DEFAULT_FONT, fg_color=color, width=width
            )
            button.pack(side=tk.LEFT, padx=5)

    def _create_right_toolbar_buttons(self):
        """创建右侧工具栏按钮"""
        self.right_button_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.right_button_frame.pack(side=tk.RIGHT, padx=5)

        self.theme_switch = ctk.CTkSwitch(
            self.right_button_frame, text="深色模式", command=self.toggle_theme,
            font=STATUS_BAR_FONT
        )
        self.theme_switch.pack(side=tk.LEFT, padx=10)

    def _create_content_frames(self):
        """创建内容框架"""
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.input_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.result_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.result_display = ResultDisplay()
        self.result_display.create_result_display(self.result_frame)

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="支持公式化输入，例如：sin(30)、arctan(1)、53-10*log(16)")
        self.status_bar = ctk.CTkLabel(
            self.main_frame, textvariable=self.status_var,
            font=STATUS_BAR_FONT, fg_color=STATUS_BAR_BG_COLOR, text_color=STATUS_BAR_TEXT_COLOR
        )
        self.status_bar.pack(fill=tk.X, pady=5)

    def change_link_type(self, link_type):
        """切换链路类型"""
        self._clear_input_frame()
        params = self._get_link_params(link_type)
        self._setup_input_handler(params)
        self._setup_gt_display(link_type)

    def _clear_input_frame(self):
        """清除输入框"""
        for widget in self.input_frame.winfo_children():
            widget.destroy()

    def _get_link_params(self, link_type):
        """获取链路参数"""
        common_params = {
            "frequency": "1.71" if link_type == "上行" else "1.81",
            "bandwidth": "0.72" if link_type == "上行" else "5",
            "satellite_height": "400",
            "satellite_scan_angle": "0",
            "atmospheric_loss": "0.1",
            "scintillation_loss": "0.3",
            "polarization_loss": "3",
            "rain_rate": "50",
            "beam_edge_loss": "1",
            "scan_loss": "4",
            "link_margin": "3",
            "interference_psd": "-inf"
        }

        specific_params = {
            "上行": {
                "terminal_eirp": "23-30-5",
                "satellite_antenna_gain": "30.72",
                "satellite_noise_figure": "2.4",
                "satellite_noise_temp": "290",
            },
            "下行": {
                "satellite_eirp": "56",
                "terminal_noise_figure": "7",
                "terminal_noise_temp": "290",
                "terminal_antenna_gain": "-5",
            }
        }

        return {**common_params, **specific_params[link_type]}

    def _setup_input_handler(self, params):
        """设置输入处理器"""
        self.input_handler = InputHandler(self.input_frame, params)
        self.input_handler.create_input_form(self.input_frame)

    def _setup_gt_display(self, link_type):
        """设置G/T值显示框"""
        gt_frame = self.input_handler.gt_frame
        if link_type == "上行":
            self._create_gt_label(gt_frame, "卫星G/T值 (dB/K):", "satellite_gt_label")
            self.terminal_gt_label = None
        else:
            self._create_gt_label(gt_frame, "终端G/T值 (dB/K):", "terminal_gt_label")
            self.satellite_gt_label = None

    def _create_gt_label(self, parent, text, attr_name):
        """创建G/T值标签"""
        ctk.CTkLabel(parent, text=text, width=180, anchor="w").pack(side=tk.LEFT, padx=5)
        label = ctk.CTkLabel(parent, text="0.00", width=120, anchor="e")
        label.pack(side=tk.RIGHT, padx=5)
        setattr(self, attr_name, label)

    def _get_input_params(self):
        """获取输入参数"""
        self.input_handler.trigger_all_focus_out()

        # 获取公共输入参数
        input_params = {
            "frequency": self.input_handler.get_numeric_value("frequency"),  # GHz,
            "bandwidth": self.input_handler.get_numeric_value("bandwidth"),  # MHz,
            "satellite_scan_angle": self.input_handler.get_numeric_value("satellite_scan_angle"),  # 度,
            "satellite_height": self.input_handler.get_numeric_value("satellite_height"),  # km,
            
            "atmospheric_loss": self.input_handler.get_numeric_value("atmospheric_loss") if self.input_handler.flags["atmospheric_loss"].get() else 0,
            "scintillation_loss": self.input_handler.get_numeric_value("scintillation_loss") if self.input_handler.flags["scintillation_loss"].get() else 0,
            "polarization_loss": self.input_handler.get_numeric_value("polarization_loss") if self.input_handler.flags["polarization_loss"].get() else 0,
            
            "rain_rate": self.input_handler.get_numeric_value("rain_rate") if self.input_handler.flags["rain_rate"].get() else 0,
            "link_margin": self.input_handler.get_numeric_value("link_margin") if self.input_handler.flags["link_margin"].get() else 0,
            "beam_edge_loss": self.input_handler.get_numeric_value("beam_edge_loss") if self.input_handler.flags["beam_edge_loss"].get() else 0,
            "scan_loss": self.input_handler.get_numeric_value("scan_loss") if self.input_handler.flags["scan_loss"].get() else 0,
        
            "interference_psd": self.input_handler.get_numeric_value("interference_psd") if self.input_handler.flags["interference_psd"].get() else -math.inf,  # 新增干扰参数
        }

        # 获取收发端参数
        if self.link_type_var.get() == "上行": # 上行链路
            # 发端参数：终端
            input_params["tx_eirp"] = self.input_handler.get_numeric_value("terminal_eirp")  # dBW
            # 收端参数：卫星
            input_params["rx_antenna_gain"] = self.input_handler.get_numeric_value("satellite_antenna_gain")  # dBi
            input_params["rx_noise_temp"] = self.input_handler.get_numeric_value("satellite_noise_temp")
            input_params["rx_noise_figure"] = self.input_handler.get_numeric_value("satellite_noise_figure")
        else: # 下行链路
            # 发端参数：卫星
            input_params["tx_eirp"] = self.input_handler.get_numeric_value("satellite_eirp")  # dBW
            # 收端参数：终端
            input_params["rx_antenna_gain"] = self.input_handler.get_numeric_value("terminal_antenna_gain")  # dBi
            input_params["rx_noise_temp"] = self.input_handler.get_numeric_value("terminal_noise_temp")
            input_params["rx_noise_figure"] = self.input_handler.get_numeric_value("terminal_noise_figure")

        return input_params

    def calculate(self):
        try:
            self.status_var.set("正在计算...")
            self.input_handler.trigger_all_focus_out()

            # 获取公共输入参数
            input_params = {
                "frequency": self.input_handler.get_numeric_value("frequency"),  # GHz,
                "bandwidth": self.input_handler.get_numeric_value("bandwidth"),  # MHz,
                "satellite_scan_angle": self.input_handler.get_numeric_value("satellite_scan_angle"),  # 度,
                "satellite_height": self.input_handler.get_numeric_value("satellite_height"),  # km,
                
                "atmospheric_loss": self.input_handler.get_numeric_value("atmospheric_loss") if self.input_handler.flags["atmospheric_loss"].get() else 0,
                "scintillation_loss": self.input_handler.get_numeric_value("scintillation_loss") if self.input_handler.flags["scintillation_loss"].get() else 0,
                "polarization_loss": self.input_handler.get_numeric_value("polarization_loss") if self.input_handler.flags["polarization_loss"].get() else 0,
                
                "rain_rate": self.input_handler.get_numeric_value("rain_rate") if self.input_handler.flags["rain_rate"].get() else 0,
                "link_margin": self.input_handler.get_numeric_value("link_margin") if self.input_handler.flags["link_margin"].get() else 0,
                "beam_edge_loss": self.input_handler.get_numeric_value("beam_edge_loss") if self.input_handler.flags["beam_edge_loss"].get() else 0,
                "scan_loss": self.input_handler.get_numeric_value("scan_loss") if self.input_handler.flags["scan_loss"].get() else 0,
            
                "interference_psd": self.input_handler.get_numeric_value("interference_psd") if self.input_handler.flags["interference_psd"].get() else -math.inf,  # 新增干扰参数
            }

            # 获取收发端参数
            if self.link_type_var.get() == "上行": # 上行链路
                # 发端参数：终端
                input_params["tx_eirp"] = self.input_handler.get_numeric_value("terminal_eirp")  # dBW
                # 收端参数：卫星
                input_params["rx_antenna_gain"] = self.input_handler.get_numeric_value("satellite_antenna_gain")  # dBi
                input_params["rx_noise_temp"] = self.input_handler.get_numeric_value("satellite_noise_temp")
                input_params["rx_noise_figure"] = self.input_handler.get_numeric_value("satellite_noise_figure")
            else: # 下行链路
                # 发端参数：卫星
                input_params["tx_eirp"] = self.input_handler.get_numeric_value("satellite_eirp")  # dBW
                # 收端参数：终端
                input_params["rx_antenna_gain"] = self.input_handler.get_numeric_value("terminal_antenna_gain")  # dBi
                input_params["rx_noise_temp"] = self.input_handler.get_numeric_value("terminal_noise_temp")
                input_params["rx_noise_figure"] = self.input_handler.get_numeric_value("terminal_noise_figure")

            # 执行计算 
            calculator = LinkCalculator()
            self.results_temp = calculator.perform_calculations(input_params)  # 将结果保存为类属性

            results = {
                "链路状态": [
                    ("（位于波束中心的）终端仰角", self.results_temp["terminal_elevation_angle"], "°"),  # 终端仰角作为输出参数
                    ("星地距离", self.results_temp["distance"], "km"),
                    ("路径损耗", self.results_temp["path_loss"], "dB"),
                    ("雨衰", self.results_temp["rain_fade"], "dB"),
                ],
                "链路性能": [
                    ("接收信号功率谱密度", self.results_temp["received_signal_psd"], "dBm/MHz"),
                    ("噪声功率谱密度", self.results_temp["noise_psd"], "dBm/MHz"),
                    ("C/N", self.results_temp["c_to_n"], "dB"),
                    ("C/(N+I)", self.results_temp["c_to_n_plus_i"], "dB"),  # 新增C/(N+I)
                ],
            }

            # 更新G/T值显示框
            if self.link_type_var.get() == "上行" and self.satellite_gt_label is not None:
                self.satellite_gt_label.configure(text=format_result(self.results_temp["gt_ratio"]))
            elif self.link_type_var.get() == "下行" and self.terminal_gt_label is not None:
                self.terminal_gt_label.configure(text=format_result(self.results_temp["gt_ratio"]))

            if self.link_type_var.get() == "上行": # 上行链路
                results["链路性能"].append(("卫星G/T值", self.results_temp["gt_ratio"], "dB/K"))
            else: # 下行链路
                results["链路性能"].append(("终端G/T值", self.results_temp["gt_ratio"], "dB/K"))

            self.result_display.update_results(results, self.link_type_var.get())
            self.status_var.set("计算完成")
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出现错误: {str(e)}")
            self.status_var.set("计算失败，请检查输入")


    def reset(self):
        self.input_handler.reset_params()
        self.status_var.set("支持公式化输入，例如：sin(30)、arctan(1)、53-10*log(16)")

    def generate_report(self):
        try:
            # 获取当前时间作为文件名的一部分
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 弹出文件保存对话框，让用户选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel 文件", "*.xlsx")],
                initialfile=f"卫星链路预算仿真报告_{timestamp}.xlsx"
            )
            if not file_path:  # 如果用户取消选择，直接返回
                return

            # 创建一个新的 Excel 工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "仿真报告"

            # 设置表格样式
            header_font = Font(name='微软雅黑', size=12, bold=True)
            data_font = Font(name='微软雅黑', size=11)
            border = Border(left=Side(style='thin'), 
                         right=Side(style='thin'), 
                         top=Side(style='thin'), 
                         bottom=Side(style='thin'))
            alignment = Alignment(horizontal='center', vertical='center')

            # 定义参数标签
            param_labels = {
                "frequency": ("频率", "GHz"),
                "bandwidth": ("带宽", "MHz"),
                "satellite_height": ("卫星高度", "km"),
                "satellite_scan_angle": ("卫星扫描角", "°"),
                "terminal_eirp": ("终端EIRP", "dBW"),
                "satellite_antenna_gain": ("卫星天线增益", "dBi"),
                "satellite_noise_figure": ("卫星噪声系数", "dB"),
                "satellite_noise_temp": ("卫星天线噪声温度", "K"),
                "satellite_eirp": ("卫星EIRP", "dBW"),
                "terminal_noise_figure": ("终端噪声系数", "dB"),
                "terminal_noise_temp": ("终端天线噪声温度", "K"),
                "terminal_antenna_gain": ("终端天线增益", "dBi"),
                "atmospheric_loss": ("大气损耗", "dB"),
                "scintillation_loss": ("闪烁损耗", "dB"),
                "polarization_loss": ("极化损耗", "dB"),
                "beam_edge_loss": ("波束边缘损耗", "dB"),
                "scan_loss": ("扫描损耗", "dB"),
                "rain_rate": ("降雨率", "mm/h"),
                "link_margin": ("链路余量", "dB"),
                "interference_psd": ("干扰信号功率谱密度", "dBm/MHz")
            }

            # 写入报告标题
            ws.merge_cells('A1:C1')
            title_cell = ws['A1']
            title_cell.value = "卫星链路预算仿真报告"
            title_cell.font = Font(name='微软雅黑', size=14, bold=True)
            title_cell.alignment = alignment
            title_cell.border = border

            ws.append([])  # 空行

            # 写入输入参数
            ws.append(["输入参数", "单位", "值"])
            ws['A'+str(ws.max_row)].font = header_font
            ws['B'+str(ws.max_row)].font = header_font
            ws['C'+str(ws.max_row)].font = header_font

            # 写入输入参数并应用样式
            for param, (label, unit) in param_labels.items():
                if param in self.input_handler.params:
                    flag_key = {
                        "atmospheric_loss": "atmospheric_loss",
                        "scintillation_loss": "scintillation_loss",
                        "polarization_loss": "polarization_loss",
                        "rain_rate": "rain_rate",
                        "beam_edge_loss": "beam_edge_loss",
                        "scan_loss": "scan_loss",
                        "link_margin": "link_margin",
                        "interference_psd": "interference_psd"
                    }.get(param, None)

                    # 如果参数没有标志位，或者标志位为 True，则显示
                    if not flag_key or self.input_handler.flags[flag_key].get():
                        value = self.input_handler.params[param].get()
                        try:
                            numeric_value = float(safe_eval(value)) if value else 0
                            ws.append([label, unit, numeric_value])
                        except:
                            ws.append([label, unit, 0])

            # 设置列宽
            ws.column_dimensions['A'].width = 30
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 20

            # 写入计算结果
            if hasattr(self, "results_temp"):
                ws.append([])  # 空行
                ws.append(["计算结果", "单位", "值"])
                ws['A'+str(ws.max_row)].font = header_font
                ws['B'+str(ws.max_row)].font = header_font
                ws['C'+str(ws.max_row)].font = header_font

                # 定义结果项与results_temp中键的映射关系
                result_mapping = {
                    "（位于波束中心的）终端仰角": "terminal_elevation_angle",
                    "星地距离": "distance",
                    "路径损耗": "path_loss",
                    "雨衰": "rain_fade",
                    "接收信号功率谱密度": "received_signal_psd",
                    "噪声功率谱密度": "noise_psd",
                    "C/N": "c_to_n",
                    "C/(N+I)": "c_to_n_plus_i",
                    "卫星G/T值": "gt_ratio",
                    "终端G/T值": "gt_ratio"
                }

                # 定义结果项
                result_items = [
                    ("（位于波束中心的）终端仰角", "度"),
                    ("星地距离", "km"),
                    ("路径损耗", "dB"),
                    ("雨衰", "dB"),
                    ("接收信号功率谱密度", "dBm/MHz"),
                    ("噪声功率谱密度", "dBm/MHz"),
                    ("C/N", "dB"),
                    ("C/(N+I)", "dB"),
                ]

                # 根据链路类型添加G/T值
                if self.link_type_var.get() == "上行":
                    result_items.append(("卫星G/T值", "dB/K"))
                else:
                    result_items.append(("终端G/T值", "dB/K"))

                # 写入结果并应用样式
                for label, unit in result_items:
                    # 通过映射关系获取正确的键
                    key = result_mapping[label]
                    # 确保获取的值是数值类型
                    try:
                        value = float(self.results_temp[key])
                        ws.append([label, unit, value])
                    except:
                        ws.append([label, unit, 0])

            # 应用边框样式到所有单元格
            for row in ws.iter_rows():
                for cell in row:
                    cell.border = border

            # 保存 Excel 文件
            wb.save(file_path)
            messagebox.showinfo("报告生成成功", f"仿真报告已保存至:\n{file_path}")
        except Exception as e:
            messagebox.showerror("报告生成失败", f"生成仿真报告时出错:\n{str(e)}")

    def show_detailed_calculation(self):
        """显示详细计算步骤"""
        try:
            # 获取输入参数
            input_params = self._get_input_params()
            # 调用详细计算方法
            calculator = LinkCalculator()
            details = calculator.detailed_calculation(input_params)
            
            # 创建新窗口显示结果
            detail_window = ctk.CTkToplevel(self.root)
            detail_window.title("详细计算步骤")
            detail_window.geometry("800x600")

            # 将新窗口设置为主窗口的子窗口
            detail_window.transient(self.root)
            # 将新窗口提升到最前面
            detail_window.lift()

            # 创建文本框显示详细步骤
            text_box = ctk.CTkTextbox(detail_window, wrap="word")
            text_box.pack(fill="both", expand=True, padx=10, pady=10)
            
            # 格式化输出
            for detail in details:
                text_box.insert("end", f"步骤: {detail['步骤']}\n")
                text_box.insert("end", f"公式: {detail['公式']}\n")
                text_box.insert("end", f"参数: {detail['参数']}\n")
                text_box.insert("end", f"结果: {detail['结果']}\n\n")
                
        except Exception as e:
            messagebox.showerror("错误", f"无法显示详细计算步骤: {str(e)}")

    def toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme_switch.get() else "light")


if __name__ == "__main__":
    root = ctk.CTk()
    app = SatelliteLinkBudgetCalculator(root)
    root.mainloop()
