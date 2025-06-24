"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: hybrid_parser.py
@DateTime: 2025/06/24 14:00:00
@Docs: 混合解析器 - 集成TextFSM + 自定义模板 + 回退策略
"""

import re
from typing import Any

from app.utils.logger import logger

try:
    import textfsm
    from ntc_templates.parse import parse_output

    TEXTFSM_AVAILABLE = True
except ImportError:
    textfsm = None
    parse_output = None
    TEXTFSM_AVAILABLE = False

# 导入自定义模板管理器
try:
    from app.network_automation.parsers.custom_template_manager import custom_template_manager

    CUSTOM_TEMPLATE_AVAILABLE = True
except ImportError:
    custom_template_manager = None
    CUSTOM_TEMPLATE_AVAILABLE = False


class HybridTextFSMParser:
    """混合TextFSM解析器 - 支持NTC-Templates + 多平台fallback + 回退策略"""

    def __init__(self):
        """初始化混合解析器"""
        self.logger = logger

        # 检查依赖
        if not TEXTFSM_AVAILABLE:
            self.logger.warning("TextFSM或NTC-Templates库未安装，将使用回退解析")  # 品牌映射策略（支持多个fallback）
        self.brand_mapping_strategies = {
            "h3c": ["hp_comware", "huawei_vrp", "hp_procurve"],  # H3C优先使用hp_comware，支持多种fallback
            "huawei": ["huawei_vrp", "huawei", "cisco_ios"],  # 华为VRP系统
            "cisco": ["cisco_ios", "cisco_nxos", "cisco_xe"],  # Cisco多版本支持
            "hp": ["hp_comware", "hp_procurve", "aruba_procurve"],  # HP多产品线
            "arista": ["arista_eos"],
            "juniper": ["juniper_junos"],
            "extreme": ["extreme_exos", "extreme_slxos"],
            "dell": ["dell_os10", "dell_powerconnect", "broadcom_icos"],
            "netgear": ["broadcom_icos"],
            "zyxel": ["zyxel_zysh"],
            "dlink": ["broadcom_icos"],
            # 添加更多厂商支持
            "fortinet": ["fortinet"],
            "paloalto": ["paloalto_panos"],
            "checkpoint": ["checkpoint_gaia"],
        }

        self.logger.info("混合TextFSM解析器初始化完成")

    def parse_command_output(
        self, command_output: str, command: str, brand: str, use_ntc_first: bool = True
    ) -> dict[str, Any]:
        """解析命令输出 - 混合策略

        Args:
            command_output: 命令输出文本
            command: 执行的命令
            brand: 设备品牌
            use_ntc_first: 是否优先使用NTC-Templates

        Returns:
            结构化解析结果
        """
        try:
            self.logger.info(f"开始混合解析 - 命令: {command}, 品牌: {brand}")

            # 策略1: 优先尝试自定义模板
            if CUSTOM_TEMPLATE_AVAILABLE and custom_template_manager:
                custom_result = self._try_custom_templates(command_output, command, brand)
                if custom_result["success"]:
                    return custom_result

            # 策略2: 优先尝试NTC-Templates（多平台fallback）
            if use_ntc_first and TEXTFSM_AVAILABLE:
                ntc_result = self._try_ntc_templates(command_output, command, brand)
                if ntc_result["success"]:
                    return ntc_result

            # 策略3: 正则表达式回退解析
            regex_result = self._try_regex_fallback(command_output, command, brand)
            if regex_result["success"]:
                return regex_result

            # 策略4: 如果之前没试过NTC-Templates，现在试试
            if not use_ntc_first and TEXTFSM_AVAILABLE:
                ntc_result = self._try_ntc_templates(command_output, command, brand)
                if ntc_result["success"]:
                    return ntc_result

            # 策略5: 返回原始输出
            return self._create_fallback_result(command_output, command, brand, "所有解析策略都失败，返回原始输出")

        except Exception as e:
            self.logger.error(f"混合解析失败: {str(e)}")
            return self._create_fallback_result(command_output, command, brand, str(e))

    def _try_custom_templates(self, output: str, command: str, brand: str) -> dict[str, Any]:
        """尝试自定义模板解析"""
        if not CUSTOM_TEMPLATE_AVAILABLE or not custom_template_manager:
            return {"success": False, "error": "自定义模板管理器不可用"}

        try:
            # 查找匹配的自定义模板
            template_path = custom_template_manager.find_custom_template(brand, command)
            if not template_path:
                return {"success": False, "error": "未找到匹配的自定义模板"}

            # 使用自定义模板解析
            parsed_data = custom_template_manager.parse_with_custom_template(output, template_path)

            if parsed_data:  # 解析成功且有数据
                return {
                    "success": True,
                    "command": command,
                    "brand": brand,
                    "platform": "custom",
                    "parser": "custom_template",
                    "template_path": template_path,
                    "data": parsed_data,
                    "data_count": len(parsed_data) if isinstance(parsed_data, list) else 1,
                }
            else:
                return {"success": False, "error": "自定义模板解析无数据"}

        except Exception as e:
            self.logger.debug(f"自定义模板解析失败: {str(e)}")
            return {"success": False, "error": f"自定义模板解析失败: {str(e)}"}

    def _try_ntc_templates(self, output: str, command: str, brand: str) -> dict[str, Any]:
        """尝试NTC-Templates解析（多平台fallback）"""
        if not TEXTFSM_AVAILABLE or parse_output is None:
            return {"success": False, "error": "NTC-Templates不可用"}

        platforms = self.brand_mapping_strategies.get(brand.lower(), ["cisco_ios"])

        for platform in platforms:
            try:
                self.logger.debug(f"尝试平台: {platform}")
                parsed_data = parse_output(platform=platform, command=command, data=output)

                if parsed_data:  # 解析成功且有数据
                    return {
                        "success": True,
                        "command": command,
                        "brand": brand,
                        "platform": platform,
                        "parser": "ntc_templates",
                        "data": parsed_data,
                        "data_count": len(parsed_data) if isinstance(parsed_data, list) else 1,
                    }

            except Exception as e:
                self.logger.debug(f"平台 {platform} 解析失败: {str(e)}")
                continue

        return {"success": False, "error": "所有NTC-Templates平台都解析失败"}

    def _try_regex_fallback(self, output: str, command: str, brand: str) -> dict[str, Any]:
        """正则表达式回退解析"""
        try:
            # 根据命令类型选择回退解析策略
            if "mac" in command.lower() and "address" in command.lower():
                return self._parse_mac_table_regex(output, command, brand)
            elif "interface" in command.lower() and "brief" in command.lower():
                return self._parse_interface_brief_regex(output, command, brand)
            elif "vlan" in command.lower():
                return self._parse_vlan_regex(output, command, brand)
            elif "arp" in command.lower():
                return self._parse_arp_regex(output, command, brand)
            else:
                return {"success": False, "error": "没有匹配的回退解析策略"}

        except Exception as e:
            return {"success": False, "error": f"正则回退解析失败: {str(e)}"}

    def _parse_mac_table_regex(self, output: str, command: str, brand: str) -> dict[str, Any]:
        """MAC地址表正则解析"""
        data = []

        # H3C MAC地址表格式: MAC-Address    VLAN    Type   Port              Aging
        if brand.lower() == "h3c":
            pattern = r"([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)"
            matches = re.findall(pattern, output)

            for match in matches:
                data.append({"mac": match[0], "vlan": match[1], "type": match[2], "port": match[3], "aging": match[4]})

        # 华为格式
        elif brand.lower() == "huawei":
            pattern = r"([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})\s+(\d+)\s+(\S+)\s+(\S+)"
            matches = re.findall(pattern, output)

            for match in matches:
                data.append({"mac": match[0], "vlan": match[1], "type": match[2], "port": match[3]})

        # Cisco格式 (xxxx.xxxx.xxxx)
        elif brand.lower() == "cisco":
            pattern = r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+(\d+)\s+(\S+)\s+(\S+)"
            matches = re.findall(pattern, output)

            for match in matches:
                data.append({"mac": match[0], "vlan": match[1], "type": match[2], "port": match[3]})

        return {
            "success": bool(data),
            "command": command,
            "brand": brand,
            "parser": "regex_fallback",
            "data": data,
            "data_count": len(data),
        }

    def _parse_interface_brief_regex(self, output: str, command: str, brand: str) -> dict[str, Any]:
        """接口简要信息正则解析"""
        data = []

        # 通用接口简要格式
        pattern = r"(\S+)\s+(up|down|admin-down|administratively\s+down)\s+(up|down)\s*(.*)"
        matches = re.findall(pattern, output, re.IGNORECASE)

        for match in matches:
            data.append(
                {
                    "interface": match[0],
                    "link": match[1].replace(" ", "-"),  # 标准化状态
                    "protocol": match[2],
                    "description": match[3].strip(),
                }
            )

        return {
            "success": bool(data),
            "command": command,
            "brand": brand,
            "parser": "regex_fallback",
            "data": data,
            "data_count": len(data),
        }

    def _parse_vlan_regex(self, output: str, command: str, brand: str) -> dict[str, Any]:
        """VLAN信息正则解析"""
        data = []

        # H3C VLAN格式
        if brand.lower() == "h3c":
            # 匹配 "VLAN ID: 1" 这种格式
            vlan_blocks = re.split(r"VLAN ID:\s*(\d+)", output)[1:]  # 去掉第一个空元素
            for i in range(0, len(vlan_blocks), 2):
                if i + 1 < len(vlan_blocks):
                    vlan_id = vlan_blocks[i]
                    vlan_info = vlan_blocks[i + 1]

                    # 提取VLAN名称和状态
                    name_match = re.search(r"VLAN Name:\s*(\S+)", vlan_info)
                    status_match = re.search(r"VLAN Status:\s*(\S+)", vlan_info)

                    data.append(
                        {
                            "vlan_id": vlan_id,
                            "name": name_match.group(1) if name_match else "default",
                            "status": status_match.group(1) if status_match else "unknown",
                        }
                    )

        # 通用VLAN表格格式
        else:
            pattern = r"(\d+)\s+(\S+)\s+(active|inactive|suspend)\s*(.*)"
            matches = re.findall(pattern, output, re.IGNORECASE)

            for match in matches:
                data.append({"vlan_id": match[0], "name": match[1], "status": match[2], "ports": match[3].strip()})

        return {
            "success": bool(data),
            "command": command,
            "brand": brand,
            "parser": "regex_fallback",
            "data": data,
            "data_count": len(data),
        }

    def _parse_arp_regex(self, output: str, command: str, brand: str) -> dict[str, Any]:
        """ARP表正则解析"""
        data = []

        # 通用ARP格式: IP地址 - MAC地址 - 接口
        if brand.lower() in ["h3c", "huawei"]:
            pattern = r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})\s+(\S+)"
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                data.append({"ip": match[0], "mac": match[1], "interface": match[2]})
        else:  # Cisco等
            # 支持两种格式: 1. IP MAC(冒号分隔) 接口 2. IP MAC(点分隔) 接口
            pattern_colon = r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})\s+(\S+)"
            pattern_dot = r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+(\S+)"
            matches_colon = re.findall(pattern_colon, output, re.IGNORECASE)
            matches_dot = re.findall(pattern_dot, output, re.IGNORECASE)
            for match in matches_colon:
                data.append({"ip": match[0], "mac": match[1], "interface": match[2]})
            for match in matches_dot:
                data.append({"ip": match[0], "mac": match[1], "interface": match[2]})

        return {
            "success": bool(data),
            "command": command,
            "brand": brand,
            "parser": "regex_fallback",
            "data": data,
            "data_count": len(data),
        }

    def _create_fallback_result(self, raw_output: str, command: str, brand: str, error: str) -> dict[str, Any]:
        """创建回退结果"""
        return {
            "success": False,
            "command": command,
            "brand": brand,
            "parser": "fallback",
            "error": error,
            "raw_output": raw_output[:1000] + "..." if len(raw_output) > 1000 else raw_output,
            "data": [],
        }

    async def get_parsing_strategies(self) -> dict[str, Any]:
        """获取解析策略信息"""
        # 获取动态支持的命令
        dynamic_commands = (
            await self._get_supported_commands_from_config_templates()
        )  # 从动态命令中提取所有唯一的命令，作为总体支持的命令列表
        all_supported_commands = set()
        for commands in dynamic_commands.values():
            all_supported_commands.update(commands)

        # 如果没有从配置模板获取到命令，提供基础的备选命令
        if not all_supported_commands:
            fallback_commands = [
                "display mac-address",
                "show mac address-table",
                "display interface brief",
                "show ip interface brief",
                "display vlan",
                "show vlan",
                "display arp",
                "show arp",
            ]
            all_supported_commands.update(fallback_commands)

        # 构建策略信息
        strategies = {
            "textfsm_available": TEXTFSM_AVAILABLE,
            "custom_template_available": CUSTOM_TEMPLATE_AVAILABLE,
            "supported_brands": list(self.brand_mapping_strategies.keys()),
            "brand_strategies": self.brand_mapping_strategies,
            "parsing_order": [
                "1. 自定义模板（优先级最高）",
                "2. NTC-Templates (多平台fallback)",
                "3. 正则表达式回退解析",
                "4. 原始输出",
            ],
            "supported_commands": sorted(all_supported_commands),
            "dynamic_commands_by_brand": dynamic_commands,
            "commands_source": "config_templates" if dynamic_commands else "fallback",
        }

        # 添加自定义模板统计信息
        if CUSTOM_TEMPLATE_AVAILABLE and custom_template_manager:
            try:
                custom_stats = custom_template_manager.get_template_stats()
                strategies["custom_template_stats"] = custom_stats
            except Exception as e:
                self.logger.warning(f"获取自定义模板统计失败: {str(e)}")

        return strategies

    def test_parsing(self, sample_outputs: dict[str, Any]) -> dict[str, Any]:
        """测试解析功能

        Args:
            sample_outputs: 测试样本 {"command": {"output": "...", "brand": "..."}}

        Returns:
            测试结果
        """
        results = {}

        for command, sample in sample_outputs.items():
            try:
                result = self.parse_command_output(
                    command_output=sample["output"], command=command, brand=sample["brand"]
                )
                results[command] = {
                    "success": result["success"],
                    "parser_used": result.get("parser", "unknown"),
                    "data_count": result.get("data_count", 0),
                    "error": result.get("error"),
                }
            except Exception as e:
                results[command] = {"success": False, "error": str(e)}

        return results

    async def _get_supported_commands_from_config_templates(self) -> dict[str, list[str]]:
        """从配置模板中获取支持的命令

        Returns:
            品牌和命令的映射关系 {"h3c": ["display mac-address", "display interface"], ...}
        """
        try:
            # 使用配置模板服务来获取命令映射
            from app.services.config_template_service import ConfigTemplateService

            config_service = ConfigTemplateService()
            brand_commands = await config_service.get_parsing_commands_by_brand()

            self.logger.info(
                f"从配置模板获取支持命令成功: "
                f"{len(brand_commands)} 个品牌, "
                f"{sum(len(cmds) for cmds in brand_commands.values())} 个命令"
            )

            return brand_commands

        except Exception as e:
            self.logger.warning(f"从配置模板获取支持命令失败: {str(e)}")

            # 回退到原来的数据库查询方式
            try:
                return await self._fallback_get_commands_from_db()
            except Exception as fallback_error:
                self.logger.error(f"回退方式获取命令也失败: {str(fallback_error)}")
                return {}

    async def _fallback_get_commands_from_db(self) -> dict[str, list[str]]:
        """回退方式：直接从数据库获取命令（保留原有逻辑）"""
        from app.models.network_models import TemplateCommand

        # 查询所有活跃的模板命令，预加载关联的品牌和配置模板
        template_commands = (
            await TemplateCommand.filter(config_template__is_active=True, is_deleted=False)
            .prefetch_related("brand", "config_template")
            .all()
        )

        # 按品牌分组命令
        brand_commands = {}
        for cmd in template_commands:
            brand_name = cmd.brand.name.lower()
            template_name = cmd.config_template.name

            if brand_name not in brand_commands:
                brand_commands[brand_name] = []

            # 从Jinja2模板内容中提取命令（简化版）
            if cmd.jinja_content:
                # 提取命令行（假设模板第一行是命令）
                lines = cmd.jinja_content.strip().split("\n")
                if lines:
                    command = lines[0].strip()
                    # 移除Jinja2语法
                    import re

                    command = re.sub(r"\{\{.*?\}\}", "", command).strip()
                    if command and command not in brand_commands[brand_name]:
                        brand_commands[brand_name].append(command)

            # 如果没有提取到命令，使用模板名称作为备选
            if template_name not in brand_commands[brand_name]:
                brand_commands[brand_name].append(template_name)

        return brand_commands


# 全局解析器实例
hybrid_parser = HybridTextFSMParser()
