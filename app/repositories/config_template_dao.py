"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_template_dao.py
@DateTime: 2025-06-20
@Docs: 配置模板数据访问层实现
"""

from app.models.network_models import ConfigTemplate
from app.repositories.base_dao import BaseDAO


class ConfigTemplateDAO(BaseDAO[ConfigTemplate]):
    """配置模板数据访问层

    继承BaseDAO，提供配置模板相关的数据访问方法
    """

    def __init__(self):
        """初始化配置模板DAO"""
        super().__init__(ConfigTemplate)

    async def get_by_name(self, name: str) -> ConfigTemplate | None:
        """根据模板名称获取配置模板

        Args:
            name: 模板名称

        Returns:
            配置模板实例或None
        """
        return await self.get_by_field("name", name)

    async def get_by_template_type(self, template_type: str) -> list[ConfigTemplate]:
        """根据模板类型获取配置模板列表

        Args:
            template_type: 模板类型

        Returns:
            配置模板列表
        """
        return await self.list_by_filters({"template_type": template_type}, order_by=["name"])

    async def search_by_name(self, name_keyword: str) -> list[ConfigTemplate]:
        """根据名称关键字搜索配置模板

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的配置模板列表
        """
        return await self.list_by_filters({"name": name_keyword}, order_by=["name"])

    async def check_name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """检查模板名称是否已存在

        Args:
            name: 模板名称
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"name": name}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def get_active_templates(self) -> list[ConfigTemplate]:
        """获取活跃的配置模板

        Returns:
            活跃的配置模板列表
        """
        return await self.list_by_filters({"is_active": True}, order_by=["template_type", "name"])

    async def get_templates_with_usage_count(self) -> list[dict]:
        """获取配置模板及其使用次数

        Returns:
            包含模板信息和使用次数的字典列表
        """
        from tortoise.functions import Count

        return await (
            self.model.all()
            .annotate(usage_count=Count("operation_logs"))
            .values("id", "name", "template_type", "description", "is_active", "usage_count")
        )

    async def get_type_statistics(self) -> dict[str, int]:
        """获取各模板类型的数量统计

        Returns:
            模板类型与数量的映射
        """
        return await self.get_count_by_status("template_type")

    async def paginate_templates(
        self,
        page: int = 1,
        page_size: int = 20,
        template_type: str | None = None,
        is_active: bool | None = None,
        name_keyword: str | None = None,
    ) -> dict:
        """分页获取配置模板（性能优化版本）

        Args:
            page: 页码
            page_size: 每页大小
            template_type: 模板类型过滤
            is_active: 是否活跃过滤
            name_keyword: 名称关键字过滤

        Returns:
            分页模板列表
        """
        filters = {}
        if template_type:
            filters["template_type"] = template_type
        if is_active is not None:
            filters["is_active"] = is_active
        if name_keyword:
            filters["name"] = name_keyword

        return await self.paginate(page=page, page_size=page_size, filters=filters, order_by=["template_type", "name"])

    async def bulk_create_templates(self, templates_data: list[dict]) -> list[ConfigTemplate]:
        """批量创建配置模板

        Args:
            templates_data: 模板数据列表

        Returns:
            创建的模板列表
        """
        return await self.bulk_create(templates_data)

    async def bulk_toggle_status(self, template_ids: list[int], is_active: bool) -> int:
        """批量切换模板状态

        Args:
            template_ids: 模板ID列表
            is_active: 新的状态

        Returns:
            更新的模板数量
        """
        return await self.update_by_filters({"id__in": template_ids}, is_active=is_active)

    async def get_templates_statistics(self) -> dict:
        """获取模板统计信息

        Returns:
            模板统计信息
        """
        # 总数统计
        total_count = await self.count()
        active_count = await self.count(is_active=True)

        # 按类型统计
        type_stats = await self.get_count_by_status("template_type")

        return {
            "total_templates": total_count,
            "active_templates": active_count,
            "inactive_templates": total_count - active_count,
            "by_type": type_stats,
        }
