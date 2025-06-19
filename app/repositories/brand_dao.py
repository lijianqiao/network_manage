"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: brand_dao.py
@DateTime: 2025-06-20
@Docs: 品牌数据访问层实现
"""

from typing import Optional
from tortoise.functions import Count
from app.models.network_models import Brand
from app.repositories.base_dao import BaseDAO


class BrandDAO(BaseDAO[Brand]):
    """品牌数据访问层

    继承BaseDAO，提供品牌相关的数据访问方法
    """

    def __init__(self):
        """初始化品牌DAO"""
        super().__init__(Brand)

    async def get_by_name(self, name: str) -> Optional[Brand]:
        """根据品牌名称获取品牌

        Args:
            name: 品牌名称

        Returns:
            品牌实例或None
        """
        return await self.get_by_field("name", name)
        
    async def get_by_platform_type(self, platform_type: str) -> Optional[Brand]:
        """根据平台类型获取品牌

        Args:
            platform_type: 平台类型

        Returns:
            品牌实例或None
        """
        return await self.get_by_field("platform_type", platform_type)

    async def search_by_name(self, name_keyword: str) -> list[Brand]:
        """根据名称关键字搜索品牌

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的品牌列表
        """
        return await self.list_by_filters(
            {"name": name_keyword},
            order_by=["name"]
        )

    async def check_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """检查品牌名称是否已存在

        Args:
            name: 品牌名称
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"name": name}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def check_platform_type_exists(self, platform_type: str, exclude_id: Optional[int] = None) -> bool:
        """检查平台类型是否已存在

        Args:
            platform_type: 平台类型
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"platform_type": platform_type}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def get_brands_with_model_count(self) -> list[dict]:
        """获取品牌及其设备型号数量

        Returns:
            包含品牌信息和型号数量的字典列表
        """


        return await (
            self.model.all()
            .annotate(model_count=Count("device_models"))
            .values("id", "name", "platform_type", "description", "model_count")
        )

    async def get_all_brands_cached(self) -> list[Brand]:
        """获取所有品牌（适合缓存的方法）

        Returns:
            所有品牌列表
        """
        return await self.list_all(prefetch_related=["device_models"])

    async def bulk_create_brands(self, brands_data: list[dict]) -> list[Brand]:
        """批量创建品牌

        Args:
            brands_data: 品牌数据列表

        Returns:
            创建的品牌列表
        """
        return await self.bulk_create(brands_data)

    async def get_brands_with_statistics(self) -> list[dict]:
        """获取品牌及其统计信息（优化版本）

        Returns:
            包含统计信息的品牌列表       
        """


        return await (
            self.model.all()
            .annotate(
                model_count=Count("device_models"),
                device_count=Count("device_models__devices")
            )
            .order_by("name")
            .values(
                "id", "name", "platform_type", "description",
                "model_count", "device_count"
            )
        )

    async def search_brands_optimized(
        self, 
        keyword: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> dict:
        """优化的品牌搜索（支持分页）

        Args:
            keyword: 搜索关键字
            page: 页码
            page_size: 每页大小

        Returns:
            分页搜索结果
        """
        filters = {"name": keyword}
        
        return await self.paginate(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=["name"]
        )
