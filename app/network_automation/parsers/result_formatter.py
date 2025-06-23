"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: result_formatter.py
@DateTime: 2025/06/23 15:55:00
@Docs: 解析结果格式化器 - 将TTP解析结果转换为标准JSON格式
"""

from typing import Any

from app.utils.logger import logger


class ResultFormatter:
    """解析结果格式化器"""

    def __init__(self):
        """初始化结果格式化器"""
        self.logger = logger

    def format_parse_result(self, parse_result: dict[str, Any], format_type: str = "standard") -> dict[str, Any]:
        """格式化解析结果

        Args:
            parse_result: TTP解析器返回的原始结果
            format_type: 格式化类型 (standard/compact/detailed)

        Returns:
            格式化后的结果
        """
        try:
            if format_type == "standard":
                return self._format_standard(parse_result)
            elif format_type == "compact":
                return self._format_compact(parse_result)
            elif format_type == "detailed":
                return self._format_detailed(parse_result)
            else:
                self.logger.warning(f"未知的格式化类型: {format_type}, 使用标准格式")
                return self._format_standard(parse_result)

        except Exception as e:
            self.logger.error(f"结果格式化失败: {e}")
            return self._create_error_result(str(e))

    def _format_standard(self, parse_result: dict[str, Any]) -> dict[str, Any]:
        """标准格式化

        Args:
            parse_result: 原始解析结果

        Returns:
            标准格式化结果
        """
        formatted_result = {
            "success": parse_result.get("success", False),
            "data": parse_result.get("parsed_data"),
            "metadata": {
                "command": parse_result.get("command"),
                "brand": parse_result.get("metadata", {}).get("brand"),
                "parse_method": parse_result.get("metadata", {}).get("parse_method"),
                "timestamp": self._get_current_timestamp(),
            },
        }

        # 添加错误信息（如果有）
        if "error" in parse_result:
            formatted_result["error"] = parse_result["error"]

        return formatted_result

    def _format_compact(self, parse_result: dict[str, Any]) -> dict[str, Any]:
        """紧凑格式化 - 仅返回关键数据

        Args:
            parse_result: 原始解析结果

        Returns:
            紧凑格式化结果
        """
        if parse_result.get("success", False):
            return {"success": True, "data": parse_result.get("parsed_data")}
        else:
            return {"success": False, "error": parse_result.get("error", "解析失败")}

    def _format_detailed(self, parse_result: dict[str, Any]) -> dict[str, Any]:
        """详细格式化 - 包含所有信息

        Args:
            parse_result: 原始解析结果

        Returns:
            详细格式化结果
        """
        formatted_result = {
            "success": parse_result.get("success", False),
            "data": parse_result.get("parsed_data"),
            "raw_output": parse_result.get("raw_output"),
            "metadata": {
                "command": parse_result.get("command"),
                "brand": parse_result.get("metadata", {}).get("brand"),
                "command_type": parse_result.get("metadata", {}).get("command_type"),
                "template_used": parse_result.get("metadata", {}).get("template_used"),
                "parse_method": parse_result.get("metadata", {}).get("parse_method"),
                "confidence": parse_result.get("metadata", {}).get("confidence"),
                "timestamp": self._get_current_timestamp(),
            },
        }

        # 添加错误信息（如果有）
        if "error" in parse_result:
            formatted_result["error"] = parse_result["error"]

        return formatted_result

    def format_batch_results(
        self, batch_results: list[dict[str, Any]], format_type: str = "standard"
    ) -> list[dict[str, Any]]:
        """批量格式化解析结果

        Args:
            batch_results: 批量解析结果列表
            format_type: 格式化类型

        Returns:
            格式化后的结果列表
        """
        formatted_results = []

        for result in batch_results:
            formatted_result = self.format_parse_result(result, format_type)

            # 保持请求ID
            if "request_id" in result:
                formatted_result["request_id"] = result["request_id"]

            formatted_results.append(formatted_result)

        return formatted_results

    def create_summary_report(self, batch_results: list[dict[str, Any]]) -> dict[str, Any]:
        """创建批量解析的汇总报告

        Args:
            batch_results: 批量解析结果

        Returns:
            汇总报告
        """
        try:
            total_count = len(batch_results)
            success_count = sum(1 for r in batch_results if r.get("success", False))
            failure_count = total_count - success_count

            # 统计品牌分布
            brand_stats = {}
            parse_method_stats = {}

            for result in batch_results:
                metadata = result.get("metadata", {})

                # 品牌统计
                brand = metadata.get("brand")
                if brand:
                    brand_stats[brand] = brand_stats.get(brand, 0) + 1

                # 解析方法统计
                parse_method = metadata.get("parse_method")
                if parse_method:
                    parse_method_stats[parse_method] = parse_method_stats.get(parse_method, 0) + 1

            # 收集错误信息
            errors = []
            for result in batch_results:
                if not result.get("success", False) and "error" in result:
                    errors.append(
                        {
                            "request_id": result.get("request_id"),
                            "command": result.get("command"),
                            "error": result["error"],
                        }
                    )

            return {
                "summary": {
                    "total_count": total_count,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "success_rate": round(success_count / total_count * 100, 2) if total_count > 0 else 0,
                },
                "statistics": {"brand_distribution": brand_stats, "parse_method_distribution": parse_method_stats},
                "errors": errors[:10],  # 仅显示前10个错误
                "timestamp": self._get_current_timestamp(),
            }

        except Exception as e:
            self.logger.error(f"创建汇总报告失败: {e}")
            return self._create_error_result(str(e))

    def _create_error_result(self, error_message: str) -> dict[str, Any]:
        """创建错误结果

        Args:
            error_message: 错误消息

        Returns:
            错误结果字典
        """
        return {"success": False, "error": error_message, "timestamp": self._get_current_timestamp()}

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳

        Returns:
            ISO格式时间戳字符串
        """
        from datetime import datetime

        return datetime.now().isoformat()

    def export_to_json(self, data: dict[str, Any] | list[dict[str, Any]], filename: str | None = None) -> str:
        """导出为JSON文件

        Args:
            data: 要导出的数据
            filename: 文件名，如果不提供则自动生成

        Returns:
            导出的文件路径
        """
        import json
        from pathlib import Path

        try:
            if not filename:
                timestamp = self._get_current_timestamp().replace(":", "-")
                filename = f"parse_results_{timestamp}.json"

            # 确保文件有.json扩展名
            if not filename.endswith(".json"):
                filename += ".json"

            # 创建输出目录
            output_dir = Path("logs/parse_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            # 输出文件路径
            output_path = output_dir / filename

            # 写入JSON文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"解析结果已导出: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"导出JSON失败: {e}")
            raise

    def validate_result_structure(self, result: dict[str, Any]) -> bool:
        """验证结果结构是否有效

        Args:
            result: 要验证的结果

        Returns:
            是否有效
        """
        try:
            required_fields = ["success"]

            for field in required_fields:
                if field not in result:
                    return False

            # 如果成功，应该有data字段
            if result.get("success", False) and "data" not in result:
                return False

            return True

        except Exception:
            return False
