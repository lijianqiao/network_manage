"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: rollback_operation.py
@DateTime: 2025/06/20 00:00:00
@Docs: 回滚操作相关Pydantic校验模型
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.models.network_models import RollbackStatusEnum

from .base import BaseCreateSchema, BaseQueryParams, BaseResponseSchema, BaseUpdateSchema, TimeRangeQuery


class RollbackOperationCreateRequest(BaseCreateSchema):
    """回滚操作创建请求"""

    original_operation_id: UUID = Field(description="原始操作记录ID")
    target_snapshot_id: UUID = Field(description="目标回滚快照ID")
    executed_by: str = Field(min_length=1, max_length=100, description="执行回滚的操作者")
    rollback_reason: str | None = Field(default=None, description="回滚原因")

    @field_validator("executed_by")
    @classmethod
    def validate_executed_by(cls, v: str) -> str:
        """验证操作者"""
        if not v.strip():
            raise ValueError("操作者不能为空")
        return v.strip()


class RollbackOperationUpdateRequest(BaseUpdateSchema):
    """回滚操作更新请求"""

    rollback_status: RollbackStatusEnum | None = Field(default=None, description="回滚状态")
    executed_by: str | None = Field(default=None, min_length=1, max_length=100, description="执行回滚的操作者")
    rollback_reason: str | None = Field(default=None, description="回滚原因")


class RollbackOperationResponse(BaseResponseSchema):
    """回滚操作响应"""

    original_operation_id: UUID = Field(description="原始操作记录ID")
    target_snapshot_id: UUID = Field(description="目标回滚快照ID")
    rollback_status: RollbackStatusEnum = Field(description="回滚状态")
    executed_by: str = Field(description="执行回滚的操作者")
    executed_at: datetime = Field(description="回滚执行时间")
    rollback_reason: str | None = Field(description="回滚原因")

    # 关联信息
    device_id: UUID | None = Field(default=None, description="设备ID")
    device_name: str | None = Field(default=None, description="设备名称")
    device_ip: str | None = Field(default=None, description="设备IP")
    original_operation_type: str | None = Field(default=None, description="原始操作类型")
    snapshot_type: str | None = Field(default=None, description="快照类型")

    # 执行统计
    rollback_duration: float | None = Field(default=None, description="回滚耗时（秒）")
    rollback_attempts: int | None = Field(default=None, description="回滚尝试次数")


class RollbackOperationListResponse(BaseResponseSchema):
    """回滚操作列表响应（简化版）"""

    original_operation_id: UUID = Field(description="原始操作记录ID")
    target_snapshot_id: UUID = Field(description="目标回滚快照ID")
    rollback_status: RollbackStatusEnum = Field(description="回滚状态")
    executed_by: str = Field(description="执行者")
    executed_at: datetime = Field(description="执行时间")

    # 关联信息
    device_name: str | None = Field(default=None, description="设备名称")
    device_ip: str | None = Field(default=None, description="设备IP")

    # 简化统计
    rollback_duration: float | None = Field(default=None, description="回滚耗时（秒）")


class RollbackOperationDetailResponse(RollbackOperationResponse):
    """回滚操作详情响应"""

    # 包含详细的回滚过程信息
    rollback_log: list[dict[str, Any]] | None = Field(default=None, description="回滚日志")
    validation_results: dict[str, Any] | None = Field(default=None, description="验证结果")
    related_snapshots: list[dict[str, Any]] | None = Field(default=None, description="相关快照")


class RollbackOperationQueryParams(BaseQueryParams, TimeRangeQuery):
    """回滚操作查询参数"""

    original_operation_id: UUID | None = Field(default=None, description="按原始操作ID筛选")
    target_snapshot_id: UUID | None = Field(default=None, description="按目标快照ID筛选")
    rollback_status: RollbackStatusEnum | None = Field(default=None, description="按回滚状态筛选")
    executed_by: str | None = Field(default=None, description="按执行者筛选")
    device_id: UUID | None = Field(default=None, description="按设备ID筛选")
    device_name: str | None = Field(default=None, description="按设备名称筛选")
    region_id: UUID | None = Field(default=None, description="按区域ID筛选")
    duration_min: float | None = Field(default=None, ge=0, description="最小耗时（秒）")
    duration_max: float | None = Field(default=None, ge=0, description="最大耗时（秒）")


class RollbackExecuteRequest(BaseCreateSchema):
    """回滚执行请求"""

    operation_log_id: UUID = Field(description="要回滚的操作记录ID")
    target_snapshot_id: UUID | None = Field(default=None, description="指定目标快照ID（可选）")
    username: str | None = Field(default=None, description="连接用户名")
    password: str | None = Field(default=None, description="连接密码")
    enable_password: str | None = Field(default=None, description="Enable密码")
    rollback_reason: str = Field(min_length=1, description="回滚原因")
    create_backup: bool = Field(default=True, description="回滚前是否创建备份")
    validate_after_rollback: bool = Field(default=True, description="回滚后是否验证")
    timeout: int = Field(default=300, ge=30, le=600, description="回滚超时时间（秒）")
    force_rollback: bool = Field(default=False, description="是否强制回滚")


class RollbackExecuteResponse(BaseResponseSchema):
    """回滚执行响应"""

    rollback_operation_id: UUID = Field(description="回滚操作ID")
    original_operation_id: UUID = Field(description="原始操作ID")
    device_id: UUID = Field(description="设备ID")
    device_name: str = Field(description="设备名称")
    rollback_status: RollbackStatusEnum = Field(description="回滚状态")

    # 执行信息
    backup_snapshot_id: UUID | None = Field(default=None, description="回滚前备份快照ID")
    target_snapshot_id: UUID = Field(description="目标快照ID")
    rollback_time: float = Field(description="回滚耗时（秒）")

    # 验证信息
    validation_passed: bool | None = Field(default=None, description="验证是否通过")
    validation_details: dict[str, Any] | None = Field(default=None, description="验证详情")

    # 错误信息
    error_message: str | None = Field(default=None, description="错误信息")
    rollback_log: list[str] | None = Field(default=None, description="回滚日志")


class RollbackBatchExecuteRequest(BaseCreateSchema):
    """批量回滚执行请求"""

    operation_log_ids: list[UUID] = Field(min_length=1, max_length=20, description="操作记录ID列表")
    rollback_reason: str = Field(min_length=1, description="回滚原因")
    username: str | None = Field(default=None, description="连接用户名")
    password: str | None = Field(default=None, description="连接密码")
    enable_password: str | None = Field(default=None, description="Enable密码")
    create_backup: bool = Field(default=True, description="回滚前是否创建备份")
    validate_after_rollback: bool = Field(default=True, description="回滚后是否验证")
    continue_on_error: bool = Field(default=False, description="遇到错误是否继续")
    parallel_count: int = Field(default=1, ge=1, le=5, description="并发回滚数量")


class RollbackBatchExecuteResponse(BaseResponseSchema):
    """批量回滚执行响应"""

    batch_id: UUID = Field(description="批量操作ID")
    total_operations: int = Field(description="总操作数")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    pending_count: int = Field(description="待处理数量")
    total_time: float = Field(description="总耗时（秒）")

    # 详细结果
    results: list[RollbackExecuteResponse] = Field(description="详细结果")
    overall_status: str = Field(description="整体状态")


class RollbackValidationRequest(BaseCreateSchema):
    """回滚验证请求"""

    rollback_operation_id: UUID = Field(description="回滚操作ID")
    validation_type: str = Field(default="basic", description="验证类型(basic|full|connectivity)")
    timeout: int = Field(default=60, ge=10, le=300, description="验证超时时间（秒）")


class RollbackValidationResponse(BaseResponseSchema):
    """回滚验证响应"""

    rollback_operation_id: UUID = Field(description="回滚操作ID")
    validation_type: str = Field(description="验证类型")
    validation_status: str = Field(description="验证状态")
    validation_time: float = Field(description="验证耗时（秒）")

    # 验证结果
    connectivity_check: bool | None = Field(default=None, description="连通性检查")
    config_integrity: bool | None = Field(default=None, description="配置完整性")
    service_status: dict[str, Any] | None = Field(default=None, description="服务状态")

    # 详细信息
    validation_details: dict[str, Any] = Field(description="验证详情")
    issues_found: list[dict[str, Any]] | None = Field(default=None, description="发现的问题")
    recommendations: list[str] | None = Field(default=None, description="建议")


class RollbackStatsResponse(BaseResponseSchema):
    """回滚统计响应"""

    total_rollbacks: int = Field(description="总回滚数")
    successful_rollbacks: int = Field(description="成功回滚数")
    failed_rollbacks: int = Field(description="失败回滚数")
    pending_rollbacks: int = Field(description="待处理回滚数")
    success_rate: float = Field(description="成功率")

    # 时间统计
    avg_rollback_time: float = Field(description="平均回滚时间（秒）")
    fastest_rollback: float = Field(description="最快回滚时间（秒）")
    slowest_rollback: float = Field(description="最慢回滚时间（秒）")

    # 设备统计
    devices_with_rollbacks: int = Field(description="发生回滚的设备数")
    avg_rollbacks_per_device: float = Field(description="每设备平均回滚数")
    most_rolled_back_device: dict[str, Any] | None = Field(default=None, description="回滚最多的设备")

    # 操作者统计
    top_rollback_operators: list[dict[str, Any]] = Field(description="回滚操作最多的用户")

    # 时间分布
    rollbacks_by_hour: dict[str, int] = Field(description="按小时分布")
    rollbacks_by_day: dict[str, int] = Field(description="按天分布")


class RollbackReportRequest(BaseCreateSchema):
    """回滚报告请求"""

    device_ids: list[UUID] | None = Field(default=None, description="设备ID列表")
    start_time: datetime = Field(description="开始时间")
    end_time: datetime = Field(description="结束时间")
    include_successful: bool = Field(default=True, description="是否包含成功的回滚")
    include_failed: bool = Field(default=True, description="是否包含失败的回滚")
    group_by: str = Field(default="device", description="分组方式(device|operator|date)")
    export_format: str = Field(default="json", description="导出格式(json|xlsx|pdf)")


class RollbackReportResponse(BaseResponseSchema):
    """回滚报告响应"""

    report_id: UUID = Field(description="报告ID")
    report_period: str = Field(description="报告周期")
    total_rollbacks: int = Field(description="总回滚数")
    affected_devices: int = Field(description="涉及设备数")

    # 统计摘要
    summary: dict[str, Any] = Field(description="回滚摘要")

    # 详细数据
    rollback_details: list[dict[str, Any]] = Field(description="回滚详情")
    device_analysis: list[dict[str, Any]] = Field(description="设备分析")
    failure_analysis: list[dict[str, Any]] = Field(description="失败分析")

    # 导出信息
    export_url: str | None = Field(default=None, description="导出文件URL")
    generated_at: datetime = Field(description="生成时间")
