"""
打包命令：pyinstaller --onedir --windowed  --hidden-import customtkinter  --hidden-import openpyxl --collect-all customtkinter  "D:\PySimpleGUI.py"
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import pandas as pd
from datetime import datetime
import os

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
        s = f"{value:.2f}"
        if '.' in s:
            s = s.rstrip('0').rstrip('.') if '.' in s else s
        return s
    return str(value)

class SatelliteLinkCalculator:
    """主应用类 - 管理整个应用的结构和流程"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("卫星链路参数计算器 (支持公式版)")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # 设置主题
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # 初始化三大核心模块
        self.input_handler = InputHandler(self)  # 输入处理模块
        self.calculator = Calculator(self)  # 计算模块
        self.result_display = ResultDisplay(self)  # 结果显示模块
        
        # 创建用户界面
        self.create_widgets()

    def create_widgets(self):
        """创建应用的整体界面布局"""
        # 主框架 - 使用 pack 布局管理器
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建顶部工具栏
        self.create_toolbar()
        
        # 中间内容区域 - 分为左右两部分
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 左侧输入区域（参数设置）
        self.input_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 右侧结果区域（计算结果显示）
        self.result_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 创建输入表单
        self.input_handler.create_input_form(self.input_frame)
        
        # 创建结果显示区域
        self.result_display.create_result_display(self.result_frame)
        
        # 状态栏 - 显示操作提示和状态信息
        self.status_var = tk.StringVar(value="支持公式化输入，例如：sin(30)、arctan(1)、53-10*log(16)")
        self.status_bar = ctk.CTkLabel(
            self.main_frame, textvariable=self.status_var,
            font=("微软雅黑", 10), fg_color="#f0f0f0", text_color="#333"
        )
        self.status_bar.pack(fill=tk.X, pady=5)

    def create_toolbar(self):
        """创建顶部工具栏，包含常用操作按钮"""
        self.toolbar = ctk.CTkFrame(self.main_frame)
        self.toolbar.pack(fill=tk.X, pady=5)
        
        # 左侧按钮组
        self.button_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.button_frame.pack(side=tk.LEFT, padx=5)
        
        self.calculate_button = ctk.CTkButton(
            self.button_frame, text="计算", command=self.calculate,
            font=("微软雅黑", 12), fg_color="#165DFF", width=100
        )
        self.calculate_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ctk.CTkButton(
            self.button_frame, text="重置", command=self.reset,
            font=("微软雅黑", 12), fg_color="#6B7280", width=100
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.report_button = ctk.CTkButton(
            self.button_frame, text="输出仿真报告", command=self.generate_report,
            font=("微软雅黑", 12), fg_color="#36B37E", width=120
        )
        self.report_button.pack(side=tk.LEFT, padx=5)
        
        # 右侧按钮组 - 仅保留主题切换
        self.right_button_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.right_button_frame.pack(side=tk.RIGHT, padx=5)
        
        self.theme_switch = ctk.CTkSwitch(
            self.right_button_frame, text="深色模式", command=self.toggle_theme,
            font=("微软雅黑", 10)
        )
        self.theme_switch.pack(side=tk.LEFT, padx=10)

    def calculate(self):
        """执行计算流程"""
        try:
            self.status_var.set("正在解析公式并计算...")
            # 触发所有输入框失去焦点，计算并显示公式结果
            self.input_handler.trigger_all_focus_out()
            # 执行核心计算逻辑
            self.calculator.perform_calculations()
            self.status_var.set("计算完成！")
        except Exception as e:
            self.status_var.set(f"计算错误: {str(e)}")

    def reset(self):
        """重置所有参数为默认值"""
        self.input_handler.reset_params()
        self.result_display.reset_results()
        self.status_var.set("参数已重置")

    def toggle_theme(self):
        """切换深色/浅色模式"""
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def generate_report(self):
        """生成仿真报告并导出为Excel文件"""
        try:
            self.status_var.set("正在生成仿真报告...")
            
            # 生成默认文件名（包含时间戳）
            now = datetime.now()
            default_filename = f"卫星链路仿真报告_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # 打开文件保存对话框
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                initialfile=default_filename
            )
            
            if not filename:  # 用户点击取消
                self.status_var.set("生成报告已取消")
                return
                
            # 收集输入数据（只包含启用的参数，确保为数字类型）
            input_data = []
            
            # 基础参数（无启用选项）
            base_params = [
                "frequency", "bandwidth", "satellite_height", 
                "terminal_elevation_angle", "terminal_noise_figure",
                "terminal_noise_temp", "terminal_antenna_gain",
            ]
            
            for param in base_params:
                display_name = self.get_display_name(param)
                # 使用get_numeric_value确保获取数字值
                value = self.input_handler.get_numeric_value(param)
                input_data.append((display_name, value))
            
            # 可选参数（根据启用状态决定是否添加）
            optional_params = [
                ("atmospheric_loss", "atmospheric_loss"),
                ("scintillation_loss", "scintillation_loss"),
                ("polarization_loss", "polarization_loss"),
                ("rain_rate", "rain_fade"),
                ("beam_edge_loss", "beam_edge_loss"),
                ("scan_loss", "scan_loss"),
                ("link_margin", "link_margin"),
            ]
            
            for param, flag_key in optional_params:
                if self.input_handler.flags[flag_key].get():
                    display_name = self.get_display_name(param)
                    # 使用get_numeric_value确保获取数字值
                    value = self.input_handler.get_numeric_value(param)
                    input_data.append((display_name, value))
            
            # 收集计算结果（确保为数字类型）
            result_data = []
            for var_name, var in self.calculator.results.items():
                display_name = self.get_result_display_name(var_name)
                # 直接从DoubleVar获取数值
                value = var.get()
                result_data.append((display_name, value))
            
            # 创建ExcelWriter对象
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 创建单个工作表
                sheet_name = "卫星链路计算报告"
                
                # 写入标题
                title_df = pd.DataFrame({"标题": ["卫星链路参数计算报告"]})
                title_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                
                # 写入时间戳
                timestamp_df = pd.DataFrame({"时间": [now.strftime("%Y-%m-%d %H:%M:%S")]})
                timestamp_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=2)
                
                # 写入输入参数（从第4行开始）
                input_df = pd.DataFrame(input_data, columns=['参数', '值'])
                input_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=4)
                
                # 写入计算结果（在参数下方空两行）
                result_start_row = 6 + len(input_data)
                result_df = pd.DataFrame(result_data, columns=['结果', '值'])
                result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=result_start_row)
                
                # 获取工作表对象
                ws = writer.sheets[sheet_name]
                
                # 设置标题样式
                title_cell = ws['A1']
                title_cell.font = title_cell.font.copy(bold=True, size=16)
                
                # 设置列宽
                ws.column_dimensions['A'].width = 30
                ws.column_dimensions['B'].width = 20
                
                # 设置标题和分隔行的合并单元格
                ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)
                ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=2)
                ws.merge_cells(start_row=result_start_row-1, start_column=1, end_row=result_start_row-1, end_column=2)
                
                # 在结果上方添加"计算结果"标题
                ws.cell(row=result_start_row-1, column=1, value="计算结果")
                ws.cell(row=result_start_row-1, column=1).font = ws.cell(row=result_start_row-1, column=1).font.copy(bold=True)
                
                # 为数值列设置数字格式（可选）
                for row in range(5, 5 + len(input_data)):
                    ws[f'B{row}'].number_format = '0.00'
                for row in range(result_start_row + 1, result_start_row + 1 + len(result_data)):
                    ws[f'B{row}'].number_format = '0.00'
            
            # 提示用户
            messagebox.showinfo("成功", f"仿真报告已保存至：\n{os.path.abspath(filename)}")
            self.status_var.set("仿真报告生成完成")
            
        except Exception as e:
            self.status_var.set(f"生成报告失败: {str(e)}")
            messagebox.showerror("错误", f"生成报告失败: {str(e)}")

    def get_input_data(self):
        """获取所有输入参数数据，用于报告生成"""
        input_data = {}
        
        # 获取所有输入参数
        for param, var in self.input_handler.params.items():
            # 获取参数的显示名称
            display_name = self.get_display_name(param)
            input_data[display_name] = var.get()
            
            # 添加是否启用的信息（如果适用）
            if param in ['atmospheric_loss', 'scintillation_loss', 'polarization_loss', 'rain_rate', 'beam_edge_loss', 'scan_loss', 'link_margin']:
                flag_key = {
                    'atmospheric_loss': 'atmospheric_loss',
                    'scintillation_loss': 'scintillation_loss',
                    'polarization_loss': 'polarization_loss',
                    'rain_rate': 'rain_fade',
                    'beam_edge_loss': 'beam_edge_loss',
                    'scan_loss': 'scan_loss',
                    'link_margin': 'link_margin',
                }[param]
                enabled = self.input_handler.flags[flag_key].get()
                input_data[f"{display_name} (启用)"] = "是" if enabled else "否"
        
        return input_data

    def get_display_name(self, param):
        """获取参数的显示名称（带单位）"""
        display_names = {
            "frequency": "频率 (GHz)",
            "bandwidth": "带宽 (MHz)",
            "satellite_height": "卫星高度 (km)",
            "satellite_eirp": "卫星EIRP (dBW)",
            "terminal_elevation_angle": "终端仰角 (度)",
            "terminal_noise_figure": "终端噪声系数 (dB)",
            "terminal_noise_temp": "终端噪声温度 (K)",
            "terminal_antenna_gain": "终端天线增益 (dBi)",
            "atmospheric_loss": "大气损耗 (dB)",
            "scintillation_loss": "闪烁损耗 (dB)",
            "polarization_loss": "极化损耗 (dB)",
            "rain_rate": "降雨率 (mm/h)",
            "beam_edge_loss": "波束边缘损耗 (dB)",
            "scan_loss": "扫描损耗 (dB)",
            "link_margin": "链路余量 (dB)",
        }
        return display_names.get(param, param)

    def get_result_data(self):
        """获取所有计算结果数据，用于报告生成"""
        result_data = {}
        
        # 获取所有计算结果
        for var_name, var in self.calculator.results.items():
            # 获取结果的显示名称
            display_name = self.get_result_display_name(var_name)
            result_data[display_name] = var.get()
        
        return result_data

    def get_result_display_name(self, var_name):
        """获取结果的显示名称（带单位）"""
        display_names = {
            "scan_angle": "卫星扫描角 (度)",
            "distance": "星地距离 (km)",
            "path_loss": "路径损耗 (dB)",
            "rain_fade": "雨衰 (dB)",
            "received_signal_psd": "接收信号功率谱密度 (dBm/MHz)",
            "noise_psd": "噪声功率谱密度 (dBm/MHz)",
            "c_to_n": "C/N (dB)",
            "total_received_power": "总接收功率 (dBm)",
            "gt_ratio": "终端G/T值 (dB/K)",
        }
        return display_names.get(var_name, var_name)

class InputHandler:
    """输入处理模块 - 负责管理用户输入和参数设置"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # 定义所有输入参数及其默认值
        self.params = {
            "frequency": tk.StringVar(value="1.81"),  # 频率 (GHz)
            "bandwidth": tk.StringVar(value="5"),  # 带宽 (MHz)
            "satellite_height": tk.StringVar(value="400"),  # 卫星高度 (km)
            "satellite_eirp": tk.StringVar(value="56"),  # 卫星EIRP (dBW)
            "terminal_elevation_angle": tk.StringVar(value="90"),  # 终端仰角 (度)
            "terminal_noise_figure": tk.StringVar(value="7"),  # 终端噪声系数 (dB)
            "terminal_noise_temp": tk.StringVar(value="290"),  # 终端噪声温度 (K)
            "terminal_antenna_gain": tk.StringVar(value="-5"),  # 终端天线增益 (dBi)
            "atmospheric_loss": tk.StringVar(value="0.1"),  # 大气损耗 (dB)
            "scintillation_loss": tk.StringVar(value="0.3"),  # 闪烁损耗 (dB)
            "polarization_loss": tk.StringVar(value="3"),  # 极化损耗 (dB)
            "rain_rate": tk.StringVar(value="50"),  # 降雨率 (mm/h)
            "beam_edge_loss": tk.StringVar(value="1"),  # 波束边缘损耗 (dB)
            "scan_loss": tk.StringVar(value="4"),  # 扫描损耗 (dB)
            "link_margin": tk.StringVar(value="3"),  # 链路余量 (dB)
        }
        
        # 存储原始公式的变量（用于在编辑时恢复）
        self.raw_formulas = {param: "" for param in self.params}
        
        # 定义可切换的参数标志
        self.flags = {
            "atmospheric_loss": tk.BooleanVar(value=True),  # 大气损耗
            "scintillation_loss": tk.BooleanVar(value=True),  # 闪烁损耗
            "polarization_loss": tk.BooleanVar(value=True),  # 极化损耗
            "rain_fade": tk.BooleanVar(value=False),  # 雨衰
            "beam_edge_loss": tk.BooleanVar(value=False),  # 波束边缘损耗
            "scan_loss": tk.BooleanVar(value=False),  # 扫描损耗
            "link_margin": tk.BooleanVar(value=True),  # 链路余量（默认开启）
        }
        
        # 保存默认值用于重置
        self.defaults = {p: v.get() for p, v in self.params.items()}
        
        # 存储输入框引用
        self.entries = {}

    def create_input_form(self, parent):
        """创建输入表单界面，分组展示不同类型的参数"""
        # 标题
        title_label = ctk.CTkLabel(
            parent, text="输入参数 (支持公式如sin, cos, tan, log, 幂(^))",
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(pady=(5, 10))
        
        # 滚动区域 - 当参数较多时支持滚动
        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分组标题样式
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
        self.create_group_title(scrollable_frame, "2. 卫星参数", group_title_font, group_title_color)
        param_labels = [
            ("satellite_height", "卫星高度 (km):"),
            ("satellite_eirp", "卫星EIRP (dBW):"),
        ]
        self.create_param_entries(scrollable_frame, param_labels, compact=True)
        
        # 分隔线
        self.create_separator(scrollable_frame)
        
        # 第三组：终端参数
        self.create_group_title(scrollable_frame, "3. 终端参数", group_title_font, group_title_color)
        param_labels = [
            ("terminal_elevation_angle", "终端仰角 (度):"),
            ("terminal_noise_figure", "终端噪声系数 (dB):"),
            ("terminal_noise_temp", "终端噪声温度 (K):"),
            ("terminal_antenna_gain", "终端天线增益 (dBi):"),
        ]
        self.create_param_entries(scrollable_frame, param_labels, compact=True)
        
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

    def create_group_title(self, parent, title, font, color):
        """创建分组标题"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=5, pady=(5, 3))
        
        title_label = ctk.CTkLabel(frame, text=title, font=font, text_color=color)
        title_label.pack(anchor="w", padx=5)

    def create_separator(self, parent):
        """创建分隔线，用于视觉分组"""
        separator = ctk.CTkFrame(parent, height=1, fg_color="#e0e0e0")
        separator.pack(fill=tk.X, padx=5, pady=3)

    def create_param_entries(self, parent, param_labels, compact=False, has_checkboxes=False):
        """创建参数输入框组，支持带复选框的参数和紧凑布局"""
        for i, label_info in enumerate(param_labels):
            param, label_text = label_info
            if has_checkboxes:
                # 为每个参数创建一个复选框和输入框
                self.create_param_entry_with_checkbox(parent, param, label_text, compact)
            else:
                # 创建普通参数输入框
                self.create_param_entry(parent, param, label_text, compact)

    def create_param_entry(self, parent, param, label_text, compact=False):
        """创建普通参数输入框"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=5, pady=(0, 2) if compact else 3)
        
        ctk.CTkLabel(frame, text=label_text, width=180 if compact else 200, anchor="w").pack(side=tk.LEFT, padx=5)
        
        entry = ctk.CTkEntry(frame, textvariable=self.params[param], width=120 if compact else 150)
        entry.pack(side=tk.RIGHT, padx=5)
        self.entries[param] = entry
        
        # 添加焦点事件处理
        entry.bind("<FocusIn>", lambda event, p=param: self.on_entry_focus_in(event, p))
        entry.bind("<FocusOut>", lambda event, p=param: self.on_entry_focus_out(event, p))

    def create_param_entry_with_checkbox(self, parent, param, label_text, compact=False):
        """创建带复选框的参数输入框，用于可选参数"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.X, padx=5, pady=(0, 2) if compact else 3)
        
        # 确定对应的标志键
        flag_key = {
            "atmospheric_loss": "atmospheric_loss",
            "scintillation_loss": "scintillation_loss",
            "polarization_loss": "polarization_loss",
            "rain_rate": "rain_fade",
            "beam_edge_loss": "beam_edge_loss",
            "scan_loss": "scan_loss",
            "link_margin": "link_margin",
        }.get(param, None)
        
        # 只对有标志的参数创建复选框
        if flag_key:
            flag_var = self.flags[flag_key]
            
            # 创建复选框（无边框，无文本）
            checkbutton = ctk.CTkCheckBox(
                frame, text="", variable=flag_var,
                command=lambda p=param, f=flag_var: self.toggle_entry_state(p, f),
                border_width=1, width=20
            )
            checkbutton.pack(side=tk.LEFT, padx=(5, 0))
        else:
            # 对于没有标志的参数，创建一个空的占位符
            placeholder = ctk.CTkLabel(frame, text="", width=20)
            placeholder.pack(side=tk.LEFT, padx=(5, 0))
        
        ctk.CTkLabel(frame, text=label_text, width=160 if compact else 180, anchor="w").pack(side=tk.LEFT, padx=5)
        
        entry = ctk.CTkEntry(frame, textvariable=self.params[param], width=120 if compact else 150)
        entry.pack(side=tk.RIGHT, padx=5)
        self.entries[param] = entry
        
        # 添加焦点事件处理
        entry.bind("<FocusIn>", lambda event, p=param: self.on_entry_focus_in(event, p))
        entry.bind("<FocusOut>", lambda event, p=param: self.on_entry_focus_out(event, p))
        
        # 初始状态设置 - 只对有标志的参数应用
        if flag_key:
            entry.configure(state="normal" if flag_var.get() else "disabled")

    def on_entry_focus_in(self, event, param):
        """输入框获得焦点时，恢复原始公式以便编辑"""
        # 如果当前显示的是计算结果，则恢复原始公式
        if self.raw_formulas[param]:
            self.params[param].set(self.raw_formulas[param])

    def on_entry_focus_out(self, event, param):
        """输入框失去焦点时，计算并显示结果"""
        expr = self.params[param].get()
        
        # 保存原始公式
        self.raw_formulas[param] = expr
        
        # 计算结果
        try:
            result = safe_eval(expr)
            if result is not None:
                # 使用智能格式化
                formatted_result = format_result(float(result))
                self.params[param].set(formatted_result)
        except Exception as e:
            # 如果计算失败，保持原样
            pass

    def toggle_entry_state(self, param, flag_var):
        """根据复选框状态启用/禁用输入框"""
        entry = self.entries[param]
        entry.configure(state="normal" if flag_var.get() else "disabled")

    def get_numeric_value(self, param):
        """将公式转换为数值，确保返回数字类型"""
        expr = self.params[param].get()
        try:
            return float(expr)
        except ValueError:
            result = safe_eval(expr)
            return float(result) if result is not None else 0

    def reset_params(self):
        """重置所有参数为默认值"""
        for param, value in self.defaults.items():
            self.params[param].set(value)
            self.raw_formulas[param] = ""  # 清空原始公式
        
        # 重置标志状态（链路余量默认开启）
        for flag_key, flag_var in self.flags.items():
            if flag_key == "link_margin":
                flag_var.set(True)  # 链路余量默认开启
            else:
                flag_var.set(False)  # 其他参数默认关闭
        
        # 更新输入框状态
        for param, flag_key in {
            "atmospheric_loss": "atmospheric_loss",
            "scintillation_loss": "scintillation_loss",
            "polarization_loss": "polarization_loss",
            "rain_rate": "rain_fade",
            "beam_edge_loss": "beam_edge_loss",
            "scan_loss": "scan_loss",
            "link_margin": "link_margin",
        }.items():
            if param in self.entries:
                self.entries[param].configure(
                    state="normal" if self.flags[flag_key].get() else "disabled"
                )

    def trigger_all_focus_out(self):
        """触发所有输入框的焦点离开事件，强制更新所有公式计算结果"""
        for entry in self.entries.values():
            # 模拟焦点离开事件
            entry.event_generate("<FocusOut>")


class Calculator:
    """计算模块 - 负责执行卫星链路参数的所有计算逻辑"""
    
    def __init__(self, parent):
        self.parent = parent
        self.earth_radius = 6371  # 地球半径 (km)
        
        # 使用主窗口作为master创建结果变量
        master = parent.root
        
        # 定义计算结果变量
        self.results = {
            "scan_angle": tk.DoubleVar(master, value=0),  # 卫星扫描角 (度)
            "distance": tk.DoubleVar(master, value=0),  # 星地距离 (km)
            "path_loss": tk.DoubleVar(master, value=0),  # 路径损耗 (dB)
            "rain_fade": tk.DoubleVar(master, value=0),  # 雨衰 (dB)
            "received_signal_psd": tk.DoubleVar(master, value=0),  # 接收信号功率谱密度 (dBm/MHz)
            "noise_psd": tk.DoubleVar(master, value=0),  # 噪声功率谱密度 (dBm/MHz)
            "c_to_n": tk.DoubleVar(master, value=0),  # C/N比 (dB)
            "total_received_power": tk.DoubleVar(master, value=0),  # 总接收功率 (dBm)
            "gt_ratio": tk.DoubleVar(master, value=0),  # G/T值 (dB/K)
        }

    def perform_calculations(self):
        """执行所有计算步骤，按顺序计算各个参数"""
        ih = self.parent.input_handler
        
        # 获取输入参数（通过get_numeric_value解析公式）
        freq = ih.get_numeric_value("frequency")
        height = ih.get_numeric_value("satellite_height")
        eirp = ih.get_numeric_value("satellite_eirp")
        atmos_loss = ih.get_numeric_value("atmospheric_loss")
        scint_loss = ih.get_numeric_value("scintillation_loss")
        pol_loss = ih.get_numeric_value("polarization_loss")
        ant_gain = ih.get_numeric_value("terminal_antenna_gain")
        nf = ih.get_numeric_value("terminal_noise_figure")
        t_antenna = ih.get_numeric_value("terminal_noise_temp")
        elev_deg = ih.get_numeric_value("terminal_elevation_angle")
        bandwidth = ih.get_numeric_value("bandwidth")  # 获取带宽值
        
        # 计算几何参数
        self.calculate_geometric_parameters(elev_deg, height)
        
        # 计算路径损耗
        self.results["path_loss"].set(self.calculate_path_loss(freq))
        
        # 计算雨衰（如果启用）
        if self.parent.input_handler.flags["rain_fade"].get():
            rain_rate = ih.get_numeric_value("rain_rate")
            self.results["rain_fade"].set(self.calculate_rain_fade(freq, elev_deg, rain_rate))
        else:
            self.results["rain_fade"].set(0)
        
        # 计算噪声功率谱密度
        self.results["noise_psd"].set(self.calculate_noise_psd(nf, t_antenna))
        
        # 计算接收信号功率谱密度
        self.calculate_received_signal(eirp, atmos_loss, scint_loss, pol_loss, ant_gain, bandwidth)
        
        # 计算C/N比
        self.results["c_to_n"].set(self.results["received_signal_psd"].get() - self.results["noise_psd"].get())
        
        # 计算G/T值
        self.results["gt_ratio"].set(self.calculate_gt_ratio(ant_gain, nf, t_antenna))

    def calculate_geometric_parameters(self, elev_deg, height):
        """计算几何参数：扫描角和星地距离"""
        elev_rad = math.radians(elev_deg)
        cos_elev = math.cos(elev_rad)
        ratio = (self.earth_radius * cos_elev) / (self.earth_radius + height)
        angle_rad = math.acos(max(min(ratio, 1.0), -1.0))
        scan_angle_deg = 90 - math.degrees(angle_rad)
        self.results["scan_angle"].set(round(scan_angle_deg, 2))
        
        # 计算星地距离
        distance = math.sqrt(
            self.earth_radius**2 * math.sin(elev_rad)**2 +
            2 * self.earth_radius * height +
            height**2
        ) - self.earth_radius * math.sin(elev_rad)
        self.results["distance"].set(round(distance, 2))

    def calculate_path_loss(self, freq):
        """计算自由空间路径损耗 (dB)
        公式：L = 92.45 + 20*log10(f) + 20*log10(d)
        其中f为频率(GHz)，d为距离(km)
        """
        d = self.results["distance"].get()
        return 92.45 + 20 * math.log10(freq) + 20 * math.log10(d)

    def calculate_rain_fade(self, freq, elev_deg, rain_rate):
        """简化的雨衰计算模型
        使用ITU-R P.618建议中的简化公式
        """
        a = 0.0051 * freq**1.41
        b = 0.655 * freq**-0.075
        Ls = 35 * (math.sin(math.radians(elev_deg)))**-0.6
        return a * (rain_rate ** b) * Ls

    def calculate_noise_psd(self, nf, t_antenna):
        """计算噪声功率谱密度 (dBm/MHz)
        基于噪声系数和天线噪声温度计算
        """
        # 计算系统噪声温度 (K)
        f_linear = 10 ** (nf / 10)
        t_sys = 290 * (f_linear - 1) + t_antenna
        
        # 计算热噪声功率谱密度：k*T (W/Hz)
        # k = 1.38e-23 J/K (Boltzmann常数)
        # 转换为dBW/Hz: 10*log10(k*T)
        noise_psd_dbw_hz = 10 * math.log10(1.38e-23 * t_sys)
        
        # 转换为dBm/MHz: dBW/Hz + 30(dBW→dBm) + 60(Hz→MHz)
        noise_psd_dbm_mhz = noise_psd_dbw_hz + 30 + 60
        
        return noise_psd_dbm_mhz

    def calculate_received_signal(self, eirp, atmos_loss, scint_loss, pol_loss, ant_gain, bandwidth):
        """计算接收信号功率谱密度"""
        path_loss = self.results["path_loss"].get()
        rain_fade = self.results["rain_fade"].get()
        
        # 处理可选损耗 - 只添加已启用的损耗
        atmos_loss = atmos_loss if self.parent.input_handler.flags["atmospheric_loss"].get() else 0
        scint_loss = scint_loss if self.parent.input_handler.flags["scintillation_loss"].get() else 0
        pol_loss = pol_loss if self.parent.input_handler.flags["polarization_loss"].get() else 0
        
        link_margin = 0
        if self.parent.input_handler.flags["link_margin"].get():
            link_margin = float(self.parent.input_handler.params["link_margin"].get())
        
        beam_loss = 0
        if self.parent.input_handler.flags["beam_edge_loss"].get():
            beam_loss = float(self.parent.input_handler.params["beam_edge_loss"].get())
        
        scan_loss = 0
        if self.parent.input_handler.flags["scan_loss"].get():
            scan_loss = float(self.parent.input_handler.params["scan_loss"].get())
        
        total_loss = (atmos_loss + scint_loss + pol_loss + link_margin + 
                      beam_loss + scan_loss + path_loss + rain_fade)
        
        # 计算总接收功率 (dBm)
        # EIRP (dBW) + 30 → dBm - 总损耗 + 天线增益
        total_power_dbm = eirp + 30 - total_loss + ant_gain  # dBW → dBm
        
        # 计算功率谱密度 (dBm/MHz)
        psd_dbm_mhz = total_power_dbm - 10 * math.log10(bandwidth)
        
        self.results["received_signal_psd"].set(psd_dbm_mhz)
        self.results["total_received_power"].set(total_power_dbm)

    def calculate_gt_ratio(self, ant_gain, nf, t_antenna):
        """计算G/T值 (dB/K)
        G/T是接收系统性能的关键指标，表示接收增益与噪声温度之比
        """
        f_linear = 10 ** (nf / 10)
        t_sys = 290 * (f_linear - 1) + t_antenna
        return ant_gain - 10 * math.log10(t_sys)

class ResultDisplay:
    """结果显示模块 - 负责展示计算结果"""
    
    def __init__(self, parent):
        self.parent = parent
        self.results = parent.calculator.results
        self.result_labels = {}

    def create_result_display(self, parent):
        """创建结果显示区域"""
        # 标题
        title_label = ctk.CTkLabel(
            parent, text="计算结果",
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(pady=(5, 10))
        
        # 结果表格
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 定义结果项
        results = [
            ("scan_angle", "卫星扫描角 (度):"),
            ("distance", "星地距离 (km):"),
            ("path_loss", "路径损耗 (dB):"),
            ("rain_fade", "雨衰 (dB):"),
            ("received_signal_psd", "接收信号功率谱密度 (dBm/MHz):"),
            ("noise_psd", "噪声功率谱密度 (dBm/MHz):"),
            ("c_to_n", "C/N (dB):"),
            ("total_received_power", "总接收功率 (dBm):"),
            ("gt_ratio", "终端G/T值 (dB/K):"),
        ]
        
        # 创建结果标签
        for i, (var, label) in enumerate(results):
            ctk.CTkLabel(
                frame, text=label, font=("微软雅黑", 11),
                anchor="w"
            ).grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            
            value_label = ctk.CTkLabel(
                frame, text="0.00", font=("微软雅黑", 11, "bold"),
                anchor="e", text_color="#165DFF"
            )
            value_label.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            
            # 保存标签引用以便后续更新
            self.result_labels[var] = value_label
        
        # 设置列权重
        frame.columnconfigure(1, weight=1)
        
        # 绑定变量变化事件，实时更新显示
        for var_name in self.results:
            self.results[var_name].trace_add("write", 
                lambda *args, v=var_name: self.update_result_label(v))
        
        # 初始更新
        self.reset_results()

    def update_result_label(self, var_name):
        """更新结果标签显示"""
        value = self.results[var_name].get()
        formatted_value = format_result(value)
        self.result_labels[var_name].configure(text=formatted_value)

    def reset_results(self):
        """重置结果显示为0"""
        for var in self.results.values():
            var.set(0)
        for label in self.result_labels.values():
            label.configure(text="0.00")

if __name__ == "__main__":
    root = ctk.CTk()
    app = SatelliteLinkCalculator(root)
    root.mainloop()