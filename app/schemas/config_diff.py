"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_diff.py
@DateTime: 2025/06/20 00:00:00
@Docs: 配置差异相关Pydantic校验模型
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from .base import (
    BaseCreateSchema,
    BaseQueryParams,
    BaseResponseSchema,
    BaseUpdateSchema,
    BatchOperationResponse,
    BulkCreateRequest,
    BulkDeleteRequest,
    BulkUpdateRequest,
    PaginationResponse,
    TimeRangeQuery,
)


class ConfigDiffCreateRequest(BaseCreateSchema):
    """配置差异创建请求"""

    before_snapshot_id: UUID = Field(description="变更前快照ID")
    after_snapshot_id: UUID = Field(description="变更后快照ID")
    diff_content: str = Field(min_length=1, description="差异内容")
    added_lines: int = Field(ge=0, description="新增行数")
    removed_lines: int = Field(ge=0, description="删除行数")

    @field_validator("diff_content")
    @classmethod
    def validate_diff_content(cls, v: str) -> str:
        """验证差异内容"""
        if not v.strip():
            raise ValueError("差异内容不能为空")
        return v.strip()


class ConfigDiffUpdateRequest(BaseUpdateSchema):
    """配置差异更新请求"""

    diff_content: str | None = Field(default=None, min_length=1, description="差异内容")
    added_lines: int | None = Field(default=None, ge=0, description="新增行数")
    removed_lines: int | None = Field(default=None, ge=0, description="删除行数")


class ConfigDiffResponse(BaseResponseSchema):
    """配置差异响应"""

    before_snapshot_id: UUID = Field(description="变更前快照ID")
    after_snapshot_id: UUID = Field(description="变更后快照ID")
    diff_content: str = Field(description="差异内容")
    added_lines: int = Field(description="新增行数")
    removed_lines: int = Field(description="删除行数")

    # 关联快照信息
    before_snapshot_type: str | None = Field(default=None, description="变更前快照类型")
    after_snapshot_type: str | None = Field(default=None, description="变更后快照类型")
    device_id: UUID | None = Field(default=None, description="设备ID")
    device_name: str | None = Field(default=None, description="设备名称")
    device_ip: str | None = Field(default=None, description="设备IP")

    # 差异统计
    total_changes: int | None = Field(default=None, description="总变更行数")
    change_percentage: float | None = Field(default=None, description="变更百分比")
    diff_size: int | None = Field(default=None, description="差异内容大小（字节）")


class ConfigDiffListResponse(BaseResponseSchema):
    """配置差异列表响应（简化版）"""

    before_snapshot_id: UUID = Field(description="变更前快照ID")
    after_snapshot_id: UUID = Field(description="变更后快照ID")
    added_lines: int = Field(description="新增行数")
    removed_lines: int = Field(description="删除行数")

    # 关联信息
    device_name: str | None = Field(default=None, description="设备名称")
    device_ip: str | None = Field(default=None, description="设备IP")

    # 简化统计
    total_changes: int | None = Field(default=None, description="总变更行数")

    # 隐藏详细差异内容以提高性能
    diff_preview: str | None = Field(default=None, description="差异预览（前200字符）")


class ConfigDiffDetailResponse(ConfigDiffResponse):
    """配置差异详情响应"""

    # 包含差异分析结果
    change_summary: dict[str, Any] | None = Field(default=None, description="变更摘要")
    affected_sections: list[dict[str, Any]] | None = Field(default=None, description="影响的配置段落")
    risk_analysis: dict[str, Any] | None = Field(default=None, description="风险分析")


class ConfigDiffQueryParams(BaseQueryParams, TimeRangeQuery):
    """配置差异查询参数"""

    before_snapshot_id: UUID | None = Field(default=None, description="按变更前快照ID筛选")
    after_snapshot_id: UUID | None = Field(default=None, description="按变更后快照ID筛选")
    device_id: UUID | None = Field(default=None, description="按设备ID筛选")
    device_name: str | None = Field(default=None, description="按设备名称筛选")
    region_id: UUID | None = Field(default=None, description="按区域ID筛选")
    added_lines_min: int | None = Field(default=None, ge=0, description="最小新增行数")
    added_lines_max: int | None = Field(default=None, ge=0, description="最大新增行数")
    removed_lines_min: int | None = Field(default=None, ge=0, description="最小删除行数")
    removed_lines_max: int | None = Field(default=None, ge=0, description="最大删除行数")
    has_significant_changes: bool | None = Field(default=None, description="是否有重大变更")


class ConfigDiffAnalysisRequest(BaseCreateSchema):
    """配置差异分析请求"""

    diff_id: UUID = Field(description="差异记录ID")
    analysis_type: str = Field(default="full", description="分析类型(basic|full|security)")
    include_recommendations: bool = Field(default=True, description="是否包含建议")


class ConfigDiffAnalysisResponse(BaseResponseSchema):
    """配置差异分析响应"""

    diff_id: UUID = Field(description="差异记录ID")
    analysis_type: str = Field(description="分析类型")

    # 基础分析
    change_categories: dict[str, int] = Field(description="变更类别统计")
    affected_features: list[str] = Field(description="影响的功能特性")
    complexity_score: float = Field(description="复杂度评分")

    # 风险评估
    risk_level: str = Field(description="风险等级")
    risk_factors: list[dict[str, Any]] = Field(description="风险因素")
    security_impact: dict[str, Any] | None = Field(default=None, description="安全影响")

    # 建议
    recommendations: list[dict[str, Any]] | None = Field(default=None, description="优化建议")
    rollback_complexity: str | None = Field(default=None, description="回滚复杂度")


class ConfigDiffBatchAnalysisRequest(BaseCreateSchema):
    """批量配置差异分析请求"""

    diff_ids: list[UUID] = Field(min_length=1, max_length=20, description="差异记录ID列表")
    analysis_type: str = Field(default="basic", description="分析类型")
    generate_report: bool = Field(default=True, description="是否生成分析报告")


class ConfigDiffTrendResponse(BaseResponseSchema):
    """配置差异趋势响应"""

    date: str = Field(description="日期")
    total_diffs: int = Field(description="总差异数")
    avg_added_lines: float = Field(description="平均新增行数")
    avg_removed_lines: float = Field(description="平均删除行数")
    high_risk_changes: int = Field(description="高风险变更数")
    devices_changed: int = Field(description="发生变更的设备数")


class ConfigDiffStatsResponse(BaseResponseSchema):
    """配置差异统计响应"""

    total_diffs: int = Field(description="总差异记录数")
    total_added_lines: int = Field(description="总新增行数")
    total_removed_lines: int = Field(description="总删除行数")

    # 设备统计
    devices_with_changes: int = Field(description="有变更的设备数")
    avg_changes_per_device: float = Field(description="每设备平均变更数")
    most_changed_device: dict[str, Any] | None = Field(default=None, description="变更最多的设备")

    # 时间统计
    diffs_today: int = Field(description="今日差异数")
    diffs_this_week: int = Field(description="本周差异数")
    diffs_this_month: int = Field(description="本月差异数")

    # 变更类型统计
    change_type_distribution: dict[str, int] = Field(description="变更类型分布")
    risk_level_distribution: dict[str, int] = Field(description="风险等级分布")


class ConfigChangeReportRequest(BaseCreateSchema):
    """配置变更报告请求"""

    device_ids: list[UUID] | None = Field(default=None, description="设备ID列表")
    start_time: datetime = Field(description="开始时间")
    end_time: datetime = Field(description="结束时间")
    include_details: bool = Field(default=True, description="是否包含详细信息")
    group_by: str = Field(default="device", description="分组方式(device|date|type)")
    export_format: str = Field(default="json", description="导出格式(json|xlsx|pdf)")


class ConfigChangeReportResponse(BaseResponseSchema):
    """配置变更报告响应"""

    report_id: UUID = Field(description="报告ID")
    report_period: str = Field(description="报告周期")
    total_devices: int = Field(description="涉及设备数")
    total_changes: int = Field(description="总变更数")

    # 摘要统计
    summary: dict[str, Any] = Field(description="变更摘要")

    # 详细数据
    device_changes: list[dict[str, Any]] = Field(description="设备变更详情")
    trend_analysis: list[ConfigDiffTrendResponse] = Field(description="趋势分析")
    risk_assessment: dict[str, Any] = Field(description="风险评估")

    # 导出信息
    export_url: str | None = Field(default=None, description="导出文件URL")
    generated_at: datetime = Field(description="生成时间")


# 分页和批量操作类型别名
ConfigDiffPaginationResponse = PaginationResponse[ConfigDiffListResponse]
ConfigDiffBulkCreateRequest = BulkCreateRequest[ConfigDiffCreateRequest]
ConfigDiffBulkUpdateRequest = BulkUpdateRequest
ConfigDiffBulkDeleteRequest = BulkDeleteRequest
ConfigDiffBatchOperationResponse = BatchOperationResponse
