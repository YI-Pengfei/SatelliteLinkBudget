import math
from ChannelModel_3GPP38901 import pathLoss_3GPP38901
class LinkCalculator:
    def __init__(self):
        # 地球半径 (km)
        self.earth_radius = 6371
        # 玻尔兹曼常数 (J/K)
        self.BOLTZMANN_CONSTANT = 1.38e-23

    def perform_calculations_terrestrial(self, input_params):
        """执行所有计算步骤，按顺序计算各个参数"""
        # 获取输入参数
        # 信号参数
        freq = input_params["frequency"]  # 信号频率，单位：GHz
        bandwidth = input_params["bandwidth"]  # 信号带宽，单位：MHz

        # 发射机参数
        eirp = input_params["tx_eirp"]  # 发射机等效全向辐射功率，单位：dBW

        # 接收机参数
        ant_gain = input_params["rx_antenna_gain"]  # 接收天线增益，单位：dBi
        nf = input_params["rx_noise_figure"]  # 接收机噪声系数，单位：dB
        t_antenna = input_params["rx_noise_temp"]  # 接收天线噪声温度，单位：K

        # 收发设备距离
        distance = input_params["distance"]  # 星地距离，单位：km

        # 损耗参数 
        link_margin = input_params["link_margin"] if "link_margin" in input_params else 0  # 链路余量，单位：dB
        beam_loss = input_params["beam_edge_loss"] if "beam_edge_loss" in input_params else 0  # 波束边缘损耗，单位：dB
        interference_psd = input_params["interference_psd"] if "interference_psd" in input_params else -math.inf  # 干扰，单位：dBm/MHz
        # 计算路径损耗
        path_loss = pathLoss_3GPP38901(freq, "农村宏蜂窝", distance*1000)

        # 计算噪声功率谱密度
        noise_psd = self.calculate_noise_psd(nf, t_antenna)

        # 计算总损耗
        total_loss = path_loss + link_margin + beam_loss

        # 计算接收信号功率谱密度
        received_signal_psd, total_received_power = self.calculate_received_signal(
            eirp, total_loss, ant_gain, bandwidth
        )

        # 计算C/N比
        c_to_n = received_signal_psd - noise_psd

        # 计算C/(N+I)
        if interference_psd != -math.inf:
            # 将dB值转换为线性值进行计算
            c_linear = 10 ** (received_signal_psd / 10)
            n_linear = 10 ** (noise_psd / 10)
            i_linear = 10 ** (interference_psd / 10)
            c_n_plus_i_linear = c_linear / (n_linear + i_linear)
            c_to_n_plus_i = 10 * math.log10(c_n_plus_i_linear)  # 转换回dB
        else:
            c_to_n_plus_i = c_to_n  # 无干扰时等于C/N

        # 计算G/T值
        gt_ratio = self.calculate_gt_ratio(ant_gain, nf, t_antenna)

        results = {
            "distance": distance,
            "path_loss": path_loss,
            "total_loss": total_loss,
            "noise_psd": noise_psd,
            "received_signal_psd": received_signal_psd,
            "total_received_power": total_received_power,
            "c_to_n": c_to_n,
            "c_to_n_plus_i": c_to_n_plus_i,
            "gt_ratio": gt_ratio
        }
        print(results)
        return results


    def perform_calculations_sat(self, input_params):
        """执行所有计算步骤，按顺序计算各个参数"""
        # 获取输入参数
        # 信号参数
        freq = input_params["frequency"]  # 信号频率，单位：GHz
        bandwidth = input_params["bandwidth"]  # 信号带宽，单位：MHz

        # 发射机参数
        eirp = input_params["tx_eirp"]  # 发射机等效全向辐射功率，单位：dBW

        # 接收机参数
        ant_gain = input_params["rx_antenna_gain"]  # 接收天线增益，单位：dBi
        nf = input_params["rx_noise_figure"]  # 接收机噪声系数，单位：dB
        t_antenna = input_params["rx_noise_temp"]  # 接收天线噪声温度，单位：K

        # 几何参数
        scan_angle = input_params["satellite_scan_angle"]  # 卫星扫描角，单位：度
        height = input_params["satellite_height"]  # 卫星高度，单位：km

        # 计算终端仰角、星地距离
        terminal_elevation_angle, distance = self.calculate_geometric_parameters(scan_angle, height)

        # 损耗参数 
        atmos_loss = input_params["atmospheric_loss"] if "atmospheric_loss" in input_params else 0  # 大气损耗，单位：dB
        scint_loss = input_params["scintillation_loss"] if "scintillation_loss" in input_params else 0  # 闪烁损耗，单位：dB
        pol_loss = input_params["polarization_loss"] if "polarization_loss" in input_params else 0  # 极化损耗，单位：dB
        
        rain_rate = input_params["rain_rate"] if "rain_rate" in input_params else 0  # 降雨率，单位：mm/h
        link_margin = input_params["link_margin"] if "link_margin" in input_params else 0  # 链路余量，单位：dB
        beam_loss = input_params["beam_edge_loss"] if "beam_edge_loss" in input_params else 0  # 波束边缘损耗，单位：dB
        scan_loss = input_params["scan_loss"] if "scan_loss" in input_params else 0  # 扫描损耗，单位：dB
        interference_psd = input_params["interference_psd"] if "interference_psd" in input_params else -math.inf  # 干扰，单位：dBm/MHz
        # 计算路径损耗
        path_loss = self.calculate_path_loss(freq, distance)

        # 计算雨衰（如果启用）
        rain_fade = self.calculate_rain_fade(freq, terminal_elevation_angle, rain_rate) if "rain_rate" in input_params else 0

        # 计算噪声功率谱密度
        noise_psd = self.calculate_noise_psd(nf, t_antenna)

        # 计算总损耗
        total_loss = self.calculate_total_loss(atmos_loss, scint_loss, pol_loss, path_loss, rain_fade, link_margin, beam_loss, scan_loss)

        # 计算接收信号功率谱密度
        received_signal_psd, total_received_power = self.calculate_received_signal(
            eirp, total_loss, ant_gain, bandwidth
        )

        # 计算C/N比
        c_to_n = received_signal_psd - noise_psd

        # 计算C/(N+I)
        if interference_psd != -math.inf:
            # 将dB值转换为线性值进行计算
            c_linear = 10 ** (received_signal_psd / 10)
            n_linear = 10 ** (noise_psd / 10)
            i_linear = 10 ** (interference_psd / 10)
            c_n_plus_i_linear = c_linear / (n_linear + i_linear)
            c_to_n_plus_i = 10 * math.log10(c_n_plus_i_linear)  # 转换回dB
        else:
            c_to_n_plus_i = c_to_n  # 无干扰时等于C/N

        # 计算G/T值
        gt_ratio = self.calculate_gt_ratio(ant_gain, nf, t_antenna)

        return {
            "terminal_elevation_angle": terminal_elevation_angle,  # 终端仰角作为输出参数
            "distance": distance,
            "path_loss": path_loss,
            "rain_fade": rain_fade,
            "total_loss": total_loss,
            "noise_psd": noise_psd,
            "received_signal_psd": received_signal_psd,
            "total_received_power": total_received_power,
            "c_to_n": c_to_n,
            "c_to_n_plus_i": c_to_n_plus_i,
            "gt_ratio": gt_ratio
        }

    def calculate_geometric_parameters(self, scan_angle_degrees, height):
        """
        计算给定卫星扫描角对应的地面用户仰角
        根据已知条件求解三角形的第三条边和夹角
        
        参数:
        r (float): 第一条边a的长度
        h (float): 第二条边b比第一条边多出的长度
        scan_angle_degrees (float): 边a和边c的夹角(度)
        
        返回:
        tuple: (第三条边c的长度, 边b和边c的夹角B(度)-90) 即星地距离 和 终端仰角
        """
        h = height
        r = self.earth_radius
        if h <= 0:
            raise ValueError("h必须大于0，以确保边b > 边a")
        
        a, b = r, r + h
        max_angle = math.degrees(math.asin(a / b))
        
        if scan_angle_degrees >= max_angle:
            raise ValueError(f"扫描角需小于{max_angle:.2f}度")
        
        A_rad = math.radians(scan_angle_degrees)
        sin_B = b * math.sin(A_rad) / a
        B_deg = 180 - math.degrees(math.asin(sin_B))
        C_deg = 180 - scan_angle_degrees - B_deg
        
        # 使用正确的余弦定理计算边c
        c = math.sqrt(a**2 + b**2 - 2 * a * b * math.cos(math.radians(C_deg)))
        
        return  B_deg-90, c

    def calculate_path_loss(self, freq, distance):
        """计算自由空间路径损耗 (dB)
        公式：L = 92.45 + 20*log10(f) + 20*log10(d)
        其中f为频率(GHz)，d为距离(km)
        """
        return 92.45 + 20 * math.log10(freq) + 20 * math.log10(distance)

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
        noise_psd_dbw_hz = 10 * math.log10(self.BOLTZMANN_CONSTANT * t_sys)

        # 转换为dBm/MHz: dBW/Hz + 30(dBW→dBm) + 60(Hz→MHz)
        noise_psd_dbm_mhz = noise_psd_dbw_hz + 30 + 60

        return noise_psd_dbm_mhz

    def calculate_total_loss(self, atmos_loss, scint_loss, pol_loss, path_loss, rain_fade, link_margin, beam_loss, scan_loss):
        """计算总损耗"""
        return (atmos_loss + scint_loss + pol_loss + link_margin +
                beam_loss + scan_loss + path_loss + rain_fade)

    def calculate_received_signal(self, eirp, total_loss, ant_gain, bandwidth):
        """计算接收信号功率谱密度"""
        # 计算总接收功率 (dBm)
        # EIRP (dBW) + 30 → dBm - 总损耗 + 天线增益
        total_power_dbm = eirp + 30 - total_loss + ant_gain  # dBW → dBm

        # 计算功率谱密度 (dBm/MHz)
        psd_dbm_mhz = total_power_dbm - 10 * math.log10(bandwidth)

        return psd_dbm_mhz, total_power_dbm

    def calculate_received_signal(self, eirp, total_loss, ant_gain, bandwidth):
        """计算接收信号功率谱密度"""
        # 计算总接收功率 (dBm)
        # EIRP (dBW) + 30 → dBm - 总损耗 + 天线增益
        total_power_dbm = eirp + 30 - total_loss + ant_gain  # dBW → dBm

        # 计算功率谱密度 (dBm/MHz)
        psd_dbm_mhz = total_power_dbm - 10 * math.log10(bandwidth)

        return psd_dbm_mhz, total_power_dbm

    def calculate_gt_ratio(self, ant_gain, nf, t_antenna):
        """计算G/T值 (dB/K)
        G/T是接收系统性能的关键指标，表示接收增益与噪声温度之比
        """
        f_linear = 10 ** (nf / 10)
        t_sys = 290 * (f_linear - 1) + t_antenna
        return ant_gain - 10 * math.log10(t_sys)


    def detailed_calculation(self, input_params):
        results = self.perform_calculations(input_params)
        
        # 定义计算步骤的模板
        steps = [
            {
                '步骤': '几何参数计算',
                '公式': '三角公式（略）',
                '参数': f'地球半径={self.earth_radius}km, 卫星轨道高度={input_params["satellite_height"]}km, 卫星扫描角={input_params["satellite_scan_angle"]}°',
                '结果': f'终端仰角={results["terminal_elevation_angle"]:.2f}°, 星地距离={results["distance"]:.2f}km'
            },
            {
                '步骤': '路径损耗',
                '公式': '路径损耗 = 92.45 + 20*log10(频率) + 20*log10(距离)',
                '参数': f'频率={input_params["frequency"]}GHz, 距离={results["distance"]:.2f}km',
                '结果': f'{results["path_loss"]:.2f}dB'
            },
            {
                '步骤': '总损耗',
                '公式': '总损耗 = 路径损耗+雨衰+大气损耗+闪烁损耗+极化损耗+链路余量+波束边缘损耗+扫描损耗',
                '参数': f"路径损耗={results['path_loss']:.2f}dB, 雨衰={results['rain_fade']:.2f}dB, 大气损耗={input_params['atmospheric_loss']}dB, 闪烁损耗={input_params['scintillation_loss']}dB, 极化损耗={input_params['polarization_loss']}dB, 链路余量={input_params['link_margin']}dB, 波束边缘损耗={input_params['beam_edge_loss']}dB, 扫描损耗={input_params['scan_loss']}dB",
                '结果': f'{results["total_loss"]:.2f}dB'
            },
            {
                '步骤': '接收信号功率谱密度',
                '公式': '接收信号功率谱密度 = EIRP + 30 - 总损耗 + 接收天线增益 - 10*log10(带宽)',
                '参数': f'EIRP={input_params["tx_eirp"]}dBW, 总损耗={results["total_loss"]:.2f}dB, 接收天线增益={input_params["rx_antenna_gain"]}dBi, 带宽={input_params["bandwidth"]}MHz',
                '结果': f'{results["received_signal_psd"]:.2f}dBm/MHz'
            },
            {
                '步骤': '噪声功率谱密度',
                '公式': '噪声功率谱密度 = 10*log10(玻尔兹曼常数*系统噪声温度) + 30 + 60\n其中，系统噪声温度=290*(噪声系数线性值-1)+天线噪声温度, 噪声系数线性值=10^(噪声系数/10)',
                '参数': f'k={self.BOLTZMANN_CONSTANT:.2e} J/K, 噪声系数={input_params["rx_noise_figure"]}dB, 天线噪声温度={input_params["rx_noise_temp"]}K',
                '结果': f'{results["noise_psd"]:.2f}dBm/MHz'
            },
            {
                '步骤': 'C/N',
                '公式': 'C/N = 接收信号功率谱密度 - 噪声功率谱密度',
                '参数': f'接收信号功率谱密度={results["received_signal_psd"]:.2f}dBm/MHz, 噪声功率谱密度={results["noise_psd"]:.2f}dBm/MHz',
                '结果': f'{results["c_to_n"]:.2f}dB'
            },
            {
                '步骤': 'C/(N+I)',
                '公式': 'C/(N+I) = 10*log10(接收信号功率谱密度线性值/(噪声功率谱密度线性值+干扰功率谱密度线性值))',
                '参数': f'接收信号功率谱密度={results["received_signal_psd"]:.2f}dBm/MHz, 噪声功率谱密度={results["noise_psd"]:.2f}dBm/MHz, 干扰功率谱密度={input_params["interference_psd"]:.2f}dBm/MHz',
                '结果': f'{results["c_to_n"]:.2f}dB'
            },
            {
                '步骤': 'G/T值',
                '公式': 'G/T = 接收天线增益 - 10*log10(系统噪声温度)\n其中，系统噪声温度=290*(噪声系数线性值-1)+天线噪声温度',
                '参数': f'接收天线增益={input_params["rx_antenna_gain"]}dBi, 噪声系数={input_params["rx_noise_figure"]}dB, 天线噪声温度={input_params["rx_noise_temp"]}K',
                '结果': f'{results["gt_ratio"]:.2f}dB/K'
            }
        ]

        # 添加雨衰计算（如果启用）
        if "rain_rate" in input_params and input_params["rain_rate"] > 0:
            steps.insert(2, {
                '步骤': '雨衰',
                '公式': '雨衰 = a * (降雨率^b) * 路径长度\n其中a=0.0051*频率^1.41, b=0.655*频率^-0.075, 路径长度=35*(sinθ)^-0.6',
                '参数': f'频率={input_params["frequency"]}GHz, θ={results["terminal_elevation_angle"]:.2f}°, 降雨率={input_params["rain_rate"]}mm/h',
                '结果': f'{results["rain_fade"]:.2f}dB'
            })

        return steps



if __name__ == "__main__":
    # 示例输入参数
    input_params = {
        "frequency": 1.81,
        "satellite_height": 400,
        "tx_eirp": 56,
        "atmospheric_loss": 0.1,
        "scintillation_loss": 0.3,
        "polarization_loss": 3,
        "rx_antenna_gain": -5,
        "rx_noise_figure": 7,
        "rx_noise_temp": 290,
        "satellite_scan_angle": 57,
        "bandwidth": 5,
        "rain_rate": 50,
        "link_margin": 3,
        "beam_edge_loss": 1,
        "scan_loss": 4
    }

    calculator = LinkCalculator()
    results = calculator.perform_calculations(input_params)

    for key, value in results.items():
        print(f"{key}: {value}")