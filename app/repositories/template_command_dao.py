"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: template_command_dao.py
@DateTime: 2025-06-22
@Docs: 模板命令数据访问层实现
"""

from uuid import UUID

from app.models.network_models import TemplateCommand
from app.repositories.base_dao import BaseDAO


class TemplateCommandDAO(BaseDAO[TemplateCommand]):
    """模板命令数据访问层

    继承BaseDAO，提供模板命令相关的数据访问方法
    """

    def __init__(self):
        """初始化模板命令DAO"""
        super().__init__(TemplateCommand)

    async def get_by_template_and_brand(self, template_id: UUID, brand_id: UUID) -> TemplateCommand | None:
        """根据模板ID和品牌ID获取模板命令

        Args:
            template_id: 配置模板ID
            brand_id: 品牌ID

        Returns:
            模板命令实例或None
        """
        return await self.get_by_filters(config_template_id=template_id, brand_id=brand_id)

    async def get_commands_by_template(self, template_id: UUID) -> list[TemplateCommand]:
        """根据配置模板ID获取所有模板命令

        Args:
            template_id: 配置模板ID

        Returns:
            模板命令列表
        """
        return await self.list_by_filters(
            {"config_template_id": template_id}, prefetch_related=["brand", "config_template"], order_by=["brand__name"]
        )

    async def get_commands_by_brand(self, brand_id: UUID) -> list[TemplateCommand]:
        """根据品牌ID获取所有模板命令

        Args:
            brand_id: 品牌ID

        Returns:
            模板命令列表
        """
        return await self.list_by_filters(
            {"brand_id": brand_id}, prefetch_related=["brand", "config_template"], order_by=["config_template__name"]
        )

    async def check_command_exists(self, template_id: UUID, brand_id: UUID, exclude_id: UUID | None = None) -> bool:
        """检查模板命令组合是否已存在

        Args:
            template_id: 配置模板ID
            brand_id: 品牌ID
            exclude_id: 排除的ID（用于更新时检查）

        Returns:
            是否存在
        """
        filters = {"config_template_id": template_id, "brand_id": brand_id}
        if exclude_id:
            queryset = self.filter(**filters).exclude(id=exclude_id)
            return await queryset.exists()
        return await self.exists(**filters)

    async def get_template_supported_brands(self, template_id: UUID) -> list[dict]:
        """获取模板支持的品牌列表

        Args:
            template_id: 配置模板ID

        Returns:
            品牌信息列表
        """
        return await (
            self.model.filter(config_template_id=template_id)
            .select_related("brand")
            .values("brand__id", "brand__name", "brand__platform_type")
        )

    async def get_brand_supported_templates(self, brand_id: UUID) -> list[dict]:
        """获取品牌支持的模板列表

        Args:
            brand_id: 品牌ID

        Returns:
            模板信息列表
        """
        return await (
            self.model.filter(brand_id=brand_id)
            .select_related("config_template")
            .values("config_template__id", "config_template__name", "config_template__template_type")
        )

    async def bulk_create_commands(self, commands_data: list[dict]) -> list[TemplateCommand]:
        """批量创建模板命令

        Args:
            commands_data: 命令数据列表

        Returns:
            创建的命令列表
        """
        return await self.bulk_create(commands_data)

    async def delete_commands_by_template(self, template_id: UUID) -> int:
        """删除指定模板的所有命令

        Args:
            template_id: 配置模板ID

        Returns:
            删除的命令数量
        """
        commands = await self.model.filter(config_template_id=template_id).all()
        count = len(commands)
        await self.model.filter(config_template_id=template_id).delete()
        return count

    async def delete_commands_by_brand(self, brand_id: UUID) -> int:
        """删除指定品牌的所有命令

        Args:
            brand_id: 品牌ID

        Returns:
            删除的命令数量
        """
        commands = await self.model.filter(brand_id=brand_id).all()
        count = len(commands)
        await self.model.filter(brand_id=brand_id).delete()
        return count

    async def get_commands_statistics(self) -> dict:
        """获取模板命令统计信息

        Returns:
            统计信息字典
        """
        from tortoise.functions import Count

        # 总命令数量
        total_commands = await self.count()

        # 按模板统计
        template_stats = await (
            self.model.all()
            .select_related("config_template")
            .group_by("config_template_id")
            .annotate(command_count=Count("id"))
            .values("config_template__name", "config_template__template_type", "command_count")
        )

        # 按品牌统计
        brand_stats = await (
            self.model.all()
            .select_related("brand")
            .group_by("brand_id")
            .annotate(command_count=Count("id"))
            .values("brand__name", "brand__platform_type", "command_count")
        )

        return {
            "total_commands": total_commands,
            "by_template": template_stats,
            "by_brand": brand_stats,
        }

    async def paginate_commands(
        self,
        page: int = 1,
        page_size: int = 20,
        template_id: UUID | None = None,
        brand_id: UUID | None = None,
        template_name: str | None = None,
        brand_name: str | None = None,
    ) -> dict:
        """分页获取模板命令

        Args:
            page: 页码
            page_size: 每页大小
            template_id: 配置模板ID过滤
            brand_id: 品牌ID过滤
            template_name: 模板名称过滤
            brand_name: 品牌名称过滤

        Returns:
            分页命令列表
        """
        filters = {}
        if template_id:
            filters["config_template_id"] = template_id
        if brand_id:
            filters["brand_id"] = brand_id
        if template_name:
            filters["config_template__name__icontains"] = template_name
        if brand_name:
            filters["brand__name__icontains"] = brand_name

        return await self.paginate(
            page=page,
            page_size=page_size,
            filters=filters,
            prefetch_related=["brand", "config_template"],
            order_by=["config_template__name", "brand__name"],
        )
