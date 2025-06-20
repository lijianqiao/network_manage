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

    async def search_by_name(self, name_keyword: str) -> list[DeviceGroup]:
        """根据名称关键字搜索设备分组

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的设备分组列表
        """
        return await self.list_by_filters({"name": name_keyword}, order_by=["name"])

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
            self.model.all().annotate(device_count=Count("devices")).values("id", "name", "description", "device_count")
        )
