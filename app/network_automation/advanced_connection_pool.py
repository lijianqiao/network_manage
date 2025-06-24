"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: advanced_connection_pool.py
@DateTime: 2025/01/20 12:00:00
@Docs: 高级连接池管理器 - 支持连接复用、动态并发控制、健康检查
"""

import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from scrapli import AsyncScrapli

from app.core.enums import ConnectionState
from app.core.exceptions import DeviceAuthenticationError, DeviceConnectionError
from app.utils.logger import logger
from app.utils.network_logger import log_device_connection_failed, log_device_connection_success


@dataclass
class ConnectionInfo:
    """连接信息"""

    connection: AsyncScrapli
    device_key: str
    created_at: float
    last_used: float
    use_count: int = 0
    state: ConnectionState = ConnectionState.IDLE
    health_check_count: int = 0
    consecutive_failures: int = 0

    def is_expired(self, max_idle_time: float, max_lifetime: float) -> bool:
        """检查连接是否过期"""
        now = time.time()
        idle_time = now - self.last_used
        lifetime = now - self.created_at
        return idle_time > max_idle_time or lifetime > max_lifetime

    def is_healthy(self) -> bool:
        """检查连接是否健康"""
        return (
            self.state in (ConnectionState.IDLE, ConnectionState.ACTIVE)
            and self.consecutive_failures < 3
            and self.connection.isalive()
        )


@dataclass
class PoolStats:
    """连接池统计信息"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    connection_errors: int = 0
    average_response_time: float = 0.0
    peak_connections: int = 0
    created_connections: int = 0
    destroyed_connections: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


class DynamicConcurrencyController:
    """动态并发控制器"""

    def __init__(self, initial_limit: int = 20, min_limit: int = 5, max_limit: int = 100):
        self.current_limit = initial_limit
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.semaphore = asyncio.Semaphore(initial_limit)

        # 性能监控
        self.response_times: list[float] = []
        self.error_count = 0
        self.success_count = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 30.0  # 30秒调整一次

    async def acquire(self) -> None:
        """获取并发许可"""
        await self.semaphore.acquire()

    def release(self) -> None:
        """释放并发许可"""
        self.semaphore.release()

    def record_success(self, response_time: float) -> None:
        """记录成功操作"""
        self.success_count += 1
        self.response_times.append(response_time)

        # 保持最近100个响应时间
        if len(self.response_times) > 100:
            self.response_times.pop(0)

    def record_error(self) -> None:
        """记录错误操作"""
        self.error_count += 1

    def should_adjust(self) -> bool:
        """是否应该调整并发限制"""
        return time.time() - self.last_adjustment > self.adjustment_interval

    def calculate_optimal_limit(self) -> int:
        """计算最优并发限制"""
        if not self.response_times:
            return self.current_limit

        # 计算平均响应时间
        avg_response_time = sum(self.response_times) / len(self.response_times)

        # 计算错误率
        total_operations = self.success_count + self.error_count
        error_rate = self.error_count / total_operations if total_operations > 0 else 0

        # 动态调整策略
        if error_rate > 0.1:  # 错误率超过10%，降低并发
            new_limit = max(self.min_limit, int(self.current_limit * 0.8))
        elif error_rate < 0.02 and avg_response_time < 2.0:  # 错误率低且响应快，增加并发
            new_limit = min(self.max_limit, int(self.current_limit * 1.2))
        elif avg_response_time > 5.0:  # 响应时间过长，降低并发
            new_limit = max(self.min_limit, int(self.current_limit * 0.9))
        else:
            new_limit = self.current_limit

        return new_limit

    async def adjust_if_needed(self) -> None:
        """根据性能指标调整并发限制"""
        if not self.should_adjust():
            return

        new_limit = self.calculate_optimal_limit()

        if new_limit != self.current_limit:
            old_limit = self.current_limit
            self.current_limit = new_limit

            # 创建新的信号量
            self.semaphore = asyncio.Semaphore(new_limit)

            logger.info(
                f"动态调整并发限制: {old_limit} -> {new_limit}",
                old_limit=old_limit,
                new_limit=new_limit,
                error_rate=self.error_count / (self.success_count + self.error_count)
                if (self.success_count + self.error_count) > 0
                else 0,
                avg_response_time=sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            )

        # 重置统计
        self.error_count = 0
        self.success_count = 0
        self.response_times.clear()
        self.last_adjustment = time.time()


class AdvancedConnectionPool:
    """高级连接池管理器"""

    def __init__(
        self,
        max_connections_per_device: int = 3,
        max_total_connections: int = 50,
        max_idle_time: float = 300.0,  # 5分钟
        max_lifetime: float = 3600.0,  # 1小时
        health_check_interval: float = 60.0,  # 1分钟
        cleanup_interval: float = 120.0,  # 2分钟
    ):
        self.max_connections_per_device = max_connections_per_device
        self.max_total_connections = max_total_connections
        self.max_idle_time = max_idle_time
        self.max_lifetime = max_lifetime
        self.health_check_interval = health_check_interval
        self.cleanup_interval = cleanup_interval

        # 连接池存储
        self.pools: dict[str, list[ConnectionInfo]] = defaultdict(list)
        self.active_connections: set[ConnectionInfo] = set()
        self.connection_lock = asyncio.Lock()

        # 动态并发控制
        self.concurrency_controller = DynamicConcurrencyController()

        # 统计信息
        self.stats = PoolStats()

        # 后台任务
        self._cleanup_task: asyncio.Task | None = None
        self._health_check_task: asyncio.Task | None = None
        self._started = False

    async def start(self) -> None:
        """启动连接池"""
        if self._started:
            return

        self._started = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(
            "高级连接池已启动",
            max_connections_per_device=self.max_connections_per_device,
            max_total_connections=self.max_total_connections,
            max_idle_time=self.max_idle_time,
            max_lifetime=self.max_lifetime,
        )

    async def stop(self) -> None:
        """停止连接池"""
        if not self._started:
            return

        self._started = False

        # 取消后台任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # 关闭所有连接
        async with self.connection_lock:
            for device_pools in self.pools.values():
                for conn_info in device_pools:
                    await self._close_connection(conn_info)
            self.pools.clear()
            self.active_connections.clear()

        logger.info("高级连接池已停止")

    def _generate_device_key(self, host_data: dict[str, Any]) -> str:
        """生成设备唯一标识"""
        return f"{host_data['hostname']}:{host_data.get('port', 22)}:{host_data['username']}"

    async def _create_connection(self, host_data: dict[str, Any]) -> AsyncScrapli:
        """创建新连接"""
        device_ip = host_data.get("hostname")
        device_id = host_data.get("device_id")
        username = host_data.get("username")

        try:
            # 构建Scrapli连接参数
            connection_params = {
                "host": device_ip,
                "auth_username": username,
                "auth_password": host_data["password"],
                "auth_strict_key": False,
                "ssh_config_file": False,
                "timeout_socket": host_data.get("timeout_socket", 30),
                "timeout_transport": host_data.get("timeout_transport", 60),
                "port": host_data.get("port", 22),
                "transport": "asyncssh",
            }

            # 根据平台选择驱动
            platform = host_data.get("platform", "").lower()
            if platform in ["cisco_ios", "ios", "cisco"]:
                connection_params["platform"] = "cisco_iosxe"
            elif platform in ["cisco_nxos", "nxos"]:
                connection_params["platform"] = "cisco_nxos"
            elif platform in ["cisco_iosxr", "iosxr"]:
                connection_params["platform"] = "cisco_iosxr"
            elif platform in ["huawei_vrp", "vrp", "huawei"]:
                connection_params["platform"] = "huawei_vrp"
            elif platform in ["h3c_comware", "comware", "h3c"]:
                connection_params["platform"] = "hp_comware"
            else:
                connection_params["platform"] = "hp_comware"

            # 如果有enable密码，添加到连接参数
            if host_data.get("enable_password"):
                connection_params["auth_secondary"] = host_data["enable_password"]

            logger.debug(
                f"创建新连接: {device_ip}",
                device_ip=device_ip,
                device_id=device_id,
                platform=platform,
                port=connection_params["port"],
            )

            # 创建并打开连接
            conn = AsyncScrapli(**connection_params)
            await conn.open()

            self.stats.created_connections += 1

            return conn

        except Exception as e:
            error_msg = f"连接创建失败: {str(e)}"
            logger.error(
                f"创建连接失败 {device_ip}: {e}",
                device_ip=device_ip,
                device_id=device_id,
                error=str(e),
                error_type=e.__class__.__name__,
            )

            self.stats.connection_errors += 1

            if "authentication" in str(e).lower() or "login" in str(e).lower():
                raise DeviceAuthenticationError(
                    message="设备认证失败",
                    detail=error_msg,
                    device_id=device_id,
                    device_ip=device_ip,
                    username=username,
                ) from e
            else:
                raise DeviceConnectionError(
                    message=error_msg, detail=str(e), device_id=device_id, device_ip=device_ip
                ) from e

    async def _close_connection(self, conn_info: ConnectionInfo) -> None:
        """关闭连接"""
        try:
            if conn_info.connection.isalive():
                await conn_info.connection.close()
            self.stats.destroyed_connections += 1
            logger.debug(f"连接已关闭: {conn_info.device_key}")
        except Exception as e:
            logger.warning(f"关闭连接时出错: {e}")

    async def _get_or_create_connection(self, host_data: dict[str, Any]) -> ConnectionInfo:
        """获取或创建连接"""
        device_key = self._generate_device_key(host_data)

        async with self.connection_lock:
            # 尝试从池中获取可用连接
            device_pool = self.pools[device_key]

            for conn_info in device_pool[:]:  # 使用切片避免修改列表时的问题
                if conn_info.state == ConnectionState.IDLE and conn_info.is_healthy():
                    # 找到可用连接
                    conn_info.state = ConnectionState.ACTIVE
                    conn_info.last_used = time.time()
                    conn_info.use_count += 1
                    self.active_connections.add(conn_info)

                    self.stats.cache_hits += 1
                    self.stats.total_requests += 1

                    logger.debug(f"复用连接: {device_key} (使用次数: {conn_info.use_count})")
                    return conn_info

            # 检查是否可以创建新连接
            if (
                len(device_pool) >= self.max_connections_per_device
                or self.stats.total_connections >= self.max_total_connections
            ):
                # 尝试清理过期连接
                await self._cleanup_expired_connections()

                # 再次检查
                if (
                    len(device_pool) >= self.max_connections_per_device
                    or self.stats.total_connections >= self.max_total_connections
                ):
                    raise DeviceConnectionError(
                        message="连接池已满，无法创建新连接",
                        device_ip=host_data.get("hostname"),
                        device_id=host_data.get("device_id"),
                    )

            # 创建新连接
            connection = await self._create_connection(host_data)

            conn_info = ConnectionInfo(
                connection=connection,
                device_key=device_key,
                created_at=time.time(),
                last_used=time.time(),
                use_count=1,
                state=ConnectionState.ACTIVE,
            )

            device_pool.append(conn_info)
            self.active_connections.add(conn_info)

            self.stats.cache_misses += 1
            self.stats.total_requests += 1
            self.stats.total_connections += 1
            self.stats.peak_connections = max(self.stats.peak_connections, self.stats.total_connections)

            logger.debug(f"创建新连接: {device_key}")
            return conn_info

    async def _return_connection(self, conn_info: ConnectionInfo) -> None:
        """归还连接到池中"""
        async with self.connection_lock:
            if conn_info in self.active_connections:
                self.active_connections.remove(conn_info)

            if conn_info.is_healthy() and not conn_info.is_expired(self.max_idle_time, self.max_lifetime):
                conn_info.state = ConnectionState.IDLE
                logger.debug(f"连接已归还: {conn_info.device_key}")
            else:
                # 连接不健康或已过期，移除并关闭
                device_pool = self.pools[conn_info.device_key]
                if conn_info in device_pool:
                    device_pool.remove(conn_info)

                await self._close_connection(conn_info)
                self.stats.total_connections -= 1
                logger.debug(f"连接已移除: {conn_info.device_key}")

    @asynccontextmanager
    async def get_connection(self, host_data: dict[str, Any]):
        """获取连接的上下文管理器"""
        if not self._started:
            await self.start()

        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id") or ""
        start_time = time.time()

        # 动态并发控制
        await self.concurrency_controller.acquire()

        try:
            # 调整并发限制
            await self.concurrency_controller.adjust_if_needed()

            # 获取连接
            conn_info = await self._get_or_create_connection(host_data)

            try:
                yield conn_info.connection

                # 记录成功
                duration = time.time() - start_time
                self.concurrency_controller.record_success(duration)
                log_device_connection_success(device_ip, device_id, duration)

            except Exception as e:
                # 记录错误
                self.concurrency_controller.record_error()
                conn_info.consecutive_failures += 1

                if conn_info.consecutive_failures >= 3:
                    conn_info.state = ConnectionState.FAILED

                duration = time.time() - start_time
                log_device_connection_failed(device_ip, str(e), device_id, duration)
                raise

            finally:
                # 归还连接
                await self._return_connection(conn_info)

        finally:
            self.concurrency_controller.release()

    async def _cleanup_expired_connections(self) -> None:
        """清理过期连接"""
        removed_count = 0

        for device_key, device_pool in list(self.pools.items()):
            for conn_info in device_pool[:]:  # 使用切片避免修改列表时的问题
                if conn_info.state == ConnectionState.IDLE and conn_info.is_expired(
                    self.max_idle_time, self.max_lifetime
                ):
                    device_pool.remove(conn_info)
                    await self._close_connection(conn_info)
                    self.stats.total_connections -= 1
                    removed_count += 1

            # 如果设备池为空，移除它
            if not device_pool:
                del self.pools[device_key]

        if removed_count > 0:
            logger.debug(f"清理过期连接: {removed_count} 个")

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self._started:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"连接池清理异常: {e}")

    async def _health_check_connection(self, conn_info: ConnectionInfo) -> bool:
        """健康检查单个连接"""
        if not conn_info.connection.isalive():
            return False

        try:
            # 发送简单命令测试连接
            await conn_info.connection.send_command("", strip_prompt=False)
            conn_info.health_check_count += 1
            conn_info.consecutive_failures = 0
            return True
        except Exception:
            conn_info.consecutive_failures += 1
            return False

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self._started:
            try:
                await asyncio.sleep(self.health_check_interval)

                async with self.connection_lock:
                    for device_pool in self.pools.values():
                        for conn_info in device_pool[:]:
                            if conn_info.state == ConnectionState.IDLE:
                                conn_info.state = ConnectionState.CHECKING

                                if not await self._health_check_connection(conn_info):
                                    # 健康检查失败，移除连接
                                    device_pool.remove(conn_info)
                                    await self._close_connection(conn_info)
                                    self.stats.total_connections -= 1
                                    self.stats.failed_connections += 1
                                else:
                                    conn_info.state = ConnectionState.IDLE

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查异常: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取连接池统计信息"""
        # 更新实时统计
        self.stats.active_connections = len(self.active_connections)
        self.stats.idle_connections = sum(
            len([c for c in pool if c.state == ConnectionState.IDLE]) for pool in self.pools.values()
        )

        return {
            "pool_stats": {
                "total_connections": self.stats.total_connections,
                "active_connections": self.stats.active_connections,
                "idle_connections": self.stats.idle_connections,
                "failed_connections": self.stats.failed_connections,
                "peak_connections": self.stats.peak_connections,
                "created_connections": self.stats.created_connections,
                "destroyed_connections": self.stats.destroyed_connections,
            },
            "performance_stats": {
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "cache_hit_rate": f"{self.stats.cache_hit_rate:.2f}%",
                "connection_errors": self.stats.connection_errors,
                "average_response_time": self.stats.average_response_time,
            },
            "concurrency_stats": {
                "current_limit": self.concurrency_controller.current_limit,
                "min_limit": self.concurrency_controller.min_limit,
                "max_limit": self.concurrency_controller.max_limit,
                "available_permits": self.concurrency_controller.semaphore._value,
            },
            "device_pools": {device_key: len(pool) for device_key, pool in self.pools.items()},
        }


# 全局高级连接池实例
advanced_connection_pool = AdvancedConnectionPool()
