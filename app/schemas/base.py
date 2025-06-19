"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/06/20 00:00:00
@Docs: 基础Pydantic校验模型
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# 泛型类型变量
T = TypeVar("T")


class BaseSchema(BaseModel):
    """基础Schema类"""

    model_config = ConfigDict(
        from_attributes=True,  # 允许从ORM对象创建
        use_enum_values=True,  # 使用枚举值
        validate_assignment=True,  # 赋值时验证
        str_strip_whitespace=True,  # 自动去除字符串空白
        frozen=False,  # 允许修改
    )


class IDResponse(BaseSchema):
    """ID响应模型"""

    id: UUID = Field(description="资源ID")


class StatusResponse(BaseSchema):
    """状态响应模型"""

    success: bool = Field(description="操作是否成功")
    message: str = Field(description="状态消息")


class SuccessResponse(BaseSchema, Generic[T]):
    """统一成功响应模型"""

    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class ErrorResponse(BaseSchema):
    """统一错误响应模型"""

    success: bool = Field(default=False, description="请求是否成功")
    message: str = Field(description="错误消息")
    error_code: str | None = Field(default=None, description="错误代码")
    details: dict[str, Any] | None = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class PaginationInfo(BaseSchema):
    """分页信息模型"""

    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, le=100, description="每页数量")
    total: int = Field(ge=0, description="总记录数")
    total_pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginationResponse(BaseSchema, Generic[T]):
    """分页响应模型"""

    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="查询成功", description="响应消息")
    data: list[T] = Field(description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class BaseQueryParams(BaseSchema):
    """基础查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    search: str | None = Field(default=None, description="搜索关键词")
    order_by: str | None = Field(default=None, description="排序字段")
    order_desc: bool = Field(default=False, description="是否降序")


class TimeRangeQuery(BaseSchema):
    """时间范围查询参数"""

    start_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")

    def validate_time_range(self) -> "TimeRangeQuery":
        """验证时间范围"""
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("开始时间不能大于结束时间")
        return self


class BaseCreateSchema(BaseSchema):
    """基础创建Schema"""

    description: str | None = Field(default=None, max_length=500, description="描述信息")


class BaseUpdateSchema(BaseSchema):
    """基础更新Schema"""

    description: str | None = Field(default=None, max_length=500, description="描述信息")


class BaseResponseSchema(BaseSchema):
    """基础响应Schema"""

    id: UUID = Field(description="资源ID")
    description: str | None = Field(description="描述信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    is_deleted: bool = Field(description="是否已删除")


class BatchOperationRequest(BaseSchema, Generic[T]):
    """批量操作请求"""

    items: list[T] = Field(min_length=1, max_length=100, description="操作项目列表")


class BatchOperationResponse(BaseSchema):
    """批量操作响应"""

    success: bool = Field(description="操作是否成功")
    message: str = Field(description="操作消息")
    total: int = Field(description="总数量")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    failed_items: list[dict[str, Any]] | None = Field(default=None, description="失败项目详情")


class BulkCreateRequest(BatchOperationRequest[T]):
    """批量创建请求"""

    pass


class BulkUpdateRequest(BaseSchema):
    """批量更新请求"""

    ids: list[UUID] = Field(min_length=1, max_length=100, description="要更新的ID列表")
    update_data: dict[str, Any] = Field(description="更新数据")


class BulkDeleteRequest(BaseSchema):
    """批量删除请求"""

    ids: list[UUID] = Field(min_length=1, max_length=100, description="要删除的ID列表")
    soft_delete: bool = Field(default=True, description="是否软删除")


# 响应类型别名
ApiResponse = SuccessResponse[T] | ErrorResponse
ListResponse = PaginationResponse[T] | ErrorResponse
