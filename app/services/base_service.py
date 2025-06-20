"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base_service.py
@DateTime: 2025/06/20 00:00:00
@Docs: 服务层基类，提供通用的CRUD业务逻辑方法
"""

from typing import Any, TypeVar
from uuid import UUID

from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.models import Model

from app.core.exceptions import (
    BusinessError,
    DuplicateError,
    NotFoundError,
    ValidationError,
)
from app.repositories.base_dao import BaseDAO
from app.schemas.base import (
    BaseCreateSchema,
    BaseQueryParams,
    BaseResponseSchema,
    BaseUpdateSchema,
    BatchOperationResponse,
    BulkCreateRequest,
    BulkDeleteRequest,
    BulkUpdateRequest,
    PaginationResponse,
    SuccessResponse,
)
from app.utils.logger import logger
from app.utils.operation_logger import operation_log

# 类型变量定义
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseCreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseUpdateSchema)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseResponseSchema)
QueryParamsType = TypeVar("QueryParamsType", bound=BaseQueryParams)


class BaseService[
    ModelType: Model,
    CreateSchemaType: BaseCreateSchema,
    UpdateSchemaType: BaseUpdateSchema,
    ResponseSchemaType: BaseResponseSchema,
    QueryParamsType: BaseQueryParams,
]:
    """服务层基类

    提供通用的CRUD业务逻辑方法，包括：
    - 创建、查询、更新、删除操作
    - 分页查询
    - 批量操作
    - 数据验证
    - 业务规则检查
    - 操作日志记录
    """

    def __init__(
        self,
        dao: BaseDAO[ModelType],
        response_schema: type[ResponseSchemaType],
        entity_name: str = "实体",
    ):
        """初始化服务

        Args:
            dao: 数据访问对象
            response_schema: 响应模式类
            entity_name: 实体名称，用于日志和错误消息
        """
        self.dao = dao
        self.response_schema = response_schema
        self.entity_name = entity_name

    @operation_log("创建记录", auto_save=True, include_args=True, include_result=True)
    async def create(self, data: CreateSchemaType) -> ResponseSchemaType:
        """创建单个记录

        Args:
            data: 创建数据

        Returns:
            创建的记录响应

        Raises:
            ValidationError: 数据验证失败
            DuplicateError: 数据重复
            BusinessError: 业务逻辑错误
        """
        try:
            # 验证业务规则
            await self._validate_create_data(data)

            # 转换数据
            create_data = self._prepare_create_data(data)

            # 创建记录
            instance = await self.dao.create(**create_data)
            response = self.response_schema.model_validate(instance)

            logger.info(f"成功创建{self.entity_name}: {getattr(instance, 'id', 'unknown')}")
            return response

        except IntegrityError as e:
            logger.error(f"创建{self.entity_name}失败，数据完整性错误: {e}")
            raise DuplicateError(f"{self.entity_name}已存在或违反唯一性约束") from e
        except Exception as e:
            logger.error(f"创建{self.entity_name}失败: {e}")
            raise BusinessError(f"创建{self.entity_name}失败: {str(e)}") from e

    @operation_log("获取记录详情", auto_save=False)
    async def get_by_id(self, id: UUID) -> ResponseSchemaType:
        """根据ID获取记录

        Args:
            id: 记录ID

        Returns:
            记录响应

        Raises:
            NotFoundError: 记录不存在
        """
        try:
            instance = await self.dao.get_by_id(id)
            if not instance:
                raise NotFoundError(f"{self.entity_name}不存在")

            # 检查软删除
            if hasattr(instance, "is_deleted") and getattr(instance, "is_deleted", False):
                raise NotFoundError(f"{self.entity_name}已被删除")

            response = self.response_schema.model_validate(instance)
            return response

        except DoesNotExist:
            raise NotFoundError(f"{self.entity_name}不存在") from None

    @operation_log("分页查询记录", auto_save=False)
    async def list_with_pagination(self, query_params: QueryParamsType) -> PaginationResponse[ResponseSchemaType]:
        """分页查询记录

        Args:
            query_params: 查询参数

        Returns:
            分页响应
        """
        try:
            # 构建过滤条件
            filters = self._build_filters(query_params)

            # 构建排序条件
            order_by = self._build_order_by(query_params)

            # 获取预加载字段
            prefetch_related = self._get_prefetch_related()

            # 执行分页查询
            result = await self.dao.paginate(
                page=query_params.page,
                page_size=query_params.page_size,
                filters=filters,
                prefetch_related=prefetch_related,
                order_by=order_by,
            )

            # 转换响应数据
            items = [self.response_schema.model_validate(item) for item in result["items"]]

            return PaginationResponse[ResponseSchemaType](data=items, pagination=result["pagination"])

        except Exception as e:
            logger.error(f"查询{self.entity_name}列表失败: {e}")
            raise BusinessError(f"查询{self.entity_name}列表失败: {str(e)}") from e

    @operation_log("获取所有记录", auto_save=False)
    async def list_all(self, filters: dict[str, Any] | None = None) -> list[ResponseSchemaType]:
        """获取所有记录

        Args:
            filters: 过滤条件

        Returns:
            记录列表
        """
        try:
            prefetch_related = self._get_prefetch_related()
            instances = await self.dao.list_by_filters(filters=filters, prefetch_related=prefetch_related)

            return [self.response_schema.model_validate(instance) for instance in instances]

        except Exception as e:
            logger.error(f"获取{self.entity_name}列表失败: {e}")
            raise BusinessError(f"获取{self.entity_name}列表失败: {str(e)}") from e

    @operation_log("更新记录", auto_save=True, include_args=True, include_result=True)
    async def update(self, id: UUID, data: UpdateSchemaType) -> ResponseSchemaType:
        """更新记录

        Args:
            id: 记录ID
            data: 更新数据

        Returns:
            更新后的记录响应

        Raises:
            NotFoundError: 记录不存在
            ValidationError: 数据验证失败
            DuplicateError: 数据重复
            BusinessError: 业务逻辑错误
        """
        try:
            # 检查记录是否存在
            existing = await self.dao.get_by_id(id)
            if not existing:
                raise NotFoundError(f"{self.entity_name}不存在")

            # 验证业务规则
            await self._validate_update_data(id, data, existing)

            # 准备更新数据
            update_data = self._prepare_update_data(data)

            # 执行更新
            updated_instance = await self.dao.update_by_id(id, **update_data)
            if not updated_instance:
                raise BusinessError(f"更新{self.entity_name}失败")

            response = self.response_schema.model_validate(updated_instance)

            logger.info(f"成功更新{self.entity_name}: {id}")
            return response

        except IntegrityError as e:
            logger.error(f"更新{self.entity_name}失败，数据完整性错误: {e}")
            raise DuplicateError(f"{self.entity_name}更新失败，违反唯一性约束") from e
        except (NotFoundError, ValidationError, DuplicateError):
            raise
        except Exception as e:
            logger.error(f"更新{self.entity_name}失败: {e}")
            raise BusinessError(f"更新{self.entity_name}失败: {str(e)}") from e

    @operation_log("删除记录", auto_save=True, include_args=True)
    async def delete(self, id: UUID, soft_delete: bool = True) -> SuccessResponse[None]:
        """删除记录

        Args:
            id: 记录ID
            soft_delete: 是否软删除

        Returns:
            删除结果响应

        Raises:
            NotFoundError: 记录不存在
            BusinessError: 业务逻辑错误
        """
        try:
            # 检查记录是否存在
            existing = await self.dao.get_by_id(id)
            if not existing:
                raise NotFoundError(f"{self.entity_name}不存在")

            # 验证删除规则
            await self._validate_delete(id, existing)

            # 执行删除
            if soft_delete and hasattr(existing, "is_deleted"):
                success = await self.dao.soft_delete_by_id(id)
                delete_type = "软删除"
            else:
                success = await self.dao.delete_by_id(id)
                delete_type = "物理删除"

            if not success:
                raise BusinessError(f"{delete_type}{self.entity_name}失败")

            logger.info(f"成功{delete_type}{self.entity_name}: {id}")
            return SuccessResponse(message=f"{delete_type}{self.entity_name}成功")

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"删除{self.entity_name}失败: {e}")
            raise BusinessError(f"删除{self.entity_name}失败: {str(e)}") from e

    @operation_log("批量创建记录", auto_save=True, include_args=True, include_result=True)
    async def bulk_create(self, request: BulkCreateRequest[CreateSchemaType]) -> BatchOperationResponse:
        """批量创建记录

        Args:
            request: 批量创建请求

        Returns:
            批量操作响应
        """
        try:
            create_data_list = []
            failed_items = []

            # 验证和准备数据
            for i, item in enumerate(request.items):
                try:
                    await self._validate_create_data(item)
                    create_data = self._prepare_create_data(item)
                    create_data_list.append(create_data)
                except Exception as e:
                    failed_items.append({"index": i, "data": item.model_dump(), "error": str(e)})

            # 执行批量创建
            if create_data_list:
                instances = await self.dao.bulk_create(create_data_list)
                success_count = len(instances)
            else:
                success_count = 0

            total = len(request.items)
            failed_count = len(failed_items)

            logger.info(f"批量创建{self.entity_name}完成，成功: {success_count}，失败: {failed_count}")

            return BatchOperationResponse(
                success=failed_count == 0,
                message=f"批量创建{self.entity_name}完成",
                total=total,
                success_count=success_count,
                failed_count=failed_count,
                failed_items=failed_items if failed_items else None,
            )

        except Exception as e:
            logger.error(f"批量创建{self.entity_name}失败: {e}")
            raise BusinessError(f"批量创建{self.entity_name}失败: {str(e)}") from e

    @operation_log("批量更新记录", auto_save=True, include_args=True, include_result=True)
    async def bulk_update(self, request: BulkUpdateRequest) -> BatchOperationResponse:
        """批量更新记录

        Args:
            request: 批量更新请求

        Returns:
            批量操作响应
        """
        try:
            # 验证所有ID是否存在
            existing_ids = []
            failed_items = []

            for i, id in enumerate(request.ids):
                existing = await self.dao.get_by_id(id)
                if not existing:
                    failed_items.append({"index": i, "id": str(id), "error": f"{self.entity_name}不存在"})
                else:
                    existing_ids.append({"id": id})

            # 执行批量更新
            success_count = 0
            if existing_ids:
                for update_item in existing_ids:
                    update_item.update(request.update_data)

                success_count = await self.dao.bulk_update(existing_ids)

            total = len(request.ids)
            failed_count = len(failed_items)

            logger.info(f"批量更新{self.entity_name}完成，成功: {success_count}，失败: {failed_count}")

            return BatchOperationResponse(
                success=failed_count == 0,
                message=f"批量更新{self.entity_name}完成",
                total=total,
                success_count=success_count,
                failed_count=failed_count,
                failed_items=failed_items if failed_items else None,
            )

        except Exception as e:
            logger.error(f"批量更新{self.entity_name}失败: {e}")
            raise BusinessError(f"批量更新{self.entity_name}失败: {str(e)}") from e

    @operation_log("批量删除记录", auto_save=True, include_args=True, include_result=True)
    async def bulk_delete(self, request: BulkDeleteRequest) -> BatchOperationResponse:
        """批量删除记录

        Args:
            request: 批量删除请求

        Returns:
            批量操作响应
        """
        try:
            failed_items = []
            success_count = 0

            for i, id in enumerate(request.ids):
                try:
                    existing = await self.dao.get_by_id(id)
                    if not existing:
                        failed_items.append({"index": i, "id": str(id), "error": f"{self.entity_name}不存在"})
                        continue

                    # 验证删除规则
                    await self._validate_delete(id, existing)

                    # 执行删除
                    if request.soft_delete and hasattr(existing, "is_deleted"):
                        deleted = await self.dao.soft_delete_by_id(id)
                    else:
                        deleted = await self.dao.delete_by_id(id)

                    if deleted:
                        success_count += 1
                    else:
                        failed_items.append({"index": i, "id": str(id), "error": "删除操作失败"})

                except Exception as e:
                    failed_items.append({"index": i, "id": str(id), "error": str(e)})

            total = len(request.ids)
            failed_count = len(failed_items)

            delete_type = "软删除" if request.soft_delete else "物理删除"
            logger.info(f"批量{delete_type}{self.entity_name}完成，成功: {success_count}，失败: {failed_count}")

            return BatchOperationResponse(
                success=failed_count == 0,
                message=f"批量{delete_type}{self.entity_name}完成",
                total=total,
                success_count=success_count,
                failed_count=failed_count,
                failed_items=failed_items if failed_items else None,
            )

        except Exception as e:
            logger.error(f"批量删除{self.entity_name}失败: {e}")
            raise BusinessError(f"批量删除{self.entity_name}失败: {str(e)}") from e

    async def exists(self, **filters) -> bool:
        """检查记录是否存在

        Args:
            **filters: 过滤条件

        Returns:
            是否存在
        """
        return await self.dao.exists(**filters)

    async def count(self, **filters) -> int:
        """统计记录数量

        Args:
            **filters: 过滤条件

        Returns:
            记录数量
        """
        return await self.dao.count(**filters)

    # 钩子方法，子类可以重写以实现特定的业务逻辑

    async def _validate_create_data(self, data: CreateSchemaType) -> None:
        """验证创建数据

        Args:
            data: 创建数据

        Raises:
            ValidationError: 验证失败
        """
        # 子类可以重写此方法实现特定的创建验证逻辑
        pass

    async def _validate_update_data(self, id: UUID, data: UpdateSchemaType, existing: ModelType) -> None:
        """验证更新数据

        Args:
            id: 记录ID
            data: 更新数据
            existing: 现有记录

        Raises:
            ValidationError: 验证失败
        """
        # 子类可以重写此方法实现特定的更新验证逻辑
        pass

    async def _validate_delete(self, id: UUID, existing: ModelType) -> None:
        """验证删除操作

        Args:
            id: 记录ID
            existing: 现有记录

        Raises:
            ValidationError: 验证失败
        """
        # 子类可以重写此方法实现特定的删除验证逻辑
        pass

    def _prepare_create_data(self, data: CreateSchemaType) -> dict[str, Any]:
        """准备创建数据

        Args:
            data: 创建数据

        Returns:
            准备好的数据字典
        """
        # 转换为字典并排除未设置的字段
        return data.model_dump(exclude_unset=True)

    def _prepare_update_data(self, data: UpdateSchemaType) -> dict[str, Any]:
        """准备更新数据

        Args:
            data: 更新数据

        Returns:
            准备好的数据字典
        """
        # 转换为字典并排除未设置的字段
        return data.model_dump(exclude_unset=True)

    def _build_filters(self, query_params: QueryParamsType) -> dict[str, Any]:
        """构建查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = {}

        # 通用搜索处理
        if hasattr(query_params, "search") and query_params.search:
            # 子类可以重写此方法实现特定的搜索逻辑
            filters["name__icontains"] = query_params.search

        # 排除软删除的记录
        filters["is_deleted"] = False

        return filters

    def _build_order_by(self, query_params: QueryParamsType) -> list[str]:
        """构建排序条件

        Args:
            query_params: 查询参数

        Returns:
            排序字段列表
        """
        order_by = []

        if hasattr(query_params, "order_by") and query_params.order_by:
            field = query_params.order_by
            if hasattr(query_params, "order_desc") and query_params.order_desc:
                field = f"-{field}"
            order_by.append(field)
        else:
            # 默认排序
            order_by.append("-created_at")

        return order_by

    def _get_prefetch_related(self) -> list[str]:
        """获取预加载的关联字段

        Returns:
            预加载字段列表
        """
        # 子类可以重写此方法指定需要预加载的关联字段
        return []
