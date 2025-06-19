"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region.py
@DateTime: 2025/06/20 00:00:00
@Docs: 区域相关Pydantic校验模型
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


class RegionCreateRequest(BaseCreateSchema):
    """区域创建请求"""
    name: str = Field(min_length=1, max_length=100, description="区域名称")
    snmp_community_string: str = Field(min_length=1, max_length=100, description="SNMP社区字符串")
    default_cli_username: str = Field(min_length=1, max_length=50, description="默认CLI账号")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证区域名称"""
        if not v.strip():
            raise ValueError("区域名称不能为空")
        return v.strip()


class RegionUpdateRequest(BaseUpdateSchema):
    """区域更新请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="区域名称")
    snmp_community_string: Optional[str] = Field(default=None, min_length=1, max_length=100, description="SNMP社区字符串")
    default_cli_username: Optional[str] = Field(default=None, min_length=1, max_length=50, description="默认CLI账号")


class RegionResponse(BaseResponseSchema):
    """区域响应"""
    name: str = Field(description="区域名称")
    snmp_community_string: str = Field(description="SNMP社区字符串")
    default_cli_username: str = Field(description="默认CLI账号")
    
    # 统计信息
    device_count: Optional[int] = Field(default=0, description="设备数量")
    device_group_count: Optional[int] = Field(default=0, description="设备分组数量")


class RegionListResponse(RegionResponse):
    """区域列表响应（简化版）"""
    pass


class RegionDetailResponse(RegionResponse):
    """区域详情响应"""
    # 可以包含关联的设备分组等信息
    device_groups: Optional[List[dict]] = Field(default=None, description="设备分组列表")


class RegionQueryParams(BaseQueryParams):
    """区域查询参数"""
    name: Optional[str] = Field(default=None, description="按名称筛选")
    has_devices: Optional[bool] = Field(default=None, description="是否包含设备")


class RegionStatsResponse(BaseResponseSchema):
    """区域统计响应"""
    name: str = Field(description="区域名称")
    total_devices: int = Field(description="总设备数")
    online_devices: int = Field(description="在线设备数")
    offline_devices: int = Field(description="离线设备数")
    device_groups: int = Field(description="设备分组数")
    recent_operations: int = Field(description="近期操作数")
