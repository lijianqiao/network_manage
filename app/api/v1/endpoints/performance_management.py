"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: performance_management.py
@DateTime: 2025/01/20 13:30:00
@Docs: 性能管理API端点 - 提供连接池统计、性能监控、优化建议等功能
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.network_automation.high_performance_connection_manager import high_performance_connection_manager
from app.schemas.performance import (
    ConnectionPoolStatsResponse,
    DevicePerformanceResponse,
    PerformanceOptimizationRequest,
    PerformanceOptimizationResponse,
)
from app.utils.logger import logger

router = APIRouter(prefix="/performance", tags=["性能管理"])


@router.get("/connection-pool/stats", response_model=ConnectionPoolStatsResponse, summary="获取连接池统计")
async def get_connection_pool_stats():
    """
    获取连接池统计信息

    包括：
    - 连接池状态（总连接数、活跃连接数、空闲连接数等）
    - 性能指标（缓存命中率、平均响应时间等）
    - 并发控制状态
    - 设备连接分布
    """
    try:
        stats = high_performance_connection_manager.get_connection_stats()

        logger.info("获取连接池统计信息")

        return ConnectionPoolStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取连接池统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取连接池统计失败: {str(e)}"
        ) from e


@router.get("/device/{device_ip}", response_model=DevicePerformanceResponse, summary="获取设备性能详情")
async def get_device_performance(device_ip: str, device_id: str | None = Query(None, description="设备ID")):
    """
    获取指定设备的性能详情

    包括：
    - 设备基本信息和健康状态
    - 操作统计（成功率、失败次数等）
    - 响应时间统计（平均值、中位数、最大最小值）
    - 错误分析
    - 优化建议
    """
    try:
        performance_data = high_performance_connection_manager.get_device_performance(device_ip, device_id)

        if not performance_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"设备 {device_ip} 暂无性能数据")

        logger.info(f"获取设备性能详情: {device_ip}")

        return DevicePerformanceResponse(**performance_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备性能详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备性能详情失败: {str(e)}"
        ) from e


@router.get("/device/{device_ip}/recommendations", response_model=list[str], summary="获取设备优化建议")
async def get_device_recommendations(device_ip: str, device_id: str | None = Query(None, description="设备ID")):
    """
    获取指定设备的优化建议

    基于设备的历史性能数据，提供针对性的优化建议：
    - 响应时间优化
    - 连接稳定性改善
    - 错误处理建议
    """
    try:
        recommendations = high_performance_connection_manager.get_device_recommendations(device_ip, device_id)

        logger.info(f"获取设备优化建议: {device_ip}")

        return recommendations

    except Exception as e:
        logger.error(f"获取设备优化建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备优化建议失败: {str(e)}"
        ) from e


@router.post("/optimize", response_model=PerformanceOptimizationResponse, summary="执行性能优化")
async def optimize_performance(request: PerformanceOptimizationRequest):
    """
    执行性能优化操作

    支持的优化动作：
    - adjust_concurrency: 调整并发限制
    - clear_cache: 清理连接缓存
    - restart_pool: 重启连接池
    - cleanup_expired: 清理过期连接
    """
    try:
        action = request.action
        parameters = request.parameters or {}

        logger.info(f"执行性能优化: {action}", action=action, parameters=parameters)

        if action == "adjust_concurrency":
            # 调整并发限制
            new_limit = parameters.get("new_limit")
            if not new_limit or not isinstance(new_limit, int) or new_limit < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="new_limit 参数必须是大于0的整数")

            import asyncio

            old_limit = high_performance_connection_manager.pool.concurrency_controller.current_limit
            high_performance_connection_manager.pool.concurrency_controller.current_limit = new_limit
            high_performance_connection_manager.pool.concurrency_controller.semaphore = asyncio.Semaphore(new_limit)

            return PerformanceOptimizationResponse(
                success=True,
                message=f"并发限制已调整: {old_limit} -> {new_limit}",
                old_settings={"concurrency_limit": old_limit},
                new_settings={"concurrency_limit": new_limit},
            )

        elif action == "clear_cache":
            # 清理连接缓存
            old_stats = high_performance_connection_manager.pool.get_stats()

            # 清理所有空闲连接
            await high_performance_connection_manager.pool._cleanup_expired_connections()

            new_stats = high_performance_connection_manager.pool.get_stats()

            return PerformanceOptimizationResponse(
                success=True,
                message="连接缓存已清理",
                old_settings={"total_connections": old_stats["pool_stats"]["total_connections"]},
                new_settings={"total_connections": new_stats["pool_stats"]["total_connections"]},
            )

        elif action == "restart_pool":
            # 重启连接池
            await high_performance_connection_manager.pool.stop()
            await high_performance_connection_manager.pool.start()

            return PerformanceOptimizationResponse(
                success=True, message="连接池已重启", old_settings=None, new_settings=None
            )

        elif action == "cleanup_expired":
            # 清理过期连接
            old_stats = high_performance_connection_manager.pool.get_stats()
            await high_performance_connection_manager.pool._cleanup_expired_connections()
            new_stats = high_performance_connection_manager.pool.get_stats()

            cleaned_count = old_stats["pool_stats"]["total_connections"] - new_stats["pool_stats"]["total_connections"]

            return PerformanceOptimizationResponse(
                success=True,
                message=f"已清理 {cleaned_count} 个过期连接",
                old_settings={"total_connections": old_stats["pool_stats"]["total_connections"]},
                new_settings={"total_connections": new_stats["pool_stats"]["total_connections"]},
            )

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的优化动作: {action}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"性能优化失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"性能优化失败: {str(e)}") from e


@router.get("/health", summary="性能健康检查")
async def performance_health_check():
    """
    性能健康检查

    检查连接池和性能监控系统的健康状态
    """
    try:
        stats = high_performance_connection_manager.get_connection_stats()

        # 健康检查指标
        pool_stats = stats["pool_stats"]
        performance_summary = stats["performance_summary"]

        health_issues = []

        # 检查连接池健康
        if pool_stats["total_connections"] >= pool_stats.get("max_connections", 50) * 0.9:
            health_issues.append("连接池使用率过高")

        if pool_stats["failed_connections"] > 10:
            health_issues.append("失败连接数过多")

        # 检查性能指标
        device_health = performance_summary.get("device_health", {})
        if device_health.get("health_rate", 100) < 80:
            health_issues.append("设备健康率偏低")

        recent_alerts = performance_summary.get("recent_alerts", {})
        if recent_alerts.get("critical", 0) > 0:
            health_issues.append("存在严重性能告警")

        is_healthy = len(health_issues) == 0

        result = {
            "healthy": is_healthy,
            "status": "healthy" if is_healthy else "warning",
            "issues": health_issues,
            "stats_summary": {
                "total_connections": pool_stats["total_connections"],
                "active_connections": pool_stats["active_connections"],
                "cache_hit_rate": stats["performance_stats"]["cache_hit_rate"],
                "device_health_rate": device_health.get("health_rate", 0),
                "recent_critical_alerts": recent_alerts.get("critical", 0),
            },
        }

        logger.info(f"性能健康检查完成: {'健康' if is_healthy else '存在问题'}")

        return result

    except Exception as e:
        logger.error(f"性能健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"性能健康检查失败: {str(e)}"
        ) from e


@router.get("/metrics/export", summary="导出性能指标")
async def export_performance_metrics(format: str = Query("json", description="导出格式", enum=["json", "prometheus"])):
    """
    导出性能指标

    支持格式：
    - json: JSON格式的详细指标
    - prometheus: Prometheus格式的指标（用于监控系统集成）
    """
    try:
        stats = high_performance_connection_manager.get_connection_stats()

        if format == "json":
            return stats

        elif format == "prometheus":
            # 转换为Prometheus格式
            pool_stats = stats["pool_stats"]
            performance_stats = stats["performance_stats"]
            concurrency_stats = stats["concurrency_stats"]

            prometheus_metrics = []

            # 连接池指标
            prometheus_metrics.extend(
                [
                    f"network_pool_total_connections {pool_stats['total_connections']}",
                    f"network_pool_active_connections {pool_stats['active_connections']}",
                    f"network_pool_idle_connections {pool_stats['idle_connections']}",
                    f"network_pool_failed_connections {pool_stats['failed_connections']}",
                    f"network_pool_peak_connections {pool_stats['peak_connections']}",
                ]
            )

            # 性能指标
            cache_hit_rate = float(performance_stats["cache_hit_rate"].rstrip("%"))
            prometheus_metrics.extend(
                [
                    f"network_performance_total_requests {performance_stats['total_requests']}",
                    f"network_performance_cache_hits {performance_stats['cache_hits']}",
                    f"network_performance_cache_misses {performance_stats['cache_misses']}",
                    f"network_performance_cache_hit_rate {cache_hit_rate}",
                    f"network_performance_connection_errors {performance_stats['connection_errors']}",
                ]
            )

            # 并发控制指标
            prometheus_metrics.extend(
                [
                    f"network_concurrency_current_limit {concurrency_stats['current_limit']}",
                    f"network_concurrency_available_permits {concurrency_stats['available_permits']}",
                ]
            )

            return {"content_type": "text/plain", "metrics": "\n".join(prometheus_metrics)}

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的导出格式: {format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"导出性能指标失败: {str(e)}"
        ) from e
