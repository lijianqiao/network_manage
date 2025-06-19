"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_model_dao.py
@DateTime: 2025-06-20
@Docs: 设备型号数据访问层实现
"""

from app.models.network_models import DeviceModel
from app.repositories.base_dao import BaseDAO


class DeviceModelDAO(BaseDAO[DeviceModel]):
    """设备型号数据访问层

    继承BaseDAO，提供设备型号相关的数据访问方法
    """

    def __init__(self):
        """初始化设备型号DAO"""
        super().__init__(DeviceModel)

    async def get_by_name(self, name: str) -> DeviceModel | None:
        """根据型号名称获取设备型号

        Args:
            name: 型号名称

        Returns:
            设备型号实例或None
        """
        return await self.get_by_field("name", name)

    async def get_by_brand(self, brand_id: int) -> list[DeviceModel]:
        """根据品牌ID获取设备型号列表

        Args:
            brand_id: 品牌ID

        Returns:
            设备型号列表
        """
        return await self.list_by_filters({"brand_id": brand_id}, prefetch_related=["brand"], order_by=["name"])

    async def search_by_name(self, name_keyword: str) -> list[DeviceModel]:
        """根据名称关键字搜索设备型号

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的设备型号列表
        """
        return await self.list_by_filters(
            {"name": name_keyword}, prefetch_related=["brand"], order_by=["brand__name", "name"]
        )

    async def check_name_exists_in_brand(self, name: str, brand_id: int, exclude_id: int | None = None) -> bool:
        """检查品牌下是否已存在同名型号

        Args:
            name: 型号名称
            brand_id: 品牌ID
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"name": name, "brand_id": brand_id}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def get_models_with_device_count(self) -> list[dict]:
        """获取设备型号及其设备数量

        Returns:
            包含型号信息和设备数量的字典列表
        """
        from tortoise.functions import Count

        return await (
            self.model.all()
            .select_related("brand")
            .annotate(device_count=Count("devices"))
            .values("id", "name", "description", "brand__name", "device_count")
        )
