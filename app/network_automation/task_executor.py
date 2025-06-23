"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: task_executor.py
@DateTime: 2025/06/23 11:30:00
@Docs: Nornir任务执行器 - 执行各种自动化任务
"""

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import UUID

from nornir import InitNornir
from nornir.core.inventory import Inventory
from nornir.core.task import AggregatedResult

from app.core.config import settings
from app.network_automation.inventory_manager import DynamicInventoryManager
from app.utils.logger import logger


class NetworkTaskExecutor:
    """网络任务执行器

    负责任务调度、运行和结果聚合
    """

    def __init__(self, inventory_manager: DynamicInventoryManager, max_workers: int = 30):
        """初始化任务执行器

        Args:
            inventory_manager: 动态清单管理器
            max_workers: 最大并发工作线程数
        """
        self.inventory_manager = inventory_manager
        self.max_workers = max_workers
        self._nornir_instance = None

    def _create_nornir_instance(self, inventory: Inventory) -> Any:
        """创建Nornir实例

        Args:
            inventory: 设备清单

        Returns:
            配置好的Nornir实例
        """  # 使用最简单可行的方法
        try:
            # 创建临时空的主机文件来满足SimpleInventory要求
            import os
            import tempfile
            from datetime import datetime
            from pathlib import Path

            # 确保logs目录存在
            log_dir = Path(settings.BASE_DIR) / "logs"
            log_dir.mkdir(exist_ok=True)

            # 生成日期格式的日志文件名
            current_date = datetime.now().strftime("%Y-%m-%d")
            log_file = log_dir / f"nornir_{current_date}.log"

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                f.write("{}")  # 空的YAML文件
                hosts_file = f.name

            try:
                nr = InitNornir(
                    inventory={
                        "plugin": "SimpleInventory",
                        "options": {
                            "host_file": hosts_file,
                            "group_file": hosts_file,
                        },
                    },
                    logging={
                        "enabled": True,
                        "level": "INFO",
                        "log_file": str(log_file),
                        "to_console": False,
                    },
                )
                nr.inventory = inventory
                return nr
            finally:
                try:
                    os.unlink(hosts_file)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Nornir初始化失败: {e}")
            raise

    async def execute_task_on_devices(
        self,
        device_ids: list[UUID],
        task_func: Callable,
        task_kwargs: dict[str, Any] | None = None,
        runtime_credentials: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """在指定设备上执行任务

        Args:
            device_ids: 设备ID列表
            task_func: 要执行的任务函数
            task_kwargs: 任务参数
            runtime_credentials: 运行时凭据

        Returns:
            任务执行结果
        """
        try:
            # 创建动态清单
            inventory = await self.inventory_manager.create_inventory_from_devices(
                device_ids=device_ids, runtime_credentials=runtime_credentials
            )

            # 验证清单
            validation = self.inventory_manager.validate_inventory(inventory)
            logger.info(f"任务执行前清单验证: {validation}")

            # 创建Nornir实例
            nr = self._create_nornir_instance(inventory)

            # 执行任务
            if task_kwargs is None:
                task_kwargs = {}

            logger.info(f"开始执行任务，设备数量: {len(device_ids)}")
            result = nr.run(task=task_func, **task_kwargs)

            # 聚合结果
            aggregated_result = self._aggregate_results(result)
            logger.info(
                f"任务执行完成: 成功 {aggregated_result['success_count']}，失败 {aggregated_result['failure_count']}"
            )

            return aggregated_result

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            raise

    async def execute_task_on_region(
        self,
        region_id: UUID,
        task_func: Callable,
        task_kwargs: dict[str, Any] | None = None,
        runtime_credentials: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """在指定区域的所有设备上执行任务

        Args:
            region_id: 区域ID
            task_func: 要执行的任务函数
            task_kwargs: 任务参数
            runtime_credentials: 运行时凭据

        Returns:
            任务执行结果
        """
        try:
            # 创建区域清单
            inventory = await self.inventory_manager.create_inventory_from_region(
                region_id=region_id, runtime_credentials=runtime_credentials
            )

            # 创建Nornir实例并执行任务
            nr = self._create_nornir_instance(inventory)

            if task_kwargs is None:
                task_kwargs = {}

            logger.info(f"开始在区域 {region_id} 执行任务")
            result = nr.run(task=task_func, **task_kwargs)

            # 聚合结果
            aggregated_result = self._aggregate_results(result)
            logger.info(
                f"区域任务执行完成: 成功 {aggregated_result['success_count']}，失败 {aggregated_result['failure_count']}"
            )

            return aggregated_result

        except Exception as e:
            logger.error(f"区域任务执行失败: {e}")
            raise

    async def execute_task_on_group(
        self,
        group_id: UUID,
        task_func: Callable,
        task_kwargs: dict[str, Any] | None = None,
        runtime_credentials: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """在指定设备分组的所有设备上执行任务

        Args:
            group_id: 设备分组ID
            task_func: 要执行的任务函数
            task_kwargs: 任务参数
            runtime_credentials: 运行时凭据

        Returns:
            任务执行结果
        """
        try:
            # 创建分组清单
            inventory = await self.inventory_manager.create_inventory_from_group(
                group_id=group_id, runtime_credentials=runtime_credentials
            )

            # 创建Nornir实例并执行任务
            nr = self._create_nornir_instance(inventory)

            if task_kwargs is None:
                task_kwargs = {}

            logger.info(f"开始在设备分组 {group_id} 执行任务")
            result = nr.run(task=task_func, **task_kwargs)

            # 聚合结果
            aggregated_result = self._aggregate_results(result)
            logger.info(
                f"分组任务执行完成: 成功 {aggregated_result['success_count']}，失败 {aggregated_result['failure_count']}"
            )

            return aggregated_result

        except Exception as e:
            logger.error(f"分组任务执行失败: {e}")
            raise

    def _aggregate_results(self, result: AggregatedResult) -> dict[str, Any]:
        """聚合任务执行结果

        Args:
            result: Nornir执行结果

        Returns:
            聚合后的结果统计
        """
        aggregated = {
            "total_hosts": len(result),
            "success_count": 0,
            "failure_count": 0,
            "results": {},
            "failed_hosts": [],
            "successful_hosts": [],
        }

        for host, host_result in result.items():
            if host_result.failed:
                aggregated["failure_count"] += 1
                aggregated["failed_hosts"].append(host)
                aggregated["results"][host] = {
                    "status": "failed",
                    "error": str(host_result.exception) if host_result.exception else "Unknown error",
                    "result": None,
                }
            else:
                aggregated["success_count"] += 1
                aggregated["successful_hosts"].append(host)
                aggregated["results"][host] = {
                    "status": "success",
                    "error": None,
                    "result": host_result.result if hasattr(host_result, "result") else None,
                }

        return aggregated

    async def execute_concurrent_tasks(
        self, tasks: list[dict[str, Any]], max_concurrent: int = 5
    ) -> list[dict[str, Any]]:
        """并发执行多个任务

        Args:
            tasks: 任务列表，每个任务包含设备ID、任务函数等信息
            max_concurrent: 最大并发任务数

        Returns:
            所有任务的执行结果
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_task(task_info: dict[str, Any]) -> dict[str, Any]:
            """执行单个任务"""
            async with semaphore:
                try:
                    task_type = task_info.get("type", "devices")
                    task_func = task_info["task_func"]
                    task_kwargs = task_info.get("task_kwargs", {})
                    runtime_credentials = task_info.get("runtime_credentials", {})

                    if task_type == "devices":
                        return await self.execute_task_on_devices(
                            device_ids=task_info["device_ids"],
                            task_func=task_func,
                            task_kwargs=task_kwargs,
                            runtime_credentials=runtime_credentials,
                        )
                    elif task_type == "region":
                        return await self.execute_task_on_region(
                            region_id=task_info["region_id"],
                            task_func=task_func,
                            task_kwargs=task_kwargs,
                            runtime_credentials=runtime_credentials,
                        )
                    elif task_type == "group":
                        return await self.execute_task_on_group(
                            group_id=task_info["group_id"],
                            task_func=task_func,
                            task_kwargs=task_kwargs,
                            runtime_credentials=runtime_credentials,
                        )
                    else:
                        raise ValueError(f"不支持的任务类型: {task_type}")

                except Exception as e:
                    logger.error(f"任务执行失败: {e}")
                    return {"status": "error", "error": str(e), "task_info": task_info}

        # 并发执行所有任务
        raw_results = await asyncio.gather(*[execute_single_task(task) for task in tasks], return_exceptions=True)

        # 保证返回类型为 list[dict[str, Any]]
        results: list[dict[str, Any]] = []
        for item in raw_results:
            if isinstance(item, dict):
                results.append(item)
            elif isinstance(item, BaseException):
                results.append({"status": "error", "error": str(item)})
            else:
                results.append({"status": "error", "error": "Unknown error", "detail": str(item)})

        return results
