"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: textfsm_parser.py
@DateTime: 2025/06/23 17:00:00
@Docs: TextFSM解析器 - 使用TextFSM + NTC-Templates进行网络设备命令输出解析
"""

from typing import Any

from app.utils.logger import logger

try:
    import textfsm
    from ntc_templates.parse import parse_output
except ImportError:
    textfsm = None
    parse_output = None


class TextFSMParser:
    """TextFSM结构化解析器"""

    def __init__(self):
        """初始化TextFSM解析器"""
        self.logger = logger

        # 检查依赖
        if textfsm is None or parse_output is None:
            self.logger.error("TextFSM或NTC-Templates库未安装，请运行: pip install textfsm ntc-templates")
            raise ImportError("TextFSM相关库未安装")

        self.logger.info("TextFSM解析器初始化完成")

    def parse_command_output(
        self,
        command_output: str,
        command: str,
        brand: str,
    ) -> dict[str, Any]:
        """解析命令输出

        Args:
            command_output: 命令输出文本
            command: 执行的命令
            brand: 设备品牌

        Returns:
            结构化解析结果
        """
        try:
            self.logger.info(f"开始TextFSM解析 - 命令: {command}, 品牌: {brand}")

            # 映射品牌到NTC-Templates平台名称
            platform = self._map_brand_to_platform(brand)

            # 检查parse_output是否可用
            if parse_output is None:
                raise ImportError("NTC-Templates库未正确安装，无法进行解析。")

            # 使用NTC-Templates解析
            parsed_data = parse_output(platform=platform, command=command, data=command_output)

            # 格式化结果
            result = {
                "success": True,
                "command": command,
                "brand": brand,
                "platform": platform,
                "parser": "textfsm",
                "data": parsed_data,
                "data_count": len(parsed_data) if isinstance(parsed_data, list) else 1,
            }

            self.logger.info(f"TextFSM解析完成 - 解析出 {result['data_count']} 条记录")
            return result

        except Exception as e:
            self.logger.error(f"TextFSM解析失败: {str(e)}")
            return self._create_fallback_result(command_output, command, brand, str(e))

    def _map_brand_to_platform(self, brand: str) -> str:
        """映射品牌到NTC-Templates平台名称

        Args:
            brand: 设备品牌

        Returns:
            NTC-Templates平台名称
        """
        brand_mapping = {
            "cisco": "cisco_ios",
            "huawei": "huawei",
            "h3c": "hp_comware",
        }

        return brand_mapping.get(brand.lower(), "cisco_ios")

    def _create_fallback_result(self, raw_output: str, command: str, brand: str, error: str) -> dict[str, Any]:
        """创建回退结果（解析失败时）

        Args:
            raw_output: 原始输出
            command: 命令
            brand: 品牌
            error: 错误信息

        Returns:
            回退结果
        """
        return {
            "success": False,
            "command": command,
            "brand": brand,
            "parser": "textfsm",
            "error": error,
            "raw_output": raw_output,
            "data": [],
        }

    def get_supported_brands(self) -> list[str]:
        """获取支持的品牌列表

        Returns:
            品牌列表
        """
        return ["cisco", "huawei", "h3c"]

    def batch_parse(self, batch_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量解析

        Args:
            batch_data: 批量数据，每个元素包含 {output, command, brand}

        Returns:
            批量解析结果
        """
        results = []

        for item in batch_data:
            try:
                result = self.parse_command_output(
                    command_output=item["output"],
                    command=item["command"],
                    brand=item["brand"],
                )
                results.append(result)
            except Exception as e:
                error_result = self._create_fallback_result(
                    raw_output=item.get("output", ""),
                    command=item.get("command", ""),
                    brand=item.get("brand", "unknown"),
                    error=str(e),
                )
                results.append(error_result)

        return results
