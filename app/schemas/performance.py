"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: performance.py
@DateTime: 2025/01/20 16:15:00
@Docs: 性能管理相关的Pydantic模型
"""

from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import ExportFormat

# ==================== 连接池统计相关模型 ====================


class ConnectionPoolStats(BaseModel):
    """连接池统计"""

    total_connections: int = Field(..., description="总连接数")
    active_connections: int = Field(..., description="活跃连接数")
    idle_connections: int = Field(..., description="空闲连接数")
    failed_connections: int = Field(..., description="失败连接数")
    peak_connections: int = Field(..., description="峰值连接数")
    created_connections: int = Field(..., description="已创建连接数")
    destroyed_connections: int = Field(..., description="已销毁连接数")


class PerformanceStats(BaseModel):
    """性能统计"""

    total_requests: int = Field(..., description="总请求数")
    cache_hits: int = Field(..., description="缓存命中数")
    cache_misses: int = Field(..., description="缓存未命中数")
    cache_hit_rate: str = Field(..., description="缓存命中率")
    connection_errors: int = Field(..., description="连接错误数")
    average_response_time: float = Field(..., description="平均响应时间")


class ConcurrencyStats(BaseModel):
    """并发统计"""

    current_limit: int = Field(..., description="当前并发限制")
    min_limit: int = Field(..., description="最小并发限制")
    max_limit: int = Field(..., description="最大并发限制")
    available_permits: int = Field(..., description="可用许可数")


class ConnectionPoolStatsResponse(BaseModel):
    """连接池统计响应"""

    pool_stats: ConnectionPoolStats = Field(..., description="连接池统计信息")
    performance_stats: PerformanceStats = Field(..., description="性能统计信息")
    concurrency_stats: ConcurrencyStats = Field(..., description="并发统计信息")
    device_pools: dict[str, int] = Field(..., description="设备连接池分布")
    manager_info: dict[str, Any] = Field(..., description="管理器信息")


# ==================== 设备性能相关模型 ====================


class DeviceInfo(BaseModel):
    """设备信息"""

    device_ip: str = Field(..., description="设备IP")
    device_id: str | None = Field(None, description="设备ID")
    is_healthy: bool = Field(..., description="是否健康")
    reliability_score: float = Field(..., description="可靠性评分")


class OperationStats(BaseModel):
    """操作统计"""

    total_operations: int = Field(..., description="总操作数")
    successful_operations: int = Field(..., description="成功操作数")
    failed_operations: int = Field(..., description="失败操作数")
    success_rate: float = Field(..., description="成功率")
    consecutive_failures: int = Field(..., description="连续失败次数")


class ResponseTimeStats(BaseModel):
    """响应时间统计"""

    average: float = Field(..., description="平均响应时间")
    median: float = Field(..., description="中位数响应时间")
    min: float = Field(..., description="最小响应时间")
    max: float = Field(..., description="最大响应时间")


class DevicePerformanceResponse(BaseModel):
    """设备性能响应"""

    device_info: DeviceInfo = Field(..., description="设备信息")
    operation_stats: OperationStats = Field(..., description="操作统计")
    response_time_stats: ResponseTimeStats = Field(..., description="响应时间统计")
    error_analysis: dict[str, int] = Field(..., description="错误分析")
    recommendations: list[str] = Field(..., description="优化建议")
    last_success: float | None = Field(None, description="最后成功时间")
    last_failure: float | None = Field(None, description="最后失败时间")


# ==================== 性能优化相关模型 ====================


class PerformanceOptimizationRequest(BaseModel):
    """性能优化请求"""

    action: str = Field(..., description="优化动作", examples=["adjust_concurrency", "clear_cache", "restart_pool"])
    parameters: dict[str, Any] | None = Field(None, description="优化参数")


class PerformanceOptimizationResponse(BaseModel):
    """性能优化响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="操作消息")
    old_settings: dict[str, Any] | None = Field(None, description="旧设置")
    new_settings: dict[str, Any] | None = Field(None, description="新设置")


# ==================== 健康检查相关模型 ====================


class HealthCheckStats(BaseModel):
    """健康检查统计"""

    total_connections: int = Field(..., description="总连接数")
    active_connections: int = Field(..., description="活跃连接数")
    cache_hit_rate: str = Field(..., description="缓存命中率")
    device_health_rate: float = Field(..., description="设备健康率")
    recent_critical_alerts: int = Field(..., description="最近严重告警数")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""

    healthy: bool = Field(..., description="是否健康")
    status: str = Field(..., description="状态")
    issues: list[str] = Field(..., description="问题列表")
    stats_summary: HealthCheckStats = Field(..., description="统计摘要")


# ==================== 指标导出相关模型 ====================


class MetricsExportRequest(BaseModel):
    """指标导出请求"""

    format: ExportFormat = Field(ExportFormat.JSON, description="导出格式")


class PrometheusMetricsResponse(BaseModel):
    """Prometheus指标响应"""

    content_type: str = Field(..., description="内容类型")
    metrics: str = Field(..., description="指标内容")


# ==================== 性能摘要相关模型 ====================


class DeviceHealthSummary(BaseModel):
    """设备健康摘要"""

    total_devices: int = Field(..., description="总设备数")
    healthy_devices: int = Field(..., description="健康设备数")
    unhealthy_devices: int = Field(..., description="不健康设备数")
    health_rate: float = Field(..., description="健康率")


class RecentAlerts(BaseModel):
    """最近告警"""

    total: int = Field(..., description="总告警数")
    critical: int = Field(..., description="严重告警数")
    medium: int = Field(..., description="中等告警数")
    low: int = Field(..., description="低级告警数")


class PerformanceTrends(BaseModel):
    """性能趋势"""

    recent_operations: int = Field(..., description="最近操作数")
    success_rate: float = Field(..., description="成功率")
    average_response_time: float = Field(..., description="平均响应时间")


class PerformanceSummaryResponse(BaseModel):
    """性能摘要响应"""

    global_stats: dict[str, Any] = Field(..., description="全局统计")
    device_health: DeviceHealthSummary = Field(..., description="设备健康摘要")
    recent_alerts: RecentAlerts = Field(..., description="最近告警")
    performance_trends: PerformanceTrends = Field(..., description="性能趋势")
