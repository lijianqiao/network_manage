"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: brand_detector.py
@DateTime: 2025/06/23 15:35:00
@Docs: 设备品牌检测器 - 根据设备信息或命令输出自动识别设备品牌
"""

import re

from app.utils.logger import logger


class BrandDetector:
    """设备品牌检测器"""

    # 品牌识别规则配置
    BRAND_PATTERNS = {
        "cisco": {
            "platform_keywords": ["cisco", "ios", "iosxe", "iosxr", "nxos", "asa"],
            "version_patterns": [
                r"Cisco IOS",
                r"Cisco Nexus",
                r"Cisco ASA",
                r"IOS-XE",
                r"IOS-XR",
                r"System image file is.*cisco",
            ],
            "prompt_patterns": [r"Router>", r"Switch>", r"Router#", r"Switch#", r"\S+\(config\)#"],
        },
        "huawei": {
            "platform_keywords": ["huawei", "vrp", "cloudengine", "s5700", "s6700", "ar"],
            "version_patterns": [
                r"Huawei Versatile Routing Platform",
                r"VRP \(R\) software",
                r"CloudEngine",
                r"HUAWEI.*Version",
            ],
            "prompt_patterns": [r"<.*>", r"\[.*\]", r"\[~.*\]"],
        },
        "h3c": {
            "platform_keywords": ["h3c", "comware", "s5120", "s5130", "msr"],
            "version_patterns": [r"H3C Comware", r"3Com Comware", r"H3C.*Version", r"Comware Software"],
            "prompt_patterns": [r"<.*>", r"\[.*\]"],
        },
        "juniper": {
            "platform_keywords": ["juniper", "junos", "srx", "mx", "ex"],
            "version_patterns": [r"JUNOS", r"Juniper Networks", r"junos-install"],
            "prompt_patterns": [r"\S+@\S+>", r"\S+@\S+#"],
        },
        "arista": {
            "platform_keywords": ["arista", "eos"],
            "version_patterns": [r"Arista DCS", r"Arista EOS"],
            "prompt_patterns": [r"\S+>", r"\S+#"],
        },
    }

    def __init__(self):
        """初始化品牌检测器"""
        self.logger = logger

    def detect_brand_from_host_info(self, host_data: dict) -> str | None:
        """从主机信息检测设备品牌

        Args:
            host_data: 主机数据字典，包含平台、品牌等信息

        Returns:
            检测到的品牌名称，如果无法识别则返回None
        """
        try:
            # 优先使用已知的品牌信息
            if "brand_name" in host_data and host_data["brand_name"]:
                brand = host_data["brand_name"].lower()
                if brand in self.BRAND_PATTERNS:
                    self.logger.debug(f"从host_data直接获取品牌: {brand}")
                    return brand

            # 从平台信息推断品牌
            if "platform" in host_data and host_data["platform"]:
                platform = host_data["platform"].lower()
                for brand, patterns in self.BRAND_PATTERNS.items():
                    if any(keyword in platform for keyword in patterns["platform_keywords"]):
                        self.logger.debug(f"从平台信息推断品牌: {brand} (platform: {platform})")
                        return brand

            # 从设备类型推断品牌
            if "device_type" in host_data and host_data["device_type"]:
                device_type = host_data["device_type"].lower()
                for brand, patterns in self.BRAND_PATTERNS.items():
                    if any(keyword in device_type for keyword in patterns["platform_keywords"]):
                        self.logger.debug(f"从设备类型推断品牌: {brand} (device_type: {device_type})")
                        return brand

            self.logger.warning("无法从主机信息检测设备品牌")
            return None

        except Exception as e:
            self.logger.error(f"品牌检测失败: {e}")
            return None

    def detect_brand_from_output(self, command_output: str, command: str = "") -> str | None:
        """从命令输出检测设备品牌

        Args:
            command_output: 命令输出文本
            command: 执行的命令（可选，用于上下文判断）

        Returns:
            检测到的品牌名称，如果无法识别则返回None
        """
        try:
            if not command_output:
                return None

            output_lower = command_output.lower()

            # 使用版本模式匹配
            for brand, patterns in self.BRAND_PATTERNS.items():
                for pattern in patterns["version_patterns"]:
                    if re.search(pattern, command_output, re.IGNORECASE):
                        self.logger.debug(f"从输出匹配到品牌: {brand} (pattern: {pattern})")
                        return brand

            # 使用关键词匹配
            for brand, patterns in self.BRAND_PATTERNS.items():
                for keyword in patterns["platform_keywords"]:
                    if keyword in output_lower:
                        self.logger.debug(f"从输出关键词匹配到品牌: {brand} (keyword: {keyword})")
                        return brand

            self.logger.warning(f"无法从命令输出检测设备品牌，输出长度: {len(command_output)}")
            return None

        except Exception as e:
            self.logger.error(f"从输出检测品牌失败: {e}")
            return None

    def detect_brand_comprehensive(
        self, host_data: dict, command_output: str = "", command: str = ""
    ) -> tuple[str | None, float]:
        """综合检测设备品牌

        Args:
            host_data: 主机数据
            command_output: 命令输出
            command: 执行的命令

        Returns:
            (品牌名称, 置信度分数)
        """
        try:
            # 尝试从主机信息检测
            brand_from_host = self.detect_brand_from_host_info(host_data)

            # 尝试从输出检测
            brand_from_output = None
            if command_output:
                brand_from_output = self.detect_brand_from_output(command_output, command)  # 综合判断
            if brand_from_host and brand_from_output:
                if brand_from_host == brand_from_output:
                    # 两种方式检测结果一致，高置信度
                    return brand_from_host, 0.95
                else:
                    # 检测结果不一致
                    self.logger.warning(f"品牌检测结果不一致: host={brand_from_host}, output={brand_from_output}")

                    # 如果主机信息来源于显式配置（如brand_name字段），优先使用主机信息
                    if "brand_name" in host_data or "brand" in host_data:
                        self.logger.info(f"主机信息中有明确的品牌配置，优先使用: {brand_from_host}")
                        return brand_from_host, 0.9
                    else:
                        # 否则使用输出检测结果
                        return brand_from_output, 0.7
            elif brand_from_host:
                # 仅从主机信息检测到
                return brand_from_host, 0.8
            elif brand_from_output:
                # 仅从输出检测到
                return brand_from_output, 0.85
            else:
                # 都没检测到
                return None, 0.0

        except Exception as e:
            self.logger.error(f"综合品牌检测失败: {e}")
            return None, 0.0

    def get_supported_brands(self) -> list[str]:
        """获取支持的品牌列表

        Returns:
            支持的品牌名称列表
        """
        return list(self.BRAND_PATTERNS.keys())

    def validate_brand(self, brand: str) -> bool:
        """验证品牌是否被支持

        Args:
            brand: 品牌名称

        Returns:
            是否支持该品牌
        """
        return brand.lower() in self.BRAND_PATTERNS if brand else False
