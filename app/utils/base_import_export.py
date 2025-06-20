"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base_import_export.py
@DateTime: 2025/06/20 00:00:00
@Docs: 通用导入导出基础模块
"""

import io
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any

import polars as pl
from fastapi import UploadFile
from tortoise.models import Model

from app.core.exceptions import BusinessError, ValidationError
from app.utils.logger import logger


class FieldConfig:
    """字段配置类"""

    def __init__(
        self,
        name: str,
        display_name: str | None = None,
        required: bool = False,
        foreign_key_model: type[Model] | None = None,
        default_value: Any = None,
        export_only: bool = False,
        import_only: bool = False,
        transform_func: Callable[[Any], Any] | None = None,
    ):
        """
        Args:
            name: 字段名称
            display_name: 显示名称（Excel列名）
            required: 是否必需
            foreign_key_model: 外键模型类
            default_value: 默认值
            export_only: 仅导出
            import_only: 仅导入
            transform_func: 数据转换函数
        """
        self.name = name
        self.display_name = display_name or name
        self.required = required
        self.foreign_key_model = foreign_key_model
        self.default_value = default_value
        self.export_only = export_only
        self.import_only = import_only
        self.transform_func = transform_func

    @property
    def is_foreign_key(self) -> bool:
        """是否为外键字段"""
        return self.foreign_key_model is not None


class ImportExportConfig:
    """导入导出配置类"""

    def __init__(
        self,
        model_class: type[Model],
        fields: list[FieldConfig],
        sheet_name: str | None = None,
        create_missing_fk: bool = True,
        batch_size: int = 100,
    ):
        """
        Args:
            model_class: 模型类
            fields: 字段配置列表
            sheet_name: Excel工作表名称
            create_missing_fk: 是否自动创建缺失的外键记录
            batch_size: 批量处理大小
        """
        self.model_class = model_class
        self.fields = fields
        self.sheet_name = sheet_name or model_class.__name__
        self.create_missing_fk = create_missing_fk
        self.batch_size = batch_size

    @property
    def export_fields(self) -> list[FieldConfig]:
        """获取导出字段"""
        return [f for f in self.fields if not f.import_only]

    @property
    def import_fields(self) -> list[FieldConfig]:
        """获取导入字段"""
        return [f for f in self.fields if not f.export_only]

    @property
    def required_fields(self) -> list[FieldConfig]:
        """获取必需字段"""
        return [f for f in self.import_fields if f.required]

    @property
    def foreign_key_fields(self) -> list[FieldConfig]:
        """获取外键字段"""
        return [f for f in self.import_fields if f.is_foreign_key]


class BaseImportExport(ABC):
    """导入导出基础类"""

    def __init__(self, config: ImportExportConfig):
        """
        Args:
            config: 导入导出配置
        """
        self.config = config

    async def export_template(self) -> bytes:
        """导出Excel模板

        Returns:
            Excel模板文件字节数据
        """
        try:
            # 创建空的数据框，只包含列名
            columns = {field.display_name: [] for field in self.config.export_fields}
            df = pl.DataFrame(columns)

            # 转换为Excel
            excel_buffer = io.BytesIO()
            df.write_excel(excel_buffer, worksheet=self.config.sheet_name)
            excel_buffer.seek(0)

            logger.info(f"成功生成{self.config.model_class.__name__}模板")
            return excel_buffer.getvalue()

        except Exception as e:
            logger.error(f"生成模板失败: {e}")
            raise BusinessError(f"生成模板失败: {str(e)}") from e

    async def export_data(self, filters: dict[str, Any] | None = None) -> bytes:
        """导出数据到Excel

        Args:
            filters: 过滤条件

        Returns:
            Excel文件字节数据
        """
        try:
            # 构建查询
            queryset = self.config.model_class.all()

            if filters:
                queryset = queryset.filter(**filters)

            # 预加载外键关系
            fk_fields = [f.name for f in self.config.foreign_key_fields]
            if fk_fields:
                queryset = queryset.prefetch_related(*fk_fields)

            records = await queryset

            # 转换数据
            export_data = []
            for record in records:
                row_data = {}
                for field in self.config.export_fields:
                    value = await self._get_export_value(record, field)
                    row_data[field.display_name] = value
                export_data.append(row_data)

            # 创建数据框
            if export_data:
                df = pl.DataFrame(export_data)
            else:
                columns = {field.display_name: [] for field in self.config.export_fields}
                df = pl.DataFrame(columns)

            # 转换为Excel
            excel_buffer = io.BytesIO()
            df.write_excel(excel_buffer, worksheet=self.config.sheet_name)
            excel_buffer.seek(0)

            logger.info(f"成功导出{self.config.model_class.__name__}数据，共{len(export_data)}条")
            return excel_buffer.getvalue()

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise BusinessError(f"导出数据失败: {str(e)}") from e

    async def import_data(self, file: UploadFile) -> dict[str, Any]:
        """从Excel导入数据

        Args:
            file: 上传的Excel文件

        Returns:
            导入结果统计
        """
        try:
            # 验证文件格式
            if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
                raise ValidationError("只支持Excel文件格式(.xlsx或.xls)")

            # 读取Excel文件
            file_content = await file.read()
            df = pl.read_excel(io.BytesIO(file_content))

            # 验证必要列（只检查必填字段的列）
            required_display_names = {f.display_name for f in self.config.required_fields}
            missing_required_columns = required_display_names - set(df.columns)
            if missing_required_columns:
                raise ValidationError(f"缺少必填的列: {', '.join(missing_required_columns)}")

            # 验证外键必填字段的列
            required_fk_display_names = {f.display_name for f in self.config.foreign_key_fields if f.required}
            missing_required_fk_columns = required_fk_display_names - set(df.columns)
            if missing_required_fk_columns:
                raise ValidationError(f"缺少必填的外键列: {', '.join(missing_required_fk_columns)}")

            # 统计信息
            total_rows = len(df)
            success_count = 0
            error_count = 0
            errors = []

            # 批量处理数据
            for batch_start in range(0, total_rows, self.config.batch_size):
                batch_end = min(batch_start + self.config.batch_size, total_rows)
                batch_df = df[batch_start:batch_end]

                batch_result = await self._import_batch(batch_df, batch_start)
                success_count += batch_result["success"]
                error_count += batch_result["errors_count"]
                errors.extend(batch_result["errors"])

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

    async def _import_batch(self, batch_df: pl.DataFrame, start_idx: int) -> dict[str, Any]:
        """处理数据批次

        Args:
            batch_df: 批次数据框
            start_idx: 起始行索引

        Returns:
            批次处理结果
        """
        success_count = 0
        errors = []

        for row_idx, row in enumerate(batch_df.iter_rows(named=True)):
            try:
                # 构建创建数据
                create_data = {}

                # 处理普通字段
                for field in self.config.import_fields:
                    if not field.is_foreign_key:
                        # 只处理存在于Excel列中的字段
                        if field.display_name in row:
                            value = await self._process_field_value(row, field)
                            if value is not None:
                                create_data[field.name] = value
                        elif field.required:
                            # 必填字段但列不存在，这种情况应该在之前的验证中被捕获
                            raise ValueError(f"必填字段 '{field.display_name}' 在Excel中不存在")

                # 处理外键字段
                for field in self.config.foreign_key_fields:
                    # 只处理存在于Excel列中的外键字段
                    if field.display_name in row:
                        fk_obj = await self._process_foreign_key(row, field)
                        if fk_obj:
                            create_data[field.name] = fk_obj
                    elif field.required:
                        # 必填外键字段但列不存在
                        raise ValueError(f"必填外键字段 '{field.display_name}' 在Excel中不存在")

                # 验证必需字段
                await self._validate_required_fields(create_data)

                # 执行自定义验证
                await self._custom_validate(create_data, row)

                # 创建记录
                await self.config.model_class.create(**create_data)
                success_count += 1

            except Exception as row_error:
                error_msg = f"第{start_idx + row_idx + 2}行: {str(row_error)}"
                errors.append(error_msg)
                logger.warning(error_msg)

        return {"success": success_count, "errors_count": len(errors), "errors": errors}

    async def _get_export_value(self, record: Model, field: FieldConfig) -> str:
        """获取导出值

        Args:
            record: 记录对象
            field: 字段配置

        Returns:
            格式化后的值
        """
        if field.is_foreign_key:
            # 处理外键字段
            related_obj = getattr(record, field.name, None)
            if related_obj:
                return getattr(related_obj, "name", str(related_obj))
            return ""
        else:
            # 处理普通字段
            value = getattr(record, field.name, "")
            if field.transform_func:
                value = field.transform_func(value)
            return str(value) if value is not None else ""

    async def _process_field_value(self, row: dict[str, Any], field: FieldConfig) -> Any:
        """处理字段值

        Args:
            row: 行数据
            field: 字段配置

        Returns:
            处理后的值
        """
        value = row.get(field.display_name)

        if value is None or (isinstance(value, str) and not value.strip()):
            # 如果是必填字段且值为空，抛出错误
            if field.required:
                raise ValueError(f"必填字段 '{field.display_name}' 不能为空")
            return field.default_value

        if field.transform_func:
            try:
                value = field.transform_func(value)
            except Exception as e:
                if field.required:
                    raise ValueError(f"必填字段 '{field.display_name}' 值转换失败: {str(e)}") from e
                else:
                    # 非必填字段转换失败时使用默认值
                    logger.warning(f"字段 '{field.display_name}' 值转换失败，使用默认值: {str(e)}")
                    return field.default_value

        return value

    async def _process_foreign_key(self, row: dict[str, Any], field: FieldConfig) -> Model | None:
        """处理外键字段

        Args:
            row: 行数据
            field: 字段配置

        Returns:
            外键对象
        """
        fk_value = row.get(field.display_name)
        if not fk_value or not str(fk_value).strip():
            # 如果外键字段为空且是必填字段，抛出错误
            if field.required:
                raise ValueError(f"必填外键字段 '{field.display_name}' 不能为空")
            return None

        fk_name = str(fk_value).strip()

        # 检查外键模型是否存在
        if not field.foreign_key_model:
            raise ValueError(f"字段 {field.display_name} 没有配置外键模型")

        # 查找外键对象
        fk_obj = await field.foreign_key_model.filter(name=fk_name).first()

        if not fk_obj and self.config.create_missing_fk:
            # 创建缺失的外键对象
            fk_obj = await self._create_missing_foreign_key(field.foreign_key_model, fk_name, row)
            logger.info(f"自动创建{field.foreign_key_model.__name__}: {fk_name}")
        elif not fk_obj:
            # 外键对象不存在的处理
            if field.required:
                raise ValueError(f"必填外键字段 '{field.display_name}' 的值 '{fk_name}' 不存在")
            else:
                # 非必填字段，记录警告但不阻止导入
                logger.warning(f"外键字段 '{field.display_name}' 的值 '{fk_name}' 不存在，跳过此字段")
                return None

        return fk_obj

    async def _validate_required_fields(self, create_data: dict[str, Any]) -> None:
        """验证必需字段（包括普通字段和外键字段）

        Args:
            create_data: 创建数据

        Raises:
            ValueError: 当必需字段缺失时
        """
        # 检查所有必填字段（包括普通字段和外键字段）
        for field in self.config.fields:
            if field.required and not field.export_only:
                if field.name not in create_data or create_data[field.name] is None:
                    # 对于字符串类型，还要检查是否为空字符串
                    if isinstance(create_data.get(field.name), str) and not create_data[field.name].strip():
                        raise ValueError(f"必需字段 '{field.display_name}' 不能为空")
                    elif field.name not in create_data:
                        raise ValueError(f"必需字段 '{field.display_name}' 不能为空")

    @abstractmethod
    async def _create_missing_foreign_key(self, fk_model: type[Model], fk_name: str, row: dict[str, Any]) -> Model:
        """创建缺失的外键记录（子类实现）

        Args:
            fk_model: 外键模型类
            fk_name: 外键名称
            row: 当前行数据

        Returns:
            创建的外键对象
        """
        pass

    async def _custom_validate(self, create_data: dict[str, Any], row: dict[str, Any]) -> None:
        """自定义验证（子类可重写）

        Args:
            create_data: 创建数据
            row: 原始行数据
        """
        # 默认实现：不进行额外验证
        return

    def get_filename(self, file_type: str = "data") -> str:
        """生成文件名

        Args:
            file_type: 文件类型（template/data）

        Returns:
            文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = self.config.model_class.__name__.lower()
        return f"{model_name}_{file_type}_{timestamp}.xlsx"

    def get_field_info(self) -> dict[str, Any]:
        """获取字段信息

        Returns:
            包含字段信息的字典
        """
        field_info = {
            "model_name": self.config.model_class.__name__,
            "display_name": self.config.sheet_name,
            "fields": [],
            "required_fields": [f.name for f in self.config.required_fields],
            "foreign_key_fields": [f.name for f in self.config.foreign_key_fields],
        }

        # 详细字段信息
        for field in self.config.fields:
            field_detail = {
                "name": field.name,
                "display_name": field.display_name,
                "required": field.required,
                "is_foreign_key": field.is_foreign_key,
                "foreign_model": field.foreign_key_model.__name__ if field.foreign_key_model else None,
            }
            field_info["fields"].append(field_detail)

        return field_info
