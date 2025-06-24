"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: performance_monitor.py
@DateTime: 2025/01/20 12:30:00
@Docs: 性能监控和优化管理器 - 监控网络操作性能并提供优化建议
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from statistics import mean, median
from typing import Any

from app.utils.logger import logger


@dataclass
class OperationMetrics:
    """操作指标"""

    operation_type: str
    device_ip: str
    device_id: str | None
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_type: str | None = None
    error_message: str | None = None

    @property
    def response_time_ms(self) -> float:
        """响应时间（毫秒）"""
        return self.duration * 1000


@dataclass
class DevicePerformanceProfile:
    """设备性能画像"""

    device_ip: str
    device_id: str | None
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_types: dict[str, int] = field(default_factory=dict)
    last_success_time: float | None = None
    last_failure_time: float | None = None
    consecutive_failures: int = 0
    reliability_score: float = 1.0

    def update_metrics(self, metrics: OperationMetrics) -> None:
        """更新设备指标"""
        self.total_operations += 1

        if metrics.success:
            self.successful_operations += 1
            self.consecutive_failures = 0
            self.last_success_time = metrics.end_time
        else:
            self.failed_operations += 1
            self.consecutive_failures += 1
            self.last_failure_time = metrics.end_time

            if metrics.error_type:
                self.error_types[metrics.error_type] = self.error_types.get(metrics.error_type, 0) + 1

        # 更新响应时间统计
        self.recent_response_times.append(metrics.duration)
        self.min_response_time = min(self.min_response_time, metrics.duration)
        self.max_response_time = max(self.max_response_time, metrics.duration)

        if self.recent_response_times:
            self.average_response_time = mean(self.recent_response_times)

        # 计算可靠性评分
        self._calculate_reliability_score()

    def _calculate_reliability_score(self) -> None:
        """计算可靠性评分（0-1之间）"""
        if self.total_operations == 0:
            self.reliability_score = 1.0
            return

        # 基础成功率
        success_rate = self.successful_operations / self.total_operations

        # 连续失败惩罚
        failure_penalty = min(0.5, self.consecutive_failures * 0.1)

        # 响应时间惩罚
        time_penalty = 0.0
        if self.average_response_time > 5.0:  # 超过5秒
            time_penalty = min(0.3, (self.average_response_time - 5.0) * 0.05)

        self.reliability_score = max(0.0, success_rate - failure_penalty - time_penalty)

    @property
    def success_rate(self) -> float:
        """成功率"""
        return (self.successful_operations / self.total_operations * 100) if self.total_operations > 0 else 0.0

    @property
    def median_response_time(self) -> float:
        """中位数响应时间"""
        return median(self.recent_response_times) if self.recent_response_times else 0.0

    @property
    def is_healthy(self) -> bool:
        """设备是否健康"""
        return self.reliability_score > 0.7 and self.consecutive_failures < 3 and self.average_response_time < 10.0


@dataclass
class PerformanceAlert:
    """性能告警"""

    alert_type: str
    severity: str  # low, medium, high, critical
    device_ip: str
    device_id: str | None
    message: str
    timestamp: float
    metrics: dict[str, Any]


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size

        # 性能数据存储
        self.operation_history: deque = deque(maxlen=max_history_size)
        self.device_profiles: dict[str, DevicePerformanceProfile] = {}
        self.alerts: deque = deque(maxlen=1000)

        # 统计数据
        self.global_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_response_time": 0.0,
            "operations_per_minute": 0.0,
        }

        # 性能阈值
        self.thresholds = {
            "response_time_warning": 3.0,  # 3秒
            "response_time_critical": 10.0,  # 10秒
            "error_rate_warning": 0.1,  # 10%
            "error_rate_critical": 0.3,  # 30%
            "consecutive_failures_warning": 3,
            "consecutive_failures_critical": 5,
        }

        # 监控任务
        self._monitor_task: asyncio.Task | None = None
        self._started = False

    async def start(self) -> None:
        """启动性能监控"""
        if self._started:
            return

        self._started = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info("性能监控器已启动")

    async def stop(self) -> None:
        """停止性能监控"""
        if not self._started:
            return

        self._started = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("性能监控器已停止")

    def record_operation(
        self,
        operation_type: str,
        device_ip: str,
        device_id: str | None,
        start_time: float,
        end_time: float,
        success: bool,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """记录操作指标"""
        metrics = OperationMetrics(
            operation_type=operation_type,
            device_ip=device_ip,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=success,
            error_type=error_type,
            error_message=error_message,
        )

        # 添加到历史记录
        self.operation_history.append(metrics)

        # 更新设备性能画像
        device_key = f"{device_ip}:{device_id}" if device_id else device_ip
        if device_key not in self.device_profiles:
            self.device_profiles[device_key] = DevicePerformanceProfile(device_ip=device_ip, device_id=device_id)

        self.device_profiles[device_key].update_metrics(metrics)

        # 更新全局统计
        self._update_global_stats()

        # 检查告警条件
        self._check_alerts(device_key, metrics)

    def _update_global_stats(self) -> None:
        """更新全局统计"""
        if not self.operation_history:
            return

        # 计算最近1小时的统计
        current_time = time.time()
        recent_operations = [
            op
            for op in self.operation_history
            if current_time - op.end_time <= 3600  # 1小时
        ]

        if not recent_operations:
            return

        self.global_stats["total_operations"] = len(recent_operations)
        self.global_stats["successful_operations"] = sum(1 for op in recent_operations if op.success)
        self.global_stats["failed_operations"] = len(recent_operations) - self.global_stats["successful_operations"]
        self.global_stats["average_response_time"] = mean([op.duration for op in recent_operations])

        # 计算每分钟操作数
        if recent_operations:
            time_span = current_time - min(op.start_time for op in recent_operations)
            self.global_stats["operations_per_minute"] = (
                len(recent_operations) / (time_span / 60) if time_span > 0 else 0
            )

    def _check_alerts(self, device_key: str, metrics: OperationMetrics) -> None:
        """检查告警条件"""
        device_profile = self.device_profiles[device_key]
        alerts = []

        # 响应时间告警
        if metrics.duration > self.thresholds["response_time_critical"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="response_time",
                    severity="critical",
                    device_ip=metrics.device_ip,
                    device_id=metrics.device_id,
                    message=f"响应时间过长: {metrics.duration:.2f}秒",
                    timestamp=metrics.end_time,
                    metrics={"response_time": metrics.duration, "threshold": self.thresholds["response_time_critical"]},
                )
            )
        elif metrics.duration > self.thresholds["response_time_warning"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="response_time",
                    severity="medium",
                    device_ip=metrics.device_ip,
                    device_id=metrics.device_id,
                    message=f"响应时间较慢: {metrics.duration:.2f}秒",
                    timestamp=metrics.end_time,
                    metrics={"response_time": metrics.duration, "threshold": self.thresholds["response_time_warning"]},
                )
            )

        # 错误率告警
        error_rate = 1 - device_profile.success_rate / 100
        if error_rate > self.thresholds["error_rate_critical"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="error_rate",
                    severity="critical",
                    device_ip=metrics.device_ip,
                    device_id=metrics.device_id,
                    message=f"错误率过高: {error_rate * 100:.1f}%",
                    timestamp=metrics.end_time,
                    metrics={"error_rate": error_rate, "threshold": self.thresholds["error_rate_critical"]},
                )
            )
        elif error_rate > self.thresholds["error_rate_warning"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="error_rate",
                    severity="medium",
                    device_ip=metrics.device_ip,
                    device_id=metrics.device_id,
                    message=f"错误率较高: {error_rate * 100:.1f}%",
                    timestamp=metrics.end_time,
                    metrics={"error_rate": error_rate, "threshold": self.thresholds["error_rate_warning"]},
                )
            )

        # 连续失败告警
        if device_profile.consecutive_failures >= self.thresholds["consecutive_failures_critical"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="consecutive_failures",
                    severity="critical",
                    device_ip=metrics.device_ip,
                    device_id=metrics.device_id,
                    message=f"连续失败次数过多: {device_profile.consecutive_failures}次",
                    timestamp=metrics.end_time,
                    metrics={"consecutive_failures": device_profile.consecutive_failures},
                )
            )
        elif device_profile.consecutive_failures >= self.thresholds["consecutive_failures_warning"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="consecutive_failures",
                    severity="medium",
                    device_ip=metrics.device_ip,
                    device_id=metrics.device_id,
                    message=f"连续失败次数较多: {device_profile.consecutive_failures}次",
                    timestamp=metrics.end_time,
                    metrics={"consecutive_failures": device_profile.consecutive_failures},
                )
            )

        # 添加告警到队列
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(
                f"性能告警: {alert.message}",
                alert_type=alert.alert_type,
                severity=alert.severity,
                device_ip=alert.device_ip,
                device_id=alert.device_id,
                **alert.metrics,
            )

    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._started:
            try:
                await asyncio.sleep(60)  # 每分钟执行一次

                # 更新全局统计
                self._update_global_stats()

                # 生成性能报告
                await self._generate_performance_insights()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能监控异常: {e}")

    async def _generate_performance_insights(self) -> None:
        """生成性能洞察"""
        # 识别性能最差的设备
        worst_devices = sorted(self.device_profiles.values(), key=lambda d: d.reliability_score)[:5]

        if worst_devices and worst_devices[0].reliability_score < 0.5:
            logger.warning(
                "发现性能较差的设备",
                worst_device_ip=worst_devices[0].device_ip,
                reliability_score=worst_devices[0].reliability_score,
                consecutive_failures=worst_devices[0].consecutive_failures,
                average_response_time=worst_devices[0].average_response_time,
            )

        # 识别响应时间异常
        slow_devices = [
            device
            for device in self.device_profiles.values()
            if device.average_response_time > 5.0 and device.total_operations > 10
        ]

        if slow_devices:
            logger.info(
                f"发现响应较慢的设备: {len(slow_devices)}个",
                slow_devices=[
                    {"device_ip": d.device_ip, "average_response_time": d.average_response_time}
                    for d in slow_devices[:3]
                ],
            )

    def get_device_recommendations(self, device_ip: str, device_id: str | None = None) -> list[str]:
        """获取设备优化建议"""
        device_key = f"{device_ip}:{device_id}" if device_id else device_ip

        if device_key not in self.device_profiles:
            return ["设备暂无性能数据"]

        profile = self.device_profiles[device_key]
        recommendations = []

        # 响应时间建议
        if profile.average_response_time > 5.0:
            recommendations.append(f"响应时间较慢({profile.average_response_time:.2f}秒)，建议检查网络连接或设备负载")

        # 可靠性建议
        if profile.reliability_score < 0.7:
            recommendations.append(f"设备可靠性较低({profile.reliability_score:.2f})，建议检查设备状态和网络稳定性")

        # 错误类型建议
        if profile.error_types:
            most_common_error = max(profile.error_types.items(), key=lambda x: x[1])
            recommendations.append(f"常见错误类型: {most_common_error[0]}，建议针对性排查")

        # 连续失败建议
        if profile.consecutive_failures > 0:
            recommendations.append(f"当前连续失败{profile.consecutive_failures}次，建议立即检查设备连接")

        if not recommendations:
            recommendations.append("设备性能良好，无需特别优化")

        return recommendations

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        current_time = time.time()

        # 最近告警
        recent_alerts = [
            alert
            for alert in self.alerts
            if current_time - alert.timestamp <= 3600  # 最近1小时
        ]

        # 设备健康状态
        healthy_devices = sum(1 for device in self.device_profiles.values() if device.is_healthy)
        total_devices = len(self.device_profiles)

        # 性能趋势
        recent_operations = [op for op in self.operation_history if current_time - op.end_time <= 3600]

        return {
            "global_stats": self.global_stats,
            "device_health": {
                "total_devices": total_devices,
                "healthy_devices": healthy_devices,
                "unhealthy_devices": total_devices - healthy_devices,
                "health_rate": (healthy_devices / total_devices * 100) if total_devices > 0 else 0,
            },
            "recent_alerts": {
                "total": len(recent_alerts),
                "critical": len([a for a in recent_alerts if a.severity == "critical"]),
                "medium": len([a for a in recent_alerts if a.severity == "medium"]),
                "low": len([a for a in recent_alerts if a.severity == "low"]),
            },
            "performance_trends": {
                "recent_operations": len(recent_operations),
                "success_rate": (sum(1 for op in recent_operations if op.success) / len(recent_operations) * 100)
                if recent_operations
                else 0,
                "average_response_time": mean([op.duration for op in recent_operations]) if recent_operations else 0,
            },
        }

    def get_device_details(self, device_ip: str, device_id: str | None = None) -> dict[str, Any] | None:
        """获取设备详细性能信息"""
        device_key = f"{device_ip}:{device_id}" if device_id else device_ip

        if device_key not in self.device_profiles:
            return None

        profile = self.device_profiles[device_key]

        return {
            "device_info": {
                "device_ip": profile.device_ip,
                "device_id": profile.device_id,
                "is_healthy": profile.is_healthy,
                "reliability_score": profile.reliability_score,
            },
            "operation_stats": {
                "total_operations": profile.total_operations,
                "successful_operations": profile.successful_operations,
                "failed_operations": profile.failed_operations,
                "success_rate": profile.success_rate,
                "consecutive_failures": profile.consecutive_failures,
            },
            "response_time_stats": {
                "average": profile.average_response_time,
                "median": profile.median_response_time,
                "min": profile.min_response_time,
                "max": profile.max_response_time,
            },
            "error_analysis": profile.error_types,
            "recommendations": self.get_device_recommendations(device_ip, device_id),
            "last_success": profile.last_success_time,
            "last_failure": profile.last_failure_time,
        }


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
