"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_logger.py
@DateTime: 2025/01/20 10:00:00
@Docs: 网络自动化专用日志装饰器和工具函数
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from app.utils.logger import logger


def log_network_operation(
    operation_type: str, include_args: bool = False, include_result: bool = False, log_level: str = "INFO"
):
    """网络操作日志装饰器

    专门用于记录网络自动化操作的日志，包含设备信息、操作类型、耗时等

    Args:
        operation_type: 操作类型（如 "device_connection", "command_execution", "config_deployment"）
        include_args: 是否记录函数参数
        include_result: 是否记录返回值
        log_level: 日志级别
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            # 提取设备相关信息
            device_info = _extract_device_info(args, kwargs)

            # 构建日志上下文
            log_context = {
                "operation_type": operation_type,
                "function": func_name,
                "device_id": device_info.get("device_id"),
                "device_ip": device_info.get("device_ip"),
                "device_name": device_info.get("device_name"),
            }

            if include_args:
                # 过滤敏感信息
                safe_args, safe_kwargs = _sanitize_args(args, kwargs)
                log_context.update({"args": safe_args, "kwargs": safe_kwargs})

            # 记录操作开始
            logger.bind(**log_context).log(log_level, f"开始执行网络操作: {operation_type} - {func_name}")

            try:
                result = await func(*args, **kwargs)

                # 计算耗时
                duration = time.time() - start_time
                log_context["duration"] = f"{duration:.3f}s"

                if include_result:
                    # 限制结果长度，避免日志过大
                    result_str = str(result)[:500] if result else "None"
                    log_context["result"] = result_str

                # 记录操作成功
                logger.bind(**log_context).log(log_level, f"网络操作成功完成: {operation_type} - {func_name}")

                return result

            except Exception as e:
                # 计算耗时
                duration = time.time() - start_time
                log_context.update(
                    {"duration": f"{duration:.3f}s", "error": str(e), "error_type": e.__class__.__name__}
                )

                # 记录操作失败
                logger.bind(**log_context).error(f"网络操作失败: {operation_type} - {func_name} - {str(e)}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            # 提取设备相关信息
            device_info = _extract_device_info(args, kwargs)

            # 构建日志上下文
            log_context = {
                "operation_type": operation_type,
                "function": func_name,
                "device_id": device_info.get("device_id"),
                "device_ip": device_info.get("device_ip"),
                "device_name": device_info.get("device_name"),
            }

            if include_args:
                # 过滤敏感信息
                safe_args, safe_kwargs = _sanitize_args(args, kwargs)
                log_context.update({"args": safe_args, "kwargs": safe_kwargs})

            # 记录操作开始
            logger.bind(**log_context).log(log_level, f"开始执行网络操作: {operation_type} - {func_name}")

            try:
                result = func(*args, **kwargs)

                # 计算耗时
                duration = time.time() - start_time
                log_context["duration"] = f"{duration:.3f}s"

                if include_result:
                    # 限制结果长度，避免日志过大
                    result_str = str(result)[:500] if result else "None"
                    log_context["result"] = result_str

                # 记录操作成功
                logger.bind(**log_context).log(log_level, f"网络操作成功完成: {operation_type} - {func_name}")

                return result

            except Exception as e:
                # 计算耗时
                duration = time.time() - start_time
                log_context.update(
                    {"duration": f"{duration:.3f}s", "error": str(e), "error_type": e.__class__.__name__}
                )

                # 记录操作失败
                logger.bind(**log_context).error(f"网络操作失败: {operation_type} - {func_name} - {str(e)}")
                raise

        # 根据函数是否为协程选择包装器
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_device_connection(device_ip: str, device_id: str | None = None, username: str | None = None):
    """记录设备连接日志

    Args:
        device_ip: 设备IP地址
        device_id: 设备ID
        username: 用户名
    """
    log_context = {
        "operation_type": "device_connection",
        "device_ip": device_ip,
        "device_id": device_id,
        "username": username,
    }

    logger.bind(**log_context).info(f"尝试连接设备: {device_ip}")


def log_device_connection_success(device_ip: str, device_id: str | None = None, duration: float | None = None):
    """记录设备连接成功日志

    Args:
        device_ip: 设备IP地址
        device_id: 设备ID
        duration: 连接耗时
    """
    log_context = {
        "operation_type": "device_connection",
        "device_ip": device_ip,
        "device_id": device_id,
        "status": "success",
    }

    if duration:
        log_context["duration"] = f"{duration:.3f}s"

    logger.bind(**log_context).info(f"设备连接成功: {device_ip}")


def log_device_connection_failed(
    device_ip: str, error: str, device_id: str | None = None, duration: float | None = None
):
    """记录设备连接失败日志

    Args:
        device_ip: 设备IP地址
        error: 错误信息
        device_id: 设备ID
        duration: 连接耗时
    """
    log_context = {
        "operation_type": "device_connection",
        "device_ip": device_ip,
        "device_id": device_id,
        "status": "failed",
        "error": error,
    }

    if duration:
        log_context["duration"] = f"{duration:.3f}s"

    logger.bind(**log_context).error(f"设备连接失败: {device_ip} - {error}")


def log_command_execution(device_ip: str, command: str, device_id: str | None = None):
    """记录命令执行日志

    Args:
        device_ip: 设备IP地址
        command: 执行的命令
        device_id: 设备ID
    """
    log_context = {
        "operation_type": "command_execution",
        "device_ip": device_ip,
        "device_id": device_id,
        "command": command,
    }

    logger.bind(**log_context).info(f"执行设备命令: {device_ip} - {command}")


def log_command_execution_result(
    device_ip: str,
    command: str,
    success: bool,
    duration: float | None = None,
    error: str | None = None,
    device_id: str | None = None,
):
    """记录命令执行结果日志

    Args:
        device_ip: 设备IP地址
        command: 执行的命令
        success: 是否成功
        duration: 执行耗时
        error: 错误信息（如果失败）
        device_id: 设备ID
    """
    log_context = {
        "operation_type": "command_execution",
        "device_ip": device_ip,
        "device_id": device_id,
        "command": command,
        "status": "success" if success else "failed",
    }

    if duration:
        log_context["duration"] = f"{duration:.3f}s"

    if error:
        log_context["error"] = error

    if success:
        logger.bind(**log_context).info(f"命令执行成功: {device_ip} - {command}")
    else:
        logger.bind(**log_context).error(f"命令执行失败: {device_ip} - {command} - {error}")


def log_config_deployment(
    device_ip: str, config_type: str, device_id: str | None = None, template_id: str | None = None
):
    """记录配置部署日志

    Args:
        device_ip: 设备IP地址
        config_type: 配置类型
        device_id: 设备ID
        template_id: 模板ID
    """
    log_context = {
        "operation_type": "config_deployment",
        "device_ip": device_ip,
        "device_id": device_id,
        "config_type": config_type,
        "template_id": template_id,
    }

    logger.bind(**log_context).info(f"开始配置部署: {device_ip} - {config_type}")


def log_config_deployment_result(
    device_ip: str,
    config_type: str,
    success: bool,
    duration: float | None = None,
    error: str | None = None,
    device_id: str | None = None,
    template_id: str | None = None,
):
    """记录配置部署结果日志

    Args:
        device_ip: 设备IP地址
        config_type: 配置类型
        success: 是否成功
        duration: 部署耗时
        error: 错误信息（如果失败）
        device_id: 设备ID
        template_id: 模板ID
    """
    log_context = {
        "operation_type": "config_deployment",
        "device_ip": device_ip,
        "device_id": device_id,
        "config_type": config_type,
        "template_id": template_id,
        "status": "success" if success else "failed",
    }

    if duration:
        log_context["duration"] = f"{duration:.3f}s"

    if error:
        log_context["error"] = error

    if success:
        logger.bind(**log_context).info(f"配置部署成功: {device_ip} - {config_type}")
    else:
        logger.bind(**log_context).error(f"配置部署失败: {device_ip} - {config_type} - {error}")


def _extract_device_info(args: tuple, kwargs: dict) -> dict[str, Any]:
    """从函数参数中提取设备信息

    Args:
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        设备信息字典
    """
    device_info = {}

    # 从kwargs中提取
    device_info["device_id"] = kwargs.get("device_id")
    device_info["device_ip"] = kwargs.get("device_ip") or kwargs.get("hostname") or kwargs.get("host")
    device_info["device_name"] = kwargs.get("device_name")

    # 从args中提取（通常第一个参数可能包含设备信息）
    if args:
        first_arg = args[0]
        if hasattr(first_arg, "hostname"):
            device_info["device_ip"] = first_arg.hostname
        elif hasattr(first_arg, "host"):
            device_info["device_ip"] = first_arg.host
        elif hasattr(first_arg, "ip"):
            device_info["device_ip"] = first_arg.ip

    return {k: v for k, v in device_info.items() if v is not None}


def _sanitize_args(args: tuple, kwargs: dict) -> tuple[list, dict]:
    """过滤敏感信息

    Args:
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        过滤后的参数
    """
    # 敏感字段列表
    sensitive_fields = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "key",
        "auth",
        "credential",
        "enable_password",
        "auth_password",
        "auth_secondary",
    }

    # 过滤kwargs
    safe_kwargs = {}
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            safe_kwargs[key] = "***"
        else:
            # 限制值的长度
            if isinstance(value, str) and len(value) > 100:
                safe_kwargs[key] = value[:100] + "..."
            else:
                safe_kwargs[key] = value

    # 过滤args（转换为列表以便修改）
    safe_args = []
    for arg in args:
        if hasattr(arg, "__dict__"):
            # 如果是对象，检查是否包含敏感信息
            safe_args.append(f"<{arg.__class__.__name__} object>")
        elif isinstance(arg, str) and len(arg) > 100:
            safe_args.append(arg[:100] + "...")
        else:
            safe_args.append(arg)

    return safe_args, safe_kwargs
