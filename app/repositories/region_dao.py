"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region_dao.py
@DateTime: 2025-06-17
@Docs: 区域数据访问层实现
"""

from app.models.network_models import Region
from app.repositories.base_dao import BaseDAO


class RegionDAO(BaseDAO[Region]):
    """区域数据访问层

    继承BaseDAO，提供区域相关的数据访问方法
    """

    def __init__(self):
        """初始化区域DAO"""
        super().__init__(Region)

    async def get_by_name(self, name: str) -> Region | None:
        """根据区域名称获取区域

        Args:
            name: 区域名称

        Returns:
            区域实例或None
        """
        return await self.get_by_field("name", name)

    async def search_by_name(self, name_keyword: str) -> list[Region]:
        """根据名称关键字搜索区域

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的区域列表
        """
        return await self.list_by_filters(
            {"name": name_keyword},  # 会自动转换为模糊查询
            order_by=["name"],
        )

    async def check_name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """检查区域名称是否已存在

        Args:
            name: 区域名称
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"name": name}
        if exclude_id:
            # 排除指定ID的记录
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def get_regions_with_device_count(self) -> list[dict]:
        """获取区域及其设备数量

        Returns:
            包含区域信息和设备数量的字典列表
        """
        from tortoise.functions import Count

        return await (
            self.model.all().annotate(device_count=Count("devices")).values("id", "name", "description", "device_count")
        )

    async def paginate_regions(self, page: int = 1, page_size: int = 20, name_keyword: str | None = None) -> dict:
        """分页获取区域列表（性能优化版本）

        Args:
            page: 页码
            page_size: 每页大小
            name_keyword: 名称关键字过滤

        Returns:
            分页区域列表
        """
        filters = {}
        if name_keyword:
            filters["name"] = name_keyword

        return await self.paginate(page=page, page_size=page_size, filters=filters, order_by=["name"])

    async def bulk_create_regions(self, regions_data: list[dict]) -> list[Region]:
        """批量创建区域

        Args:
            regions_data: 区域数据列表

        Returns:
            创建的区域列表
        """
        return await self.bulk_create(regions_data)

    async def get_regions_with_device_statistics(self) -> list[dict]:
        """获取区域及其设备统计信息（优化版本）

        Returns:
            包含设备统计的区域列表
        """
        from tortoise.functions import Count

        return await (
            self.model.all()
            .annotate(device_count=Count("devices"))
            .order_by("name")
            .values(
                "id",
                "name",
                "snmp_community_string",
                "default_cli_username",
                "description",
                "device_count",
            )
        )

    async def get_regions_summary(self) -> dict:
        """获取区域概览统计

        Returns:
            区域统计信息
        """
        total_regions = await self.count()

        # 统计设备总数
        from tortoise.functions import Count

        device_stats = await self.model.all().annotate(total_devices=Count("devices")).values("total_devices")

        total_devices = sum(item["total_devices"] for item in device_stats)

        return {
            "total_regions": total_regions,
            "total_devices": total_devices,
            "avg_devices_per_region": round(total_devices / total_regions, 2) if total_regions > 0 else 0,
        }
