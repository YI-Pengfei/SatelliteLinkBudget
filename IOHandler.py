"""
IOHandler.py
功能：处理用户输入，包括参数输入和标志设置。
包含：
- InputHandler 类：用于处理用户输入，包括参数输入和标志设置。
- OutputHandler 类：用于处理输出，包括结果显示和导出功能。
"""

import tkinter as tk
import customtkinter as ctk
from SafeMath import safe_eval, format_result

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
        if 'bs_eirp' in self.params or 'bs_noise_figure' in self.params:
            param_labels.extend([
                ("distance", "距离 (km):"),
            ])
        self.create_param_entries(scrollable_frame, param_labels, compact=True)

        # 分隔线
        self.create_separator(scrollable_frame)

        if 'satellite_height' in self.params:
            # Option1: 星地   第二组：卫星参数
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
        else:
            # Option2： 地地   第二组2：地面基站参数
            bs_params = [
            ]
            if 'bs_eirp' in self.params:
                bs_params.append(("bs_eirp", "基站EIRP (dBW):"))
            if 'bs_noise_figure' in self.params:
                bs_params.extend([
                    ("bs_noise_figure", "基站噪声系数 (dB):"),
                    ("bs_noise_temp", "基站天线噪声温度 (K):"),
                    ("bs_antenna_gain", "基站天线增益 (dBi):"),
                ])
            self.create_group_title(scrollable_frame, "2. 基站参数", group_title_font, group_title_color)
            self.create_param_entries(scrollable_frame, bs_params, compact=True)

            # 添加基站G/T值显示框
            if 'bs_noise_figure' in self.params:
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
        if 'satellite_height' in self.params:
            # Option1: 星地
            param_labels = [
                ("atmospheric_loss", "大气损耗 (dB):"),
                ("scintillation_loss", "闪烁损耗 (dB):"),
                ("polarization_loss", "极化损耗 (dB):"),
                ("beam_edge_loss", "波束边缘损耗 (dB):"),
                ("scan_loss", "扫描损耗 (dB):"),
                ("rain_rate", "降雨率 (mm/h):"),
            ]
        else:
            # Option2： 地地
            param_labels = [
                ("beam_edge_loss", "波束边缘损耗 (dB):"),
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
            category_frame.item_frames = []
            
            # 更新或创建结果项
            for item_idx, (label, value, unit) in enumerate(items):
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
