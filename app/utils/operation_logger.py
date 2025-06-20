"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_logger.py
@DateTime: 2025/06/20 00:00:00
@Docs: 操作日志装饰器工具
"""

import asyncio
import inspect
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.models.network_models import OperationLog, OperationStatusEnum
from app.utils.logger import logger


class OperationContext:
    """操作上下文管理器

    用于在请求处理过程中传递操作者身份信息
    """

    _context: dict[str, Any] = {}

    @classmethod
    def set_operator(cls, operator_id: str, operator_type: str = "system", **kwargs) -> None:
        """设置操作者信息

        Args:
            operator_id: 操作者标识
            operator_type: 操作者类型 (system|api|admin|external)
            **kwargs: 其他操作者信息
        """
        cls._context.update(
            {"operator_id": operator_id, "operator_type": operator_type, "timestamp": datetime.now(), **kwargs}
        )

    @classmethod
    def get_operator(cls) -> str:
        """获取当前操作者标识

        Returns:
            操作者标识字符串
        """
        if not cls._context:
            # 使用配置文件中的默认操作者
            return settings.DEFAULT_OPERATOR

        operator_id = cls._context.get("operator_id", "unknown")
        operator_type = cls._context.get("operator_type", "system")

        # 构建操作者标识
        if operator_type == "system":
            return f"system:{operator_id}"
        elif operator_type == "api":
            return f"api:{operator_id}"
        elif operator_type == "admin":
            return f"admin:{operator_id}"
        else:
            return f"{operator_type}:{operator_id}"

    @classmethod
    def get_context(cls) -> dict[str, Any]:
        """获取完整的操作上下文"""
        return cls._context.copy()

    @classmethod
    def clear(cls) -> None:
        """清空操作上下文"""
        cls._context.clear()


def operation_log(
    operation_description: str = "",
    auto_save: bool = True,
    include_args: bool = False,
    include_result: bool = False,
    template_id: UUID | None = None,
    device_id: UUID | None = None,
) -> Callable:
    """操作日志装饰器

    Args:
        operation_description: 操作描述
        auto_save: 是否自动保存日志到数据库
        include_args: 是否记录函数参数
        include_result: 是否记录函数返回结果
        template_id: 关联的模板ID
        device_id: 关联的设备ID
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 检查是否启用操作日志
            if not settings.ENABLE_OPERATION_LOG:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # 获取操作者信息
            operator = OperationContext.get_operator()
            start_time = datetime.now()

            # 构建操作描述
            func_name = func.__name__
            description = operation_description or f"执行函数: {func_name}"

            # 记录函数参数（如果需要）
            function_args = {}
            if include_args:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                function_args = dict(bound_args.arguments)
                # 过滤敏感信息
                function_args = _filter_sensitive_data(function_args)

            log_data = {
                "device_id": device_id,
                "template_id": template_id,
                "command_executed": description,
                "executed_by": operator,
                "timestamp": start_time,
                "status": OperationStatusEnum.PENDING,
                "parsed_output": {
                    "function": func_name,
                    "args": function_args,
                    "context": OperationContext.get_context(),
                },
            }

            try:
                # 执行原函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 计算执行时间
                execution_time = (datetime.now() - start_time).total_seconds()

                # 更新日志数据
                log_data.update(
                    {
                        "status": OperationStatusEnum.SUCCESS,
                        "output_received": f"操作成功完成，耗时: {execution_time:.2f}秒",
                    }
                )

                # 记录返回结果（如果需要）
                if include_result and result is not None:
                    log_data["parsed_output"]["result"] = _serialize_result(result)

                logger.info(f"操作成功: {description} | 操作者: {operator} | 耗时: {execution_time:.2f}秒")

                return result

            except Exception as e:
                # 记录错误信息
                log_data.update(
                    {
                        "status": OperationStatusEnum.FAILURE,
                        "error_message": str(e),
                        "output_received": f"操作失败: {str(e)}",
                    }
                )

                logger.error(f"操作失败: {description} | 操作者: {operator} | 错误: {str(e)}")
                raise

            finally:
                # 保存操作日志
                if auto_save:
                    try:
                        await _save_operation_log(log_data)
                    except Exception as save_error:
                        logger.error(f"保存操作日志失败: {save_error}")

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 检查是否启用操作日志
            if not settings.ENABLE_OPERATION_LOG:
                return func(*args, **kwargs)

            # 同步函数的包装器
            operator = OperationContext.get_operator()
            start_time = datetime.now()

            func_name = func.__name__
            description = operation_description or f"执行函数: {func_name}"

            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"操作成功: {description} | 操作者: {operator} | 耗时: {execution_time:.2f}秒")
                return result
            except Exception as e:
                logger.error(f"操作失败: {description} | 操作者: {operator} | 错误: {str(e)}")
                raise

        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _save_operation_log(log_data: dict[str, Any]) -> None:
    """保存操作日志到数据库

    Args:
        log_data: 日志数据
    """
    try:
        await OperationLog.create(**log_data)
    except Exception as e:
        logger.error(f"保存操作日志到数据库失败: {e}")


def _filter_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """过滤敏感数据

    Args:
        data: 原始数据

    Returns:
        过滤后的数据
    """
    sensitive_keys = ["password", "secret", "token", "key", "credential"]
    filtered = {}

    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            filtered[key] = "***已隐藏***"
        elif isinstance(value, dict):
            filtered[key] = _filter_sensitive_data(value)
        else:
            filtered[key] = str(value)[:100]  # 限制长度

    return filtered


def _serialize_result(result: Any) -> Any:
    """序列化函数返回结果

    Args:
        result: 函数返回结果

    Returns:
        可序列化的结果
    """
    try:
        if hasattr(result, "dict"):  # Pydantic模型
            return result.dict()
        elif isinstance(result, list | dict | str | int | float | bool):
            return result
        else:
            return str(result)[:200]  # 限制长度
    except Exception:
        return f"<{type(result).__name__} 对象>"


# 便捷的操作者设置函数
def set_system_operator(operation_id: str = "auto_task") -> None:
    """设置系统操作者"""
    OperationContext.set_operator(operation_id, "system")


def set_api_operator(api_key: str = "external_api", source: str = "unknown") -> None:
    """设置API操作者"""
    OperationContext.set_operator(api_key, "api", source=source)


def set_admin_operator(admin_id: str = "admin_user") -> None:
    """设置管理员操作者"""
    OperationContext.set_operator(admin_id, "admin")


def set_external_operator(external_id: str, system_name: str = "external_system") -> None:
    """设置外部系统操作者"""
    OperationContext.set_operator(external_id, "external", system_name=system_name)


# 常用的操作者身份预设
class CommonOperators:
    """常用操作者身份预设"""

    SYSTEM_SCHEDULER = "system:scheduler"  # 系统调度器
    SYSTEM_MONITOR = "system:monitor"  # 系统监控
    SYSTEM_BACKUP = "system:backup"  # 系统备份
    API_EXTERNAL = "api:external"  # 外部API调用
    API_WEBHOOK = "api:webhook"  # Webhook调用
    ADMIN_DEFAULT = "admin:default"  # 默认管理员
    MANUAL_OPERATION = "manual:operator"  # 手动操作
