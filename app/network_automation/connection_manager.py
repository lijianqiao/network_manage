"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: connection_manager.py
@DateTime: 2025/06/23 12:00:00
@Docs: Scrapli连接管理器 - 处理设备SSH/Telnet连接，支持Windows平台
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from scrapli import AsyncScrapli
from scrapli.exceptions import ScrapliException

from app.core.exceptions import CommandExecutionError, DeviceAuthenticationError, DeviceConnectionError
from app.utils.logger import logger
from app.utils.network_logger import (
    log_device_connection,
    log_device_connection_failed,
    log_device_connection_success,
    log_network_operation,
)


class ScrapliConnectionManager:
    """Scrapli连接管理器

    管理设备的SSH/Telnet连接，支持连接池和并发控制
    专为Windows平台优化，使用asyncssh transport
    """

    def __init__(self, max_connections: int = 50):
        """初始化连接管理器

        Args:
            max_connections: 最大并发连接数
        """
        self.max_connections = max_connections
        self.connection_semaphore = asyncio.Semaphore(max_connections)
        self._active_connections: dict[str, AsyncScrapli] = {}

    @log_network_operation("connection_creation", include_args=False)
    async def create_connection(self, host_data: dict[str, Any]) -> AsyncScrapli:
        """创建Scrapli连接

        Args:
            host_data: 主机连接信息

        Returns:
            配置好的Scrapli连接对象

        Raises:
            DeviceConnectionError: 连接创建失败
        """
        device_ip = host_data.get("hostname")
        device_id = host_data.get("device_id")
        username = host_data.get("username")

        try:
            # 构建Scrapli连接参数
            connection_params = {
                "host": device_ip,
                "auth_username": username,
                "auth_password": host_data["password"],
                "auth_strict_key": False,
                "ssh_config_file": False,
                "timeout_socket": host_data.get("timeout_socket", 30),
                "timeout_transport": host_data.get("timeout_transport", 60),
                "port": host_data.get("port", 22),
                "transport": "asyncssh",  # 明确使用asyncssh transport，支持Windows
            }

            # 根据平台选择驱动
            platform = host_data.get("platform", "").lower()
            if platform in ["cisco_ios", "ios", "cisco"]:
                connection_params["platform"] = "cisco_iosxe"
            elif platform in ["cisco_nxos", "nxos"]:
                connection_params["platform"] = "cisco_nxos"
            elif platform in ["cisco_iosxr", "iosxr"]:
                connection_params["platform"] = "cisco_iosxr"
            elif platform in ["huawei_vrp", "vrp", "huawei"]:
                connection_params["platform"] = "huawei_vrp"
            elif platform in ["h3c_comware", "comware", "h3c"]:
                connection_params["platform"] = "hp_comware"  # H3C使用HP Comware驱动
            else:
                # 默认使用通用驱动
                connection_params["platform"] = "hp_comware"

            # 如果有enable密码，添加到连接参数
            if host_data.get("enable_password"):
                connection_params["auth_secondary"] = host_data["enable_password"]

            logger.debug(
                f"创建Scrapli连接: {device_ip} ({platform}) 使用asyncssh transport",
                device_ip=device_ip,
                device_id=device_id,
                platform=platform,
                port=connection_params["port"],
            )

            # 创建连接对象
            conn = AsyncScrapli(**connection_params)

            return conn

        except Exception as e:
            error_msg = f"连接创建失败: {str(e)}"
            logger.error(
                f"创建Scrapli连接失败 {device_ip}: {e}",
                device_ip=device_ip,
                device_id=device_id,
                error=str(e),
                error_type=e.__class__.__name__,
            )
            raise DeviceConnectionError(
                message=error_msg, detail=str(e), device_id=device_id, device_ip=device_ip
            ) from e

    @asynccontextmanager
    async def get_connection(self, host_data: dict[str, Any]):
        """获取连接的上下文管理器

        Args:
            host_data: 主机连接信息

        Yields:
            已连接的Scrapli对象
        """
        device_ip = host_data.get("hostname")
        device_id = host_data.get("device_id")
        username = host_data.get("username")

        async with self.connection_semaphore:
            conn = None
            start_time = asyncio.get_event_loop().time()

            try:
                # 记录连接开始
                log_device_connection(
                    str(device_ip) if device_ip is not None else "",
                    str(device_id) if device_id is not None else "",
                    str(username) if username is not None else "",
                )

                # 创建连接
                conn = await self.create_connection(host_data)

                # 打开连接
                logger.debug(f"正在连接到设备: {device_ip}...", device_ip=device_ip, device_id=device_id)
                await conn.open()

                # 计算连接耗时
                duration = asyncio.get_event_loop().time() - start_time

                logger.info(
                    f"成功连接到设备: {device_ip}",
                    device_ip=device_ip,
                    device_id=device_id,
                    duration=f"{duration:.3f}s",
                )

                # 记录连接成功
                log_device_connection_success(
                    str(device_ip) if device_ip is not None else "",
                    str(device_id) if device_id is not None else "",
                    duration,
                )

                yield conn

            except TimeoutError as e:
                duration = asyncio.get_event_loop().time() - start_time
                error_msg = f"连接超时: {str(e)}"

                logger.error(
                    f"连接超时 {device_ip}: {e}",
                    device_ip=device_ip,
                    device_id=device_id,
                    error=str(e),
                    duration=f"{duration:.3f}s",
                )

                log_device_connection_failed(
                    str(device_ip) if device_ip is not None else "",
                    error_msg,
                    str(device_id) if device_id is not None else "",
                    duration,
                )

                raise DeviceConnectionError(
                    message=error_msg,
                    detail=str(e),
                    device_id=device_id,
                    device_ip=device_ip,
                    timeout=host_data.get("timeout_socket", 30),
                ) from e

            except ConnectionRefusedError as e:
                duration = asyncio.get_event_loop().time() - start_time
                error_msg = f"连接被拒绝: {str(e)}"

                logger.error(
                    f"连接被拒绝 {device_ip}: {e}",
                    device_ip=device_ip,
                    device_id=device_id,
                    error=str(e),
                    duration=f"{duration:.3f}s",
                )

                log_device_connection_failed(
                    str(device_ip) if device_ip is not None else "",
                    error_msg,
                    str(device_id) if device_id is not None else "",
                    duration,
                )

                raise DeviceConnectionError(
                    message=error_msg, detail=str(e), device_id=device_id, device_ip=device_ip
                ) from e

            except ScrapliException as e:
                duration = asyncio.get_event_loop().time() - start_time
                error_msg = str(e)

                logger.error(
                    f"Scrapli连接失败 {device_ip}: {e}",
                    device_ip=device_ip,
                    device_id=device_id,
                    error=error_msg,
                    duration=f"{duration:.3f}s",
                )

                log_device_connection_failed(
                    str(device_ip) if device_ip is not None else "",
                    error_msg,
                    str(device_id) if device_id is not None else "",
                    duration,
                )

                # 根据错误类型抛出相应异常
                if "authentication" in error_msg.lower() or "login" in error_msg.lower():
                    raise DeviceAuthenticationError(
                        message="设备认证失败",
                        detail=error_msg,
                        device_id=device_id,
                        device_ip=device_ip,
                        username=username,
                    ) from e
                else:
                    raise DeviceConnectionError(
                        message="设备连接失败", detail=error_msg, device_id=device_id, device_ip=device_ip
                    ) from e

            except Exception as e:
                duration = asyncio.get_event_loop().time() - start_time
                error_msg = f"连接失败: {str(e)}"

                logger.error(
                    f"连接失败 {device_ip}: {e}",
                    device_ip=device_ip,
                    device_id=device_id,
                    error=str(e),
                    error_type=e.__class__.__name__,
                    duration=f"{duration:.3f}s",
                )

                log_device_connection_failed(
                    str(device_ip) if device_ip is not None else "",
                    error_msg,
                    str(device_id) if device_id is not None else "",
                    duration,
                )

                raise DeviceConnectionError(
                    message=error_msg, detail=str(e), device_id=device_id, device_ip=device_ip
                ) from e
            finally:
                # 确保连接被关闭
                if conn and conn.isalive():
                    try:
                        await conn.close()
                        logger.debug(f"已关闭连接: {device_ip}", device_ip=device_ip, device_id=device_id)
                    except Exception as e:
                        logger.warning(
                            f"关闭连接时出错 {device_ip}: {e}", device_ip=device_ip, device_id=device_id, error=str(e)
                        )

    async def test_connectivity(self, host_data: dict[str, Any]) -> dict[str, Any]:
        """测试设备连通性

        Args:
            host_data: 主机连接信息

        Returns:
            连通性测试结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            async with self.get_connection(host_data) as conn:
                # 发送简单命令测试连接
                logger.debug(f"发送测试命令到 {host_data['hostname']}")
                response = await conn.send_command("show version", strip_prompt=False)

                elapsed_time = asyncio.get_event_loop().time() - start_time

                return {
                    "hostname": host_data["hostname"],
                    "status": "success",
                    "message": "设备连通性正常",
                    "response_time": round(elapsed_time, 3),
                    "platform_detected": getattr(conn, "platform", "unknown"),
                    "response_length": len(response.result) if hasattr(response, "result") else 0,
                }

        except ScrapliException as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.warning(f"连通性测试失败 {host_data['hostname']}: {e}")
            return {
                "hostname": host_data["hostname"],
                "status": "failed",
                "message": f"连通性测试失败: {str(e)}",
                "error": str(e),
                "response_time": round(elapsed_time, 3),
                "error_type": type(e).__name__,
            }
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"连通性测试异常 {host_data['hostname']}: {e}")
            return {
                "hostname": host_data["hostname"],
                "status": "failed",
                "message": f"连通性测试异常: {str(e)}",
                "error": str(e),
                "response_time": round(elapsed_time, 3),
                "error_type": type(e).__name__,
            }

    @log_network_operation("command_execution", include_args=False)
    async def execute_command(self, host_data: dict[str, Any], command: str) -> dict[str, Any]:
        """执行单条命令

        Args:
            host_data: 主机连接信息
            command: 要执行的命令

        Returns:
            命令执行结果
        """
        device_ip = host_data.get("hostname")
        device_id = host_data.get("device_id")
        start_time = asyncio.get_event_loop().time()

        try:
            async with self.get_connection(host_data) as conn:
                logger.info(f"执行命令: {command}", device_ip=device_ip, device_id=device_id, command=command)

                response = await conn.send_command(command)
                elapsed_time = asyncio.get_event_loop().time() - start_time

                logger.info(
                    f"命令执行成功: {command}",
                    device_ip=device_ip,
                    device_id=device_id,
                    command=command,
                    duration=f"{elapsed_time:.3f}s",
                    output_length=len(response.result),
                )

                return {
                    "hostname": device_ip,
                    "command": command,
                    "status": "success",
                    "output": response.result,
                    "elapsed_time": round(elapsed_time, 3),
                }

        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time

            logger.error(
                f"命令执行失败: {command}",
                device_ip=device_ip,
                device_id=device_id,
                command=command,
                error=str(e),
                error_type=e.__class__.__name__,
                duration=f"{elapsed_time:.3f}s",
            )

            # 根据错误类型抛出相应异常
            if isinstance(e, DeviceConnectionError | DeviceAuthenticationError):
                # 连接相关异常直接重新抛出
                raise
            else:
                # 其他异常转换为命令执行异常
                raise CommandExecutionError(
                    message=f"命令执行失败: {command}",
                    detail=str(e),
                    device_id=device_id,
                    device_ip=device_ip,
                    command=command,
                    error_output=str(e),
                ) from e

    async def execute_commands(self, host_data: dict[str, Any], commands: list[str]) -> dict[str, Any]:
        """执行多条命令

        Args:
            host_data: 主机连接信息
            commands: 要执行的命令列表

        Returns:
            命令执行结果
        """
        results = []
        total_start_time = asyncio.get_event_loop().time()

        try:
            async with self.get_connection(host_data) as conn:
                for command in commands:
                    cmd_start_time = asyncio.get_event_loop().time()
                    try:
                        response = await conn.send_command(command)
                        cmd_elapsed_time = asyncio.get_event_loop().time() - cmd_start_time

                        results.append(
                            {
                                "command": command,
                                "status": "success",
                                "output": response.result,
                                "elapsed_time": round(cmd_elapsed_time, 3),
                            }
                        )
                    except Exception as e:
                        cmd_elapsed_time = asyncio.get_event_loop().time() - cmd_start_time
                        results.append(
                            {
                                "command": command,
                                "status": "failed",
                                "output": "",
                                "error": str(e),
                                "elapsed_time": round(cmd_elapsed_time, 3),
                            }
                        )

                total_elapsed_time = asyncio.get_event_loop().time() - total_start_time

                return {
                    "hostname": host_data["hostname"],
                    "total_commands": len(commands),
                    "successful_commands": len([r for r in results if r["status"] == "success"]),
                    "failed_commands": len([r for r in results if r["status"] == "failed"]),
                    "total_time": round(total_elapsed_time, 3),
                    "commands_detail": results,
                }

        except Exception as e:
            total_elapsed_time = asyncio.get_event_loop().time() - total_start_time
            logger.error(f"批量命令执行失败 {host_data['hostname']}: {e}")
            return {
                "hostname": host_data["hostname"],
                "total_commands": len(commands),
                "successful_commands": 0,
                "failed_commands": len(commands),
                "total_time": round(total_elapsed_time, 3),
                "error": str(e),
                "error_type": type(e).__name__,
                "commands_detail": [{"command": cmd, "status": "failed", "error": str(e)} for cmd in commands],
            }

    async def get_device_facts(self, host_data: dict[str, Any]) -> dict[str, Any]:
        """获取设备基础信息

        Args:
            host_data: 主机连接信息

        Returns:
            设备信息
        """
        try:
            async with self.get_connection(host_data) as conn:
                # 尝试获取设备版本信息
                version_response = await conn.send_command("show version")

                facts = {
                    "hostname": host_data["hostname"],
                    "platform": getattr(conn, "platform", "unknown"),
                    "version_output": version_response.result,
                    "status": "success",
                }  # 尝试获取更多信息（根据平台）
                try:
                    platform = host_data.get("platform", "").lower()
                    if "cisco" in platform:
                        # Cisco设备
                        inventory_response = await conn.send_command("show inventory")
                        facts["inventory"] = inventory_response.result
                    elif "huawei" in platform:
                        # 华为设备
                        system_response = await conn.send_command("display device")
                        facts["system_info"] = system_response.result
                    elif "h3c" in platform or "comware" in platform:
                        # H3C设备
                        device_response = await conn.send_command("display device")
                        facts["device_info"] = device_response.result
                except Exception as extra_info_error:
                    # 如果获取额外信息失败，忽略错误
                    logger.debug(f"获取额外设备信息失败 {host_data['hostname']}: {extra_info_error}")

                return facts

        except Exception as e:
            logger.error(f"获取设备信息失败 {host_data['hostname']}: {e}")
            return {
                "hostname": host_data["hostname"],
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def backup_configuration(self, host_data: dict[str, Any]) -> dict[str, Any]:
        """备份设备配置

        Args:
            host_data: 主机连接信息

        Returns:
            配置备份结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            async with self.get_connection(host_data) as conn:  # 根据平台选择配置命令
                platform = getattr(conn, "platform", "").lower()
                if "cisco" in platform:
                    config_command = "show running-config"
                elif "huawei" in platform:
                    config_command = "display current-configuration"
                elif "h3c" in platform or "comware" in platform:
                    config_command = "display current-configuration"
                else:
                    config_command = "show running-config"  # 默认

                response = await conn.send_command(config_command)
                elapsed_time = asyncio.get_event_loop().time() - start_time

                return {
                    "hostname": host_data["hostname"],
                    "status": "success",
                    "config_content": response.result,
                    "config_size": len(response.result),
                    "elapsed_time": round(elapsed_time, 3),
                }

        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"配置备份失败 {host_data['hostname']}: {e}")
            return {
                "hostname": host_data["hostname"],
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "elapsed_time": round(elapsed_time, 3),
            }

    def get_connection_stats(self) -> dict[str, Any]:
        """获取连接池统计信息

        Returns:
            连接池统计
        """
        return {
            "max_connections": self.max_connections,
            "available_connections": self.connection_semaphore._value,
            "active_connections": self.max_connections - self.connection_semaphore._value,
            "transport": "asyncssh",
            "platform_support": "Windows/Linux/MacOS",
        }


# 全局连接管理器实例
connection_manager = ScrapliConnectionManager()
