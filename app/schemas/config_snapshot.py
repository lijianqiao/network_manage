"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_snapshot.py
@DateTime: 2025/06/20 00:00:00
@Docs: 配置快照相关Pydantic校验模型
"""

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.models.network_models import SnapshotTypeEnum

from .base import BaseCreateSchema, BaseQueryParams, BaseResponseSchema, BaseUpdateSchema, TimeRangeQuery


class ConfigSnapshotCreateRequest(BaseCreateSchema):
    """配置快照创建请求"""

    device_id: UUID = Field(description="关联设备ID")
    snapshot_type: SnapshotTypeEnum = Field(description="快照类型")
    config_content: str = Field(min_length=1, description="配置内容")
    operation_log_id: UUID | None = Field(default=None, description="关联操作记录ID")

    @field_validator("config_content")
    @classmethod
    def validate_config_content(cls, v: str) -> str:
        """验证配置内容"""
        if not v.strip():
            raise ValueError("配置内容不能为空")
        return v.strip()


class ConfigSnapshotUpdateRequest(BaseUpdateSchema):
    """配置快照更新请求"""

    config_content: str | None = Field(default=None, min_length=1, description="配置内容")
    operation_log_id: UUID | None = Field(default=None, description="关联操作记录ID")


class ConfigSnapshotResponse(BaseResponseSchema):
    """配置快照响应"""

    device_id: UUID = Field(description="设备ID")
    snapshot_type: SnapshotTypeEnum = Field(description="快照类型")
    config_content: str = Field(description="配置内容")
    checksum: str = Field(description="配置MD5校验码")
    operation_log_id: UUID | None = Field(description="关联操作记录ID")

    # 关联设备信息
    device_name: str | None = Field(default=None, description="设备名称")
    device_ip: str | None = Field(default=None, description="设备IP")
    region_name: str | None = Field(default=None, description="区域名称")

    # 配置统计
    config_size: int | None = Field(default=None, description="配置大小（字节）")
    line_count: int | None = Field(default=None, description="配置行数")


class ConfigSnapshotListResponse(BaseResponseSchema):
    """配置快照列表响应（简化版）"""

    device_id: UUID = Field(description="设备ID")
    snapshot_type: SnapshotTypeEnum = Field(description="快照类型")
    checksum: str = Field(description="配置MD5校验码")

    # 关联信息
    device_name: str | None = Field(default=None, description="设备名称")
    device_ip: str | None = Field(default=None, description="设备IP")

    # 简化统计
    config_size: int | None = Field(default=None, description="配置大小（字节）")

    # 隐藏配置内容以提高性能
    config_preview: str | None = Field(default=None, description="配置预览（前100字符）")


class ConfigSnapshotDetailResponse(ConfigSnapshotResponse):
    """配置快照详情响应"""

    # 包含相关的差异记录
    related_diffs: list[dict] | None = Field(default=None, description="相关差异记录")
    rollback_operations: list[dict] | None = Field(default=None, description="回滚操作记录")


class ConfigSnapshotQueryParams(BaseQueryParams, TimeRangeQuery):
    """配置快照查询参数"""

    device_id: UUID | None = Field(default=None, description="按设备ID筛选")
    snapshot_type: SnapshotTypeEnum | None = Field(default=None, description="按快照类型筛选")
    operation_log_id: UUID | None = Field(default=None, description="按操作记录ID筛选")
    checksum: str | None = Field(default=None, description="按校验码筛选")
    device_name: str | None = Field(default=None, description="按设备名称筛选")
    region_id: UUID | None = Field(default=None, description="按区域ID筛选")
    size_min: int | None = Field(default=None, ge=0, description="最小配置大小")
    size_max: int | None = Field(default=None, ge=0, description="最大配置大小")


class ConfigSnapshotCompareRequest(BaseCreateSchema):
    """配置快照比较请求"""

    before_snapshot_id: UUID = Field(description="变更前快照ID")
    after_snapshot_id: UUID = Field(description="变更后快照ID")
    context_lines: int = Field(default=3, ge=0, le=10, description="上下文行数")
    ignore_whitespace: bool = Field(default=True, description="是否忽略空白字符")
    ignore_case: bool = Field(default=False, description="是否忽略大小写")


class ConfigSnapshotCompareResponse(BaseResponseSchema):
    """配置快照比较响应"""

    before_snapshot_id: UUID = Field(description="变更前快照ID")
    after_snapshot_id: UUID = Field(description="变更后快照ID")
    diff_content: str = Field(description="差异内容（unified diff格式）")
    added_lines: int = Field(description="新增行数")
    removed_lines: int = Field(description="删除行数")
    modified_lines: int = Field(description="修改行数")
    similarity_percentage: float = Field(description="相似度百分比")

    # 详细差异统计
    diff_summary: dict[str, Any] = Field(description="差异摘要")
    change_sections: list[dict[str, Any]] = Field(description="变更段落")


class ConfigSnapshotBackupRequest(BaseCreateSchema):
    """配置备份请求"""

    device_ids: list[UUID] = Field(min_length=1, max_length=50, description="设备ID列表")
    backup_type: SnapshotTypeEnum = Field(default=SnapshotTypeEnum.BACKUP, description="备份类型")
    username: str | None = Field(default=None, description="连接用户名")
    password: str | None = Field(default=None, description="连接密码")
    enable_password: str | None = Field(default=None, description="Enable密码")
    timeout: int = Field(default=60, ge=10, le=300, description="备份超时时间（秒）")
    auto_compare: bool = Field(default=True, description="是否与上次备份自动比较")


class ConfigSnapshotBackupResponse(BaseResponseSchema):
    """配置备份响应"""

    device_id: UUID = Field(description="设备ID")
    device_name: str = Field(description="设备名称")
    snapshot_id: UUID | None = Field(description="生成的快照ID")
    backup_status: str = Field(description="备份状态")
    config_size: int | None = Field(default=None, description="配置大小")
    backup_time: float = Field(description="备份耗时（秒）")
    error_message: str | None = Field(default=None, description="错误信息")

    # 如果启用自动比较
    has_changes: bool | None = Field(default=None, description="是否有变更")
    change_summary: dict[str, Any] | None = Field(default=None, description="变更摘要")


class ConfigSnapshotBatchBackupResponse(BaseResponseSchema):
    """批量配置备份响应"""

    total_devices: int = Field(description="总设备数")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    total_time: float = Field(description="总耗时（秒）")
    results: list[ConfigSnapshotBackupResponse] = Field(description="详细结果")


class ConfigSnapshotRestoreRequest(BaseCreateSchema):
    """配置恢复请求"""

    snapshot_id: UUID = Field(description="要恢复的快照ID")
    device_id: UUID = Field(description="目标设备ID")
    username: str | None = Field(default=None, description="连接用户名")
    password: str | None = Field(default=None, description="连接密码")
    enable_password: str | None = Field(default=None, description="Enable密码")
    create_backup: bool = Field(default=True, description="恢复前是否创建备份")
    force_restore: bool = Field(default=False, description="是否强制恢复")


class ConfigSnapshotRestoreResponse(BaseResponseSchema):
    """配置恢复响应"""

    snapshot_id: UUID = Field(description="恢复的快照ID")
    device_id: UUID = Field(description="目标设备ID")
    device_name: str = Field(description="设备名称")
    restore_status: str = Field(description="恢复状态")
    backup_snapshot_id: UUID | None = Field(default=None, description="恢复前备份快照ID")
    restore_time: float = Field(description="恢复耗时（秒）")
    error_message: str | None = Field(default=None, description="错误信息")


class ConfigSnapshotStatsResponse(BaseResponseSchema):
    """配置快照统计响应"""

    total_snapshots: int = Field(description="总快照数")
    backup_snapshots: int = Field(description="备份快照数")
    pre_change_snapshots: int = Field(description="变更前快照数")
    post_change_snapshots: int = Field(description="变更后快照数")

    # 存储统计
    total_storage_size: int = Field(description="总存储大小（字节）")
    avg_snapshot_size: float = Field(description="平均快照大小（字节）")
    largest_snapshot_size: int = Field(description="最大快照大小（字节）")

    # 时间统计
    snapshots_today: int = Field(description="今日快照数")
    snapshots_this_week: int = Field(description="本周快照数")
    snapshots_this_month: int = Field(description="本月快照数")

    # 设备统计
    devices_with_snapshots: int = Field(description="有快照的设备数")
    avg_snapshots_per_device: float = Field(description="每设备平均快照数")


class ConfigSnapshotCleanupRequest(BaseCreateSchema):
    """配置快照清理请求"""

    device_ids: list[UUID] | None = Field(default=None, description="指定设备ID列表")
    older_than_days: int | None = Field(default=None, ge=1, description="清理N天前的快照")
    keep_latest_count: int | None = Field(default=None, ge=1, description="每设备保留最新N个快照")
    snapshot_types: list[SnapshotTypeEnum] | None = Field(default=None, description="要清理的快照类型")
    exclude_referenced: bool = Field(default=True, description="是否排除被引用的快照")
    dry_run: bool = Field(default=True, description="是否仅预览而不实际删除")
