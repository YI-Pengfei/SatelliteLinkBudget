"""
地面信道模型
3GPP TR 38.901 V18.0.0 (2024-03)
Study on channel model for frequencies from 0.5 to 100 GHz
(Release 18)

Table 7.4.1-1: Pathloss models
Table 7.4.2-1 LOS probability
"""

import math

def pathLoss_3GPP38901(frequency, d, scene, los_condition):
    """
    根据3GPP TR 38.901 V18.0.0标准计算不同场景下的路径损耗。
    :param frequency: 频率，单位为GHz
    :param scene: 场景，取值为 "农村宏蜂窝RMa"（RMa） 或 "城市宏蜂窝"（UMa）
    :param d: 基站和用户之间的直线距离，单位为m
    :return: 计算得到的路径损耗值，单位为dB
    """
    c = 3e8  # 光速，单位m/s
    PL = 0
    if scene == "农村宏蜂窝RMa":
        # 基础参数
        h_bs = 35  # 基站高度，单位米
        h_ut = 1.5  # 用户高度，单位米
        W = 20  # 街道平均宽度，单位米
        h = 5  # 建筑物平均高度，单位米

        # 计算LOS的概率
        if d <= 10:
            p_los = 1
        else:
            p_los = math.exp(-((d - 10) / 1000))
        
        # 计算断点距离和3D距离
        d_break = (2 * math.pi * h_bs * h_ut * frequency * 10 ** 9) / c
        d_3d = math.sqrt(d ** 2 + (h_bs - h_ut) ** 2)
        print(f"农村宏蜂窝RMa场景下，断点距离为: {d_break}")
        # 计算LoS路径损耗
        PL1 = 20 * math.log10(40 * math.pi * d_3d * frequency / 3) + min(0.03 * h ** 1.72, 10) * math.log10(d_3d) - min(
            0.044 * h ** 1.72, 14.77) + 0.002 * math.log10(h) * d_3d
        PL1_dbp = 20 * math.log10(40 * math.pi * d_break * frequency / 3) + min(0.03 * h ** 1.72, 10) * math.log10(d_break) - min(
            0.044 * h ** 1.72, 14.77) + 0.002 * math.log10(h) * d_break
        PL2 = PL1_dbp + 40 * math.log10(d_3d / d_break)
        if 10 <= d <= d_break:
            PL_LoS = PL1
        elif d_break <= d <= 10e3:
            PL_LoS = PL2

        # 计算NLoS路径损耗
        if 10 <= d <= d_break:
            PL3 = PL1
        elif d_break <= d <= 10e3:
            PL3 = PL2
        PL4 = 161.04 - 7.1 * math.log10(W) + 7.5 * math.log10(h) - (24.37 - 3.7 * (h / h_bs) ** 2) * math.log10(
            h_bs) + (43.42 - 3.1 * math.log10(h_bs)) * (math.log10(d_3d) - 3) + 20 * math.log10(frequency) - (
                    3.2 * (math.log10(11.75 * h_ut)) ** 2 - 4.97)
        if 10 <= d <= 5e3:
            PL_NLoS = max(PL3, PL4)
        else:
            PL_NLoS = PL4
        # 加权计算路径损耗
        PL = p_los * PL_LoS + (1 - p_los) * PL_NLoS

    elif scene == "城市宏蜂窝UMa":
        # 基础参数
        h_bs = 25  # 基站高度，单位米
        h_ut = 1.5  # 用户高度，单位米
        h_e = 1  # 有效环境高度，对于UMi,为1m
        h_bs2 = h_bs - h_e
        h_ut2 = h_ut - h_e

        # 计算LOS的概率
        if h_ut <= 13:
            C = 0
        else:
            C = ((h_ut - 13) / 10) ** 1.5
        if d < 18:
            p_los = 1
        elif d > 18:
            p_los = ((18 / d) + math.exp(-(d / 63)) * (1 - (18 / d))) * (
                    1 + C * (5 / 4) * ((d / 100) ** 3) * math.exp(-(d / 150)))

        # 计算3D距离和断点距离
        d_3d = math.sqrt(d ** 2 + (h_bs - h_ut) ** 2)
        d_break = 4 * h_bs2 * h_ut2 * frequency * 10 ** 9 / c
        print(f"城市宏蜂窝场景下，断点距离为: {d_break}")

        # 计算LoS路径损耗
        PL1 = 28 + 22 * math.log10(d_3d) + 20 * math.log10(frequency)
        PL2 = 28 + 40 * math.log10(d_3d) + 20 * math.log10(frequency) - 9 * math.log10(d_break ** 2 + (h_bs - h_ut) ** 2)
        if 10 <= d <= d_break:
            PL_LoS = PL1
        elif d_break <= d <= 5e3:
            PL_LoS = PL2

        # 计算NLoS路径损耗
        if 10 <= d <= d_break:
            PL3 = PL1
        elif d_break <= d <= 5e3:
            PL3 = PL2
        PL4 = 13.54 + 39.08 * math.log10(d_3d) + 20 * math.log10(frequency) - 0.6 * (h_ut - 1.5)
        if 10 <= d <= 5e3:
            PL_NLoS = PL4
        # 加权计算路径损耗
        PL = p_los * PL_LoS + (1 - p_los) * PL_NLoS
        # print(f"城市宏蜂窝场景下，LoS路损: {PL_LoS}")
        # print(f"城市宏蜂窝场景下，NLoS路损: {PL_NLoS}")
        # print(f"城市宏蜂窝场景下，加权后的路损: {PL}")


    if los_condition == "LoS":
        return PL_LoS
    elif los_condition == "NLoS":
        return PL_NLoS
    else:
        return PL


if __name__ == "__main__":
    pl = pathLoss_3GPP38901(1.71,  500,"农村宏蜂窝RMa", 'LoS')
    print(f'路径损耗为{pl:.2f}dB')