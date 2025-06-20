"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025-06-17
@Docs: 数据访问层基类，提供通用的CRUD操作
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar
from uuid import UUID

from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.models import Model
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction

from app.utils.logger import logger

ModelType = TypeVar("ModelType", bound=Model)


def with_transaction(func: Callable) -> Callable:
    """事务装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            async with in_transaction():
                return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} 中的事务失败： {e}")
            raise

    return wrapper


class BaseDAO[ModelType: Model]:
    """数据访问层基类

    提供通用的增删改查、计数、是否存在等方法
    所有具体的DAO类都应该继承此基类
    """

    def __init__(self, model: type[ModelType]):
        """初始化DAO

        Args:
            model: 对应的Tortoise ORM模型类
        """
        self.model = model

    async def create(self, **kwargs) -> ModelType:
        """创建单个记录

        Args:
            **kwargs: 创建记录的字段值

        Returns:
            创建的模型实例

        Raises:
            IntegrityError: 违反数据完整性约束
        """
        try:
            return await self.model.create(**kwargs)
        except IntegrityError as e:
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating {self.model.__name__}: {e}")
            raise

    @with_transaction
    async def bulk_create(
        self, objects: list[dict[str, Any]], batch_size: int = 1000, ignore_conflicts: bool = False
    ) -> list[ModelType]:
        """批量创建记录

        Args:
            objects: 要创建的记录列表
            batch_size: 批处理大小
            ignore_conflicts: 是否忽略冲突

        Returns:
            创建的模型实例列表

        Raises:
            IntegrityError: 违反数据完整性约束
        """
        if not objects:
            return []

        try:
            # 分批处理大量数据
            all_instances = []
            for i in range(0, len(objects), batch_size):
                batch = objects[i : i + batch_size]
                instances = [self.model(**obj) for obj in batch]

                # 执行批量创建
                await self.model.bulk_create(instances, ignore_conflicts=ignore_conflicts)

                # 如果需要返回带ID的实例，重新查询
                if not ignore_conflicts:
                    # 获取刚创建的实例（通过某个唯一字段查询）
                    # 这里简化处理，直接返回创建的实例
                    all_instances.extend(instances)
                else:
                    all_instances.extend(instances)

            logger.info(f"Bulk created {len(all_instances)} {self.model.__name__} records")
            return all_instances

        except IntegrityError as e:
            logger.error(f"Failed to bulk create {self.model.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in bulk create {self.model.__name__}: {e}")
            raise

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """根据ID获取记录

        Args:
            id: 记录ID

        Returns:
            模型实例或None
        """
        try:
            return await self.model.get(id=id)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            raise

    async def get_or_404(self, id: UUID) -> ModelType:
        """根据ID获取记录，不存在则抛出异常

        Args:
            id: 记录ID

        Returns:
            模型实例

        Raises:
            DoesNotExist: 记录不存在
        """
        try:
            return await self.model.get(id=id)
        except DoesNotExist:
            logger.warning(f"{self.model.__name__} with id {id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            raise

    async def get_by_field(self, field_name: str, value: Any) -> ModelType | None:
        """根据指定字段获取记录

        Args:
            field_name: 字段名
            value: 字段值

        Returns:
            模型实例或None
        """
        try:
            return await self.model.get(**{field_name: value})
        except DoesNotExist:
            return None

    async def get_by_filters(self, **filters) -> ModelType | None:
        """根据多个筛选条件获取单个记录
        Args:
            **filters: 筛选条件
        Returns:
            模型实例或None
        """
        try:
            return await self.model.get(**filters)
        except DoesNotExist:
            return None

    async def get_or_create(self, defaults: dict[str, Any] | None = None, **kwargs: Any) -> tuple[ModelType, bool]:
        """获取或创建记录
        如果记录存在，则返回该记录和 False。
        如果记录不存在，则创建新记录并返回它和 True。
        Args:
            defaults: 创建新记录时使用的默认字段值。
            **kwargs: 用于查询记录的字段。
        Returns:
            一个元组，包含模型实例和表示是否已创建的布尔值。
        """
        return await self.model.get_or_create(defaults=defaults, **kwargs)

    async def list_all(self, prefetch_related: list[str] | None = None) -> list[ModelType]:
        """获取所有记录

        Args:
            prefetch_related: 预加载的关联字段列表

        Returns:
            模型实例列表
        """
        queryset = self.model.all()
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return await queryset

    async def list_by_filters(
        self,
        filters: dict[str, Any] | None = None,
        prefetch_related: list[str] | None = None,
        order_by: list[str] | None = None,
    ) -> list[ModelType]:
        """根据过滤条件获取记录列表

        Args:
            filters: 过滤条件字典
            prefetch_related: 预加载的关联字段列表
            order_by: 排序字段列表

        Returns:
            模型实例列表
        """
        queryset = self._apply_filters(self.model.all(), filters)

        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        if order_by:
            queryset = queryset.order_by(*order_by)

        return await queryset

    def _apply_filters(self, queryset: QuerySet[ModelType], filters: dict[str, Any] | None) -> QuerySet[ModelType]:
        """应用过滤条件，支持模糊查询"""
        if not filters:
            return queryset

        processed_filters = {}
        for key, value in filters.items():
            if value is None or value == "":
                continue
            # 对name字段进行模糊查询
            if key == "name" and isinstance(value, str):
                processed_filters[f"{key}__icontains"] = value
            else:
                processed_filters[key] = value

        if processed_filters:
            queryset = queryset.filter(**processed_filters)
        return queryset

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: dict[str, Any] | None = None,
        prefetch_related: list[str] | None = None,
        order_by: list[str] | None = None,
    ) -> dict[str, Any]:
        """分页查询

        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            filters: 过滤条件字典
            prefetch_related: 预加载的关联字段列表
            order_by: 排序字段列表

        Returns:
            包含分页信息的字典
        """
        queryset = self._apply_filters(self.model.all(), filters)

        if order_by:
            queryset = queryset.order_by(*order_by)

        # 计算总数
        total = await queryset.count()

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取当前页数据
        page_queryset = queryset.offset(offset).limit(page_size)
        if prefetch_related:
            page_queryset = page_queryset.prefetch_related(*prefetch_related)

        items = await page_queryset  # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            },
        }

    async def update_by_id(self, id: UUID, **kwargs) -> ModelType | None:
        """根据ID更新记录

        Args:
            id: 记录ID
            **kwargs: 更新的字段值

        Returns:
            更新后的模型实例或None

        Raises:
            IntegrityError: 违反数据完整性约束
        """
        try:
            # 直接更新，避免先查询再更新
            updated_count = await self.model.filter(id=id).update(**kwargs)
            if updated_count > 0:
                # 重新获取更新后的记录
                return await self.get_by_id(id)
            return None
        except IntegrityError as e:
            logger.error(f"Failed to update {self.model.__name__} id {id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating {self.model.__name__} id {id}: {e}")
            raise

    @with_transaction
    async def bulk_update(self, updates: list[dict[str, Any]], key_field: str = "id") -> int:
        """批量更新记录

        Args:
            updates: 更新数据列表，每个字典必须包含key_field
            key_field: 用于匹配记录的键字段名

        Returns:
            更新的记录数量

        Raises:
            IntegrityError: 违反数据完整性约束
        """
        if not updates:
            return 0

        try:
            total_updated = 0
            for update_data in updates:
                if key_field not in update_data:
                    continue

                key_value = update_data.pop(key_field)
                updated_count = await self.model.filter(**{key_field: key_value}).update(**update_data)
                total_updated += updated_count

            logger.info(f"Bulk updated {total_updated} {self.model.__name__} records")
            return total_updated

        except IntegrityError as e:
            logger.error(f"Failed to bulk update {self.model.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in bulk update {self.model.__name__}: {e}")
            raise

    async def update_by_filters(self, filters: dict[str, Any], **kwargs) -> int:
        """根据过滤条件批量更新记录

        Args:
            filters: 过滤条件字典
            **kwargs: 更新的字段值

        Returns:
            更新的记录数量
        """
        return await self.model.filter(**filters).update(**kwargs)

    async def delete_by_id(self, id: UUID) -> bool:
        """根据ID删除记录

        Args:
            id: 记录ID

        Returns:
            是否删除成功
        """
        instance = await self.get_by_id(id)
        if instance:
            await instance.delete()
            return True
        return False

    async def soft_delete_by_id(self, id: UUID) -> bool:
        """根据ID软删除记录（标记为已删除）

        Args:
            id: 记录ID

        Returns:
            是否删除成功
        """
        # 检查模型是否有is_deleted字段
        if "is_deleted" not in self.model._meta.fields_map:
            logger.warning(f"{self.model.__name__} does not support soft delete (no is_deleted field)")
            return False

        try:
            updated_count = await self.model.filter(id=id).update(is_deleted=True)
            success = updated_count > 0
            if success:
                logger.info(f"Soft deleted {self.model.__name__} id {id}")
            return success
        except Exception as e:
            logger.error(f"Error soft deleting {self.model.__name__} id {id}: {e}")
            raise

    async def delete_by_filters(self, **filters) -> int:
        """根据过滤条件批量删除记录

        Args:
            **filters: 过滤条件

        Returns:
            删除的记录数量
        """
        return await self.model.filter(**filters).delete()

    async def soft_delete_by_filters(self, **filters) -> int:
        """根据过滤条件批量软删除记录

        Args:
            **filters: 过滤条件

        Returns:
            删除的记录数量
        """
        # 检查模型是否有is_deleted字段
        if not hasattr(self.model, "is_deleted"):
            logger.warning(f"{self.model.__name__} does not support soft delete (no is_deleted field)")
            return 0

        try:
            updated_count = await self.model.filter(**filters).update(is_deleted=True)
            if updated_count > 0:
                logger.info(f"Soft deleted {updated_count} {self.model.__name__} records")
            return updated_count
        except Exception as e:
            logger.error(f"Error soft deleting {self.model.__name__} records: {e}")
            raise

    async def count(self, **filters) -> int:
        """统计记录数量

        Args:
            **filters: 过滤条件

        Returns:
            记录数量
        """
        return await self.model.filter(**filters).count()

    async def exists(self, **filters) -> bool:
        """检查记录是否存在

        Args:
            **filters: 过滤条件

        Returns:
            是否存在
        """
        return await self.model.filter(**filters).exists()

    async def exists_by_id(self, id: UUID) -> bool:
        """检查指定ID的记录是否存在

        Args:
            id: 记录ID

        Returns:
            是否存在
        """
        return await self.exists(id=id)

    async def get_active_records(self, **filters) -> list[ModelType]:
        """获取活跃记录（未删除且启用的记录）

        Args:
            **filters: 额外的过滤条件

        Returns:
            模型实例列表
        """
        base_filters = {}

        # 检查并添加is_deleted过滤条件
        if hasattr(self.model, "is_deleted"):
            base_filters["is_deleted"] = False

        # 检查并添加is_active过滤条件
        if hasattr(self.model, "is_active"):
            base_filters["is_active"] = True

        base_filters.update(filters)
        return await self.list_by_filters(base_filters)

    async def get_count_by_status(self, status_field: str) -> dict[str, int]:
        """按状态字段统计记录数量

        Args:
            status_field: 状态字段名

        Returns:
            状态与数量的映射字典
        """
        try:
            from tortoise.functions import Count

            result = (
                await self.model.all().group_by(status_field).annotate(count=Count("id")).values(status_field, "count")
            )
            return {item[status_field]: item["count"] for item in result}
        except Exception as e:
            logger.error(f"Error getting count by status for {self.model.__name__}: {e}")
            raise

    def get_queryset(self) -> QuerySet[ModelType]:
        """获取基础查询集，用于自定义复杂查询

        Returns:
            QuerySet对象
        """
        return self.model.all()

    def filter(self, **filters) -> QuerySet[ModelType]:
        """获取过滤后的查询集

        Args:
            **filters: 过滤条件

        Returns:
            QuerySet对象
        """
        return self.model.filter(**filters)

    async def upsert(self, defaults: dict[str, Any] | None = None, **kwargs: Any) -> tuple[ModelType, bool]:
        """更新或创建记录的别名方法

        Args:
            defaults: 创建新记录时使用的默认字段值
            **kwargs: 用于查询记录的字段

        Returns:
            一个元组，包含模型实例和表示是否已创建的布尔值
        """
        return await self.get_or_create(defaults=defaults, **kwargs)

    async def count_active(self, **filters) -> int:
        """统计活跃记录数量

        Args:
            **filters: 额外的过滤条件

        Returns:
            活跃记录数量
        """
        base_filters = {}

        if hasattr(self.model, "is_deleted"):
            base_filters["is_deleted"] = False

        if hasattr(self.model, "is_active"):
            base_filters["is_active"] = True

        base_filters.update(filters)
        return await self.count(**base_filters)

    async def exists_active(self, **filters) -> bool:
        """检查活跃记录是否存在

        Args:
            **filters: 过滤条件

        Returns:
            是否存在活跃记录
        """
        base_filters = {}

        if hasattr(self.model, "is_deleted"):
            base_filters["is_deleted"] = False

        if hasattr(self.model, "is_active"):
            base_filters["is_active"] = True

        base_filters.update(filters)
        return await self.exists(**base_filters)
