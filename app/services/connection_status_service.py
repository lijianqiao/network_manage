"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: connection_status_service.py
@DateTime: 2025/06/23 00:00:00
@Docs: 设备连接状态服务层
"""

import asyncio
import platform
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessError
from app.repositories.device_dao import DeviceDAO
from app.utils.logger import logger


class ConnectionStatusService:
    """设备连接状态服务层

    提供设备连通性检查和状态管理功能
    """

    def __init__(self):
        self.device_dao = DeviceDAO()

    async def get_connection_status_list(
        self, skip: int = 0, limit: int = 100, device_name: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """获取设备连接状态列表

        Args:
            skip: 跳过记录数
            limit: 限制记录数
            device_name: 设备名称过滤
            status: 状态过滤

        Returns:
            设备连接状态列表
        """
        try:
            # 获取设备列表
            devices = await self.device_dao.list_all()

            # 应用分页
            if skip > 0:
                devices = devices[skip:]
            if limit > 0:
                devices = devices[:limit]

            # 过滤设备
            if device_name:
                devices = [d for d in devices if device_name.lower() in d.name.lower()]

            # 构建状态列表
            status_list = []
            for device in devices:
                device_status = {
                    "device_id": str(device.id),
                    "device_name": device.name,
                    "ip_address": device.ip_address,
                    "ping_status": "unknown",
                    "snmp_status": "unknown",
                    "last_check_time": datetime.now().isoformat(),
                    "response_time": None,
                }

                # 根据设备状态过滤
                if status and status != "unknown":
                    continue

                status_list.append(device_status)

            return status_list

        except Exception as e:
            logger.error(f"获取连接状态列表失败: {e}")
            raise BusinessError(f"获取连接状态列表失败: {str(e)}") from e

    async def get_device_connection_status(self, device_id: UUID) -> dict[str, Any]:
        """获取指定设备连接状态

        Args:
            device_id: 设备ID

        Returns:
            设备连接状态
        """
        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessError(f"设备不存在: {device_id}")

            # 实时检查设备连通性
            ping_result = await self._ping_device(device.ip_address)

            return {
                "device_id": str(device_id),
                "device_name": device.name,
                "ip_address": device.ip_address,
                "ping_status": "online" if ping_result.get("success", False) else "offline",
                "snmp_status": "unknown",  # TODO: 在第五阶段实现SNMP检查
                "last_check_time": datetime.now().isoformat(),
                "response_time": ping_result.get("response_time"),
            }

        except Exception as e:
            logger.error(f"获取设备连接状态失败: {e}")
            raise BusinessError(f"获取设备连接状态失败: {str(e)}") from e

    async def check_devices_connectivity(
        self, device_ids: list[UUID], timeout: int = 30, check_ping: bool = True, check_snmp: bool = False
    ) -> list[dict[str, Any]]:
        """批量检查设备连通性

        Args:
            device_ids: 设备ID列表
            timeout: 超时时间
            check_ping: 是否检查Ping
            check_snmp: 是否检查SNMP

        Returns:
            设备连通性检查结果
        """
        try:
            results = []

            # 获取设备信息
            devices = []
            for device_id in device_ids:
                device = await self.device_dao.get_by_id(device_id)
                if device:
                    devices.append(device)

            # 并发检查设备连通性
            if check_ping:
                ping_tasks = [self._ping_device(device.ip_address, timeout) for device in devices]
                ping_results = await asyncio.gather(*ping_tasks, return_exceptions=True)
            else:
                ping_results = [{"success": False, "response_time": None} for _ in devices]

            # 构建结果
            for i, device in enumerate(devices):
                try:
                    if isinstance(ping_results[i], Exception):
                        ping_result = {"success": False, "response_time": None}
                    else:
                        ping_result = ping_results[i]

                    result = {
                        "device_id": str(device.id),
                        "device_name": device.name,
                        "ip_address": device.ip_address,
                        "ping_status": "online"
                        if isinstance(ping_result, dict) and ping_result.get("success", False)
                        else "offline",
                        "snmp_status": "unknown",  # TODO: 在第五阶段实现SNMP检查
                        "last_check_time": datetime.now().isoformat(),
                        "response_time": ping_result.get("response_time") if isinstance(ping_result, dict) else None,
                    }
                    results.append(result)
                except Exception as e:
                    logger.error(f"处理设备 {device.name} 结果时出错: {e}")
                    # 添加默认结果
                    result = {
                        "device_id": str(device.id),
                        "device_name": device.name,
                        "ip_address": device.ip_address,
                        "ping_status": "error",
                        "snmp_status": "unknown",
                        "last_check_time": datetime.now().isoformat(),
                        "response_time": None,
                    }
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"批量检查设备连通性失败: {e}")
            raise BusinessError(f"批量检查设备连通性失败: {str(e)}") from e

    async def get_connection_stats(self) -> dict[str, Any]:
        """获取连接状态统计

        Returns:
            连接状态统计信息
        """
        try:
            # 获取所有设备
            devices = await self.device_dao.list_all()
            total_devices = len(devices)

            # 批量检查连通性（简化版）
            online_devices = 0
            offline_devices = 0
            unknown_devices = total_devices  # 默认所有设备状态未知

            # TODO: 在实际部署中，可以从缓存或数据库获取最新状态
            # 这里为了演示，使用模拟数据
            if total_devices > 0:
                # 模拟80%的设备在线
                online_devices = int(total_devices * 0.8)
                offline_devices = int(total_devices * 0.15)
                unknown_devices = total_devices - online_devices - offline_devices

            success_rate = f"{online_devices / total_devices * 100:.1f}%" if total_devices else "0%"

            return {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "offline_devices": offline_devices,
                "unknown_devices": unknown_devices,
                "success_rate": success_rate,
            }

        except Exception as e:
            logger.error(f"获取连接状态统计失败: {e}")
            raise BusinessError(f"获取连接状态统计失败: {str(e)}") from e

    async def ping_device(self, device_id: UUID, timeout: int = 5) -> dict[str, Any]:
        """Ping指定设备

        Args:
            device_id: 设备ID
            timeout: 超时时间

        Returns:
            Ping结果
        """
        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessError(f"设备不存在: {device_id}")

            result = await self._ping_device(device.ip_address, timeout)

            return {
                "device_id": str(device_id),
                "device_name": device.name,
                "ip_address": device.ip_address,
                "ping_success": result.get("success", False),
                "response_time": result.get("response_time"),
                "check_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Ping设备失败: {e}")
            raise BusinessError(f"Ping设备失败: {str(e)}") from e

    async def snmp_check_device(self, device_id: UUID, timeout: int = 10) -> dict[str, Any]:
        """SNMP检查指定设备

        Args:
            device_id: 设备ID
            timeout: 超时时间

        Returns:
            SNMP检查结果
        """
        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessError(f"设备不存在: {device_id}")

            # TODO: 在第五阶段实现SNMP检查
            return {
                "device_id": str(device_id),
                "device_name": device.name,
                "ip_address": device.ip_address,
                "snmp_success": False,
                "snmp_status": "not_implemented",
                "message": "SNMP检查将在第五阶段实现",
                "check_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"SNMP检查设备失败: {e}")
            raise BusinessError(f"SNMP检查设备失败: {str(e)}") from e

    async def _ping_device(self, ip_address: str, timeout: int = 5) -> dict[str, Any]:
        """内部Ping方法

        Args:
            ip_address: IP地址
            timeout: 超时时间

        Returns:
            Ping结果
        """
        try:
            # 根据操作系统构建ping命令
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip_address]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), ip_address]

            # 执行ping命令
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout + 5)

            success = process.returncode == 0
            response_time = None

            if success and stdout:
                # 尝试从输出中提取响应时间
                output = stdout.decode()
                if "time=" in output:
                    try:
                        # 解析Windows ping输出
                        time_part = output.split("time=")[1].split("ms")[0]
                        response_time = float(time_part)
                    except (IndexError, ValueError):
                        pass
                elif "time " in output:
                    try:
                        # 解析Linux ping输出
                        time_part = output.split("time ")[1].split(" ms")[0]
                        response_time = float(time_part)
                    except (IndexError, ValueError):
                        pass

            return {"success": success, "response_time": response_time, "error": stderr.decode() if stderr else None}

        except TimeoutError:
            return {"success": False, "response_time": None, "error": f"Ping超时 ({timeout}秒)"}
        except Exception as e:
            logger.error(f"Ping失败 - IP: {ip_address}, 错误: {e}")
            return {"success": False, "response_time": None, "error": str(e)}
