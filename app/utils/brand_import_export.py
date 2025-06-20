"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: brand_import_export.py
@DateTime: 2025/01/19 00:00:00
@Docs: 品牌导入导出实现
"""

from typing import Any

from tortoise.models import Model

from app.models.network_models import Brand
from app.utils.base_import_export import BaseImportExport, FieldConfig, ImportExportConfig


class BrandImportExport(BaseImportExport):
    """品牌导入导出实现类"""

    def __init__(self):
        """初始化品牌导入导出配置"""
        fields = [
            FieldConfig(
                name="name",
                display_name="品牌名称",
                required=True,
            ),
            FieldConfig(
                name="description",
                display_name="品牌描述",
                required=False,
            ),
            FieldConfig(
                name="platform_type",
                display_name="平台类型",
                required=True,
                default_value="hp_comware",
            ),
        ]

        config = ImportExportConfig(
            model_class=Brand,
            fields=fields,
            sheet_name="品牌信息",
            create_missing_fk=False,  # 品牌没有外键依赖
            batch_size=100,
        )

        super().__init__(config)

    async def _create_missing_foreign_key(self, fk_model: type[Model], fk_name: str, row: dict[str, Any]) -> Model:
        """
        创建缺失的外键记录

        Args:
            fk_model: 外键模型类
            fk_name: 外键名称
            row: 当前行数据

        Returns:
            创建的外键对象

        Note:
            品牌模型没有外键依赖，此方法不应被调用
        """
        raise NotImplementedError("品牌模型没有外键依赖")

    async def _custom_validate(self, create_data: dict[str, Any], row: dict[str, Any]) -> None:
        """
        自定义验证

        Args:
            create_data: 创建数据
            row: 原始行数据
        """
        # 验证品牌名称不能重复
        name = create_data.get("name")
        if name:
            existing = await Brand.filter(name=name, is_deleted=False).first()
            if existing:
                raise ValueError(f"品牌名称 '{name}' 已存在")

        # 验证平台类型不能重复
        platform_type = create_data.get("platform_type")
        if platform_type:
            existing = await Brand.filter(platform_type=platform_type, is_deleted=False).first()
            if existing:
                raise ValueError(f"平台类型 '{platform_type}' 已存在")

        # 验证平台类型不能为空
        if not platform_type or not platform_type.strip():
            raise ValueError("平台类型不能为空")


# 创建全局实例，便于在API中直接使用
brand_import_export = BrandImportExport()
