"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: brand.py
@DateTime: 2025/06/20 00:00:00
@Docs: 品牌相关Pydantic校验模型
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


class BrandCreateRequest(BaseCreateSchema):
    """品牌创建请求"""
    name: str = Field(min_length=1, max_length=50, description="品牌名称")
    platform_type: str = Field(min_length=1, max_length=50, description="平台驱动类型")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证品牌名称"""
        if not v.strip():
            raise ValueError("品牌名称不能为空")
        return v.strip().upper()  # 品牌名统一大写
    
    @field_validator('platform_type')
    @classmethod
    def validate_platform_type(cls, v: str) -> str:
        """验证平台类型"""
        allowed_platforms = [
            'hp_comware', 'huawei_vrp', 'cisco_iosxe', 
            'cisco_iosxr', 'cisco_nxos', 'juniper_junos'
        ]
        if v not in allowed_platforms:
            raise ValueError(f"不支持的平台类型，支持的类型: {', '.join(allowed_platforms)}")
        return v


class BrandUpdateRequest(BaseUpdateSchema):
    """品牌更新请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50, description="品牌名称")
    platform_type: Optional[str] = Field(default=None, min_length=1, max_length=50, description="平台驱动类型")


class BrandResponse(BaseResponseSchema):
    """品牌响应"""
    name: str = Field(description="品牌名称")
    platform_type: str = Field(description="平台驱动类型")
    
    # 统计信息
    device_model_count: Optional[int] = Field(default=0, description="设备型号数量")
    device_count: Optional[int] = Field(default=0, description="设备数量")
    template_count: Optional[int] = Field(default=0, description="模板数量")


class BrandListResponse(BrandResponse):
    """品牌列表响应（简化版）"""
    pass


class BrandDetailResponse(BrandResponse):
    """品牌详情响应"""
    # 可以包含关联的设备型号等信息
    device_models: Optional[List[dict]] = Field(default=None, description="设备型号列表")
    supported_features: Optional[List[str]] = Field(default=None, description="支持的功能特性")


class BrandQueryParams(BaseQueryParams):
    """品牌查询参数"""
    name: Optional[str] = Field(default=None, description="按名称筛选")
    platform_type: Optional[str] = Field(default=None, description="按平台类型筛选")
    has_devices: Optional[bool] = Field(default=None, description="是否包含设备")


class BrandStatsResponse(BaseResponseSchema):
    """品牌统计响应"""
    name: str = Field(description="品牌名称")
    platform_type: str = Field(description="平台类型")
    total_models: int = Field(description="型号总数")
    total_devices: int = Field(description="设备总数")
    online_devices: int = Field(description="在线设备数")
    recent_operations: int = Field(description="近期操作数")
