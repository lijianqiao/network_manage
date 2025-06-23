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

from app.utils.logger import logger


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

    async def create_connection(self, host_data: dict[str, Any]) -> AsyncScrapli:
        """创建Scrapli连接

        Args:
            host_data: 主机连接信息

        Returns:
            配置好的Scrapli连接对象

        Raises:
            ScrapliException: 连接创建失败
        """
        try:
            # 构建Scrapli连接参数
            connection_params = {
                "host": host_data["hostname"],
                "auth_username": host_data["username"],
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
            if platform in ["cisco_ios", "ios"]:
                connection_params["platform"] = "cisco_iosxe"
            elif platform in ["cisco_nxos", "nxos"]:
                connection_params["platform"] = "cisco_nxos"
            elif platform in ["cisco_iosxr", "iosxr"]:
                connection_params["platform"] = "cisco_iosxr"
            elif platform in ["arista_eos", "eos"]:
                connection_params["platform"] = "arista_eos"
            elif platform in ["juniper_junos", "junos"]:
                connection_params["platform"] = "juniper_junos"
            elif platform in ["huawei_vrp", "vrp"]:
                connection_params["platform"] = "huawei_vrp"
            else:
                # 默认使用通用Linux驱动
                connection_params["platform"] = "hp_comware"  # 这里可以根据实际情况调整

            # 如果有enable密码，添加到连接参数
            if host_data.get("enable_password"):
                connection_params["auth_secondary"] = host_data["enable_password"]

            logger.debug(f"创建Scrapli连接: {host_data['hostname']} ({platform}) 使用asyncssh transport")

            # 创建连接对象
            conn = AsyncScrapli(**connection_params)

            return conn

        except Exception as e:
            logger.error(f"创建Scrapli连接失败 {host_data.get('hostname', 'unknown')}: {e}")
            raise ScrapliException(f"连接创建失败: {str(e)}") from e

    @asynccontextmanager
    async def get_connection(self, host_data: dict[str, Any]):
        """获取连接的上下文管理器

        Args:
            host_data: 主机连接信息

        Yields:
            已连接的Scrapli对象
        """
        async with self.connection_semaphore:
            conn = None
            try:
                # 创建连接
                conn = await self.create_connection(host_data)

                # 打开连接
                logger.debug(f"正在连接到设备: {host_data['hostname']}...")
                await conn.open()
                logger.info(f"成功连接到设备: {host_data['hostname']}")

                yield conn

            except TimeoutError as e:
                logger.error(f"连接超时 {host_data.get('hostname', 'unknown')}: {e}")
                raise ScrapliException(f"连接超时: {str(e)}") from e
            except ConnectionRefusedError as e:
                logger.error(f"连接被拒绝 {host_data.get('hostname', 'unknown')}: {e}")
                raise ScrapliException(f"连接被拒绝: {str(e)}") from e
            except Exception as e:
                logger.error(f"连接失败 {host_data.get('hostname', 'unknown')}: {e}")
                raise ScrapliException(f"连接失败: {str(e)}") from e
            finally:
                # 确保连接被关闭
                if conn and conn.isalive():
                    try:
                        await conn.close()
                        logger.debug(f"已关闭连接: {host_data.get('hostname', 'unknown')}")
                    except Exception as e:
                        logger.warning(f"关闭连接时出错 {host_data.get('hostname', 'unknown')}: {e}")

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

    async def execute_command(self, host_data: dict[str, Any], command: str) -> dict[str, Any]:
        """执行单条命令

        Args:
            host_data: 主机连接信息
            command: 要执行的命令

        Returns:
            命令执行结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            async with self.get_connection(host_data) as conn:
                response = await conn.send_command(command)

                elapsed_time = asyncio.get_event_loop().time() - start_time

                return {
                    "hostname": host_data["hostname"],
                    "command": command,
                    "status": "success",
                    "output": response.result,
                    "elapsed_time": round(elapsed_time, 3),
                }

        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"命令执行失败 {host_data['hostname']}: {e}")
            return {
                "hostname": host_data["hostname"],
                "command": command,
                "status": "failed",
                "output": "",
                "error": str(e),
                "elapsed_time": round(elapsed_time, 3),
                "error_type": type(e).__name__,
            }

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
                }

                # 尝试获取更多信息（根据平台）
                try:
                    platform = host_data.get("platform", "").lower()
                    if "cisco" in platform:
                        # Cisco设备
                        inventory_response = await conn.send_command("show inventory")
                        facts["inventory"] = inventory_response.result
                    elif "huawei" in platform:
                        # 华为设备
                        system_response = await conn.send_command("display version")
                        facts["system_info"] = system_response.result
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
            async with self.get_connection(host_data) as conn:
                # 根据平台选择配置命令
                platform = getattr(conn, "platform", "").lower()
                if "cisco" in platform:
                    config_command = "show running-config"
                elif "huawei" in platform:
                    config_command = "display current-configuration"
                elif "juniper" in platform:
                    config_command = "show configuration"
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
