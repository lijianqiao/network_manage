"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_group_dao.py
@DateTime: 2025-06-20
@Docs: 设备分组数据访问层实现
"""

from app.models.network_models import DeviceGroup
from app.repositories.base_dao import BaseDAO


class DeviceGroupDAO(BaseDAO[DeviceGroup]):
    """设备分组数据访问层

    继承BaseDAO，提供设备分组相关的数据访问方法
    """

    def __init__(self):
        """初始化设备分组DAO"""
        super().__init__(DeviceGroup)

    async def get_by_name(self, name: str) -> DeviceGroup | None:
        """根据分组名称获取设备分组

        Args:
            name: 分组名称

        Returns:
            设备分组实例或None
        """
        return await self.get_by_field("name", name)

    async def get_by_region(self, region_id: int) -> list[DeviceGroup]:
        """根据区域ID获取设备分组列表

        Args:
            region_id: 区域ID

        Returns:
            设备分组列表
        """
        return await self.list_by_filters({"region_id": region_id}, prefetch_related=["region"], order_by=["name"])

    async def get_unassigned_groups(self) -> list[DeviceGroup]:
        """获取未分配区域的设备分组

        Returns:
            未分配区域的设备分组列表
        """
        return await self.list_by_filters({"region_id": None}, order_by=["name"])

    async def search_by_name(self, name_keyword: str) -> list[DeviceGroup]:
        """根据名称关键字搜索设备分组

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的设备分组列表
        """
        return await self.list_by_filters({"name": name_keyword}, prefetch_related=["region"], order_by=["name"])

    async def check_name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """检查分组名称是否已存在

        Args:
            name: 分组名称
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"name": name}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def get_groups_with_device_count(self) -> list[dict]:
        """获取设备分组及其设备数量

        Returns:
            包含分组信息和设备数量的字典列表
        """
        from tortoise.functions import Count

        return await (
            self.model.all()
            .select_related("region")
            .annotate(device_count=Count("devices"))
            .values("id", "name", "description", "region__name", "device_count")
        )

    async def get_groups_by_region_with_count(self) -> dict[str, list[dict]]:
        """按区域分组获取设备分组及设备数量

        Returns:
            按区域分组的设备分组数据
        """
        groups_data = await self.get_groups_with_device_count()

        result = {}
        for group in groups_data:
            region_name = group.get("region__name", "未分配区域")
            if region_name not in result:
                result[region_name] = []
            result[region_name].append(group)

        return result
