"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_tasks.py
@DateTime: 2025/06/23 11:45:00
@Docs: 网络自动化基础任务函数 - 集成Scrapli真实连接 + 混合解析器
"""

from typing import Any

from nornir.core.task import Result, Task

from app.core.exceptions import CommandExecutionError, DeviceAuthenticationError, DeviceConnectionError
from app.network_automation.connection_manager import connection_manager
from app.network_automation.parsers.hybrid_parser import hybrid_parser
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
        host_data = getattr(host, "data", {})
        device_id = host_data.get("device_id")

        # 构建主机连接数据
        connection_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": host_data.get("timeout_socket", 30),
            "timeout_transport": host_data.get("timeout_transport", 60),
            "device_id": device_id,
        }

        # 添加enable密码（如果有）
        if hasattr(host, "enable_password"):
            connection_data["enable_password"] = host.enable_password

        logger.info(
            f"执行Ping测试: {host.hostname}", device_ip=host.hostname, device_id=device_id, operation_type="ping_test"
        )

        # 使用连接管理器测试连通性
        import asyncio

        result = asyncio.run(connection_manager.test_connectivity(connection_data))

        # 添加设备详细信息
        result["details"] = {
            "device_id": device_id,
            "device_name": host_data.get("device_name"),
            "platform": host.platform,
        }

        if result["status"] == "success":
            logger.info(
                f"Ping测试成功: {host.hostname}",
                device_ip=host.hostname,
                device_id=device_id,
                response_time=result.get("response_time"),
                operation_type="ping_test",
            )
            return Result(host=task.host, result=result)
        else:
            error_msg = result.get("error", "连通性测试失败")
            logger.error(
                f"Ping测试失败: {host.hostname} - {error_msg}",
                device_ip=host.hostname,
                device_id=device_id,
                error=error_msg,
                operation_type="ping_test",
            )
            return Result(
                host=task.host,
                failed=True,
                exception=DeviceConnectionError(
                    message="连通性测试失败", detail=error_msg, device_id=device_id, device_ip=host.hostname
                ),
            )

    except Exception as e:
        device_id = getattr(task.host, "data", {}).get("device_id")
        logger.error(
            f"Ping任务异常 {task.host.name}: {e}",
            device_ip=task.host.hostname,
            device_id=device_id,
            error=str(e),
            error_type=e.__class__.__name__,
            operation_type="ping_test",
        )
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
        host_data = getattr(host, "data", {})

        # 构建主机连接数据
        connection_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": host_data.get("timeout_socket", 30),
            "timeout_transport": host_data.get("timeout_transport", 60),
        }

        if hasattr(host, "enable_password"):
            connection_data["enable_password"] = host.enable_password

        # 使用连接管理器获取设备信息
        import asyncio

        device_facts = asyncio.run(connection_manager.get_device_facts(connection_data))

        if device_facts["status"] == "success":
            # 合并Nornir主机信息和设备事实
            device_info = {
                "hostname": host.hostname,
                "device_name": host_data.get("device_name", "Unknown"),
                "device_type": host_data.get("device_type", "Unknown"),
                "platform": host.platform,
                "region": host_data.get("region_name", "Unknown"),
                "brand": host_data.get("brand_name", "Unknown"),
                "model": host_data.get("model_name", "Unknown"),
                "group": host_data.get("group_name", "Unknown"),
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


def execute_command_task(task: Task, command: str, enable_parsing: bool = True) -> Result:
    """执行单条命令任务（支持结构化解析）

    Args:
        task: Nornir任务对象
        command: 要执行的命令
        enable_parsing: 是否启用结构化解析

    Returns:
        任务执行结果
    """
    try:
        host = task.host
        host_data = getattr(host, "data", {})
        device_id = host_data.get("device_id")

        # 构建主机连接数据
        connection_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": host_data.get("timeout_socket", 30),
            "timeout_transport": host_data.get("timeout_transport", 60),
            "device_id": device_id,
        }

        if hasattr(host, "enable_password"):
            connection_data["enable_password"] = host.enable_password

        logger.info(
            f"在设备 {host.hostname} 执行命令: {command}",
            device_ip=host.hostname,
            device_id=device_id,
            command=command,
            operation_type="command_execution",
        )

        # 使用连接管理器执行命令
        import asyncio

        try:
            result = asyncio.run(connection_manager.execute_command(connection_data, command))

            # 基础结果
            command_result = {
                "hostname": host.hostname,
                "command": command,
                "raw_output": result.get("output", ""),
                "execution_time": result.get("elapsed_time", 0),
                "status": "success",
            }

            # 如果启用解析且有输出内容
            if enable_parsing and result.get("output"):
                try:
                    # 获取设备品牌信息
                    device_brand = host_data.get("brand") or host_data.get("brand_name")

                    if not device_brand:
                        # 如果没有品牌信息，记录警告并跳过解析
                        logger.warning(
                            f"设备 {host.hostname} 缺少品牌信息，跳过结构化解析",
                            device_ip=host.hostname,
                            device_id=device_id,
                            command=command,
                        )
                        command_result["parsing_enabled"] = False
                        command_result["parsing_error"] = "设备品牌信息缺失"
                    else:
                        # 使用混合解析器执行结构化解析
                        parse_result = hybrid_parser.parse_command_output(
                            command_output=result["output"],
                            command=command,
                            brand=device_brand,
                            use_ntc_first=True,  # 优先使用NTC-Templates
                        )

                        # 添加解析结果
                        command_result["parsed_data"] = parse_result
                        command_result["parsing_enabled"] = True

                        logger.info(
                            f"混合解析完成: {host.hostname} - {command} (解析成功: {parse_result.get('success', False)}, 解析器: {parse_result.get('parser', 'unknown')})",
                            device_ip=host.hostname,
                            device_id=device_id,
                            command=command,
                            parsing_success=parse_result.get("success", False),
                            parser_used=parse_result.get("parser", "unknown"),
                        )

                except Exception as parse_error:
                    logger.warning(
                        f"结构化解析失败: {parse_error}",
                        device_ip=host.hostname,
                        device_id=device_id,
                        command=command,
                        error=str(parse_error),
                    )
                    command_result["parsing_enabled"] = False
                    command_result["parsing_error"] = str(parse_error)
            else:
                command_result["parsing_enabled"] = False

            logger.info(
                f"命令执行成功: {host.hostname} - {command}",
                device_ip=host.hostname,
                device_id=device_id,
                command=command,
                execution_time=command_result["execution_time"],
                output_length=len(command_result["raw_output"]),
                operation_type="command_execution",
            )

            return Result(host=task.host, result=command_result)

        except (DeviceConnectionError, DeviceAuthenticationError, CommandExecutionError) as e:
            # 网络设备相关异常，直接重新抛出
            logger.error(
                f"命令执行失败: {host.hostname} - {command} - {e.message}",
                device_ip=host.hostname,
                device_id=device_id,
                command=command,
                error=e.message,
                error_type=e.__class__.__name__,
                operation_type="command_execution",
            )
            return Result(host=task.host, failed=True, exception=e)

    except Exception as e:
        device_id = getattr(task.host, "data", {}).get("device_id")
        logger.error(
            f"命令执行任务异常 {task.host.name}: {e}",
            device_ip=task.host.hostname,
            device_id=device_id,
            command=command if "command" in locals() else "unknown",
            error=str(e),
            error_type=e.__class__.__name__,
            operation_type="command_execution",
        )
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
        host_data = getattr(host, "data", {})

        # 构建主机连接数据
        connection_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": host_data.get("timeout_socket", 30),
            "timeout_transport": host_data.get("timeout_transport", 60),
        }

        if hasattr(host, "enable_password"):
            connection_data["enable_password"] = host.enable_password

        logger.info(f"备份设备配置: {host.hostname}")

        # 使用连接管理器备份配置
        import asyncio

        result = asyncio.run(connection_manager.backup_configuration(connection_data))

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
        host_data = getattr(host, "data", {})  # 构建主机连接数据
        connection_data = {
            "hostname": host.hostname,
            "username": host.username,
            "password": host.password,
            "platform": host.platform,
            "port": getattr(host, "port", 22),
            "timeout_socket": host_data.get("timeout_socket", 30),
            "timeout_transport": host_data.get("timeout_transport", 60),
        }

        if hasattr(host, "enable_password"):
            connection_data["enable_password"] = host.enable_password

        logger.info(f"在设备 {host.hostname} 部署配置，命令数量: {len(config_commands)}")

        # 使用连接管理器执行配置命令
        import asyncio

        result = asyncio.run(connection_manager.execute_commands(connection_data, config_commands))

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
        host_data = getattr(host, "data", {})

        # 添加主机信息到模板变量
        template_vars.update(
            {
                "hostname": host.hostname,
                "device_name": host_data.get("device_name", ""),
                "device_type": host_data.get("device_type", ""),
                "platform": host.platform,
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
