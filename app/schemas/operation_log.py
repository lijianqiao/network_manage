"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_log.py
@DateTime: 2025/06/20 00:00:00
@Docs: 操作日志相关Pydantic校验模型
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.network_models import OperationStatusEnum

from .base import (
    BaseCreateSchema,
    BaseQueryParams,
    BaseResponseSchema,
    BatchOperationResponse,
    BulkCreateRequest,
    BulkDeleteRequest,
    PaginationResponse,
    TimeRangeQuery,
)


class OperationLogCreateRequest(BaseCreateSchema):
    """操作日志创建请求"""

    device_id: UUID | None = Field(default=None, description="操作的设备ID")
    template_id: UUID | None = Field(default=None, description="使用的模板ID")
    command_executed: str | None = Field(default=None, description="执行的命令")
    output_received: str | None = Field(default=None, description="设备返回的输出")
    parsed_output: dict[str, Any] | None = Field(default=None, description="解析后的输出")
    status: OperationStatusEnum = Field(description="操作状态")
    error_message: str | None = Field(default=None, description="错误信息")
    executed_by: str | None = Field(default=None, max_length=100, description="操作者")


class OperationLogResponse(BaseResponseSchema):
    """操作日志响应"""

    device_id: UUID | None = Field(description="设备ID")
    template_id: UUID | None = Field(description="模板ID")
    command_executed: str | None = Field(description="执行的命令")
    output_received: str | None = Field(description="设备输出")
    parsed_output: dict[str, Any] | None = Field(description="解析后输出")
    status: OperationStatusEnum = Field(description="操作状态")
    error_message: str | None = Field(description="错误信息")
    executed_by: str | None = Field(description="操作者")
    timestamp: datetime = Field(description="操作时间")

    # 关联信息
    device_name: str | None = Field(default=None, description="设备名称")
    device_ip: str | None = Field(default=None, description="设备IP")
    template_name: str | None = Field(default=None, description="模板名称")
    region_name: str | None = Field(default=None, description="区域名称")


class OperationLogListResponse(OperationLogResponse):
    """操作日志列表响应（简化版）"""

    # 隐藏详细输出信息以提高性能
    output_received: str | None = Field(default=None, description="设备输出（截断）")
    parsed_output: dict[str, Any] | None = Field(default=None, description="解析后输出（简化）")


class OperationLogDetailResponse(OperationLogResponse):
    """操作日志详情响应"""

    # 包含完整的输出信息和相关上下文
    execution_duration: float | None = Field(default=None, description="执行时长（秒）")
    command_count: int | None = Field(default=None, description="命令数量")
    output_size: int | None = Field(default=None, description="输出大小（字节）")


class OperationLogQueryParams(BaseQueryParams, TimeRangeQuery):
    """操作日志查询参数"""

    device_id: UUID | None = Field(default=None, description="按设备ID筛选")
    template_id: UUID | None = Field(default=None, description="按模板ID筛选")
    status: OperationStatusEnum | None = Field(default=None, description="按操作状态筛选")
    executed_by: str | None = Field(default=None, description="按操作者筛选")
    device_name: str | None = Field(default=None, description="按设备名称筛选")
    region_id: UUID | None = Field(default=None, description="按区域ID筛选")
    has_error: bool | None = Field(default=None, description="是否有错误")
    command_contains: str | None = Field(default=None, description="命令包含关键词")


class OperationLogStatsResponse(BaseResponseSchema):
    """操作日志统计响应"""

    total_operations: int = Field(description="总操作数")
    success_operations: int = Field(description="成功操作数")
    failed_operations: int = Field(description="失败操作数")
    pending_operations: int = Field(description="待处理操作数")
    success_rate: float = Field(description="成功率")

    # 时间统计
    today_operations: int = Field(description="今日操作数")
    week_operations: int = Field(description="本周操作数")
    month_operations: int = Field(description="本月操作数")

    # Top统计
    top_devices: list[dict[str, Any]] = Field(description="操作最多的设备")
    top_templates: list[dict[str, Any]] = Field(description="使用最多的模板")
    top_operators: list[dict[str, Any]] = Field(description="操作最多的用户")


class OperationLogTrendResponse(BaseResponseSchema):
    """操作日志趋势响应"""

    date: str = Field(description="日期")
    total_count: int = Field(description="总操作数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    success_rate: float = Field(description="成功率")


class OperationLogExportRequest(BaseCreateSchema):
    """操作日志导出请求"""

    device_ids: list[UUID] | None = Field(default=None, description="设备ID列表")
    start_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")
    status: OperationStatusEnum | None = Field(default=None, description="操作状态")
    executed_by: str | None = Field(default=None, description="操作者")
    include_output: bool = Field(default=False, description="是否包含输出内容")
    export_format: str = Field(default="xlsx", description="导出格式(xlsx|csv)")


class OperationLogBatchDeleteRequest(BaseCreateSchema):
    """批量删除操作日志请求"""

    log_ids: list[UUID] | None = Field(default=None, description="指定日志ID列表")
    before_date: datetime | None = Field(default=None, description="删除此日期之前的日志")
    status: OperationStatusEnum | None = Field(default=None, description="按状态删除")
    device_ids: list[UUID] | None = Field(default=None, description="按设备删除")
    keep_latest_count: int | None = Field(default=None, ge=0, description="每设备保留最新N条")


class OperationLogAnalysisResponse(BaseResponseSchema):
    """操作日志分析响应"""

    period: str = Field(description="分析周期")
    total_operations: int = Field(description="总操作数")
    unique_devices: int = Field(description="涉及设备数")
    unique_operators: int = Field(description="操作用户数")
    avg_operations_per_day: float = Field(description="日均操作数")
    peak_hour: int = Field(description="操作高峰时段")

    # 错误分析
    error_analysis: dict[str, int] = Field(description="错误类型统计")
    device_reliability: list[dict[str, Any]] = Field(description="设备可靠性分析")
    template_performance: list[dict[str, Any]] = Field(description="模板性能分析")


# 分页和批量操作类型别名
OperationLogPaginationResponse = PaginationResponse[OperationLogListResponse]
OperationLogBulkCreateRequest = BulkCreateRequest[OperationLogCreateRequest]
OperationLogBulkDeleteRequest = BulkDeleteRequest
OperationLogBatchOperationResponse = BatchOperationResponse

# 注意：操作日志通常不支持批量更新，因为它是审计记录
# OperationLogBulkUpdateRequest = BulkUpdateRequest  # 注释掉，不建议使用
