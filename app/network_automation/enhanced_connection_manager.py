"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: enhanced_connection_manager.py
@DateTime: 2025/06/23 17:00:00
@Docs: 增强的连接管理器 - 集成Scrapli-Community解析功能
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from app.utils.logger import logger

try:
    from scrapli.driver.core.cisco_iosxe import AsyncIOSXEDriver
    from scrapli.exceptions import ScrapliException
    from scrapli_community.hp.comware.async_driver import AsyncHPComwareDriver
    from scrapli_community.huawei.vrp.async_driver import AsyncHuaweiVRPDriver
except ImportError:
    AsyncIOSXEDriver = None
    AsyncHuaweiVRPDriver = None
    AsyncHPComwareDriver = None
    ScrapliException = None


class EnhancedConnectionManager:
    """增强的连接管理器 - 支持TextFSM解析"""

    def __init__(self, max_connections: int = 50):
        """初始化连接管理器

        Args:
            max_connections: 最大并发连接数
        """
        self.max_connections = max_connections
        self.connection_semaphore = asyncio.Semaphore(max_connections)

        # 检查依赖
        if not all([AsyncIOSXEDriver, AsyncHuaweiVRPDriver, AsyncHPComwareDriver]):
            logger.warning("Scrapli-Community未安装，将使用基础Scrapli功能")
            self.use_community = False
        else:
            self.use_community = True
            logger.info("Scrapli-Community已加载，支持TextFSM解析")

    async def create_connection(self, host_data: dict[str, Any]):
        """创建Scrapli连接

        Args:
            host_data: 主机连接信息

        Returns:
            配置好的Scrapli连接对象
        """
        try:
            # 基础连接参数
            connection_params = {
                "host": host_data["hostname"],
                "auth_username": host_data["username"],
                "auth_password": host_data["password"],
                "auth_strict_key": False,
                "ssh_config_file": False,
                "timeout_socket": host_data.get("timeout_socket", 30),
                "timeout_transport": host_data.get("timeout_transport", 60),
                "port": host_data.get("port", 22),
                "transport": "asyncssh",
            }

            # 如果有enable密码，添加到连接参数
            if host_data.get("enable_password"):
                connection_params["auth_secondary"] = host_data["enable_password"]

            # 根据平台选择驱动
            platform = host_data.get("platform", "").lower()
            brand = host_data.get("brand", "").lower()

            if self.use_community:
                # 使用Scrapli-Community驱动
                if brand in ["cisco"] or "cisco" in platform:
                    if AsyncIOSXEDriver is None:
                        raise ImportError("AsyncIOSXEDriver 不可用。请安装所需的 scrapli 软件包.")
                    conn = AsyncIOSXEDriver(**connection_params)
                elif brand in ["huawei"] or "huawei" in platform:
                    if AsyncHuaweiVRPDriver is None:
                        raise ImportError("AsyncHuaweiVRPDriver 不可用。请安装所需的 scrapli-community 软件包。")
                    conn = AsyncHuaweiVRPDriver(**connection_params)
                elif brand in ["h3c"] or "h3c" in platform or "comware" in platform:
                    if AsyncHPComwareDriver is None:
                        raise ImportError("AsyncHPComwareDriver 不可用。请安装所需的 scrapli-community 软件包。")
                    conn = AsyncHPComwareDriver(**connection_params)
                else:
                    # 默认使用Cisco驱动
                    if AsyncHPComwareDriver is None:
                        raise ImportError("AsyncIOSXEDriver 不可用。请安装所需的 scrapli 软件包。")
                    conn = AsyncHPComwareDriver(**connection_params)
            else:
                # 回退到基础Scrapli
                from scrapli import AsyncScrapli

                if brand in ["cisco"] or "cisco" in platform:
                    connection_params["platform"] = "cisco_iosxe"
                elif brand in ["huawei"] or "huawei" in platform:
                    connection_params["platform"] = "huawei_vrp"
                elif brand in ["h3c"] or "h3c" in platform or "comware" in platform:
                    connection_params["platform"] = "hp_comware"
                else:
                    connection_params["platform"] = "cisco_iosxe"

                conn = AsyncScrapli(**connection_params)

            logger.debug(
                f"创建连接: {host_data['hostname']} ({brand}) 使用{'Community' if self.use_community else 'Standard'} Scrapli"
            )
            return conn

        except Exception as e:
            logger.error(f"创建连接失败 {host_data.get('hostname', 'unknown')}: {e}")
            raise

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

            except Exception as e:
                logger.error(f"连接失败 {host_data.get('hostname', 'unknown')}: {e}")
                raise
            finally:
                # 确保连接被关闭
                if conn and hasattr(conn, "isalive") and conn.isalive():
                    try:
                        await conn.close()
                        logger.debug(f"已关闭连接: {host_data.get('hostname', 'unknown')}")
                    except Exception as e:
                        logger.warning(f"关闭连接时出错 {host_data.get('hostname', 'unknown')}: {e}")

    async def execute_command_with_parsing(self, host_data: dict[str, Any], command: str) -> dict[str, Any]:
        """执行命令并自动解析

        Args:
            host_data: 主机连接信息
            command: 要执行的命令

        Returns:
            命令执行和解析结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            async with self.get_connection(host_data) as conn:
                # 尝试使用TextFSM解析
                if self.use_community:
                    try:
                        # 使用Scrapli-Community的parsed=True功能
                        response = await conn.send_command(command, strip_prompt=False)
                        parsed_response = await conn.send_command(command, strip_prompt=False)

                        elapsed_time = asyncio.get_event_loop().time() - start_time

                        return {
                            "hostname": host_data["hostname"],
                            "command": command,
                            "status": "success",
                            "raw_output": response.result,
                            "parsed_data": parsed_response.result if hasattr(parsed_response, "result") else [],
                            "parsing_method": "scrapli_community_textfsm",
                            "elapsed_time": round(elapsed_time, 3),
                        }
                    except Exception as parse_error:
                        logger.warning(f"Scrapli-Community解析失败，回退到原始输出: {parse_error}")
                        # 如果解析失败，返回原始输出
                        response = await conn.send_command(command, strip_prompt=False)
                        elapsed_time = asyncio.get_event_loop().time() - start_time

                        return {
                            "hostname": host_data["hostname"],
                            "command": command,
                            "status": "success",
                            "raw_output": response.result,
                            "parsed_data": [],
                            "parsing_method": "raw_only",
                            "parse_error": str(parse_error),
                            "elapsed_time": round(elapsed_time, 3),
                        }
                else:
                    # 使用基础Scrapli
                    response = await conn.send_command(command, strip_prompt=False)
                    elapsed_time = asyncio.get_event_loop().time() - start_time

                    return {
                        "hostname": host_data["hostname"],
                        "command": command,
                        "status": "success",
                        "raw_output": response.result,
                        "parsed_data": [],
                        "parsing_method": "raw_only",
                        "elapsed_time": round(elapsed_time, 3),
                    }

        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"命令执行失败 {host_data['hostname']}: {e}")
            return {
                "hostname": host_data["hostname"],
                "command": command,
                "status": "failed",
                "raw_output": "",
                "parsed_data": [],
                "error": str(e),
                "elapsed_time": round(elapsed_time, 3),
                "error_type": type(e).__name__,
            }


# 全局增强连接管理器实例
enhanced_connection_manager = EnhancedConnectionManager()
