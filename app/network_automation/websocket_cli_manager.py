"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: websocket_cli_manager.py
@DateTime: 2025/06/26 16:00:00
@Docs: WebSocket CLI会话管理器
"""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from scrapli.exceptions import ScrapliException

from app.core.credential_manager import CredentialManager
from app.core.exceptions import DeviceAuthenticationError, DeviceConnectionError
from app.models.network_models import Device
from app.network_automation.connection_manager import ScrapliConnectionManager
from app.schemas.websocket_cli import (
    CLICommandMessage,
    CLIConnectMessage,
    CLIDisconnectMessage,
    CLIErrorMessage,
    CLIResponseMessage,
)
from app.utils.logger import logger


class CLISession:
    """CLI会话类"""

    def __init__(self, session_id: str, device_id: UUID, websocket: WebSocket):
        """初始化CLI会话

        Args:
            session_id: 会话ID
            device_id: 设备ID
            websocket: WebSocket连接
        """
        self.session_id = session_id
        self.device_id = device_id
        self.websocket = websocket
        self.device: Device | None = None
        self.connection = None
        self.connection_manager = ScrapliConnectionManager()
        self.credential_manager = CredentialManager()
        self.is_connected = False
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self._command_lock = asyncio.Lock()

    async def connect_device(self, credentials: dict[str, Any] | None = None) -> bool:
        """连接到设备

        Args:
            credentials: 连接凭据

        Returns:
            连接是否成功
        """
        try:
            # 获取设备信息
            self.device = await Device.get(id=self.device_id)
            await self.device.fetch_related("region", "model__brand")

            # 解析凭据
            device_credentials = await self.credential_manager.resolve_device_credentials(self.device, credentials)

            # 创建连接
            self.connection = await self.connection_manager.create_connection(device_credentials)
            await self.connection.open()

            self.is_connected = True
            self.last_activity = datetime.now()

            # 发送连接成功消息
            await self._send_message(
                CLIConnectMessage(
                    timestamp=datetime.now().isoformat(),
                    device_info={
                        "device_id": str(self.device_id),
                        "hostname": self.device.name,
                        "ip_address": self.device.ip_address,
                        "platform": self.device.model.brand.platform_type,
                        "brand": self.device.model.brand.name,
                        "model": self.device.model.name,
                    },
                )
            )

            logger.info(f"CLI会话连接成功: {self.session_id} -> {self.device.ip_address}")
            return True

        except DeviceAuthenticationError as e:
            await self._send_error("设备认证失败", str(e))
            return False
        except DeviceConnectionError as e:
            await self._send_error("设备连接失败", str(e))
            return False
        except Exception as e:
            logger.error(f"CLI会话连接异常: {e}")
            await self._send_error("连接异常", str(e))
            return False

    async def execute_command(self, command: str, timeout: int = 30) -> bool:
        """执行命令

        Args:
            command: 要执行的命令
            timeout: 超时时间

        Returns:
            执行是否成功
        """
        if not self.is_connected or not self.connection:
            await self._send_error("设备未连接", "请先连接到设备")
            return False

        async with self._command_lock:
            try:
                self.last_activity = datetime.now()

                # 发送命令执行开始消息
                await self._send_message(CLICommandMessage(timestamp=datetime.now().isoformat(), command=command))

                # 执行命令
                logger.info(f"CLI会话执行命令: {self.session_id} -> {command}")

                # 使用Scrapli执行命令
                result = await self.connection.send_command(command, timeout_ops=timeout)

                # 发送响应消息
                await self._send_message(
                    CLIResponseMessage(
                        timestamp=datetime.now().isoformat(), output=result.result, success=not result.failed
                    )
                )

                return not result.failed

            except ScrapliException as e:
                logger.error(f"CLI命令执行失败: {e}")
                await self._send_error("命令执行失败", str(e))
                return False
            except TimeoutError:
                await self._send_error("命令执行超时", f"命令 '{command}' 执行超时")
                return False
            except Exception as e:
                logger.error(f"CLI命令执行异常: {e}")
                await self._send_error("执行异常", str(e))
                return False

    async def get_status(self) -> dict[str, Any]:
        """获取会话状态"""
        return {
            "session_id": self.session_id,
            "device_id": str(self.device_id),
            "is_connected": self.is_connected,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "device_info": {
                "hostname": self.device.name if self.device else "Unknown",
                "ip_address": self.device.ip_address if self.device else "Unknown",
            }
            if self.device
            else None,
        }

    async def disconnect(self, reason: str = "用户断开连接"):
        """断开连接"""
        try:
            if self.connection and self.connection.isalive():
                await self.connection.close()

            self.is_connected = False

            # 发送断开连接消息
            await self._send_message(CLIDisconnectMessage(timestamp=datetime.now().isoformat(), reason=reason))

            logger.info(f"CLI会话断开连接: {self.session_id} - {reason}")

        except Exception as e:
            logger.error(f"CLI会话断开连接异常: {e}")

    async def _send_message(self, message: Any):
        """发送WebSocket消息"""
        try:
            if self.websocket:
                await self.websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.debug(f"发送WebSocket消息失败: {e}")

    async def _send_error(self, error: str, detail: str = ""):
        """发送错误消息"""
        await self._send_message(
            CLIErrorMessage(timestamp=datetime.now().isoformat(), error=error, error_code=None, data={"detail": detail})
        )


class CLISessionByHost:
    """基于主机地址的CLI会话类"""

    def __init__(self, session_id: str, host: str, websocket: WebSocket, device: Device | None = None):
        """初始化CLI会话

        Args:
            session_id: 会话ID
            host: 主机IP地址或主机名
            websocket: WebSocket连接
            device: 设备对象（可选）
        """
        self.session_id = session_id
        self.host = host
        self.websocket = websocket
        self.device = device
        self.connection = None
        self.connection_manager = ScrapliConnectionManager()
        self.credential_manager = CredentialManager()
        self.is_connected = False
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self._command_lock = asyncio.Lock()

    async def connect_device(self, credentials: dict[str, Any] | None = None) -> bool:
        """连接到设备

        Args:
            credentials: 连接凭据

        Returns:
            连接是否成功
        """
        try:
            # 构建连接参数
            if self.device:
                # 如果设备在数据库中，使用数据库信息
                device_credentials = await self.credential_manager.resolve_device_credentials(self.device, credentials)
            else:
                # 直接使用IP连接
                device_credentials = {
                    "hostname": self.host,
                    "username": credentials.get("username", "admin") if credentials else "admin",
                    "password": credentials.get("password", "") if credentials else "",
                    "enable_password": credentials.get("enable_password") if credentials else None,
                    "platform": credentials.get("platform", "generic") if credentials else "generic",
                    "port": credentials.get("port", 22) if credentials else 22,
                    "timeout_socket": 30,
                    "timeout_transport": 60,
                }

            # 创建连接
            self.connection = await self.connection_manager.create_connection(device_credentials)
            await self.connection.open()

            self.is_connected = True
            self.last_activity = datetime.now()

            # 发送连接成功消息
            device_info = {
                "host": self.host,
                "hostname": self.device.name if self.device else self.host,
                "ip_address": self.host,
            }

            if self.device:
                device_info.update(
                    {
                        "platform": self.device.model.brand.platform_type,
                        "brand": self.device.model.brand.name,
                        "model": self.device.model.name,
                    }
                )

            await self._send_message(
                CLIConnectMessage(
                    timestamp=datetime.now().isoformat(),
                    device_info=device_info,
                )
            )

            logger.info(f"CLI会话连接成功: {self.session_id} -> {self.host}")
            return True

        except DeviceAuthenticationError as e:
            await self._send_error("设备认证失败", str(e))
            return False
        except DeviceConnectionError as e:
            await self._send_error("设备连接失败", str(e))
            return False
        except Exception as e:
            logger.error(f"CLI会话连接异常: {e}")
            await self._send_error("连接异常", str(e))
            return False

    async def execute_command(self, command: str, timeout: int = 30) -> bool:
        """执行命令

        Args:
            command: 要执行的命令
            timeout: 超时时间

        Returns:
            执行是否成功
        """
        if not self.is_connected or not self.connection:
            await self._send_error("设备未连接", "请先连接到设备")
            return False

        async with self._command_lock:
            try:
                self.last_activity = datetime.now()

                # 发送命令执行开始消息
                await self._send_message(CLICommandMessage(timestamp=datetime.now().isoformat(), command=command))

                # 执行命令
                logger.info(f"CLI会话执行命令: {self.session_id} -> {command}")

                # 使用Scrapli执行命令
                result = await self.connection.send_command(command, timeout_ops=timeout)

                # 发送响应消息
                await self._send_message(
                    CLIResponseMessage(
                        timestamp=datetime.now().isoformat(), output=result.result, success=not result.failed
                    )
                )

                return not result.failed

            except ScrapliException as e:
                logger.error(f"CLI命令执行失败: {e}")
                await self._send_error("命令执行失败", str(e))
                return False
            except TimeoutError:
                await self._send_error("命令执行超时", f"命令 '{command}' 执行超时")
                return False
            except Exception as e:
                logger.error(f"CLI命令执行异常: {e}")
                await self._send_error("执行异常", str(e))
                return False

    async def get_status(self) -> dict[str, Any]:
        """获取会话状态"""
        return {
            "session_id": self.session_id,
            "host": self.host,
            "is_connected": self.is_connected,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "device_info": {
                "hostname": self.device.name if self.device else self.host,
                "ip_address": self.host,
            },
        }

    async def disconnect(self, reason: str = "用户断开连接"):
        """断开连接"""
        try:
            if self.connection and self.connection.isalive():
                await self.connection.close()

            self.is_connected = False

            # 发送断开连接消息
            await self._send_message(CLIDisconnectMessage(timestamp=datetime.now().isoformat(), reason=reason))

            logger.info(f"CLI会话断开连接: {self.session_id} - {reason}")

        except Exception as e:
            logger.error(f"CLI会话断开连接异常: {e}")

    async def _send_message(self, message: Any):
        """发送WebSocket消息"""
        try:
            if self.websocket:
                await self.websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.debug(f"发送WebSocket消息失败: {e}")

    async def _send_error(self, error: str, detail: str = ""):
        """发送错误消息"""
        await self._send_message(
            CLIErrorMessage(timestamp=datetime.now().isoformat(), error=error, error_code=None, data={"detail": detail})
        )


class WebSocketCLIManager:
    """WebSocket CLI管理器"""

    def __init__(self):
        """初始化管理器"""
        self.sessions: dict[str, CLISession | CLISessionByHost] = {}
        self.session_timeout = 600  # 10分钟超时
        self._cleanup_task = None

    async def start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def create_session(self, session_id: str, device_id: UUID, websocket: WebSocket) -> CLISession:
        """创建新会话

        Args:
            session_id: 会话ID
            device_id: 设备ID
            websocket: WebSocket连接

        Returns:
            创建的会话
        """
        # 如果已存在会话，先断开
        if session_id in self.sessions:
            await self.remove_session(session_id)

        session = CLISession(session_id, device_id, websocket)
        self.sessions[session_id] = session

        # 启动清理任务（如果还没有启动）
        await self.start_cleanup_task()

        logger.info(f"创建CLI会话: {session_id} for device {device_id}")
        return session

    async def create_session_by_host(self, session_id: str, host: str, websocket: WebSocket) -> CLISessionByHost:
        """基于主机地址创建新会话

        Args:
            session_id: 会话ID
            host: 主机IP地址或主机名
            websocket: WebSocket连接

        Returns:
            创建的会话
        """
        # 如果已存在会话，先断开
        if session_id in self.sessions:
            await self.remove_session(session_id)

        # 查找设备记录（如果存在）
        device = None
        try:
            device = await Device.filter(ip_address=host).first()
            if device:
                await device.fetch_related("region", "model__brand")
        except Exception:
            # 设备不在数据库中，直接使用IP连接
            pass

        session = CLISessionByHost(session_id, host, websocket, device)
        self.sessions[session_id] = session

        # 启动清理任务（如果还没有启动）
        await self.start_cleanup_task()

        logger.info(f"创建CLI会话: {session_id} for host {host}")
        return session

    async def get_session(self, session_id: str) -> CLISession | CLISessionByHost | None:
        """获取会话"""
        return self.sessions.get(session_id)

    async def remove_session(self, session_id: str):
        """移除会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session.disconnect("会话已关闭")
            del self.sessions[session_id]
            logger.info(f"移除CLI会话: {session_id}")

    async def handle_websocket_disconnect(self, session_id: str):
        """处理WebSocket断开连接"""
        await self.remove_session(session_id)

    async def get_sessions_status(self) -> dict[str, Any]:
        """获取所有会话状态"""
        sessions_status = {}
        for session_id, session in self.sessions.items():
            sessions_status[session_id] = await session.get_status()

        return {"total_sessions": len(self.sessions), "sessions": sessions_status}

    async def _cleanup_expired_sessions(self):
        """清理过期会话"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次

                current_time = datetime.now()
                expired_sessions = []

                for session_id, session in self.sessions.items():
                    time_diff = (current_time - session.last_activity).total_seconds()
                    if time_diff > self.session_timeout:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    await self.remove_session(session_id)
                    logger.info(f"清理过期CLI会话: {session_id}")

            except Exception as e:
                logger.error(f"清理过期会话异常: {e}")


# 全局CLI管理器实例
websocket_cli_manager = WebSocketCLIManager()
