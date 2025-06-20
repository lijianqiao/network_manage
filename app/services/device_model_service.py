"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_model_service.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备型号服务层实现
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationError
from app.models.network_models import DeviceModel
from app.repositories.device_model_dao import DeviceModelDAO
from app.schemas.device_model import (
    DeviceModelCreateRequest,
    DeviceModelListResponse,
    DeviceModelQueryParams,
    DeviceModelStatsResponse,
    DeviceModelUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.logger import logger


class DeviceModelService(
    BaseService[
        DeviceModel, DeviceModelCreateRequest, DeviceModelUpdateRequest, DeviceModelListResponse, DeviceModelQueryParams
    ]
):
    """设备型号服务层

    提供设备型号相关的业务逻辑处理，包括：
    - 设备型号的CRUD操作
    - 型号与品牌关联管理
    - 设备型号统计
    - 型号规格管理
    """

    def __init__(self, dao: DeviceModelDAO):
        """初始化设备型号服务

        Args:
            dao: 设备型号数据访问对象
        """
        super().__init__(dao=dao, response_schema=DeviceModelListResponse, entity_name="设备型号")

    async def _validate_create_data(self, data: DeviceModelCreateRequest) -> None:
        """验证设备型号创建数据

        Args:
            data: 设备型号创建数据

        Raises:
            ValidationError: 验证失败
        """
        # 检查型号名称是否重复
        if await self.dao.exists(name=data.name):
            raise ValidationError(f"设备型号名称 {data.name} 已存在")

        # 验证关联的品牌是否存在
        # 这里应该调用品牌服务验证brand_id是否存在，暂时跳过
        if not data.brand_id:
            raise ValidationError("必须指定关联的品牌")

        logger.debug(f"设备型号创建数据验证通过: {data.name}")

    async def _validate_update_data(self, id: UUID, data: DeviceModelUpdateRequest, existing: DeviceModel) -> None:
        """验证设备型号更新数据

        Args:
            id: 设备型号ID
            data: 更新数据
            existing: 现有设备型号记录

        Raises:
            ValidationError: 验证失败
        """
        # 检查型号名称是否重复（排除自身）
        if data.name and data.name != existing.name:
            if await self.dao.exists(name=data.name):
                raise ValidationError(f"设备型号名称 {data.name} 已存在")

        # 验证关联的品牌是否存在
        if data.brand_id:
            # 这里应该调用品牌服务验证brand_id是否存在，暂时跳过
            pass

        logger.debug(f"设备型号更新数据验证通过: {existing.name} -> {data.name or existing.name}")

    async def _validate_delete(self, id: UUID, existing: DeviceModel) -> None:
        """验证设备型号删除操作

        Args:
            id: 设备型号ID
            existing: 现有设备型号记录

        Raises:
            ValidationError: 验证失败
        """
        # 暂时跳过删除验证
        # 在实际项目中，这里应该检查是否有设备使用此型号
        logger.debug(f"设备型号删除验证通过: {existing.name}")

    def _build_filters(self, query_params: DeviceModelQueryParams) -> dict[str, Any]:
        """构建设备型号查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = super()._build_filters(query_params)

        # 按型号名称过滤
        if query_params.name:
            filters["name__icontains"] = query_params.name

        # 按品牌ID过滤
        if query_params.brand_id:
            filters["brand_id"] = str(query_params.brand_id)

        # 按品牌名称过滤
        if query_params.brand_name:
            filters["brand__name__icontains"] = query_params.brand_name

        # 按是否有设备过滤
        if query_params.has_devices is not None:
            if query_params.has_devices:
                # 有设备的型号
                filters["devices__isnull"] = False
            else:
                # 没有设备的型号
                filters["devices__isnull"] = True

        return filters

    def _get_prefetch_related(self) -> list[str]:
        """获取需要预加载的关联字段

        Returns:
            预加载字段列表
        """
        return ["brand", "devices"]

    async def get_device_model_stats(self, id: UUID) -> DeviceModelStatsResponse:
        """获取设备型号统计信息

        Args:
            id: 设备型号ID

        Returns:
            设备型号统计响应

        Raises:
            NotFoundError: 设备型号不存在
        """
        try:
            # 获取设备型号基本信息
            device_model = await self.get_by_id(id)

            # 暂时设置默认统计值
            # 在实际项目中，应该查询使用此型号的设备数据
            total_devices = 0
            online_devices = 0
            offline_devices = 0
            recent_additions = 0

            return DeviceModelStatsResponse(
                id=device_model.id,
                name=device_model.name,
                brand_name=getattr(device_model, "brand_name", ""),
                total_devices=total_devices,
                online_devices=online_devices,
                offline_devices=offline_devices,
                recent_additions=recent_additions,
                created_at=device_model.created_at,
                updated_at=device_model.updated_at,
                is_deleted=device_model.is_deleted,
                description=getattr(device_model, "description", ""),
            )

        except Exception as e:
            logger.error(f"获取设备型号 {id} 统计信息失败: {e}")
            raise

    async def get_models_by_brand(self, brand_id: UUID) -> list[DeviceModelListResponse]:
        """根据品牌ID获取设备型号列表

        Args:
            brand_id: 品牌ID

        Returns:
            设备型号列表
        """
        try:
            filters = {"brand_id": str(brand_id), "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"获取品牌 {brand_id} 的设备型号列表失败: {e}")
            raise

    async def search_by_name(self, name_keyword: str) -> list[DeviceModelListResponse]:
        """根据名称关键字搜索设备型号

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的设备型号列表
        """
        try:
            filters = {"name__icontains": name_keyword, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"按名称搜索设备型号失败，关键字: {name_keyword}, 错误: {e}")
            raise

    async def get_model_by_name(self, name: str) -> DeviceModelListResponse | None:
        """根据名称获取设备型号

        Args:
            name: 设备型号名称

        Returns:
            设备型号响应或None
        """
        try:
            # 使用基础方法查询
            models = await self.dao.list_by_filters({"name": name, "is_deleted": False})
            if not models:
                return None

            return self.response_schema.model_validate(models[0])

        except Exception as e:
            logger.error(f"根据名称获取设备型号失败，名称: {name}, 错误: {e}")
            raise

    async def change_brand(self, model_id: UUID, new_brand_id: UUID) -> DeviceModelListResponse:
        """更换设备型号的品牌

        Args:
            model_id: 设备型号ID
            new_brand_id: 新品牌ID

        Returns:
            更新后的设备型号响应
        """
        try:
            # 验证新品牌是否存在
            # 这里应该调用品牌服务验证new_brand_id是否存在，暂时跳过

            update_data = DeviceModelUpdateRequest(brand_id=new_brand_id)
            return await self.update(model_id, update_data)

        except Exception as e:
            logger.error(f"更换设备型号 {model_id} 的品牌为 {new_brand_id} 失败: {e}")
            raise

    async def get_popular_models(self, limit: int = 10) -> list[DeviceModelListResponse]:
        """获取热门设备型号（按设备数量排序）

        Args:
            limit: 返回数量限制

        Returns:
            热门设备型号列表"""
        try:
            # 暂时返回按创建时间排序的型号列表
            # 在实际项目中，应该按设备数量排序
            filters = {"is_deleted": False}
            models = await self.dao.list_by_filters(filters)
            # 手动限制返回数量
            limited_models = models[:limit]
            return [self.response_schema.model_validate(model) for model in limited_models]

        except Exception as e:
            logger.error(f"获取热门设备型号失败: {e}")
            raise

    async def get_unused_models(self) -> list[DeviceModelListResponse]:
        """获取未使用的设备型号（没有设备使用）

        Returns:
            未使用的设备型号列表
        """
        try:
            filters = {"devices__isnull": True, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"获取未使用设备型号列表失败: {e}")
            raise
