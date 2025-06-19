"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备相关Pydantic校验模型
"""

import ipaddress
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.network_models import DeviceStatusEnum, DeviceTypeEnum
from .base import (
    BaseCreateSchema,
    BaseQueryParams,
    BaseResponseSchema,
    BaseUpdateSchema,
    TimeRangeQuery
)


class DeviceCreateRequest(BaseCreateSchema):
    """设备创建请求"""
    name: str = Field(min_length=1, max_length=100, description="设备主机名")
    ip_address: str = Field(description="设备管理IP地址")
    region_id: UUID = Field(description="设备所属区域ID")
    device_group_id: UUID = Field(description="设备所属分组ID")
    model_id: UUID = Field(description="设备型号ID")
    device_type: DeviceTypeEnum = Field(description="设备类型")
    serial_number: Optional[str] = Field(default=None, max_length=100, description="设备序列号")
    is_dynamic_password: bool = Field(default=True, description="是否使用动态密码")
    cli_username: Optional[str] = Field(default=None, max_length=50, description="固定CLI账号")
    cli_password: Optional[str] = Field(default=None, description="固定CLI密码（明文，系统会自动加密）")
    enable_password: Optional[str] = Field(default=None, description="Enable密码（明文，系统会自动加密）")
    extra_info: Optional[Dict[str, Any]] = Field(default=None, description="扩展信息")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证设备名称"""
        if not v.strip():
            raise ValueError("设备名称不能为空")
        return v.strip()
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError("无效的IP地址格式")
    
    @field_validator('cli_username')
    @classmethod
    def validate_cli_username(cls, v: Optional[str], info) -> Optional[str]:
        """验证CLI用户名"""
        if info.data.get('is_dynamic_password') is False and not v:
            raise ValueError("使用固定密码时必须提供CLI用户名")
        return v
    
    @field_validator('cli_password')
    @classmethod
    def validate_cli_password(cls, v: Optional[str], info) -> Optional[str]:
        """验证CLI密码"""
        if info.data.get('is_dynamic_password') is False and not v:
            raise ValueError("使用固定密码时必须提供CLI密码")
        return v


class DeviceUpdateRequest(BaseUpdateSchema):
    """设备更新请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="设备主机名")
    ip_address: Optional[str] = Field(default=None, description="设备管理IP地址")
    region_id: Optional[UUID] = Field(default=None, description="设备所属区域ID")
    device_group_id: Optional[UUID] = Field(default=None, description="设备所属分组ID")
    model_id: Optional[UUID] = Field(default=None, description="设备型号ID")
    device_type: Optional[DeviceTypeEnum] = Field(default=None, description="设备类型")
    serial_number: Optional[str] = Field(default=None, max_length=100, description="设备序列号")
    is_dynamic_password: Optional[bool] = Field(default=None, description="是否使用动态密码")
    cli_username: Optional[str] = Field(default=None, max_length=50, description="固定CLI账号")
    cli_password: Optional[str] = Field(default=None, description="固定CLI密码")
    enable_password: Optional[str] = Field(default=None, description="Enable密码")
    status: Optional[DeviceStatusEnum] = Field(default=None, description="设备状态")
    extra_info: Optional[Dict[str, Any]] = Field(default=None, description="扩展信息")


class DeviceResponse(BaseResponseSchema):
    """设备响应"""
    name: str = Field(description="设备主机名")
    ip_address: str = Field(description="设备管理IP地址")
    region_id: UUID = Field(description="区域ID")
    device_group_id: UUID = Field(description="分组ID")
    model_id: UUID = Field(description="型号ID")
    device_type: DeviceTypeEnum = Field(description="设备类型")
    serial_number: Optional[str] = Field(description="设备序列号")
    is_dynamic_password: bool = Field(description="是否使用动态密码")
    cli_username: Optional[str] = Field(description="CLI账号")
    status: DeviceStatusEnum = Field(description="设备状态")
    extra_info: Optional[Dict[str, Any]] = Field(description="扩展信息")
    
    # 关联信息
    region_name: Optional[str] = Field(default=None, description="区域名称")
    device_group_name: Optional[str] = Field(default=None, description="分组名称")
    model_name: Optional[str] = Field(default=None, description="型号名称")
    brand_name: Optional[str] = Field(default=None, description="品牌名称")
    brand_platform_type: Optional[str] = Field(default=None, description="平台类型")


class DeviceListResponse(DeviceResponse):
    """设备列表响应"""
    # 隐藏敏感信息
    cli_username: Optional[str] = Field(default=None, description="CLI账号")
    extra_info: Optional[Dict[str, Any]] = Field(default=None, description="扩展信息")


class DeviceDetailResponse(DeviceResponse):
    """设备详情响应"""
    # 包含连接状态信息
    connection_status: Optional[dict] = Field(default=None, description="连接状态信息")
    recent_operations: Optional[List[dict]] = Field(default=None, description="最近操作记录")
    config_snapshots: Optional[List[dict]] = Field(default=None, description="配置快照")


class DeviceQueryParams(BaseQueryParams):
    """设备查询参数"""
    name: Optional[str] = Field(default=None, description="按设备名称筛选")
    ip_address: Optional[str] = Field(default=None, description="按IP地址筛选")
    region_id: Optional[UUID] = Field(default=None, description="按区域ID筛选")
    device_group_id: Optional[UUID] = Field(default=None, description="按分组ID筛选")
    device_type: Optional[DeviceTypeEnum] = Field(default=None, description="按设备类型筛选")
    status: Optional[DeviceStatusEnum] = Field(default=None, description="按状态筛选")
    brand_name: Optional[str] = Field(default=None, description="按品牌筛选")
    is_dynamic_password: Optional[bool] = Field(default=None, description="按密码类型筛选")
    has_serial_number: Optional[bool] = Field(default=None, description="是否有序列号")


class DeviceConnectionRequest(BaseCreateSchema):
    """设备连接请求"""
    device_id: UUID = Field(description="设备ID")
    username: Optional[str] = Field(default=None, description="连接用户名（覆盖默认）")
    password: Optional[str] = Field(default=None, description="连接密码（动态密码或覆盖固定密码）")
    enable_password: Optional[str] = Field(default=None, description="Enable密码（覆盖默认）")
    timeout: int = Field(default=30, ge=5, le=300, description="连接超时时间（秒）")


class DeviceConnectionResponse(BaseResponseSchema):
    """设备连接响应"""
    device_id: UUID = Field(description="设备ID")
    device_name: str = Field(description="设备名称")
    connection_status: str = Field(description="连接状态")
    connection_time: Optional[str] = Field(default=None, description="连接时间")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class DeviceCommandRequest(BaseCreateSchema):
    """设备命令执行请求"""
    device_ids: List[UUID] = Field(min_length=1, max_length=50, description="设备ID列表")
    commands: List[str] = Field(min_length=1, max_length=10, description="命令列表")
    username: Optional[str] = Field(default=None, description="连接用户名")
    password: Optional[str] = Field(default=None, description="连接密码")
    enable_password: Optional[str] = Field(default=None, description="Enable密码")
    timeout: int = Field(default=60, ge=10, le=600, description="命令执行超时时间（秒）")
    save_log: bool = Field(default=True, description="是否保存操作日志")


class DeviceCommandResponse(BaseResponseSchema):
    """设备命令执行响应"""
    device_id: UUID = Field(description="设备ID")
    device_name: str = Field(description="设备名称")
    commands: List[str] = Field(description="执行的命令")
    outputs: List[str] = Field(description="命令输出")
    execution_time: float = Field(description="执行时间（秒）")
    status: str = Field(description="执行状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class DeviceBatchCommandResponse(BaseResponseSchema):
    """批量设备命令执行响应"""
    total_devices: int = Field(description="总设备数")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    results: List[DeviceCommandResponse] = Field(description="详细结果")


class DeviceStatsResponse(BaseResponseSchema):
    """设备统计响应"""
    name: str = Field(description="设备名称")
    ip_address: str = Field(description="IP地址")
    device_type: DeviceTypeEnum = Field(description="设备类型")
    status: DeviceStatusEnum = Field(description="设备状态")
    region_name: str = Field(description="区域名称")
    brand_name: str = Field(description="品牌名称")
    last_operation_time: Optional[str] = Field(default=None, description="最后操作时间")
    operation_count: int = Field(description="总操作次数")
    success_rate: float = Field(description="操作成功率")


class DeviceBatchUpdateStatusRequest(BaseCreateSchema):
    """批量更新设备状态请求"""
    device_ids: List[UUID] = Field(min_length=1, max_length=100, description="设备ID列表")
    status: DeviceStatusEnum = Field(description="目标状态")
    reason: Optional[str] = Field(default=None, description="状态变更原因")
