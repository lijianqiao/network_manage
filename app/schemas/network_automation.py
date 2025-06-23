"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_automation.py
@DateTime: 2025/06/23 13:30:00
@Docs: 网络自动化相关的Pydantic模型
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """任务请求基础模型"""

    device_ids: list[UUID] | None = Field(None, description="设备ID列表")
    region_id: UUID | None = Field(None, description="区域ID")
    group_id: UUID | None = Field(None, description="设备分组ID")
    runtime_credentials: dict[str, Any] | None = Field(None, description="运行时凭据（如OTP等）")


class PingRequest(TaskRequest):
    """Ping测试请求"""

    pass


class CommandRequest(TaskRequest):
    """命令执行请求"""

    command: str = Field(..., description="要执行的命令")


class MultiCommandRequest(TaskRequest):
    """多命令执行请求"""

    commands: list[str] = Field(..., description="要执行的命令列表")


class ConfigBackupRequest(TaskRequest):
    """配置备份请求"""

    pass


class ConfigDeployRequest(TaskRequest):
    """配置部署请求"""

    config_commands: list[str] = Field(..., description="要部署的配置命令列表")


class TemplateRenderRequest(TaskRequest):
    """模板渲染请求"""

    template_content: str = Field(..., description="Jinja2模板内容")
    template_vars: dict[str, Any] = Field(default_factory=dict, description="模板变量")


class DeviceInfoRequest(TaskRequest):
    """设备信息获取请求"""

    pass


class HealthCheckRequest(TaskRequest):
    """健康检查请求"""

    pass


class TaskResponse(BaseModel):
    """任务响应基础模型"""

    total_hosts: int = Field(..., description="总主机数量")
    success_count: int = Field(..., description="成功数量")
    failure_count: int = Field(..., description="失败数量")
    results: dict[str, Any] = Field(..., description="详细结果")
    failed_hosts: list[str] = Field(..., description="失败主机列表")
    successful_hosts: list[str] = Field(..., description="成功主机列表")


class ConnectionStatsResponse(BaseModel):
    """连接池统计响应模型"""

    max_connections: int = Field(..., description="最大连接数")
    available_connections: int = Field(..., description="可用连接数")
    active_connections: int = Field(..., description="活跃连接数")
    transport: str = Field(..., description="传输协议")
    platform_support: str = Field(..., description="平台支持")
