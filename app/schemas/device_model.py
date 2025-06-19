"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_model.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备型号相关Pydantic校验模型
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


class DeviceModelCreateRequest(BaseCreateSchema):
    """设备型号创建请求"""
    name: str = Field(min_length=1, max_length=100, description="设备型号名称")
    brand_id: UUID = Field(description="关联品牌ID")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证型号名称"""
        if not v.strip():
            raise ValueError("设备型号名称不能为空")
        return v.strip()


class DeviceModelUpdateRequest(BaseUpdateSchema):
    """设备型号更新请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="设备型号名称")
    brand_id: Optional[UUID] = Field(default=None, description="关联品牌ID")


class DeviceModelResponse(BaseResponseSchema):
    """设备型号响应"""
    name: str = Field(description="设备型号名称")
    brand_id: UUID = Field(description="品牌ID")
    
    # 关联品牌信息
    brand_name: Optional[str] = Field(default=None, description="品牌名称")
    brand_platform_type: Optional[str] = Field(default=None, description="品牌平台类型")
    
    # 统计信息
    device_count: Optional[int] = Field(default=0, description="使用此型号的设备数量")


class DeviceModelListResponse(DeviceModelResponse):
    """设备型号列表响应（简化版）"""
    pass


class DeviceModelDetailResponse(DeviceModelResponse):
    """设备型号详情响应"""
    # 可以包含使用此型号的设备列表
    devices: Optional[List[dict]] = Field(default=None, description="使用此型号的设备列表")
    specifications: Optional[dict] = Field(default=None, description="设备规格参数")


class DeviceModelQueryParams(BaseQueryParams):
    """设备型号查询参数"""
    name: Optional[str] = Field(default=None, description="按型号名称筛选")
    brand_id: Optional[UUID] = Field(default=None, description="按品牌ID筛选")
    brand_name: Optional[str] = Field(default=None, description="按品牌名称筛选")
    has_devices: Optional[bool] = Field(default=None, description="是否包含设备")


class DeviceModelStatsResponse(BaseResponseSchema):
    """设备型号统计响应"""
    name: str = Field(description="设备型号名称")
    brand_name: str = Field(description="品牌名称")
    total_devices: int = Field(description="总设备数")
    online_devices: int = Field(description="在线设备数")
    offline_devices: int = Field(description="离线设备数")
    recent_additions: int = Field(description="近期新增设备数")
