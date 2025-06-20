"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: universal_import_export.py
@DateTime: 2025/06/20 00:00:00
@Docs: 通用动态导入导出工具 - 使用高级特性实现完全模块化
"""

import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

import polars as pl
from fastapi import UploadFile
from tortoise import fields
from tortoise.models import Model

from app.core.exceptions import BusinessError, ValidationError
from app.utils.logger import logger

T = TypeVar("T", bound=Model)


class FieldType(Enum):
    """字段类型枚举"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    UUID = "uuid"
    FOREIGN_KEY = "foreign_key"
    ENUM = "enum"


@dataclass
class FieldMetadata:
    """字段元数据类 - 使用数据类简化配置"""

    name: str
    display_name: str
    field_type: FieldType
    required: bool = False
    max_length: int | None = None
    foreign_model: type[Model] | None = None
    enum_class: type[Enum] | None = None
    default_value: Any = None
    validator: Callable[[Any], Any] | None = None
    description: str = ""
    export_only: bool = False
    import_only: bool = False

    def __post_init__(self):
        """后处理 - 自动设置显示名称"""
        if not self.display_name:
            self.display_name = self.name


class ModelIntrospector:
    """模型内省器 - 动态发现模型字段和约束"""

    @classmethod
    async def analyze_model(cls, model_class: type[Model]) -> dict[str, FieldMetadata]:
        """分析模型并生成字段元数据

        Args:
            model_class: Tortoise模型类

        Returns:
            字段名到元数据的映射
        """
        field_metadata = {}

        # 获取模型的所有字段
        for field_name, field_obj in model_class._meta.fields_map.items():
            if field_name in ["id", "created_at", "updated_at", "is_deleted"]:
                continue  # 跳过基础字段

            metadata = await cls._analyze_field(field_name, field_obj, model_class)
            if metadata:
                field_metadata[field_name] = metadata

        return field_metadata

    @classmethod
    async def _analyze_field(
        cls, field_name: str, field_obj: fields.Field, model_class: type[Model]
    ) -> FieldMetadata | None:
        """分析单个字段

        Args:
            field_name: 字段名
            field_obj: 字段对象
            model_class: 模型类

        Returns:
            字段元数据
        """
        # 基础信息
        display_name = cls._generate_display_name(field_name)
        description = getattr(field_obj, "description", "")
        required = not field_obj.null and not hasattr(field_obj, "default")

        # 根据字段类型生成元数据
        if isinstance(field_obj, fields.CharField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.STRING,
                required=required,
                max_length=field_obj.max_length,
                description=description,
            )

        elif isinstance(field_obj, fields.TextField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.STRING,
                required=required,
                description=description,
            )

        elif isinstance(field_obj, fields.IntField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.INTEGER,
                required=required,
                description=description,
            )

        elif isinstance(field_obj, fields.FloatField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.FLOAT,
                required=required,
                description=description,
            )

        elif isinstance(field_obj, fields.BooleanField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.BOOLEAN,
                required=required,
                default_value=field_obj.default if hasattr(field_obj, "default") else False,
                description=description,
            )

        elif isinstance(field_obj, fields.DateField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.DATE,
                required=required,
                description=description,
            )

        elif isinstance(field_obj, fields.DatetimeField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.DATETIME,
                required=required,
                description=description,
            )

        elif isinstance(field_obj, fields.UUIDField):
            return FieldMetadata(
                name=field_name,
                display_name=display_name,
                field_type=FieldType.UUID,
                required=required,
                description=description,
            )
        elif hasattr(field_obj, "model_name") and getattr(field_obj, "model_name", None):
            # 外键字段 - 使用动态属性检查代替isinstance
            try:
                model_name = getattr(field_obj, "model_name")  # noqa: B009
                foreign_model = cls._resolve_foreign_model(model_name)
                return FieldMetadata(
                    name=field_name,
                    display_name=display_name,
                    field_type=FieldType.FOREIGN_KEY,
                    required=required,
                    foreign_model=foreign_model,
                    description=description,
                )
            except Exception:
                logger.warning(f"无法解析外键字段 {field_name} 的模型")

        elif hasattr(field_obj, "enum_type") and getattr(field_obj, "enum_type", None):
            # 枚举字段 - 使用动态属性检查代替isinstance
            try:
                enum_class = getattr(field_obj, "enum_type")  # noqa: B009
                return FieldMetadata(
                    name=field_name,
                    display_name=display_name,
                    field_type=FieldType.ENUM,
                    required=required,
                    enum_class=enum_class,
                    description=description,
                )
            except Exception:
                logger.warning(f"无法解析枚举字段 {field_name} 的枚举类型")

        return None

    @classmethod
    def _generate_display_name(cls, field_name: str) -> str:
        """生成字段显示名称"""
        # 简单的映射规则，可以扩展为配置文件
        name_mapping = {
            "name": "名称",
            "description": "描述",
            "snmp_community_string": "SNMP社区字符串",
            "default_cli_username": "默认CLI用户名",
            "platform_type": "平台类型",
            "brand": "品牌",
            "device_type": "设备类型",
            "management_ip": "管理IP",
            "status": "状态",
            "region": "区域",
            "device_group": "设备分组",
            "device_model": "设备型号",
        }
        return name_mapping.get(field_name, field_name)

    @classmethod
    def _resolve_foreign_model(cls, model_name: str) -> type[Model] | None:
        """解析外键模型类"""
        # 这里需要根据实际的模型注册方式来实现
        # 可以从Tortoise的模型注册表中获取
        try:
            from app.models.network_models import Brand, DeviceGroup, DeviceModel, Region

            model_mapping = {
                "models.Region": Region,
                "models.Brand": Brand,
                "models.DeviceModel": DeviceModel,
                "models.DeviceGroup": DeviceGroup,
            }
            return model_mapping.get(model_name)
        except ImportError:
            return None


class FieldProcessor:
    """字段处理器 - 处理不同类型字段的转换和验证"""

    @classmethod
    async def process_import_value(cls, value: Any, metadata: FieldMetadata) -> Any:
        """处理导入值

        Args:
            value: 原始值
            metadata: 字段元数据

        Returns:
            处理后的值
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if metadata.required:
                raise ValueError(f"必填字段 '{metadata.display_name}' 不能为空")
            return metadata.default_value

        try:
            # 根据字段类型处理值
            if metadata.field_type == FieldType.STRING:
                return cls._process_string(value, metadata)
            elif metadata.field_type == FieldType.INTEGER:
                return cls._process_integer(value, metadata)
            elif metadata.field_type == FieldType.FLOAT:
                return cls._process_float(value, metadata)
            elif metadata.field_type == FieldType.BOOLEAN:
                return cls._process_boolean(value, metadata)
            elif metadata.field_type == FieldType.ENUM:
                return cls._process_enum(value, metadata)
            elif metadata.field_type == FieldType.FOREIGN_KEY:
                return await cls._process_foreign_key(value, metadata)
            else:
                return str(value).strip() if value else metadata.default_value

        except Exception as e:
            if metadata.required:
                raise ValueError(f"字段 '{metadata.display_name}' 值转换失败: {str(e)}") from e
            else:
                logger.warning(f"字段 '{metadata.display_name}' 值转换失败，使用默认值: {str(e)}")
                return metadata.default_value

    @classmethod
    def _process_string(cls, value: Any, metadata: FieldMetadata) -> str:
        """处理字符串类型"""
        str_value = str(value).strip()
        if metadata.max_length and len(str_value) > metadata.max_length:
            raise ValueError(f"字符串长度超过限制 {metadata.max_length}")
        return str_value

    @classmethod
    def _process_integer(cls, value: Any, metadata: FieldMetadata) -> int:
        """处理整数类型"""
        if isinstance(value, int | float):
            return int(value)
        return int(str(value).strip())

    @classmethod
    def _process_float(cls, value: Any, metadata: FieldMetadata) -> float:
        """处理浮点数类型"""
        if isinstance(value, int | float):
            return float(value)
        return float(str(value).strip())

    @classmethod
    def _process_boolean(cls, value: Any, metadata: FieldMetadata) -> bool:
        """处理布尔类型"""
        if isinstance(value, bool):
            return value
        str_value = str(value).strip().lower()
        return str_value in ["true", "1", "yes", "on", "是", "真"]

    @classmethod
    def _process_enum(cls, value: Any, metadata: FieldMetadata) -> Enum:
        """处理枚举类型"""
        if not metadata.enum_class:
            raise ValueError("枚举类型未配置")

        str_value = str(value).strip()
        # 尝试通过值或名称匹配枚举
        for enum_item in metadata.enum_class:
            if enum_item.value == str_value or enum_item.name == str_value:
                return enum_item

        raise ValueError(f"无效的枚举值: {str_value}")

    @classmethod
    async def _process_foreign_key(cls, value: Any, metadata: FieldMetadata) -> Model | None:
        """处理外键类型"""
        if not metadata.foreign_model:
            raise ValueError("外键模型未配置")

        fk_name = str(value).strip()
        # 查找外键对象
        fk_obj = await metadata.foreign_model.filter(name=fk_name).first()

        if not fk_obj:
            if metadata.required:
                raise ValueError(f"外键 '{metadata.display_name}' 的值 '{fk_name}' 不存在")
            else:
                logger.warning(f"外键 '{metadata.display_name}' 的值 '{fk_name}' 不存在，跳过")
                return None

        return fk_obj

    @classmethod
    async def process_export_value(cls, obj: Model, metadata: FieldMetadata) -> str:
        """处理导出值

        Args:
            obj: 模型对象
            metadata: 字段元数据

        Returns:
            格式化的字符串值
        """
        value = getattr(obj, metadata.name, None)

        if value is None:
            return ""

        if metadata.field_type == FieldType.FOREIGN_KEY:
            # 外键对象显示名称
            return getattr(value, "name", str(value))
        elif metadata.field_type == FieldType.ENUM:
            # 枚举显示值
            return value.value if hasattr(value, "value") else str(value)
        elif metadata.field_type == FieldType.BOOLEAN:
            # 布尔值显示
            return "是" if value else "否"
        else:
            return str(value)


class UniversalImportExport[T: Model]:
    """通用导入导出工具 - 完全动态化"""

    def __init__(self, model_class: type[T]):
        """初始化

        Args:
            model_class: 模型类
        """
        self.model_class = model_class
        self._field_metadata: dict[str, FieldMetadata] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """异步初始化 - 分析模型结构"""
        if self._initialized:
            return

        self._field_metadata = await ModelIntrospector.analyze_model(self.model_class)
        self._initialized = True
        logger.info(f"已初始化 {self.model_class.__name__} 的导入导出工具")

    async def export_template(self) -> bytes:
        """导出Excel模板"""
        await self.initialize()

        try:
            # 获取导出字段
            export_fields = [meta for meta in self._field_metadata.values() if not meta.import_only]

            # 创建空的数据框
            columns = {meta.display_name: [] for meta in export_fields}
            df = pl.DataFrame(columns)

            # 转换为Excel
            excel_buffer = io.BytesIO()
            df.write_excel(excel_buffer, worksheet=f"{self.model_class.__name__}模板")
            excel_buffer.seek(0)

            logger.info(f"成功生成 {self.model_class.__name__} 模板")
            return excel_buffer.getvalue()

        except Exception as e:
            logger.error(f"生成模板失败: {e}")
            raise BusinessError(f"生成模板失败: {str(e)}") from e

    async def export_data(self, filters: dict[str, Any] | None = None) -> bytes:
        """导出数据到Excel"""
        await self.initialize()

        try:
            # 构建查询
            queryset = self.model_class.all()

            if filters:
                queryset = queryset.filter(**filters)

            # 预加载外键关系
            fk_fields = [
                meta.name
                for meta in self._field_metadata.values()
                if meta.field_type == FieldType.FOREIGN_KEY and not meta.import_only
            ]
            if fk_fields:
                queryset = queryset.prefetch_related(*fk_fields)

            records = await queryset

            # 获取导出字段
            export_fields = [meta for meta in self._field_metadata.values() if not meta.import_only]

            # 转换数据
            export_data = []
            for record in records:
                row_data = {}
                for meta in export_fields:
                    value = await FieldProcessor.process_export_value(record, meta)
                    row_data[meta.display_name] = value
                export_data.append(row_data)

            # 创建数据框
            if export_data:
                df = pl.DataFrame(export_data)
            else:
                columns = {meta.display_name: [] for meta in export_fields}
                df = pl.DataFrame(columns)

            # 转换为Excel
            excel_buffer = io.BytesIO()
            df.write_excel(excel_buffer, worksheet=f"{self.model_class.__name__}数据")
            excel_buffer.seek(0)

            logger.info(f"成功导出 {self.model_class.__name__} 数据，共 {len(export_data)} 条")
            return excel_buffer.getvalue()

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise BusinessError(f"导出数据失败: {str(e)}") from e

    async def import_data(self, file: UploadFile, batch_size: int = 100) -> dict[str, Any]:
        """从Excel导入数据"""
        await self.initialize()

        try:
            # 验证文件格式
            if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
                raise ValidationError("只支持Excel文件格式(.xlsx或.xls)")

            # 读取Excel文件
            file_content = await file.read()
            df = pl.read_excel(io.BytesIO(file_content))

            # 验证必要列
            required_fields = [meta for meta in self._field_metadata.values() if meta.required and not meta.export_only]
            missing_columns = []
            for meta in required_fields:
                if meta.display_name not in df.columns:
                    missing_columns.append(meta.display_name)

            if missing_columns:
                raise ValidationError(f"缺少必填的列: {', '.join(missing_columns)}")

            # 统计信息
            total_rows = len(df)
            success_count = 0
            error_count = 0
            errors = []

            # 批量处理数据
            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
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

            logger.info(f"导入完成: 总计 {total_rows} 行，成功 {success_count} 行，失败 {error_count} 行")
            return result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"导入数据失败: {e}")
            raise BusinessError(f"导入数据失败: {str(e)}") from e

    async def _import_batch(self, batch_df: pl.DataFrame, start_idx: int) -> dict[str, Any]:
        """处理数据批次"""
        success_count = 0
        errors = []

        for row_idx, row in enumerate(batch_df.iter_rows(named=True)):
            try:
                # 构建创建数据
                create_data = {}

                # 处理所有字段
                for meta in self._field_metadata.values():
                    if meta.export_only:
                        continue

                    # 只处理存在于Excel列中的字段
                    if meta.display_name in row:
                        value = await FieldProcessor.process_import_value(row[meta.display_name], meta)
                        if value is not None:
                            create_data[meta.name] = value

                # 执行自定义验证
                await self._custom_validate(create_data, row)

                # 创建记录
                await self.model_class.create(**create_data)
                success_count += 1

            except Exception as row_error:
                error_msg = f"第 {start_idx + row_idx + 2} 行: {str(row_error)}"
                errors.append(error_msg)
                logger.warning(error_msg)

        return {"success": success_count, "errors_count": len(errors), "errors": errors}

    async def _custom_validate(self, create_data: dict[str, Any], row: dict[str, Any]) -> None:
        """自定义验证 - 子类可重写"""
        # 默认不进行额外验证
        pass

    def get_field_info(self) -> dict[str, Any]:
        """获取字段信息"""
        if not self._initialized:
            raise RuntimeError("请先调用 initialize() 方法")

        return {
            "model_name": self.model_class.__name__,
            "fields": [
                {
                    "name": meta.name,
                    "display_name": meta.display_name,
                    "field_type": meta.field_type.value,
                    "required": meta.required,
                    "description": meta.description,
                    "foreign_model": meta.foreign_model.__name__ if meta.foreign_model else None,
                    "enum_values": [e.value for e in meta.enum_class] if meta.enum_class else None,
                }
                for meta in self._field_metadata.values()
                if not meta.export_only
            ],
        }

    def get_filename(self, file_type: str = "data") -> str:
        """生成文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = self.model_class.__name__.lower()
        return f"{model_name}_{file_type}_{timestamp}.xlsx"


# 工厂函数 - 简化使用
async def create_import_export_tool[T: Model](model_class: type[T]) -> UniversalImportExport[T]:
    """创建导入导出工具实例

    Args:
        model_class: 模型类

    Returns:
        已初始化的导入导出工具
    """
    tool = UniversalImportExport(model_class)
    await tool.initialize()
    return tool


# 全局工具缓存 - 避免重复初始化
_tool_cache: dict[type[Model], UniversalImportExport] = {}


async def get_import_export_tool[T: Model](model_class: type[T]) -> UniversalImportExport[T]:
    """获取缓存的导入导出工具

    Args:
        model_class: 模型类

    Returns:
        导入导出工具实例
    """
    if model_class not in _tool_cache:
        _tool_cache[model_class] = await create_import_export_tool(model_class)
    return _tool_cache[model_class]
