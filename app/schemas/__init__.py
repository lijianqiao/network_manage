"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/20 00:00:00
@Docs: Pydantic校验模型模块初始化
"""

from .base import (
    # 基础模型
    BaseSchema,
    BaseCreateSchema,
    BaseUpdateSchema,
    BaseResponseSchema,
    BaseQueryParams,
    TimeRangeQuery,
    
    # 响应模型
    IDResponse,
    StatusResponse,
    SuccessResponse,
    ErrorResponse,
    PaginationInfo,
    PaginationResponse,
    
    # 批量操作模型
    BatchOperationRequest,
    BatchOperationResponse,
    BulkCreateRequest,
    BulkUpdateRequest,
    BulkDeleteRequest,
    
    # 类型别名
    ApiResponse,
    ListResponse,
)

from .region import (
    RegionCreateRequest,
    RegionUpdateRequest,
    RegionResponse,
    RegionListResponse,
    RegionDetailResponse,
    RegionQueryParams,
    RegionStatsResponse,
)

from .brand import (
    BrandCreateRequest,
    BrandUpdateRequest,
    BrandResponse,
    BrandListResponse,
    BrandDetailResponse,
    BrandQueryParams,
    BrandStatsResponse,
)

from .device_model import (
    DeviceModelCreateRequest,
    DeviceModelUpdateRequest,
    DeviceModelResponse,
    DeviceModelListResponse,
    DeviceModelDetailResponse,
    DeviceModelQueryParams,
    DeviceModelStatsResponse,
)

from .device_group import (
    DeviceGroupCreateRequest,
    DeviceGroupUpdateRequest,
    DeviceGroupResponse,
    DeviceGroupListResponse,
    DeviceGroupDetailResponse,
    DeviceGroupQueryParams,
    DeviceGroupStatsResponse,
    DeviceGroupBatchAssignRequest,
)

from .device import (
    DeviceCreateRequest,
    DeviceUpdateRequest,
    DeviceResponse,
    DeviceListResponse,
    DeviceDetailResponse,
    DeviceQueryParams,
    DeviceConnectionRequest,
    DeviceConnectionResponse,
    DeviceCommandRequest,
    DeviceCommandResponse,
    DeviceBatchCommandResponse,
    DeviceStatsResponse,
    DeviceBatchUpdateStatusRequest,
)

from .config_template import (
    ConfigTemplateCreateRequest,
    ConfigTemplateUpdateRequest,
    ConfigTemplateResponse,
    ConfigTemplateListResponse,
    ConfigTemplateDetailResponse,
    ConfigTemplateQueryParams,
    TemplateCommandCreateRequest,
    TemplateCommandUpdateRequest,
    TemplateCommandResponse,
    TemplateCommandQueryParams,
    TemplateExecuteRequest,
    TemplateExecuteResponse,
    TemplateBatchExecuteResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateStatsResponse,
)

from .operation_log import (
    OperationLogCreateRequest,
    OperationLogResponse,
    OperationLogListResponse,
    OperationLogDetailResponse,
    OperationLogQueryParams,
    OperationLogStatsResponse,
    OperationLogTrendResponse,
    OperationLogExportRequest,
    OperationLogBatchDeleteRequest,
    OperationLogAnalysisResponse,
)

from .device_connection_status import (
    DeviceConnectionStatusCreateRequest,
    DeviceConnectionStatusUpdateRequest,
    DeviceConnectionStatusResponse,
    DeviceConnectionStatusQueryParams,
    ConnectionStatusStatsResponse,
    ConnectionHealthCheckRequest,
    ConnectionHealthCheckResponse,
    ConnectionMonitoringConfigRequest,
    ConnectionAlertResponse,
    ConnectionTrendResponse,
    DeviceReliabilityReportResponse,
)

from .config_snapshot import (
    ConfigSnapshotCreateRequest,
    ConfigSnapshotUpdateRequest,
    ConfigSnapshotResponse,
    ConfigSnapshotListResponse,
    ConfigSnapshotDetailResponse,
    ConfigSnapshotQueryParams,
    ConfigSnapshotCompareRequest,
    ConfigSnapshotCompareResponse,
    ConfigSnapshotBackupRequest,
    ConfigSnapshotBackupResponse,
    ConfigSnapshotBatchBackupResponse,
    ConfigSnapshotRestoreRequest,
    ConfigSnapshotRestoreResponse,
    ConfigSnapshotStatsResponse,
    ConfigSnapshotCleanupRequest,
)

from .config_diff import (
    ConfigDiffCreateRequest,
    ConfigDiffUpdateRequest,
    ConfigDiffResponse,
    ConfigDiffListResponse,
    ConfigDiffDetailResponse,
    ConfigDiffQueryParams,
    ConfigDiffAnalysisRequest,
    ConfigDiffAnalysisResponse,
    ConfigDiffBatchAnalysisRequest,
    ConfigDiffTrendResponse,
    ConfigDiffStatsResponse,
    ConfigChangeReportRequest,
    ConfigChangeReportResponse,
)

from .rollback_operation import (
    RollbackOperationCreateRequest,
    RollbackOperationUpdateRequest,
    RollbackOperationResponse,
    RollbackOperationListResponse,
    RollbackOperationDetailResponse,
    RollbackOperationQueryParams,
    RollbackExecuteRequest,
    RollbackExecuteResponse,
    RollbackBatchExecuteRequest,
    RollbackBatchExecuteResponse,
    RollbackValidationRequest,
    RollbackValidationResponse,
    RollbackStatsResponse,
    RollbackReportRequest,
    RollbackReportResponse,
)

__all__ = [
    # 基础模型
    "BaseSchema",
    "BaseCreateSchema", 
    "BaseUpdateSchema",
    "BaseResponseSchema",
    "BaseQueryParams",
    "TimeRangeQuery",
    
    # 响应模型
    "IDResponse",
    "StatusResponse",
    "SuccessResponse",
    "ErrorResponse", 
    "PaginationInfo",
    "PaginationResponse",
    
    # 批量操作模型
    "BatchOperationRequest",
    "BatchOperationResponse",
    "BulkCreateRequest",
    "BulkUpdateRequest", 
    "BulkDeleteRequest",
    
    # 类型别名
    "ApiResponse",
    "ListResponse",
    
    # 区域相关
    "RegionCreateRequest",
    "RegionUpdateRequest",
    "RegionResponse",
    "RegionListResponse",
    "RegionDetailResponse",
    "RegionQueryParams",
    "RegionStatsResponse",
    
    # 品牌相关
    "BrandCreateRequest",
    "BrandUpdateRequest", 
    "BrandResponse",
    "BrandListResponse",
    "BrandDetailResponse",
    "BrandQueryParams",
    "BrandStatsResponse",
    
    # 设备型号相关
    "DeviceModelCreateRequest",
    "DeviceModelUpdateRequest",
    "DeviceModelResponse",
    "DeviceModelListResponse",
    "DeviceModelDetailResponse",
    "DeviceModelQueryParams",
    "DeviceModelStatsResponse",
    
    # 设备分组相关
    "DeviceGroupCreateRequest",
    "DeviceGroupUpdateRequest",
    "DeviceGroupResponse",
    "DeviceGroupListResponse",
    "DeviceGroupDetailResponse",
    "DeviceGroupQueryParams",
    "DeviceGroupStatsResponse",
    "DeviceGroupBatchAssignRequest",
    
    # 设备相关
    "DeviceCreateRequest",
    "DeviceUpdateRequest",
    "DeviceResponse",
    "DeviceListResponse",
    "DeviceDetailResponse",
    "DeviceQueryParams",
    "DeviceConnectionRequest",
    "DeviceConnectionResponse",
    "DeviceCommandRequest",
    "DeviceCommandResponse",
    "DeviceBatchCommandResponse",
    "DeviceStatsResponse",
    "DeviceBatchUpdateStatusRequest",
    
    # 配置模板相关
    "ConfigTemplateCreateRequest",
    "ConfigTemplateUpdateRequest",
    "ConfigTemplateResponse",
    "ConfigTemplateListResponse",
    "ConfigTemplateDetailResponse",
    "ConfigTemplateQueryParams",
    "TemplateCommandCreateRequest",
    "TemplateCommandUpdateRequest",
    "TemplateCommandResponse",
    "TemplateCommandQueryParams",
    "TemplateExecuteRequest",
    "TemplateExecuteResponse",
    "TemplateBatchExecuteResponse",
    "TemplateRenderRequest",
    "TemplateRenderResponse",
    "TemplateStatsResponse",
    
    # 操作日志相关
    "OperationLogCreateRequest",
    "OperationLogResponse",
    "OperationLogListResponse",
    "OperationLogDetailResponse",
    "OperationLogQueryParams",
    "OperationLogStatsResponse",
    "OperationLogTrendResponse",
    "OperationLogExportRequest",
    "OperationLogBatchDeleteRequest",
    "OperationLogAnalysisResponse",
    
    # 设备连接状态相关
    "DeviceConnectionStatusCreateRequest",
    "DeviceConnectionStatusUpdateRequest",
    "DeviceConnectionStatusResponse",
    "DeviceConnectionStatusQueryParams",
    "ConnectionStatusStatsResponse",
    "ConnectionHealthCheckRequest",
    "ConnectionHealthCheckResponse",
    "ConnectionMonitoringConfigRequest",
    "ConnectionAlertResponse",
    "ConnectionTrendResponse",
    "DeviceReliabilityReportResponse",
    
    # 配置快照相关
    "ConfigSnapshotCreateRequest",
    "ConfigSnapshotUpdateRequest",
    "ConfigSnapshotResponse",
    "ConfigSnapshotListResponse",
    "ConfigSnapshotDetailResponse",
    "ConfigSnapshotQueryParams",
    "ConfigSnapshotCompareRequest",
    "ConfigSnapshotCompareResponse",
    "ConfigSnapshotBackupRequest",
    "ConfigSnapshotBackupResponse",
    "ConfigSnapshotBatchBackupResponse",
    "ConfigSnapshotRestoreRequest",
    "ConfigSnapshotRestoreResponse",
    "ConfigSnapshotStatsResponse",
    "ConfigSnapshotCleanupRequest",
    
    # 配置差异相关
    "ConfigDiffCreateRequest",
    "ConfigDiffUpdateRequest",
    "ConfigDiffResponse",
    "ConfigDiffListResponse",
    "ConfigDiffDetailResponse",
    "ConfigDiffQueryParams",
    "ConfigDiffAnalysisRequest",
    "ConfigDiffAnalysisResponse",
    "ConfigDiffBatchAnalysisRequest",
    "ConfigDiffTrendResponse",
    "ConfigDiffStatsResponse",
    "ConfigChangeReportRequest",
    "ConfigChangeReportResponse",
    
    # 回滚操作相关
    "RollbackOperationCreateRequest",
    "RollbackOperationUpdateRequest",
    "RollbackOperationResponse",
    "RollbackOperationListResponse",
    "RollbackOperationDetailResponse",
    "RollbackOperationQueryParams",
    "RollbackExecuteRequest",
    "RollbackExecuteResponse",
    "RollbackBatchExecuteRequest",
    "RollbackBatchExecuteResponse",
    "RollbackValidationRequest",
    "RollbackValidationResponse",
    "RollbackStatsResponse",
    "RollbackReportRequest",
    "RollbackReportResponse",
]
