"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_model_import_export.py
@DateTime: 2025/01/19 00:00:00
@Docs: 设备型号导入导出实现
"""

from typing import Any

from tortoise.models import Model

from app.models.network_models import Brand, DeviceModel
from app.utils.base_import_export import BaseImportExport, FieldConfig, ImportExportConfig


class DeviceModelImportExport(BaseImportExport):
    """设备型号导入导出实现类"""

    def __init__(self):
        """初始化设备型号导入导出配置"""
        fields = [
            FieldConfig(
                name="name",
                display_name="型号名称",
                required=True,
            ),
            FieldConfig(
                name="description",
                display_name="型号描述",
                required=False,
            ),
            FieldConfig(
                name="brand",
                display_name="所属品牌",
                required=True,
                foreign_key_model=Brand,
            ),
        ]

        config = ImportExportConfig(
            model_class=DeviceModel,
            fields=fields,
            sheet_name="设备型号信息",
            create_missing_fk=True,  # 允许自动创建品牌
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
        """
        if fk_model == Brand:
            # 创建品牌记录
            create_data = {
                "name": fk_name,
                "platform_type": "generic",  # 默认平台类型
            }

            # 如果行数据中包含平台类型信息，使用它
            if "平台类型" in row and row["平台类型"]:
                create_data["platform_type"] = str(row["平台类型"]).strip()

            # 如果行数据中包含品牌描述，使用它
            if "品牌描述" in row and row["品牌描述"]:
                create_data["description"] = str(row["品牌描述"]).strip()

            return await Brand.create(using_db=None, **create_data)
        else:
            raise ValueError(f"不支持自动创建的外键类型: {fk_model.__name__}")

    async def _custom_validate(self, create_data: dict[str, Any], row: dict[str, Any]) -> None:
        """
        自定义验证

        Args:
            create_data: 创建数据
            row: 原始行数据
        """
        # 验证设备型号名称不能重复
        name = create_data.get("name")
        if name:
            existing = await DeviceModel.filter(name=name, is_deleted=False).first()
            if existing:
                raise ValueError(f"设备型号名称 '{name}' 已存在")

        # 验证品牌必须存在
        brand = create_data.get("brand")
        if not brand:
            raise ValueError("所属品牌不能为空")


# 创建全局实例，便于在API中直接使用
device_model_import_export = DeviceModelImportExport()
