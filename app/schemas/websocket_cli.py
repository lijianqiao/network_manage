"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: websocket_cli.py
@DateTime: 2025/06/26 16:00:00
@Docs: WebSocket CLI交互相关的Pydantic模型
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CLIConnectionRequest(BaseModel):
    """CLI连接请求"""

    device_id: UUID = Field(..., description="设备ID")
    username: str | None = Field(None, description="连接用户名")
    password: str | None = Field(None, description="连接密码")
    enable_password: str | None = Field(None, description="Enable密码")
    timeout: int = Field(default=600, description="会话超时时间（秒）")


class CLICommandRequest(BaseModel):
    """CLI命令请求"""

    command: str = Field(..., description="要执行的命令")
    timeout: int = Field(default=30, description="命令超时时间（秒）")


class CLIMessage(BaseModel):
    """CLI消息基类"""

    type: str = Field(..., description="消息类型")
    data: dict[str, Any] = Field(default_factory=dict, description="消息数据")
    timestamp: str = Field(..., description="时间戳")


class CLIConnectMessage(CLIMessage):
    """CLI连接消息"""

    type: str = Field(default="connect", description="消息类型")
    device_info: dict[str, Any] = Field(default_factory=dict, description="设备信息")


class CLICommandMessage(CLIMessage):
    """CLI命令消息"""

    type: str = Field(default="command", description="消息类型")
    command: str = Field(..., description="执行的命令")


class CLIResponseMessage(CLIMessage):
    """CLI响应消息"""

    type: str = Field(default="response", description="消息类型")
    output: str = Field(..., description="命令输出")
    success: bool = Field(..., description="是否成功")


class CLIErrorMessage(CLIMessage):
    """CLI错误消息"""

    type: str = Field(default="error", description="消息类型")
    error: str = Field(..., description="错误信息")
    error_code: str | None = Field(None, description="错误代码")


class CLIStatusMessage(CLIMessage):
    """CLI状态消息"""

    type: str = Field(default="status", description="消息类型")
    status: str = Field(..., description="状态信息")
    connection_active: bool = Field(..., description="连接是否活跃")


class CLIDisconnectMessage(CLIMessage):
    """CLI断开连接消息"""

    type: str = Field(default="disconnect", description="消息类型")
    reason: str = Field(..., description="断开原因")
