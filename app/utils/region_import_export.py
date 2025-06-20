"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region_import_export.py
@DateTime: 2025/01/19 00:00:00
@Docs: 区域导入导出实现
"""

from typing import Any

from tortoise.models import Model

from app.models.network_models import Region
from app.utils.base_import_export import BaseImportExport, FieldConfig, ImportExportConfig


class RegionImportExport(BaseImportExport):
    """区域导入导出实现类"""

    def __init__(self):
        """初始化区域导入导出配置"""
        fields = [
            FieldConfig(
                name="name",
                display_name="区域名称",
                required=True,
            ),
            FieldConfig(
                name="description",
                display_name="区域描述",
                required=False,
            ),
            FieldConfig(
                name="snmp_community_string",
                display_name="SNMP社区字符串",
                required=True,
                default_value="public",
            ),
            FieldConfig(
                name="default_cli_username",
                display_name="默认CLI用户名",
                required=True,
                default_value="admin",
            ),
        ]

        config = ImportExportConfig(
            model_class=Region,
            fields=fields,
            sheet_name="区域信息",
            create_missing_fk=False,  # 区域没有外键依赖
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
            区域模型没有外键依赖，此方法不应被调用
        """
        raise NotImplementedError("区域模型没有外键依赖")

    async def _custom_validate(self, create_data: dict[str, Any], row: dict[str, Any]) -> None:
        """
        自定义验证

        Args:
            create_data: 创建数据
            row: 原始行数据
        """
        # 验证区域名称不能重复
        name = create_data.get("name")
        if name:
            existing = await Region.filter(name=name, is_deleted=False).first()
            if existing:
                raise ValueError(f"区域名称 '{name}' 已存在")

        # 验证SNMP社区字符串不能为空
        snmp_community = create_data.get("snmp_community_string")
        if not snmp_community or not snmp_community.strip():
            raise ValueError("SNMP社区字符串不能为空")

        # 验证默认CLI用户名不能为空
        cli_username = create_data.get("default_cli_username")
        if not cli_username or not cli_username.strip():
            raise ValueError("默认CLI用户名不能为空")


# 创建全局实例，便于在API中直接使用
region_import_export = RegionImportExport()
