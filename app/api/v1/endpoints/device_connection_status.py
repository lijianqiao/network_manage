"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_connection_status.py
@DateTime: 2025/06/23 00:00:00
@Docs: 设备连接状态管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.connection_status_service import ConnectionStatusService
from app.utils.logger import logger

router = APIRouter(prefix="/device-connection-status", tags=["设备连接状态"])


class ConnectionCheckRequest(BaseModel):
    """连接检查请求模型"""

    device_ids: list[UUID] = Field(..., description="设备ID列表")
    timeout: int = Field(default=30, ge=5, le=120, description="超时时间（秒）")
    check_ping: bool = Field(default=True, description="是否检查Ping连通性")
    check_snmp: bool = Field(default=False, description="是否检查SNMP")


class ConnectionStatusResponse(BaseModel):
    """连接状态响应模型"""

    device_id: str = Field(..., description="设备ID")
    device_name: str = Field(..., description="设备名称")
    ip_address: str = Field(..., description="设备IP地址")
    ping_status: str = Field(..., description="Ping状态")
    snmp_status: str = Field(..., description="SNMP状态")
    last_check_time: str = Field(..., description="最后检查时间")
    response_time: float | None = Field(None, description="响应时间（毫秒）")


class ConnectionStatsResponse(BaseModel):
    """连接统计响应模型"""

    total_devices: int = Field(..., description="设备总数")
    online_devices: int = Field(..., description="在线设备数")
    offline_devices: int = Field(..., description="离线设备数")
    unknown_devices: int = Field(..., description="状态未知设备数")
    success_rate: str = Field(..., description="连接成功率")


@router.get("/", response_model=list[ConnectionStatusResponse], summary="获取设备连接状态列表")
async def get_connection_status_list(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="限制记录数"),
    device_name: str | None = Query(None, description="设备名称过滤"),
    status: str | None = Query(None, description="状态过滤（online/offline/unknown）"),
    service: ConnectionStatusService = Depends(ConnectionStatusService),
):
    """获取设备连接状态列表"""
    try:
        result = await service.get_connection_status_list(
            skip=skip, limit=limit, device_name=device_name, status=status
        )
        return result
    except Exception as e:
        logger.error(f"获取连接状态列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取连接状态列表失败: {str(e)}") from e


@router.get("/{device_id}", response_model=ConnectionStatusResponse, summary="获取指定设备连接状态")
async def get_device_connection_status(
    device_id: UUID, service: ConnectionStatusService = Depends(ConnectionStatusService)
):
    """获取指定设备的连接状态"""
    try:
        result = await service.get_device_connection_status(device_id)
        return result
    except Exception as e:
        logger.error(f"获取设备连接状态失败 - 设备ID: {device_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取设备连接状态失败: {str(e)}") from e


@router.post("/check", response_model=list[ConnectionStatusResponse], summary="批量检查设备连通性")
async def check_device_connectivity(
    request: ConnectionCheckRequest, service: ConnectionStatusService = Depends(ConnectionStatusService)
):
    """批量检查设备连通性"""
    try:
        result = await service.check_devices_connectivity(
            device_ids=request.device_ids,
            timeout=request.timeout,
            check_ping=request.check_ping,
            check_snmp=request.check_snmp,
        )
        return result
    except Exception as e:
        logger.error(f"批量检查设备连通性失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量检查设备连通性失败: {str(e)}") from e


@router.get("/stats/summary", response_model=ConnectionStatsResponse, summary="获取连接状态统计")
async def get_connection_stats(service: ConnectionStatusService = Depends(ConnectionStatusService)):
    """获取连接状态统计信息"""
    try:
        result = await service.get_connection_stats()
        return result
    except Exception as e:
        logger.error(f"获取连接状态统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取连接状态统计失败: {str(e)}") from e


@router.post("/ping/{device_id}", summary="Ping指定设备")
async def ping_device(
    device_id: UUID,
    timeout: int = Query(default=5, ge=1, le=30, description="超时时间（秒）"),
    service: ConnectionStatusService = Depends(ConnectionStatusService),
):
    """Ping指定设备"""
    try:
        result = await service.ping_device(device_id, timeout)
        return result
    except Exception as e:
        logger.error(f"Ping设备失败 - 设备ID: {device_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"Ping设备失败: {str(e)}") from e


@router.post("/snmp/{device_id}", summary="SNMP检查指定设备")
async def snmp_check_device(
    device_id: UUID,
    timeout: int = Query(default=10, ge=1, le=30, description="超时时间（秒）"),
    service: ConnectionStatusService = Depends(ConnectionStatusService),
):
    """SNMP检查指定设备"""
    try:
        result = await service.snmp_check_device(device_id, timeout)
        return result
    except Exception as e:
        logger.error(f"SNMP检查设备失败 - 设备ID: {device_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"SNMP检查设备失败: {str(e)}") from e
