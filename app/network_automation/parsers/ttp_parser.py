"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: ttp_parser.py
@DateTime: 2025/06/23 15:50:00
@Docs: TTP解析器 - 使用TTP模板解析网络设备命令输出
"""

from typing import Any

from app.utils.logger import logger

from .template_manager import TemplateManager

try:
    from ttp import ttp  # type: ignore
except ImportError:
    ttp = None


class TTPParser:
    """TTP结构化解析器"""

    def __init__(self):
        """初始化TTP解析器"""
        self.logger = logger

        # 检查TTP依赖
        if ttp is None:
            self.logger.error("TTP库未安装，请运行: pip install ttp")
            raise ImportError("TTP库未安装")  # 初始化组件
        self.template_manager = TemplateManager()

        self.logger.info("TTP解析器初始化完成")

    def parse_command_output(
        self,
        command_output: str,
        command: str,
        brand: str,
        template_override: str | None = None,
    ) -> dict[str, Any]:
        """解析命令输出

        Args:
            command_output: 命令输出文本
            command: 执行的命令
            brand: 设备品牌（必需参数）
            template_override: 自定义模板内容（可选）

        Returns:
            结构化解析结果
        """
        try:
            self.logger.info(f"开始解析命令输出 - 命令: {command}, 品牌: {brand}")

            # 验证品牌是否支持
            if not self._validate_brand(brand):
                return self._create_fallback_result(command_output, command, brand, f"不支持的设备品牌: {brand}")

            # 获取模板
            template_content = self._get_template(command, brand, template_override)

            if not template_content:
                self.logger.warning(f"未找到适合的TTP模板 - 品牌: {brand}, 命令: {command}")
                return self._create_fallback_result(command_output, command, brand, "未找到模板")

            self.logger.info("获取到TTP模板")

            # 3. 执行TTP解析
            parsed_result = self._execute_ttp_parsing(command_output, template_content)

            # 4. 格式化结果
            formatted_result = self._format_result(parsed_result, command, brand)

            self.logger.info("TTP解析完成")
            return formatted_result

        except Exception as e:
            self.logger.error(f"TTP解析失败: {str(e)}")
            return self._create_fallback_result(command_output, command, brand or "unknown", str(e))

    def _validate_brand(self, brand: str) -> bool:
        """验证品牌是否支持

        Args:
            brand: 设备品牌

        Returns:
            是否支持该品牌
        """
        return brand.lower() in self.template_manager.get_supported_brands()

    def _get_template(self, command: str, brand: str, template_override: str | None = None) -> str | None:
        """获取TTP模板

        Args:
            command: 命令
            brand: 品牌
            template_override: 自定义模板内容

        Returns:
            模板内容
        """
        if template_override:
            return template_override

        # 根据命令推断命令类型
        command_type = self._infer_command_type(command)

        # 从模板管理器获取
        return self.template_manager.get_template_content(brand, command_type)

    def _execute_ttp_parsing(self, text_data: str, template_content: str) -> Any:
        """执行TTP解析

        Args:
            text_data: 要解析的文本数据
            template_content: TTP模板内容

        Returns:
            解析结果
        """
        try:
            # 创建TTP解析器实例
            parser = ttp(data=text_data, template=template_content)  # type: ignore

            # 执行解析
            parser.parse()

            # 获取结果
            results = parser.result()

            # TTP返回的是列表，通常我们需要第一个结果
            if results and len(results) > 0:
                # 如果模板有多个group，结果可能是多层嵌套
                parsed_result = results[0]

                # 处理单个结果的情况
                if isinstance(parsed_result, list) and len(parsed_result) == 1:
                    return parsed_result[0]
                else:
                    return parsed_result
            else:
                return {}

        except Exception as e:
            self.logger.error(f"TTP解析执行失败: {str(e)}")
            raise

    def _format_result(self, parsed_result: Any, command: str, brand: str) -> dict[str, Any]:
        """格式化解析结果

        Args:
            parsed_result: TTP解析结果
            command: 原始命令
            brand: 设备品牌

        Returns:
            格式化后的结果
        """
        # 基本元信息
        result = {
            "success": True,
            "command": command,
            "brand": brand,
            "parser": "ttp",
            "timestamp": None,  # 可以添加时间戳
            "data": parsed_result,
        }

        return result

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
            "parser": "ttp",
            "error": error,
            "raw_output": raw_output,
            "data": {},
        }

    def _infer_command_type(self, command: str) -> str:
        """根据命令推断命令类型

        Args:
            command: 命令字符串

        Returns:
            命令类型
        """
        command_lower = command.lower().strip()

        # 版本信息命令
        if "version" in command_lower or "dis ver" in command_lower or "display version" in command_lower:
            return "show_version"

        # 接口信息命令
        if (
            "interface" in command_lower
            or "int" in command_lower
            or "dis int" in command_lower
            or "display interface" in command_lower
        ):
            return "show_interface"

        # 路由信息命令
        if (
            "route" in command_lower
            or "ip route" in command_lower
            or "dis ip route" in command_lower
            or "display ip routing" in command_lower
        ):
            return "show_route"

        # ARP表命令
        if "arp" in command_lower or "dis arp" in command_lower or "display arp" in command_lower:
            return "show_arp"

        # MAC地址表命令
        if "mac" in command_lower or "dis mac" in command_lower or "display mac-address" in command_lower:
            return "show_mac"

        # 默认类型
        return "generic"

    def validate_template(self, template_content: str, test_data: str | None = None) -> dict[str, Any]:
        """验证TTP模板

        Args:
            template_content: 模板内容
            test_data: 测试数据（可选）

        Returns:
            验证结果
        """
        try:
            # 基础语法验证
            parser = ttp(template=template_content)  # type: ignore

            result = {"valid": True, "template_info": {}, "test_result": None, "errors": []}

            # 如果提供了测试数据，执行测试解析
            if test_data:
                parser = ttp(data=test_data, template=template_content)  # type: ignore
                parser.parse()
                test_results = parser.result()
                result["test_result"] = test_results

            return result

        except Exception as e:
            return {"valid": False, "errors": [str(e)]}

    def get_supported_brands(self) -> list[str]:
        """获取支持的品牌列表

        Returns:
            品牌列表
        """
        return self.template_manager.get_supported_brands()

    def get_supported_commands(self, brand: str | None = None) -> list[str]:
        """获取支持的命令列表

        Args:
            brand: 品牌（可选）

        Returns:
            命令列表
        """
        if brand:
            return self.template_manager.get_supported_commands(brand)
        else:
            # 如果没有指定品牌，返回所有支持的命令类型
            all_commands = []
            for b in self.template_manager.get_supported_brands():
                all_commands.extend(self.template_manager.get_supported_commands(b))
            return list(set(all_commands))  # 去重

    def batch_parse(self, batch_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量解析

        Args:
            batch_data: 批量数据，每个元素包含 {output, command, brand, template_override?}

        Returns:
            批量解析结果
        """
        results = []

        for item in batch_data:
            try:
                result = self.parse_command_output(
                    command_output=item["output"],
                    command=item["command"],
                    brand=item["brand"],  # 必需参数
                    template_override=item.get("template_override"),
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
