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
from parameters import PARAM_MAPPING, PARAM_GROUPS, PARAM_GROUP_NAMES, FLAG_DEFAULTS, RESULT_CATEGORIES

GROUP_TITLE_FONT = ("微软雅黑", 12, "bold")
GROUP_TITLE_COLOR = "#165DFF"
# 输入处理类
class InputHandler:
    def __init__(self, parent, default_params, link_type):  # 改为接收link_type参数
        self.link_type = link_type  # 存储链路类型
        self.parent = parent
        self.params = {param: tk.StringVar(value=value) for param, value in default_params.items()}
        self.flags = {
            flag_name: tk.BooleanVar(value=default) 
            for flag_name, default in FLAG_DEFAULTS.items()
        }
        self.defaults = {p: v.get() for p, v in self.params.items()}
        self.entries = {}
        self.raw_formulas = {}  # 存储原始公式

    def create_input_form(self, parent):
        # 创建标题和滚动区域
        title_label = ctk.CTkLabel(
            parent, text="输入参数 (支持公式如sin, cos, tan, log, 幂(**))",
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(pady=(5, 10))

        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollable_frame.grid_columnconfigure(0, weight=1)

        # 根据链路类型选择参数组
        config = PARAM_GROUPS[self.link_type]
        base_config = PARAM_GROUPS[config["base"]]

        # 合并所有参数组
        merged_groups = {
            "common": base_config["common"],
            "tx_params": config["tx_params"],
            "rx_params": config["rx_params"],
            "optional": base_config["optional"],
            "beam_params": base_config["beam_params"],
            "interference_params": base_config["interference_params"]
        }

        # 动态生成参数组
        group_index = 1
        for group_type, params in merged_groups.items():
            if not params:
                continue

            # 获取分组标题
            group_title = PARAM_GROUP_NAMES[config["base"]].get(group_type, "")
            if self.link_type in PARAM_GROUP_NAMES and group_type in PARAM_GROUP_NAMES[self.link_type]:
                group_title = PARAM_GROUP_NAMES[self.link_type][group_type]

            self.create_group_title(
                scrollable_frame,
                f"{group_index}. {group_title}",
                GROUP_TITLE_FONT, GROUP_TITLE_COLOR
            )

            # 生成参数输入项
            param_labels = [
                (param, f"{PARAM_MAPPING[param]['ch_name']} ({PARAM_MAPPING[param]['unit']}):") 
                for param in params if param in self.params
            ]
            
            has_checkboxes = group_type in ["optional","beam_params", "interference_params"  ]
            self.create_param_entries(
                scrollable_frame, 
                param_labels,
                compact=True,
                has_checkboxes=has_checkboxes
            )
            
            if group_type=='rx_params':
                self.gt_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
                self.gt_frame.pack(fill=tk.X, padx=5, pady=(10, 5))

            self.create_separator(scrollable_frame)
            group_index += 1

        # 特殊处理地面链路场景选择
        if config["base"] == "base_terrestrial":
            self._create_terrestrial_scenario_selector(scrollable_frame)

        # 强制刷新界面
        scrollable_frame._parent_canvas.yview_moveto(0)

    def _create_terrestrial_scenario_selector(self, parent):
        # 地面场景选择器
        scenario_frame = ctk.CTkFrame(parent)
        scenario_frame.pack(pady=10, fill=tk.X)

        # 场景类型
        ctk.CTkLabel(scenario_frame, text="地面场景:").grid(row=0, column=0, padx=5)
        self.scenario_var = tk.StringVar(value='城市宏蜂窝UMa')
        ctk.CTkRadioButton(scenario_frame, text="城市宏蜂窝UMa", variable=self.scenario_var, 
                         value='城市宏蜂窝UMa').grid(row=0, column=1)
        ctk.CTkRadioButton(scenario_frame, text="农村宏蜂窝RMa", variable=self.scenario_var,
                         value='农村宏蜂窝RMa').grid(row=0, column=2)

        # 传播条件
        ctk.CTkLabel(scenario_frame, text="链路状态:").grid(row=1, column=0, padx=5, pady=(10,0))
        self.los_var = tk.StringVar(value='LoS')
        ctk.CTkRadioButton(scenario_frame, text="LoS", variable=self.los_var, 
                         value='LoS').grid(row=1, column=1, pady=(10,0))
        ctk.CTkRadioButton(scenario_frame, text="NLoS", variable=self.los_var,
                         value='NLoS').grid(row=1, column=2, pady=(10,0))
        ctk.CTkRadioButton(scenario_frame, text="LoS/NLoS概率加权", variable=self.los_var,
                         value='LoS/NLoS概率加权').grid(row=1, column=3, pady=(10,0))

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

    def get_numeric_value2(self, param, default=0):
        """获取数值（支持公式计算）"""
        try:
            expr = self.params[param].get()
            # 优先使用safe_eval解析公式
            result = safe_eval(expr)
            if result is not None:
                return float(result)
            
            # 如果公式解析失败，尝试直接转换
            return float(expr)
        except (KeyError, ValueError, TypeError, SyntaxError):
            # 处理参数不存在或非法表达式
            return default
        except Exception as e:
            # 其他未知异常处理
            print(f"参数 {param} 解析异常: {str(e)}")
            return default

    def get_numeric_value(self, param):
        expr = self.params[param].get()
        try:
            return float(expr)
        except ValueError:
            result = safe_eval(expr)
            return float(result) if result is not None else 0

    def reset_params(self):
        """重置所有参数输入和标志位状态"""
        # 获取当前链路类型配置
        config = PARAM_GROUPS[self.link_type]
        base_config = PARAM_GROUPS[config["base"]]

        # 合并所有参数组
        all_params = (
            base_config["common"] +
            config["tx_params"] +
            config["rx_params"] +
            base_config["optional"] +
            base_config["beam_params"] +
            base_config["interference_params"]
        )

        # 重置参数值
        for param in all_params:
            if param in self.params:
                self.params[param].set(self.defaults.get(param, ""))
                self.raw_formulas[param] = ""

        # 重置标志位
        for flag_name, default in FLAG_DEFAULTS.items():
            self.flags[flag_name].set(default)

        # 重置地面场景选择器
        if hasattr(self, 'scenario_var'):
            self.scenario_var.set('城市宏蜂窝UMa')
            self.los_var.set('LoS')

        # 更新输入框状态
        for param, entry in self.entries.items():
            flag_key = {
                "atmospheric_loss": "atmospheric_loss",
                "scintillation_loss": "scintillation_loss",
                "polarization_loss": "polarization_loss",
                "link_margin": "link_margin"
            }.get(param, None)
            if flag_key:
                entry.configure(state="normal" if self.flags[flag_key].get() else "disabled")


    def trigger_all_focus_out(self):
        for entry in self.entries.values():
            entry.event_generate("<FocusOut>")

    def get_terrestrial_link_parameters(self):
        return {
            'scenario': self.scenario_var.get(),
            'los_condition': self.los_var.get(),
        }

# 结果显示类
class ResultDisplay:
    def __init__(self):
        self.result_frames = {}  # 存储各分类框架

    def create_result_display(self, parent):
        """初始化结果显示区域（新增）"""
        self.parent = parent
        self.parent.pack_propagate(False)  # 禁止自动调整大小

    def update_results(self, results, link_type):
        """优化后的结果更新方法（修复重复显示问题）"""
        # 清除旧结果（包括所有子组件和框架引用）
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.result_frames.clear()  # 清空框架引用
        
        # 根据链路类型选择元数据
        category_key = "卫星链路" if link_type.startswith("星-") else "地面链路"
        categories = RESULT_CATEGORIES[category_key]

        # 遍历元数据生成结果框架
        row_counter = 0  # 添加行号计数器
        for category_name, items in categories.items():
            # 创建分类标题
            title_label = ctk.CTkLabel(
                self.parent,
                text=category_name,
                font=GROUP_TITLE_FONT,
                text_color=GROUP_TITLE_COLOR
            )
            title_label.pack(fill="x", pady=(10, 5))

            # 创建分类内容框架
            category_frame = ctk.CTkFrame(self.parent)
            category_frame.pack(fill="x", padx=5, pady=3)
            category_frame.grid_columnconfigure(1, weight=1)

            # 遍历结果项生成控件
            for item in items:
                # 标签（左对齐）
                ctk.CTkLabel(
                    category_frame,
                    text=f"{item['label']}:",
                    anchor="w"
                ).grid(row=row_counter, column=0, sticky="w", padx=5)

                # 值显示（右对齐，带单位）
                value = results.get(item['key'], "N/A")
                ctk.CTkLabel(
                    category_frame,
                    text=f"{format_result(value)} {item['unit']}",
                    anchor="e"
                ).grid(row=row_counter, column=1, sticky="e", padx=5)
                
                row_counter += 1  # 递增行号
                self.result_frames[item['key']] = (title_label, category_frame)

        # 强制刷新界面
        self.parent.update_idletasks()

    def clear_results(self):
        """清空结果显示区域"""
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.result_frames.clear()