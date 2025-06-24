"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: advanced_operations.py
@DateTime: 2025/01/20 16:10:00
@Docs: 高级网络操作相关的Pydantic模型
"""

from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import BatchStrategy, OperationType, ReportFormat, SnapshotType

# ==================== 配置差异对比相关模型 ====================


class ConfigCompareRequest(BaseModel):
    """配置对比请求"""

    source_config: str = Field(..., description="源配置内容")
    target_config: str = Field(..., description="目标配置内容")
    source_name: str = Field("Source", description="源配置名称")
    target_name: str = Field("Target", description="目标配置名称")
    context_lines: int = Field(3, description="上下文行数", ge=0, le=10)


class ConfigCompareResponse(BaseModel):
    """配置对比响应"""

    source_name: str = Field(..., description="源配置名称")
    target_name: str = Field(..., description="目标配置名称")
    total_lines: int = Field(..., description="总行数")
    added_lines: int = Field(..., description="新增行数")
    removed_lines: int = Field(..., description="删除行数")
    modified_lines: int = Field(..., description="修改行数")
    change_percentage: float = Field(..., description="变化百分比")
    has_critical_changes: bool = Field(..., description="是否有严重变化")
    summary: dict[str, Any] = Field(..., description="差异摘要")
    risk_assessment: dict[str, Any] = Field(..., description="风险评估")
    recommendations: list[str] = Field(..., description="建议")


class ConfigDiffReportRequest(BaseModel):
    """配置差异报告请求"""

    config_compare: ConfigCompareRequest = Field(..., description="配置对比请求")
    format: ReportFormat = Field(ReportFormat.HTML, description="报告格式")


# ==================== 批量操作相关模型 ====================


class BatchOperationRequest(BaseModel):
    """批量操作请求"""

    devices: list[dict[str, Any]] = Field(..., description="设备列表")
    operation_type: OperationType = Field(..., description="操作类型")
    operation_params: dict[str, Any] = Field(..., description="操作参数")
    strategy: BatchStrategy = Field(BatchStrategy.PARALLEL, description="执行策略")
    max_retries: int = Field(3, description="最大重试次数", ge=0, le=10)
    timeout_per_device: float = Field(300.0, description="每设备超时时间", gt=0, le=3600)


class BatchOperationProgress(BaseModel):
    """批量操作进度"""

    total_devices: int = Field(..., description="总设备数")
    completed_devices: int = Field(..., description="已完成设备数")
    successful_devices: int = Field(..., description="成功设备数")
    failed_devices: int = Field(..., description="失败设备数")
    pending_devices: int = Field(..., description="待处理设备数")
    running_devices: int = Field(..., description="运行中设备数")
    completion_percentage: float = Field(..., description="完成百分比")
    success_rate: float = Field(..., description="成功率")


class BatchOperationResponse(BaseModel):
    """批量操作响应"""

    batch_id: str = Field(..., description="批次ID")
    operation_type: OperationType = Field(..., description="操作类型")
    strategy: BatchStrategy = Field(..., description="执行策略")
    total_devices: int = Field(..., description="总设备数")
    status: str = Field(..., description="当前状态")
    progress: BatchOperationProgress = Field(..., description="进度信息")


class BatchOperationStatusResponse(BaseModel):
    """批量操作状态响应"""

    batch_id: str = Field(..., description="批次ID")
    operation_type: OperationType = Field(..., description="操作类型")
    strategy: BatchStrategy = Field(..., description="执行策略")
    is_completed: bool = Field(..., description="是否已完成")
    is_successful: bool = Field(..., description="是否成功")
    progress: BatchOperationProgress = Field(..., description="进度信息")
    summary: dict[str, Any] = Field(..., description="操作摘要")
    errors: list[dict[str, Any]] = Field(..., description="错误列表")


# ==================== 配置快照相关模型 ====================


class CreateSnapshotRequest(BaseModel):
    """创建快照请求"""

    device_data: dict[str, Any] = Field(..., description="设备数据")
    snapshot_type: SnapshotType = Field(SnapshotType.MANUAL, description="快照类型")
    description: str | None = Field(None, description="快照描述")


class SnapshotResponse(BaseModel):
    """快照响应"""

    snapshot_id: str = Field(..., description="快照ID")
    device_id: str = Field(..., description="设备ID")
    device_ip: str = Field(..., description="设备IP")
    snapshot_type: SnapshotType = Field(..., description="快照类型")
    config_size: int = Field(..., description="配置大小")
    config_hash: str = Field(..., description="配置哈希")
    created_at: float = Field(..., description="创建时间")
    created_by: str = Field(..., description="创建者")
    description: str | None = Field(None, description="描述")


class DeviceSnapshotsResponse(BaseModel):
    """设备快照列表响应"""

    device_id: str = Field(..., description="设备ID")
    total_snapshots: int = Field(..., description="快照总数")
    snapshots: list[SnapshotResponse] = Field(..., description="快照列表")


class SnapshotCompareResponse(BaseModel):
    """快照对比响应"""

    snapshot1: dict[str, Any] = Field(..., description="快照1信息")
    snapshot2: dict[str, Any] = Field(..., description="快照2信息")
    diff_result: dict[str, Any] = Field(..., description="差异结果")
    comparison_summary: dict[str, Any] = Field(..., description="对比摘要")


# ==================== 配置回滚相关模型 ====================


class CreateRollbackPlanRequest(BaseModel):
    """创建回滚计划请求"""

    device_id: str = Field(..., description="设备ID")
    target_snapshot_id: str = Field(..., description="目标快照ID")
    rollback_type: str = Field("full", description="回滚类型")
    description: str | None = Field(None, description="描述")


class RollbackPlanResponse(BaseModel):
    """回滚计划响应"""

    plan_id: str = Field(..., description="计划ID")
    device_id: str = Field(..., description="设备ID")
    device_ip: str = Field(..., description="设备IP")
    target_snapshot_id: str = Field(..., description="目标快照ID")
    rollback_type: str = Field(..., description="回滚类型")
    commands_count: int = Field(..., description="命令数量")
    estimated_duration: float = Field(..., description="预估时间")
    risk_level: str = Field(..., description="风险等级")
    created_at: float = Field(..., description="创建时间")


class ExecuteRollbackRequest(BaseModel):
    """执行回滚请求"""

    plan_id: str = Field(..., description="回滚计划ID")
    device_data: dict[str, Any] = Field(..., description="设备数据")
    dry_run: bool = Field(False, description="是否为试运行")


class RollbackExecutionResponse(BaseModel):
    """回滚执行响应"""

    execution_id: str = Field(..., description="执行ID")
    plan_id: str = Field(..., description="计划ID")
    device_id: str = Field(..., description="设备ID")
    device_ip: str = Field(..., description="设备IP")
    status: str = Field(..., description="执行状态")
    start_time: float | None = Field(None, description="开始时间")
    end_time: float | None = Field(None, description="结束时间")
    duration: float | None = Field(None, description="执行时长")
    executed_commands: int = Field(..., description="已执行命令数")
    failed_commands: int = Field(..., description="失败命令数")
    error_message: str | None = Field(None, description="错误信息")
    dry_run: bool = Field(..., description="是否为试运行")


class DeviceRollbackHistoryResponse(BaseModel):
    """设备回滚历史响应"""

    device_id: str = Field(..., description="设备ID")
    total_executions: int = Field(..., description="执行总数")
    executions: list[dict[str, Any]] = Field(..., description="执行列表")


# ==================== 通用响应模型 ====================


class OperationSuccessResponse(BaseModel):
    """操作成功响应"""

    success: bool = Field(True, description="是否成功")
    message: str = Field(..., description="操作消息")
    data: dict[str, Any] | None = Field(None, description="返回数据")


class OperationErrorResponse(BaseModel):
    """操作错误响应"""

    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误信息")
    error_type: str | None = Field(None, description="错误类型")
    details: dict[str, Any] | None = Field(None, description="错误详情")
