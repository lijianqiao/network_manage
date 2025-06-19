"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_connection_status.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备连接状态相关Pydantic校验模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .base import (
    BaseCreateSchema,
    BaseQueryParams,
    BaseResponseSchema,
    BaseUpdateSchema,
    TimeRangeQuery
)


class DeviceConnectionStatusCreateRequest(BaseCreateSchema):
    """设备连接状态创建请求"""
    device_id: UUID = Field(description="关联设备ID")
    is_reachable: bool = Field(default=False, description="设备是否可达")
    last_check_time: datetime = Field(description="检查时间")
    last_success_time: Optional[datetime] = Field(default=None, description="最后成功连接时间")
    failure_count: int = Field(default=0, ge=0, description="连续失败次数")
    failure_reason: Optional[str] = Field(default=None, description="失败原因")
    snmp_response_time_ms: Optional[int] = Field(default=None, ge=0, description="SNMP响应时间（毫秒）")


class DeviceConnectionStatusUpdateRequest(BaseUpdateSchema):
    """设备连接状态更新请求"""
    is_reachable: Optional[bool] = Field(default=None, description="设备是否可达")
    last_check_time: Optional[datetime] = Field(default=None, description="检查时间")
    last_success_time: Optional[datetime] = Field(default=None, description="最后成功连接时间")
    failure_count: Optional[int] = Field(default=None, ge=0, description="连续失败次数")
    failure_reason: Optional[str] = Field(default=None, description="失败原因")
    snmp_response_time_ms: Optional[int] = Field(default=None, ge=0, description="SNMP响应时间（毫秒）")


class DeviceConnectionStatusResponse(BaseResponseSchema):
    """设备连接状态响应"""
    device_id: UUID = Field(description="设备ID")
    is_reachable: bool = Field(description="设备是否可达")
    last_check_time: datetime = Field(description="最后检查时间")
    last_success_time: Optional[datetime] = Field(description="最后成功连接时间")
    failure_count: int = Field(description="连续失败次数")
    failure_reason: Optional[str] = Field(description="失败原因")
    snmp_response_time_ms: Optional[int] = Field(description="SNMP响应时间（毫秒）")
    
    # 关联设备信息
    device_name: Optional[str] = Field(default=None, description="设备名称")
    device_ip: Optional[str] = Field(default=None, description="设备IP")
    device_type: Optional[str] = Field(default=None, description="设备类型")
    region_name: Optional[str] = Field(default=None, description="区域名称")
    
    # 计算字段
    status_duration: Optional[int] = Field(default=None, description="当前状态持续时间（分钟）")
    reliability_score: Optional[float] = Field(default=None, description="可靠性评分")


class DeviceConnectionStatusQueryParams(BaseQueryParams, TimeRangeQuery):
    """设备连接状态查询参数"""
    device_id: Optional[UUID] = Field(default=None, description="按设备ID筛选")
    is_reachable: Optional[bool] = Field(default=None, description="按可达性筛选")
    region_id: Optional[UUID] = Field(default=None, description="按区域ID筛选")
    device_type: Optional[str] = Field(default=None, description="按设备类型筛选")
    failure_count_min: Optional[int] = Field(default=None, ge=0, description="最小失败次数")
    failure_count_max: Optional[int] = Field(default=None, ge=0, description="最大失败次数")
    response_time_max: Optional[int] = Field(default=None, ge=0, description="最大响应时间（毫秒）")
    offline_duration_min: Optional[int] = Field(default=None, ge=0, description="最小离线时长（分钟）")


class ConnectionStatusStatsResponse(BaseResponseSchema):
    """连接状态统计响应"""
    total_devices: int = Field(description="总设备数")
    reachable_devices: int = Field(description="可达设备数")
    unreachable_devices: int = Field(description="不可达设备数")
    unknown_devices: int = Field(description="状态未知设备数")
    reachability_rate: float = Field(description="可达率")
    
    # 响应时间统计
    avg_response_time: Optional[float] = Field(default=None, description="平均响应时间（毫秒）")
    max_response_time: Optional[int] = Field(default=None, description="最大响应时间（毫秒）")
    min_response_time: Optional[int] = Field(default=None, description="最小响应时间（毫秒）")
    
    # 故障统计
    high_failure_devices: int = Field(description="高故障设备数（失败>5次）")
    avg_failure_count: float = Field(description="平均失败次数")
    
    # 区域统计
    region_stats: List[Dict[str, Any]] = Field(description="各区域统计")


class ConnectionHealthCheckRequest(BaseCreateSchema):
    """连接健康检查请求"""
    device_ids: Optional[List[UUID]] = Field(default=None, description="指定设备ID列表（为空则检查所有）")
    check_type: str = Field(default="ping", description="检查类型(ping|snmp|both)")
    timeout: int = Field(default=5, ge=1, le=30, description="检查超时时间（秒）")
    parallel_count: int = Field(default=10, ge=1, le=50, description="并发检查数量")
    update_status: bool = Field(default=True, description="是否更新设备状态")


class ConnectionHealthCheckResponse(BaseResponseSchema):
    """连接健康检查响应"""
    check_id: UUID = Field(description="检查任务ID")
    total_devices: int = Field(description="检查设备总数")
    completed_devices: int = Field(description="已完成检查设备数")
    reachable_devices: int = Field(description="可达设备数")
    unreachable_devices: int = Field(description="不可达设备数")
    check_duration: float = Field(description="检查耗时（秒）")
    
    # 详细结果
    results: List[Dict[str, Any]] = Field(description="详细检查结果")


class ConnectionMonitoringConfigRequest(BaseCreateSchema):
    """连接监控配置请求"""
    device_ids: Optional[List[UUID]] = Field(default=None, description="监控设备列表（为空则监控所有）")
    check_interval: int = Field(default=300, ge=60, le=3600, description="检查间隔（秒）")
    timeout: int = Field(default=5, ge=1, le=30, description="检查超时（秒）")
    failure_threshold: int = Field(default=3, ge=1, le=10, description="失败阈值")
    notification_enabled: bool = Field(default=True, description="是否启用通知")
    auto_recovery_check: bool = Field(default=True, description="是否自动恢复检查")


class ConnectionAlertResponse(BaseResponseSchema):
    """连接告警响应"""
    device_id: UUID = Field(description="设备ID")
    device_name: str = Field(description="设备名称")
    device_ip: str = Field(description="设备IP")
    alert_type: str = Field(description="告警类型")
    alert_level: str = Field(description="告警级别")
    alert_message: str = Field(description="告警消息")
    alert_time: datetime = Field(description="告警时间")
    failure_count: int = Field(description="连续失败次数")
    last_success_time: Optional[datetime] = Field(description="最后成功时间")


class ConnectionTrendResponse(BaseResponseSchema):
    """连接趋势响应"""
    date: str = Field(description="日期")
    total_devices: int = Field(description="总设备数")
    reachable_count: int = Field(description="可达设备数")
    unreachable_count: int = Field(description="不可达设备数")
    reachability_rate: float = Field(description="可达率")
    avg_response_time: Optional[float] = Field(description="平均响应时间")
    incident_count: int = Field(description="故障次数")


class DeviceReliabilityReportResponse(BaseResponseSchema):
    """设备可靠性报告响应"""
    device_id: UUID = Field(description="设备ID")
    device_name: str = Field(description="设备名称")
    device_ip: str = Field(description="设备IP")
    region_name: str = Field(description="区域名称")
    
    # 可靠性指标
    uptime_percentage: float = Field(description="在线率")
    total_checks: int = Field(description="总检查次数")
    successful_checks: int = Field(description="成功检查次数")
    failed_checks: int = Field(description="失败检查次数")
    avg_response_time: Optional[float] = Field(description="平均响应时间")
    max_downtime_minutes: int = Field(description="最长离线时间（分钟）")
    
    # 时间统计
    first_check: datetime = Field(description="首次检查时间")
    last_check: datetime = Field(description="最后检查时间")
    report_period_days: int = Field(description="报告周期（天）")
