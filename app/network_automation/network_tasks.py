"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_tasks.py
@DateTime: 2025/06/23 11:45:00
@Docs: 网络自动化基础任务函数 - 集成Scrapli真实连接
"""

from typing import Any

from nornir.core.task import Result, Task

from app.network_automation.connection_manager import connection_manager
from app.utils.logger import logger


def ping_task(task: Task) -> Result:
    """基础Ping连通性测试任务

    Args:
        task: Nornir任务对象

    Returns:
        任务执行结果
    """
    try:
        host = task.host

        # 构建主机连接数据
        host_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": getattr(host, "timeout_socket", 30),
            "timeout_transport": getattr(host, "timeout_transport", 60),
        }

        # 添加enable密码（如果有）
        if hasattr(host, "enable_password"):
            host_data["enable_password"] = host.enable_password

        logger.info(f"执行Ping测试: {host.hostname}")

        # 使用连接管理器测试连通性
        import asyncio

        result = asyncio.run(connection_manager.test_connectivity(host_data))

        # 添加设备详细信息
        result["details"] = {
            "device_id": getattr(host, "device_id", None),
            "device_name": getattr(host, "device_name", None),
            "platform": getattr(host, "platform", None),
        }

        if result["status"] == "success":
            return Result(host=task.host, result=result)
        else:
            return Result(host=task.host, failed=True, exception=Exception(result.get("error", "连通性测试失败")))

    except Exception as e:
        logger.error(f"Ping任务失败 {task.host.name}: {e}")
        return Result(host=task.host, failed=True, exception=e)


def get_device_info_task(task: Task) -> Result:
    """获取设备基础信息任务

    Args:
        task: Nornir任务对象

    Returns:
        任务执行结果
    """
    try:
        host = task.host

        # 构建主机连接数据
        host_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": getattr(host, "timeout_socket", 30),
            "timeout_transport": getattr(host, "timeout_transport", 60),
        }

        if hasattr(host, "enable_password"):
            host_data["enable_password"] = host.enable_password

        # 使用连接管理器获取设备信息
        import asyncio

        device_facts = asyncio.run(connection_manager.get_device_facts(host_data))

        if device_facts["status"] == "success":
            # 合并Nornir主机信息和设备事实
            device_info = {
                "hostname": host.hostname,
                "device_name": getattr(host, "device_name", "Unknown"),
                "device_type": getattr(host, "device_type", "Unknown"),
                "platform": getattr(host, "platform", "Unknown"),
                "region": getattr(host, "region_name", "Unknown"),
                "brand": getattr(host, "brand_name", "Unknown"),
                "model": getattr(host, "model_name", "Unknown"),
                "group": getattr(host, "group_name", "Unknown"),
                "version_info": device_facts.get("version_output", ""),
                "platform_detected": device_facts.get("platform", "unknown"),
            }

            # 添加平台特定信息
            if "inventory" in device_facts:
                device_info["inventory"] = device_facts["inventory"]
            if "system_info" in device_facts:
                device_info["system_info"] = device_facts["system_info"]

            logger.info(f"获取设备信息成功: {host.hostname}")
            return Result(host=task.host, result=device_info)
        else:
            return Result(
                host=task.host, failed=True, exception=Exception(device_facts.get("error", "获取设备信息失败"))
            )

    except Exception as e:
        logger.error(f"获取设备信息失败 {task.host.name}: {e}")
        return Result(host=task.host, failed=True, exception=e)


def execute_command_task(task: Task, command: str) -> Result:
    """执行单条命令任务

    Args:
        task: Nornir任务对象
        command: 要执行的命令

    Returns:
        任务执行结果
    """
    try:
        host = task.host

        # 构建主机连接数据
        host_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": getattr(host, "timeout_socket", 30),
            "timeout_transport": getattr(host, "timeout_transport", 60),
        }

        if hasattr(host, "enable_password"):
            host_data["enable_password"] = host.enable_password

        logger.info(f"在设备 {host.hostname} 执行命令: {command}")

        # 使用连接管理器执行命令
        import asyncio

        result = asyncio.run(connection_manager.execute_command(host_data, command))

        if result["status"] == "success":
            return Result(host=task.host, result=result)
        else:
            return Result(
                host=task.host, failed=True, exception=Exception(result.get("error", f"命令执行失败: {command}"))
            )

    except Exception as e:
        logger.error(f"命令执行失败 {task.host.name}: {e}")
        return Result(host=task.host, failed=True, exception=e)


def backup_config_task(task: Task) -> Result:
    """备份设备配置任务

    Args:
        task: Nornir任务对象

    Returns:
        任务执行结果
    """
    try:
        host = task.host

        # 构建主机连接数据
        host_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": getattr(host, "timeout_socket", 30),
            "timeout_transport": getattr(host, "timeout_transport", 60),
        }

        if hasattr(host, "enable_password"):
            host_data["enable_password"] = host.enable_password

        logger.info(f"备份设备配置: {host.hostname}")

        # 使用连接管理器备份配置
        import asyncio

        result = asyncio.run(connection_manager.backup_configuration(host_data))

        if result["status"] == "success":
            return Result(host=task.host, result=result)
        else:
            return Result(host=task.host, failed=True, exception=Exception(result.get("error", "配置备份失败")))

    except Exception as e:
        logger.error(f"配置备份失败 {task.host.name}: {e}")
        return Result(host=task.host, failed=True, exception=e)


def deploy_config_task(task: Task, config_commands: list[str]) -> Result:
    """部署配置任务

    Args:
        task: Nornir任务对象
        config_commands: 要部署的配置命令列表

    Returns:
        任务执行结果
    """
    try:
        host = task.host

        # 构建主机连接数据
        host_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": getattr(host, "timeout_socket", 30),
            "timeout_transport": getattr(host, "timeout_transport", 60),
        }

        if hasattr(host, "enable_password"):
            host_data["enable_password"] = host.enable_password

        logger.info(f"在设备 {host.hostname} 部署配置，命令数量: {len(config_commands)}")

        # 使用连接管理器执行配置命令
        import asyncio

        result = asyncio.run(connection_manager.execute_commands(host_data, config_commands))

        return Result(host=task.host, result=result)

    except Exception as e:
        logger.error(f"配置部署失败 {task.host.name}: {e}")
        return Result(host=task.host, failed=True, exception=e)


def template_render_task(task: Task, template_content: str, template_vars: dict[str, Any]) -> Result:
    """模板渲染任务

    Args:
        task: Nornir任务对象
        template_content: Jinja2模板内容
        template_vars: 模板变量

    Returns:
        任务执行结果
    """
    try:
        from jinja2 import Template

        host = task.host

        # 添加主机信息到模板变量
        template_vars.update(
            {
                "hostname": host.hostname,
                "device_name": getattr(host, "device_name", ""),
                "device_type": getattr(host, "device_type", ""),
                "platform": getattr(host, "platform", ""),
            }
        )

        # 渲染模板
        template = Template(template_content)
        rendered_content = template.render(**template_vars)

        logger.info(f"模板渲染成功: {host.hostname}")

        result = {
            "hostname": host.hostname,
            "template_vars": template_vars,
            "rendered_content": rendered_content,
            "status": "success",
        }

        return Result(host=task.host, result=result)

    except Exception as e:
        logger.error(f"模板渲染失败 {task.host.name}: {e}")
        return Result(host=task.host, failed=True, exception=e)


def health_check_task(task: Task) -> Result:
    """设备健康检查任务

    Args:
        task: Nornir任务对象

    Returns:
        任务执行结果
    """
    try:
        host = task.host

        # 模拟健康检查
        logger.info(f"执行设备健康检查: {host.hostname}")

        # 模拟健康检查结果
        health_status = {
            "hostname": host.hostname,
            "connectivity": "ok",
            "cpu_usage": "15%",
            "memory_usage": "45%",
            "uptime": "30 days",
            "status": "healthy",
        }

        return Result(host=task.host, result=health_status)

    except Exception as e:
        logger.error(f"健康检查失败 {task.host.name}: {e}")
        return Result(host=task.host, failed=True, exception=e)
