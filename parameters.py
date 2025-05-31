PARAM_MAPPING = {
    # 公共参数
    "frequency": {"ch_name": "频率", "unit": "GHz",
        "default_value": {
            "星-地上行": "1.71",
            "星-地下行": "1.81", 
            "地-地上行": "1.71",
            "地-地下行": "1.81"
        }
    },
    "bandwidth": {"ch_name": "带宽", "unit": "MHz",
        "default_value": {
            "星-地上行": "0.72",
            "星-地下行": "5",
            "地-地上行": "0.72",
            "地-地下行": "5"
        }
    },
    
    # 几何参数
    "distance": {"ch_name": "距离", "unit": "km",
        "default_value": {
            "星-地上行": "400",  # 卫星高度关联值
            "星-地下行": "400",
            "地-地上行": "1",
            "地-地下行": "1"
        }
    },
    "satellite_height": {"ch_name": "卫星高度","unit": "km", "default_value": "400"},
    "satellite_scan_angle": {"ch_name": "卫星扫描角", "unit": "°", "default_value": "0"},

    # 卫星参数
    "satellite_eirp": {"ch_name": "卫星EIRP", "unit": "dBW", "default_value": "56"},
    "satellite_antenna_gain": {"ch_name": "卫星天线增益", "unit": "dBi", "default_value": "30.72"},
    "satellite_noise_figure": {"ch_name": "卫星噪声系数", "unit": "dB", "default_value": "2.4"},
    "satellite_noise_temp": {"ch_name": "卫星噪声温度", "unit": "K", "default_value": "290"},
    
    # 终端参数
    "terminal_eirp": {"ch_name": "终端EIRP", "unit": "dBW", "default_value": "23-30-5"},
    "terminal_antenna_gain": {"ch_name": "终端天线增益", "unit": "dBi", "default_value": "-5"},
    "terminal_noise_figure": {"ch_name": "终端噪声系数", "unit": "dB", "default_value": "7"},
    "terminal_noise_temp": {"ch_name": "终端噪声温度", "unit": "K", "default_value": "290"},
    
    # 基站参数
    "bs_eirp": {"ch_name": "基站EIRP", "unit": "dBW", "default_value": {"地-地下行": "46+30+22.5"}},
    "bs_antenna_gain": {"ch_name": "基站天线增益", "unit": "dBi", "default_value": "30.72"},
    "bs_noise_figure": {"ch_name": "基站噪声系数", "unit": "dB", "default_value": "2.4"},
    "bs_noise_temp": {"ch_name": "基站噪声温度", "unit": "K", "default_value": "290"},
    
    # 损耗参数
    "atmospheric_loss": {"ch_name": "大气损耗", "unit": "dB", "default_value": "0.1"},
    "scintillation_loss": {"ch_name": "闪烁损耗", "unit": "dB", "default_value": "0.3"},
    "polarization_loss": {"ch_name": "极化损耗", "unit": "dB", "default_value": "3"},
    "beam_edge_loss": {"ch_name": "波束边缘损耗", "unit": "dB", "default_value": "1"},
    "scan_loss": {"ch_name": "扫描损耗", "unit": "dB", "default_value": "4"},
    "link_margin": {"ch_name": "链路余量", "unit": "dB", "default_value": "3"},
    
    # 其他参数
    "rain_rate": {"ch_name": "降雨率", "unit": "mm/h", "default_value": "50"},
    "interference_psd": {"ch_name": "干扰功率谱密度", "unit": "dBm/MHz", "default_value": "-inf"}
}

# 新增参数分组配置
PARAM_GROUPS = {
    # 卫星链路基础参数
    "base_satellite": {
        "common": ["frequency", "bandwidth", "satellite_scan_angle", "satellite_height"],
        "optional": [
            "atmospheric_loss", "scintillation_loss", "polarization_loss",
            "rain_rate", "link_margin", "beam_edge_loss", "scan_loss", "interference_psd"
        ]
    },
    
    # 地面链路基础参数
    "base_terrestrial": {
        "common": ["frequency", "bandwidth", "distance"], 
        "optional": [ "beam_edge_loss", "interference_psd"]
    },

    # 具体链路类型配置
    "星-地上行": {
        "base": "base_satellite",
        "tx_params": ["terminal_eirp"],
        "rx_params": ["satellite_antenna_gain", "satellite_noise_figure", "satellite_noise_temp"]
    },
    "星-地下行": {
        "base": "base_satellite",
        "tx_params": ["satellite_eirp"],
        "rx_params": ["terminal_antenna_gain", "terminal_noise_figure", "terminal_noise_temp"]
    },
    "地-地上行": {
        "base": "base_terrestrial",
        "tx_params": ["terminal_eirp"],
        "rx_params": ["bs_antenna_gain", "bs_noise_figure", "bs_noise_temp"]
    },
    "地-地下行": {
        "base": "base_terrestrial",
        "tx_params": ["bs_eirp"],
        "rx_params": ["terminal_antenna_gain", "terminal_noise_figure", "terminal_noise_temp"]
    }
}

# 新增分组名称配置
PARAM_GROUP_NAMES = {
    "base_satellite": {
        "common": "信号参数",
        "optional": "损耗参数",
        "tx_params": "卫星参数",
        "rx_params": "终端参数"
    },
    "base_terrestrial": {
        "common": "信号参数",
        "optional": "损耗参数",
        "tx_params": "基站参数", 
        "rx_params": "终端参数"
    },
    "星-地上行": {
        "tx_params": "终端参数",
        "rx_params": "卫星参数"
    },
    "地-地下行": {
        "tx_params": "基站参数",
        "rx_params": "终端参数"
    }
}