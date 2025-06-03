"""
SafeMath.py
------------------------
安全数学函数库
------------------------
"""
import math
from tkinter import messagebox
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

# 修正参数中的中文逗号为英文逗号
def safe_eval(expr, sign_massagebox=True):
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
        if sign_massagebox:
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
