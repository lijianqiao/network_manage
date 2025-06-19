"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_group.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备分组相关Pydantic校验模型
"""

from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .base import (
    BaseCreateSchema,
    BaseQueryParams,
    BaseResponseSchema,
    BaseUpdateSchema
)


class DeviceGroupCreateRequest(BaseCreateSchema):
    """设备分组创建请求"""
    name: str = Field(min_length=1, max_length=100, description="分组名称")
    region_id: Optional[UUID] = Field(default=None, description="关联区域ID（可选）")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证分组名称"""
        if not v.strip():
            raise ValueError("分组名称不能为空")
        return v.strip()


class DeviceGroupUpdateRequest(BaseUpdateSchema):
    """设备分组更新请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="分组名称")
    region_id: Optional[UUID] = Field(default=None, description="关联区域ID")


class DeviceGroupResponse(BaseResponseSchema):
    """设备分组响应"""
    name: str = Field(description="分组名称")
    region_id: Optional[UUID] = Field(description="区域ID")
    
    # 关联区域信息
    region_name: Optional[str] = Field(default=None, description="区域名称")
    
    # 统计信息
    device_count: Optional[int] = Field(default=0, description="分组内设备数量")


class DeviceGroupListResponse(DeviceGroupResponse):
    """设备分组列表响应（简化版）"""
    pass


class DeviceGroupDetailResponse(DeviceGroupResponse):
    """设备分组详情响应"""
    # 可以包含分组内的设备列表
    devices: Optional[List[dict]] = Field(default=None, description="分组内设备列表")
    device_types: Optional[dict] = Field(default=None, description="设备类型统计")


class DeviceGroupQueryParams(BaseQueryParams):
    """设备分组查询参数"""
    name: Optional[str] = Field(default=None, description="按分组名称筛选")
    region_id: Optional[UUID] = Field(default=None, description="按区域ID筛选")
    region_name: Optional[str] = Field(default=None, description="按区域名称筛选")
    has_devices: Optional[bool] = Field(default=None, description="是否包含设备")


class DeviceGroupStatsResponse(BaseResponseSchema):
    """设备分组统计响应"""
    name: str = Field(description="分组名称")
    region_name: Optional[str] = Field(description="区域名称")
    total_devices: int = Field(description="总设备数")
    online_devices: int = Field(description="在线设备数")
    offline_devices: int = Field(description="离线设备数")
    switch_count: int = Field(description="交换机数量")
    router_count: int = Field(description="路由器数量")


class DeviceGroupBatchAssignRequest(BaseCreateSchema):
    """设备分组批量分配请求"""
    group_id: UUID = Field(description="目标分组ID")
    device_ids: List[UUID] = Field(min_length=1, max_length=100, description="设备ID列表")
