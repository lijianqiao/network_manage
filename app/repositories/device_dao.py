"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_dao.py
@DateTime: 2025-06-20
@Docs: 设备数据访问层实现
"""

from typing import Optional

from tortoise.expressions import Q

from app.models.network_models import Device
from app.repositories.base_dao import BaseDAO


class DeviceDAO(BaseDAO[Device]):
    """设备数据访问层

    继承BaseDAO，提供设备相关的数据访问方法
    """

    def __init__(self):
        """初始化设备DAO"""
        super().__init__(Device)

    async def get_by_name(self, name: str) -> Optional[Device]:
        """根据设备名称获取设备

        Args:
            name: 设备名称

        Returns:
            设备实例或None
        """
        return await self.get_by_field("name", name)

    async def get_by_ip(self, ip_address: str) -> Optional[Device]:
        """根据IP地址获取设备

        Args:
            ip_address: IP地址

        Returns:
            设备实例或None
        """
        return await self.get_by_field("ip_address", ip_address)

    async def get_by_region(self, region_id: int) -> list[Device]:
        """根据区域ID获取设备列表

        Args:
            region_id: 区域ID

        Returns:
            设备列表
        """        
        return await self.list_by_filters(
            {"region_id": region_id},
            prefetch_related=["region", "device_group", "model"],
            order_by=["name"]
        )

    async def get_by_group(self, group_id: int) -> list[Device]:
        """根据设备分组ID获取设备列表

        Args:
            group_id: 设备分组ID

        Returns:
            设备列表
        """        
        return await self.list_by_filters(
            {"device_group_id": group_id},
            prefetch_related=["region", "device_group", "model"],
            order_by=["name"]
        )

    async def get_by_model(self, model_id: int) -> list[Device]:
        """根据设备型号ID获取设备列表

        Args:
            model_id: 设备型号ID

        Returns:
            设备列表
        """        
        return await self.list_by_filters(
            {"model_id": model_id},
            prefetch_related=["region", "device_group", "model"],
            order_by=["name"]
        )

    async def get_by_status(self, status: str) -> list[Device]:
        """根据设备状态获取设备列表

        Args:
            status: 设备状态

        Returns:
            设备列表
        """        
        return await self.list_by_filters(
            {"status": status},
            prefetch_related=["region", "device_group", "model"],
            order_by=["name"]
        )

    async def search_by_name(self, name_keyword: str) -> list[Device]:
        """根据名称关键字搜索设备

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的设备列表
        """
        return await self.list_by_filters(
            {"name": name_keyword},
            prefetch_related=["region", "device_group", "model"],
            order_by=["name"]
        )

    async def search_by_ip(self, ip_keyword: str) -> list[Device]:
        """根据IP关键字搜索设备

        Args:
            ip_keyword: IP关键字

        Returns:
            匹配的设备列表
        """
        # 使用自定义查询进行IP模糊搜索
        queryset = self.filter(ip_address__icontains=ip_keyword)
        return await queryset.prefetch_related("region", "device_group", "model").order_by("ip_address")

    async def check_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """检查设备名称是否已存在

        Args:
            name: 设备名称
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"name": name}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def check_ip_exists(self, ip_address: str, exclude_id: Optional[int] = None) -> bool:
        """检查IP地址是否已存在

        Args:
            ip_address: IP地址
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"ip_address": ip_address}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def get_devices_summary(self) -> dict:
        """获取设备统计摘要

        Returns:
            设备统计信息
        """
        total_count = await self.count()
        active_count = await self.count_active()
        
        # 按状态统计
        status_counts = await self.get_count_by_status("status")
        
        # 按区域统计
        from tortoise.functions import Count
        region_counts = await (
            self.model.all()
            .group_by("region_id")
            .annotate(count=Count("id"))
            .values("region__name", "count")
        )
        
        return {
            "total": total_count,
            "active": active_count,
            "by_status": status_counts,
            "by_region": {item["region__name"]: item["count"] for item in region_counts}
        }

    async def get_devices_with_connection_status(self) -> list[dict]:
        """获取设备及其连接状态

        Returns:
            包含设备信息和连接状态的字典列表
        """
        return await (
            self.model.all()
            .select_related("region", "device_group", "model")
            .prefetch_related("connection_statuses")
            .values(
                "id", "name", "ip_address", "status",
                "region__name", "device_group__name", "model__name",
                "connection_statuses__snmp_status", "connection_statuses__cli_status"
            )
        )

    async def get_online_devices(self) -> list[Device]:
        """获取在线设备列表

        Returns:
            在线设备列表
        """
        return await self.get_by_status("online")

    async def get_offline_devices(self) -> list[Device]:
        """获取离线设备列表

        Returns:
            离线设备列表
        """
        return await self.get_by_status("offline")

    async def paginate_devices(
        self,
        page: int = 1,
        page_size: int = 20,
        region_id: Optional[int] = None,
        device_group_id: Optional[int] = None,
        status: Optional[str] = None,
        name_keyword: Optional[str] = None
    ) -> dict:
        """分页获取设备列表（性能优化版本）

        Args:
            page: 页码
            page_size: 每页大小
            region_id: 区域ID过滤
            device_group_id: 设备组ID过滤
            status: 状态过滤
            name_keyword: 名称关键字过滤

        Returns:
            分页设备列表
        """
        filters = {}
        if region_id:
            filters["region_id"] = region_id
        if device_group_id:
            filters["device_group_id"] = device_group_id
        if status:
            filters["status"] = status
        if name_keyword:
            filters["name"] = name_keyword

        return await self.paginate(
            page=page,
            page_size=page_size,
            filters=filters,
            prefetch_related=["region", "device_group", "model"],
            order_by=["name"]
        )

    async def bulk_update_status(self, device_ids: list[int], status: str) -> int:
        """批量更新设备状态

        Args:
            device_ids: 设备ID列表
            status: 新状态

        Returns:
            更新的设备数量
        """
        return await self.update_by_filters(
            {"id__in": device_ids}, 
            status=status
        )

    async def get_devices_by_region_paginated(
        self, 
        region_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> dict:
        """分页获取指定区域的设备（优化版本）

        Args:
            region_id: 区域ID
            page: 页码
            page_size: 每页大小

        Returns:
            分页设备列表
        """
        return await self.paginate(
            page=page,
            page_size=page_size,
            filters={"region_id": region_id},
            prefetch_related=["region", "device_group", "model"],
            order_by=["name"]
        )

    async def get_devices_statistics(self) -> dict:
        """获取设备统计信息（优化版本）

        Returns:
            设备统计信息
        """
        from tortoise.functions import Count

        # 使用单个查询获取多种统计信息
        stats = await (
            self.model.all()
            .annotate(
                region_count=Count("region_id", distinct=True),
                total_count=Count("id")
            )
            .values("region_count", "total_count")
        )

        # 按状态统计
        status_stats = await self.get_count_by_status("status")
        
        # 按设备类型统计
        type_stats = await self.get_count_by_status("device_type")

        return {
            "total_devices": stats[0]["total_count"] if stats else 0,
            "total_regions": stats[0]["region_count"] if stats else 0,
            "by_status": status_stats,
            "by_type": type_stats
        }

    async def search_devices_optimized(
        self, 
        keyword: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> dict:
        """优化的设备搜索（支持分页）

        Args:
            keyword: 搜索关键字
            page: 页码
            page_size: 每页大小

        Returns:
            分页搜索结果
        """
        # 使用自定义查询优化搜索性能
        queryset = self.get_queryset()
        
        # 多字段模糊搜索
        queryset = queryset.filter(
            Q(name__icontains=keyword) | 
            Q(ip_address__icontains=keyword) |
            Q(serial_number__icontains=keyword)
        )
        
        # 预加载关联数据
        queryset = queryset.prefetch_related("region", "device_group", "model")
        
        # 计算总数
        total = await queryset.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = await queryset.offset(offset).limit(page_size).order_by("name")
        
        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }
