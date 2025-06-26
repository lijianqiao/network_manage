"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_automation.py
@DateTime: 2025/06/23 13:30:00
@Docs: 网络自动化API端点 - 纯路由定义
"""

from typing import Any

from fastapi import APIRouter, Depends

from app.core.dependencies import get_network_automation_service
from app.schemas.network_automation import (
    CommandRequest,
    ConfigBackupRequest,
    ConfigDeployRequest,
    ConnectionStatsResponse,
    DeviceInfoRequest,
    HealthCheckRequest,
    MultiCommandRequest,
    PingRequest,
    TaskResponse,
    TemplateRenderRequest,
)
from app.services.network_automation_service import NetworkAutomationService

router = APIRouter(prefix="/automation", tags=["网络自动化"])


@router.post("/ping", summary="Ping连通性测试", response_model=TaskResponse)
async def ping_devices(
    request: PingRequest, automation_service: NetworkAutomationService = Depends(get_network_automation_service)
) -> dict[str, Any]:
    """对指定的设备、区域或分组执行Ping连通性测试"""
    return await automation_service.ping_devices(request)


@router.post("/command", summary="执行单条命令", response_model=TaskResponse)
async def execute_command(
    request: CommandRequest, automation_service: NetworkAutomationService = Depends(get_network_automation_service)
) -> dict[str, Any]:
    """在指定的设备、区域或分组上执行单条命令"""
    return await automation_service.execute_command(request, request.command)


@router.post("/commands", summary="执行多条命令", response_model=TaskResponse)
async def execute_commands(
    request: MultiCommandRequest, automation_service: NetworkAutomationService = Depends(get_network_automation_service)
) -> dict[str, Any]:
    """在指定的设备、区域或分组上执行多条命令"""
    return await automation_service.execute_commands(request, request.commands)


@router.post("/backup", summary="备份设备配置", response_model=TaskResponse)
async def backup_configuration(
    request: ConfigBackupRequest, automation_service: NetworkAutomationService = Depends(get_network_automation_service)
) -> dict[str, Any]:
    """备份指定设备、区域或分组的配置"""
    return await automation_service.backup_configuration(request)


@router.post("/deploy", summary="部署配置", response_model=TaskResponse)
async def deploy_configuration(
    request: ConfigDeployRequest, automation_service: NetworkAutomationService = Depends(get_network_automation_service)
) -> dict[str, Any]:
    """在指定的设备、区域或分组上部署配置"""
    return await automation_service.deploy_configuration(request, request.config_commands)


@router.post("/template", summary="模板渲染", response_model=TaskResponse)
async def render_template(
    request: TemplateRenderRequest,
    automation_service: NetworkAutomationService = Depends(get_network_automation_service),
) -> dict[str, Any]:
    """使用模板渲染配置并应用到指定设备、区域或分组"""
    return await automation_service.render_template(request, request.template_content, request.template_vars)


@router.post("/device-info", summary="获取设备信息", response_model=TaskResponse)
async def get_device_info(
    request: DeviceInfoRequest, automation_service: NetworkAutomationService = Depends(get_network_automation_service)
) -> dict[str, Any]:
    """获取指定设备、区域或分组的设备信息"""
    return await automation_service.get_device_info(request)


@router.post("/health-check", summary="设备健康检查", response_model=TaskResponse)
async def health_check(
    request: HealthCheckRequest, automation_service: NetworkAutomationService = Depends(get_network_automation_service)
) -> dict[str, Any]:
    """对指定设备、区域或分组执行健康检查"""
    return await automation_service.health_check(request)


@router.get("/connection-stats", summary="获取连接池统计", response_model=ConnectionStatsResponse)
async def get_connection_stats(
    automation_service: NetworkAutomationService = Depends(get_network_automation_service),
) -> dict[str, Any]:
    """获取连接池的统计信息"""
    return await automation_service.get_connection_stats()
