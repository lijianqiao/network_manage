"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: import_export_service.py
@DateTime: 2025/06/20 14:00:00
@Docs: 导入导出服务模块
"""

import io
from datetime import datetime
from typing import Any

import polars as pl
from fastapi import UploadFile

from app.core.exceptions import BusinessError, ValidationError
from app.models.network_models import (
    Brand,
    Device,
    DeviceGroup,
    DeviceModel,
    Region,
)
from app.utils.logger import logger


class ImportExportService:
    """导入导出服务类

    提供通用的数据导入导出功能，支持Excel格式
    """

    # 支持的模型映射
    SUPPORTED_MODELS = {
        "region": Region,
        "brand": Brand,
        "device_model": DeviceModel,
        "device_group": DeviceGroup,
        "device": Device,
    }

    # 字段映射配置
    FIELD_MAPPINGS = {
        "region": {
            "display_fields": ["name", "description", "snmp_community_string", "default_cli_username"],
            "required_fields": ["name", "snmp_community_string", "default_cli_username"],
            "foreign_keys": {},
        },
        "brand": {
            "display_fields": ["name", "description", "platform_type"],
            "required_fields": ["name", "platform_type"],
            "foreign_keys": {},
        },
        "device_model": {
            "display_fields": ["name", "description", "brand"],
            "required_fields": ["name", "brand"],
            "foreign_keys": {"brand": Brand},
        },
        "device_group": {
            "display_fields": ["name", "description", "region"],
            "required_fields": ["name"],
            "foreign_keys": {"region": Region},
        },
        "device": {
            "display_fields": [
                "name",
                "ip_address",
                "description",
                "region",
                "device_group",
                "model",
                "device_type",
                "serial_number",
                "is_dynamic_password",
                "cli_username",
                "status",
            ],
            "required_fields": ["name", "ip_address", "region", "device_group", "model", "device_type"],
            "foreign_keys": {
                "region": Region,
                "device_group": DeviceGroup,
                "model": DeviceModel,
            },
        },
    }

    def __init__(self):
        """初始化导入导出服务"""
        pass

    async def export_template(self, model_name: str) -> bytes:
        """导出模板文件

        Args:
            model_name: 模型名称

        Returns:
            Excel模板文件的字节数据

        Raises:
            ValidationError: 当模型名称不支持时
        """
        try:
            if model_name not in self.SUPPORTED_MODELS:
                raise ValidationError(f"不支持的模型: {model_name}")

            mapping = self.FIELD_MAPPINGS[model_name]
            headers = mapping["display_fields"]

            # 创建空的DataFrame作为模板
            template_data = {field: [] for field in headers}
            df = pl.DataFrame(template_data)

            # 转换为Excel字节数据
            excel_buffer = io.BytesIO()
            df.write_excel(excel_buffer)
            excel_buffer.seek(0)

            logger.info(f"成功生成{model_name}模板文件")
            return excel_buffer.getvalue()

        except Exception as e:
            logger.error(f"生成模板文件失败: {e}")
            raise BusinessError(f"生成模板文件失败: {str(e)}") from e

    async def export_data(self, model_name: str) -> bytes:
        """导出数据

        Args:
            model_name: 模型名称

        Returns:
            包含数据的Excel文件字节数据

        Raises:
            ValidationError: 当模型名称不支持时
            BusinessError: 当导出失败时
        """
        try:
            if model_name not in self.SUPPORTED_MODELS:
                raise ValidationError(f"不支持的模型: {model_name}")

            model_class = self.SUPPORTED_MODELS[model_name]
            mapping = self.FIELD_MAPPINGS[model_name]

            # 获取所有数据
            queryset = model_class.all()

            # 如果有外键，则预加载相关数据
            if mapping["foreign_keys"]:
                prefetch_fields = list(mapping["foreign_keys"].keys())
                queryset = queryset.prefetch_related(*prefetch_fields)

            records = await queryset

            # 转换数据为字典列表
            export_data = []
            for record in records:
                row_data = {}
                for field in mapping["display_fields"]:
                    if field in mapping["foreign_keys"]:
                        # 处理外键字段
                        related_obj = getattr(record, field, None)
                        if related_obj:
                            row_data[field] = getattr(related_obj, "name", str(related_obj))
                        else:
                            row_data[field] = ""
                    else:
                        # 处理普通字段
                        value = getattr(record, field, "")
                        row_data[field] = str(value) if value is not None else ""

                export_data.append(row_data)

            # 创建DataFrame
            if export_data:
                df = pl.DataFrame(export_data)
            else:
                # 如果没有数据，创建空的DataFrame
                template_data = {field: [] for field in mapping["display_fields"]}
                df = pl.DataFrame(template_data)

            # 转换为Excel字节数据
            excel_buffer = io.BytesIO()
            df.write_excel(excel_buffer)
            excel_buffer.seek(0)

            logger.info(f"成功导出{model_name}数据，共{len(export_data)}条记录")
            return excel_buffer.getvalue()

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise BusinessError(f"导出数据失败: {str(e)}") from e

    async def import_data(self, model_name: str, file: UploadFile, create_missing_fk: bool = True) -> dict[str, Any]:
        """导入数据

        Args:
            model_name: 模型名称
            file: 上传的Excel文件
            create_missing_fk: 是否创建缺失的外键记录

        Returns:
            导入结果统计

        Raises:
            ValidationError: 当模型名称不支持或文件格式错误时
            BusinessError: 当导入失败时
        """
        try:
            if model_name not in self.SUPPORTED_MODELS:
                raise ValidationError(f"不支持的模型: {model_name}")

            # 验证文件格式
            if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
                raise ValidationError("只支持Excel文件格式(.xlsx或.xls)")

            model_class = self.SUPPORTED_MODELS[model_name]
            mapping = self.FIELD_MAPPINGS[model_name]

            # 读取Excel文件
            file_content = await file.read()
            df = pl.read_excel(io.BytesIO(file_content))

            # 验证必要的列是否存在
            missing_columns = set(mapping["required_fields"]) - set(df.columns)
            if missing_columns:
                raise ValidationError(f"缺少必要的列: {', '.join(missing_columns)}")

            # 统计信息
            total_rows = len(df)
            success_count = 0
            error_count = 0
            errors = []

            # 逐行处理数据
            for row_idx, row in enumerate(df.iter_rows(named=True)):
                try:
                    # 构建创建数据
                    create_data = {}

                    # 处理普通字段
                    for field in mapping["display_fields"]:
                        if field not in mapping["foreign_keys"]:
                            value = row.get(field)
                            if value is not None and str(value).strip():
                                create_data[field] = str(value).strip()

                    # 处理外键字段
                    for fk_field, fk_model in mapping["foreign_keys"].items():
                        fk_value = row.get(fk_field)
                        if fk_value and str(fk_value).strip():
                            fk_name = str(fk_value).strip()

                            # 查找外键对象
                            fk_obj = await fk_model.filter(name=fk_name).first()

                            if not fk_obj:
                                if create_missing_fk:
                                    # 创建缺失的外键对象
                                    fk_obj = await fk_model.create(name=fk_name)
                                    logger.info(f"自动创建{fk_model.__name__}: {fk_name}")
                                else:
                                    raise ValueError(f"外键 {fk_field} 的值 '{fk_name}' 不存在")

                            create_data[fk_field] = fk_obj

                    # 验证必要字段
                    for required_field in mapping["required_fields"]:
                        if required_field not in create_data or not create_data[required_field]:
                            raise ValueError(f"必要字段 '{required_field}' 不能为空")

                    # 创建记录
                    await model_class.create(**create_data)
                    success_count += 1

                except Exception as row_error:
                    error_count += 1
                    error_msg = f"第{row_idx + 2}行: {str(row_error)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

            result = {
                "total_rows": total_rows,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:50],  # 最多返回50个错误
            }

            logger.info(f"导入完成: 总计{total_rows}行，成功{success_count}行，失败{error_count}行")
            return result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"导入数据失败: {e}")
            raise BusinessError(f"导入数据失败: {str(e)}") from e

    def get_filename(self, model_name: str, file_type: str) -> str:
        """生成文件名

        Args:
            model_name: 模型名称
            file_type: 文件类型 (template/data)

        Returns:
            生成的文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{model_name}_{file_type}_{timestamp}.xlsx"
