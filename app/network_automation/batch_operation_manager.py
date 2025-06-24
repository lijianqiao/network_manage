"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: batch_operation_manager.py
@DateTime: 2025/01/20 14:30:00
@Docs: 批量操作管理器 - 提供批量设备操作、进度跟踪、错误恢复等功能
"""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from typing import Any

from app.core.enums import BatchStrategy, OperationStatus, OperationType
from app.network_automation.high_performance_connection_manager import high_performance_connection_manager
from app.utils.logger import logger


@dataclass
class DeviceOperation:
    """设备操作"""

    device_id: str
    device_ip: str
    device_name: str | None
    operation_id: str
    operation_type: OperationType
    parameters: dict[str, Any]
    status: OperationStatus = OperationStatus.PENDING
    start_time: float | None = None
    end_time: float | None = None
    duration: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    error_type: str | None = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class BatchOperationProgress:
    """批量操作进度"""

    total_devices: int
    completed_devices: int
    successful_devices: int
    failed_devices: int
    pending_devices: int
    running_devices: int

    @property
    def completion_percentage(self) -> float:
        """完成百分比"""
        if self.total_devices == 0:
            return 0.0
        return (self.completed_devices / self.total_devices) * 100

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.completed_devices == 0:
            return 0.0
        return (self.successful_devices / self.completed_devices) * 100


@dataclass
class BatchOperationResult:
    """批量操作结果"""

    batch_id: str
    operation_type: OperationType
    strategy: BatchStrategy
    start_time: float
    end_time: float | None
    total_duration: float | None
    progress: BatchOperationProgress
    device_operations: list[DeviceOperation] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.progress.completed_devices == self.progress.total_devices

    @property
    def is_successful(self) -> bool:
        """是否成功"""
        return self.is_completed and self.progress.failed_devices == 0


class BatchOperationManager:
    """批量操作管理器"""

    def __init__(self, max_concurrent_operations: int = 20):
        self.max_concurrent_operations = max_concurrent_operations
        self.active_batches: dict[str, BatchOperationResult] = {}
        self.operation_semaphore = asyncio.Semaphore(max_concurrent_operations)

        # 操作处理器映射
        self.operation_handlers = {
            OperationType.COMMAND_EXECUTION: self._handle_command_execution,
            OperationType.CONFIG_DEPLOYMENT: self._handle_config_deployment,
            OperationType.CONFIG_BACKUP: self._handle_config_backup,
            OperationType.CONNECTIVITY_TEST: self._handle_connectivity_test,
            OperationType.DEVICE_INFO_COLLECTION: self._handle_device_info_collection,
        }

    async def execute_batch_operation(
        self,
        devices: list[dict[str, Any]],
        operation_type: OperationType,
        operation_params: dict[str, Any],
        strategy: BatchStrategy = BatchStrategy.PARALLEL,
        max_retries: int = 3,
        timeout_per_device: float = 300.0,
        progress_callback: Callable[[BatchOperationProgress], None] | None = None,
    ) -> AsyncGenerator[BatchOperationResult]:
        """
        执行批量操作

        Args:
            devices: 设备列表
            operation_type: 操作类型
            operation_params: 操作参数
            strategy: 批量策略
            max_retries: 最大重试次数
            timeout_per_device: 每设备超时时间
            progress_callback: 进度回调函数

        Yields:
            批量操作结果（实时更新）
        """
        batch_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(
            f"开始批量操作: {operation_type.value}",
            batch_id=batch_id,
            device_count=len(devices),
            strategy=strategy.value,
            operation_params=operation_params,
        )

        # 创建设备操作列表
        device_operations = []
        for device in devices:
            operation = DeviceOperation(
                device_id=device.get("device_id", ""),
                device_ip=device.get("hostname", device.get("ip", "")),
                device_name=device.get("device_name", ""),
                operation_id=str(uuid.uuid4()),
                operation_type=operation_type,
                parameters={**operation_params, "host_data": device},
                max_retries=max_retries,
            )
            device_operations.append(operation)

        # 创建批量操作结果
        batch_result = BatchOperationResult(
            batch_id=batch_id,
            operation_type=operation_type,
            strategy=strategy,
            start_time=start_time,
            end_time=None,
            total_duration=None,
            progress=BatchOperationProgress(
                total_devices=len(devices),
                completed_devices=0,
                successful_devices=0,
                failed_devices=0,
                pending_devices=len(devices),
                running_devices=0,
            ),
            device_operations=device_operations,
        )

        # 注册活跃批次
        self.active_batches[batch_id] = batch_result

        try:
            # 根据策略执行操作
            if strategy == BatchStrategy.PARALLEL:
                await self._execute_parallel(batch_result, progress_callback)
            elif strategy == BatchStrategy.SEQUENTIAL:
                await self._execute_sequential(batch_result, progress_callback)
            elif strategy == BatchStrategy.FAIL_FAST:
                await self._execute_fail_fast(batch_result, progress_callback)
            elif strategy == BatchStrategy.CONTINUE_ON_ERROR:
                await self._execute_continue_on_error(batch_result, progress_callback)

            # 完成操作
            batch_result.end_time = time.time()
            batch_result.total_duration = batch_result.end_time - batch_result.start_time
            batch_result.summary = self._generate_summary(batch_result)

            logger.info(
                f"批量操作完成: {operation_type.value}",
                batch_id=batch_id,
                total_duration=batch_result.total_duration,
                success_rate=batch_result.progress.success_rate,
                successful_devices=batch_result.progress.successful_devices,
                failed_devices=batch_result.progress.failed_devices,
            )

            yield batch_result

        except Exception as e:
            logger.error(
                f"批量操作异常: {operation_type.value}",
                batch_id=batch_id,
                error=str(e),
                error_type=e.__class__.__name__,
            )

            batch_result.end_time = time.time()
            batch_result.total_duration = batch_result.end_time - batch_result.start_time
            batch_result.errors.append({"error": str(e), "error_type": e.__class__.__name__, "timestamp": time.time()})

            yield batch_result

        finally:
            # 清理活跃批次
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]

    async def _execute_parallel(
        self, batch_result: BatchOperationResult, progress_callback: Callable[[BatchOperationProgress], None] | None
    ):
        """并行执行"""
        tasks = []

        for operation in batch_result.device_operations:
            task = asyncio.create_task(self._execute_single_operation(operation, batch_result, progress_callback))
            tasks.append(task)

        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_sequential(
        self, batch_result: BatchOperationResult, progress_callback: Callable[[BatchOperationProgress], None] | None
    ):
        """顺序执行"""
        for operation in batch_result.device_operations:
            await self._execute_single_operation(operation, batch_result, progress_callback)

    async def _execute_fail_fast(
        self, batch_result: BatchOperationResult, progress_callback: Callable[[BatchOperationProgress], None] | None
    ):
        """快速失败执行"""
        for operation in batch_result.device_operations:
            await self._execute_single_operation(operation, batch_result, progress_callback)

            # 如果有失败，立即停止
            if operation.status == OperationStatus.FAILED:
                logger.warning(
                    "快速失败策略触发，停止批量操作", batch_id=batch_result.batch_id, failed_device=operation.device_ip
                )

                # 将剩余操作标记为取消
                for remaining_op in batch_result.device_operations:
                    if remaining_op.status == OperationStatus.PENDING:
                        remaining_op.status = OperationStatus.CANCELLED
                        batch_result.progress.pending_devices -= 1
                        batch_result.progress.completed_devices += 1

                break

    async def _execute_continue_on_error(
        self, batch_result: BatchOperationResult, progress_callback: Callable[[BatchOperationProgress], None] | None
    ):
        """遇错继续执行"""
        # 与并行执行相同，但会记录所有错误
        await self._execute_parallel(batch_result, progress_callback)

    async def _execute_single_operation(
        self,
        operation: DeviceOperation,
        batch_result: BatchOperationResult,
        progress_callback: Callable[[BatchOperationProgress], None] | None,
    ):
        """执行单个设备操作"""
        async with self.operation_semaphore:
            # 更新状态为运行中
            operation.status = OperationStatus.RUNNING
            operation.start_time = time.time()
            batch_result.progress.pending_devices -= 1
            batch_result.progress.running_devices += 1

            # 调用进度回调
            if progress_callback:
                progress_callback(batch_result.progress)

            try:
                # 获取操作处理器
                handler = self.operation_handlers.get(operation.operation_type)
                if not handler:
                    raise ValueError(f"不支持的操作类型: {operation.operation_type}")

                # 执行操作（带重试）
                for attempt in range(operation.max_retries + 1):
                    try:
                        operation.retry_count = attempt
                        result = await handler(operation)
                        operation.result = result
                        operation.status = OperationStatus.SUCCESS
                        break

                    except Exception as e:
                        operation.error = str(e)
                        operation.error_type = e.__class__.__name__

                        if attempt < operation.max_retries:
                            logger.warning(
                                f"设备操作失败，准备重试: {operation.device_ip}",
                                device_ip=operation.device_ip,
                                attempt=attempt + 1,
                                max_retries=operation.max_retries,
                                error=str(e),
                            )
                            await asyncio.sleep(2**attempt)  # 指数退避
                        else:
                            operation.status = OperationStatus.FAILED
                            logger.error(
                                f"设备操作最终失败: {operation.device_ip}",
                                device_ip=operation.device_ip,
                                total_attempts=attempt + 1,
                                error=str(e),
                            )

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.error = str(e)
                operation.error_type = e.__class__.__name__

                logger.error(
                    f"设备操作异常: {operation.device_ip}",
                    device_ip=operation.device_ip,
                    error=str(e),
                    error_type=e.__class__.__name__,
                )

            finally:
                # 更新完成状态
                operation.end_time = time.time()
                operation.duration = operation.end_time - operation.start_time

                batch_result.progress.running_devices -= 1
                batch_result.progress.completed_devices += 1

                if operation.status == OperationStatus.SUCCESS:
                    batch_result.progress.successful_devices += 1
                else:
                    batch_result.progress.failed_devices += 1
                    batch_result.errors.append(
                        {
                            "device_ip": operation.device_ip,
                            "device_id": operation.device_id,
                            "error": operation.error,
                            "error_type": operation.error_type,
                            "timestamp": operation.end_time,
                        }
                    )

                # 调用进度回调
                if progress_callback:
                    progress_callback(batch_result.progress)

    async def _handle_command_execution(self, operation: DeviceOperation) -> dict[str, Any]:
        """处理命令执行操作"""
        host_data = operation.parameters["host_data"]
        command = operation.parameters.get("command", "")

        if not command:
            raise ValueError("缺少命令参数")

        return await high_performance_connection_manager.execute_command(host_data, command)

    async def _handle_config_deployment(self, operation: DeviceOperation) -> dict[str, Any]:
        """处理配置部署操作"""
        host_data = operation.parameters["host_data"]
        config = operation.parameters.get("config", "")

        if not config:
            raise ValueError("缺少配置参数")

        return await high_performance_connection_manager.send_config(host_data, config)

    async def _handle_config_backup(self, operation: DeviceOperation) -> dict[str, Any]:
        """处理配置备份操作"""
        host_data = operation.parameters["host_data"]
        return await high_performance_connection_manager.backup_configuration(host_data)

    async def _handle_connectivity_test(self, operation: DeviceOperation) -> dict[str, Any]:
        """处理连通性测试操作"""
        host_data = operation.parameters["host_data"]
        return await high_performance_connection_manager.test_connectivity(host_data)

    async def _handle_device_info_collection(self, operation: DeviceOperation) -> dict[str, Any]:
        """处理设备信息收集操作"""
        host_data = operation.parameters["host_data"]
        return await high_performance_connection_manager.get_device_facts(host_data)

    def _generate_summary(self, batch_result: BatchOperationResult) -> dict[str, Any]:
        """生成批量操作摘要"""
        summary = {
            "total_devices": batch_result.progress.total_devices,
            "successful_devices": batch_result.progress.successful_devices,
            "failed_devices": batch_result.progress.failed_devices,
            "success_rate": batch_result.progress.success_rate,
            "total_duration": batch_result.total_duration,
            "average_duration_per_device": 0.0,
            "fastest_device": None,
            "slowest_device": None,
            "error_breakdown": {},
        }

        # 计算平均耗时
        completed_operations = [op for op in batch_result.device_operations if op.duration is not None]
        if completed_operations:
            total_duration = sum(op.duration for op in completed_operations if op.duration is not None)
            summary["average_duration_per_device"] = total_duration / len(completed_operations)

            # 找出最快和最慢的设备
            # 由于completed_operations都保证了duration不为None，可以直接用op.duration
            fastest = min(completed_operations, key=lambda op: op.duration)  # type: ignore
            slowest = max(completed_operations, key=lambda op: op.duration)  # type: ignore

            summary["fastest_device"] = {"device_ip": fastest.device_ip, "duration": fastest.duration}
            summary["slowest_device"] = {"device_ip": slowest.device_ip, "duration": slowest.duration}

        # 错误类型统计
        for error in batch_result.errors:
            error_type = error.get("error_type", "Unknown")
            if error_type not in summary["error_breakdown"]:
                summary["error_breakdown"][error_type] = 0
            summary["error_breakdown"][error_type] += 1

        return summary

    def get_batch_status(self, batch_id: str) -> BatchOperationResult | None:
        """获取批量操作状态"""
        return self.active_batches.get(batch_id)

    def cancel_batch_operation(self, batch_id: str) -> bool:
        """取消批量操作"""
        if batch_id not in self.active_batches:
            return False

        batch_result = self.active_batches[batch_id]

        # 将所有待执行的操作标记为取消
        cancelled_count = 0
        for operation in batch_result.device_operations:
            if operation.status == OperationStatus.PENDING:
                operation.status = OperationStatus.CANCELLED
                cancelled_count += 1

        logger.info(f"批量操作已取消: {batch_id}", batch_id=batch_id, cancelled_operations=cancelled_count)

        return True

    def get_active_batches(self) -> list[str]:
        """获取活跃的批量操作ID列表"""
        return list(self.active_batches.keys())


# 全局批量操作管理器实例
batch_operation_manager = BatchOperationManager()
