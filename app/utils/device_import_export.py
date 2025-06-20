"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_import_export.py
@DateTime: 2025/01/19 00:00:00
@Docs: 设备导入导出实现
"""

import ipaddress
from typing import Any

from tortoise.models import Model

from app.models.network_models import (
    Brand,
    Device,
    DeviceGroup,
    DeviceModel,
    DeviceStatusEnum,
    DeviceTypeEnum,
    Region,
)
from app.utils.base_import_export import BaseImportExport, FieldConfig, ImportExportConfig


def validate_ip_address(value: Any) -> str:
    """验证并格式化IP地址"""
    try:
        ip = ipaddress.ip_address(str(value).strip())
        return str(ip)
    except ipaddress.AddressValueError as e:
        raise ValueError(f"无效的IP地址: {value}") from e


def transform_device_type(value: Any) -> str:
    """转换设备类型"""
    value_str = str(value).strip().lower()
    if value_str in ["switch", "交换机"]:
        return DeviceTypeEnum.SWITCH
    elif value_str in ["router", "路由器"]:
        return DeviceTypeEnum.ROUTER
    else:
        raise ValueError(f"不支持的设备类型: {value}")


def transform_device_status(value: Any) -> str:
    """转换设备状态"""
    if not value or str(value).strip() == "":
        return DeviceStatusEnum.UNKNOWN

    value_str = str(value).strip().lower()
    if value_str in ["online", "在线"]:
        return DeviceStatusEnum.ONLINE
    elif value_str in ["offline", "离线"]:
        return DeviceStatusEnum.OFFLINE
    else:
        return DeviceStatusEnum.UNKNOWN


def transform_boolean(value: Any) -> bool:
    """转换布尔值"""
    if isinstance(value, bool):
        return value

    value_str = str(value).strip().lower()
    if value_str in ["true", "1", "是", "yes", "y"]:
        return True
    elif value_str in ["false", "0", "否", "no", "n"]:
        return False
    else:
        return False  # 默认为False


class DeviceImportExport(BaseImportExport):
    """设备导入导出实现类"""

    def __init__(self):
        """初始化设备导入导出配置"""
        fields = [
            FieldConfig(
                name="name",
                display_name="设备名称",
                required=True,
            ),
            FieldConfig(
                name="ip_address",
                display_name="IP地址",
                required=True,
                transform_func=validate_ip_address,
            ),
            FieldConfig(
                name="description",
                display_name="设备描述",
                required=False,
            ),
            FieldConfig(
                name="region",
                display_name="所属区域",
                required=True,
                foreign_key_model=Region,
            ),
            FieldConfig(
                name="device_group",
                display_name="设备分组",
                required=True,
                foreign_key_model=DeviceGroup,
            ),
            FieldConfig(
                name="model",
                display_name="设备型号",
                required=True,
                foreign_key_model=DeviceModel,
            ),
            FieldConfig(
                name="device_type",
                display_name="设备类型",
                required=True,
                transform_func=transform_device_type,
            ),
            FieldConfig(
                name="serial_number",
                display_name="序列号",
                required=False,
            ),
            FieldConfig(
                name="is_dynamic_password",
                display_name="动态密码",
                required=False,
                default_value=True,
                transform_func=transform_boolean,
            ),
            FieldConfig(
                name="cli_username",
                display_name="CLI用户名",
                required=False,
            ),
            FieldConfig(
                name="status",
                display_name="设备状态",
                required=False,
                default_value=DeviceStatusEnum.UNKNOWN,
                transform_func=transform_device_status,
            ),
        ]

        config = ImportExportConfig(
            model_class=Device,
            fields=fields,
            sheet_name="设备信息",
            create_missing_fk=True,  # 允许自动创建外键
            batch_size=50,  # 设备数据较复杂，减小批量大小
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
        if fk_model == Region:
            # 创建区域记录
            create_data = {
                "name": fk_name,
                "snmp_community_string": "public",
                "default_cli_username": "admin",
            }

            # 如果行数据中包含SNMP社区字符串，使用它
            if "SNMP社区字符串" in row and row["SNMP社区字符串"]:
                create_data["snmp_community_string"] = str(row["SNMP社区字符串"]).strip()

            # 如果行数据中包含默认CLI用户名，使用它
            if "默认CLI用户名" in row and row["默认CLI用户名"]:
                create_data["default_cli_username"] = str(row["默认CLI用户名"]).strip()

            # 如果行数据中包含区域描述，使用它
            if "区域描述" in row and row["区域描述"]:
                create_data["description"] = str(row["区域描述"]).strip()

            return await Region.create(using_db=None, **create_data)

        elif fk_model == DeviceGroup:
            # 创建设备分组记录
            create_data = {
                "name": fk_name,
            }

            # 如果行数据中包含分组描述，使用它
            if "分组描述" in row and row["分组描述"]:
                create_data["description"] = str(row["分组描述"]).strip()

            return await DeviceGroup.create(using_db=None, **create_data)

        elif fk_model == DeviceModel:
            # 创建设备型号记录，需要先确保品牌存在
            # 从设备型号中尝试提取品牌信息
            brand_name = "Unknown"
            if "品牌" in row and row["品牌"]:
                brand_name = str(row["品牌"]).strip()
            else:
                # 尝试从型号名称中提取品牌（简单策略）
                if fk_name.upper().startswith(("H3C", "HP")):
                    brand_name = "H3C"
                elif fk_name.upper().startswith(("HUAWEI", "CE", "S5", "S6")):
                    brand_name = "Huawei"
                elif fk_name.upper().startswith("CISCO"):
                    brand_name = "Cisco"

            # 查找或创建品牌
            brand = await Brand.filter(name=brand_name).first()
            if not brand:
                brand = await Brand.create(name=brand_name, platform_type="generic")

            create_data = {
                "name": fk_name,
                "brand": brand,
            }

            # 如果行数据中包含型号描述，使用它
            if "型号描述" in row and row["型号描述"]:
                create_data["description"] = str(row["型号描述"]).strip()

            return await DeviceModel.create(using_db=None, **create_data)

        else:
            raise ValueError(f"不支持自动创建的外键类型: {fk_model.__name__}")

    async def _custom_validate(self, create_data: dict[str, Any], row: dict[str, Any]) -> None:
        """
        自定义验证

        Args:
            create_data: 创建数据
            row: 原始行数据
        """
        # 验证设备名称不能重复
        name = create_data.get("name")
        if name:
            existing = await Device.filter(name=name, is_deleted=False).first()
            if existing:
                raise ValueError(f"设备名称 '{name}' 已存在")

        # 验证IP地址不能重复
        ip_address = create_data.get("ip_address")
        if ip_address:
            existing = await Device.filter(ip_address=ip_address, is_deleted=False).first()
            if existing:
                raise ValueError(f"IP地址 '{ip_address}' 已存在")

        # 验证当不使用动态密码时，CLI用户名必须提供
        is_dynamic_password = create_data.get("is_dynamic_password", True)
        cli_username = create_data.get("cli_username")

        if not is_dynamic_password and not cli_username:
            raise ValueError("当不使用动态密码时，CLI用户名不能为空")

        # 验证必需的外键
        required_fks = ["region", "device_group", "model"]
        for fk_field in required_fks:
            if not create_data.get(fk_field):
                field_display = {"region": "所属区域", "device_group": "设备分组", "model": "设备型号"}
                raise ValueError(f"{field_display.get(fk_field, fk_field)}不能为空")


# 创建全局实例，便于在API中直接使用
device_import_export = DeviceImportExport()
