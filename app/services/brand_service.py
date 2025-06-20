"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: brand_service.py
@DateTime: 2025/06/20 00:00:00
@Docs: 品牌服务层实现
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationError
from app.models.network_models import Brand
from app.repositories.brand_dao import BrandDAO
from app.schemas.brand import (
    BrandCreateRequest,
    BrandListResponse,
    BrandQueryParams,
    BrandStatsResponse,
    BrandUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.logger import logger


class BrandService(BaseService[Brand, BrandCreateRequest, BrandUpdateRequest, BrandListResponse, BrandQueryParams]):
    """品牌服务层

    提供品牌相关的业务逻辑处理，包括：
    - 品牌的CRUD操作
    - 品牌设备型号管理
    - 品牌设备统计
    - 平台类型管理
    """

    def __init__(self, dao: BrandDAO):
        """初始化品牌服务

        Args:
            dao: 品牌数据访问对象
        """
        super().__init__(dao=dao, response_schema=BrandListResponse, entity_name="品牌")

    async def _validate_create_data(self, data: BrandCreateRequest) -> None:
        """验证品牌创建数据

        Args:
            data: 品牌创建数据

        Raises:
            ValidationError: 验证失败
        """
        # 检查品牌名称是否重复
        if await self.dao.exists(name=data.name):
            raise ValidationError(f"品牌名称 {data.name} 已存在")

        # 检查平台类型是否重复
        if await self.dao.exists(platform_type=data.platform_type):
            raise ValidationError(f"平台类型 {data.platform_type} 已存在")  # 验证平台类型格式
        allowed_platforms = ["hp_comware", "huawei_vrp", "cisco_iosxe", "cisco_iosxr", "cisco_nxos", "juniper_junos"]
        if data.platform_type not in allowed_platforms:
            raise ValidationError(f"不支持的平台类型，支持的类型: {', '.join(allowed_platforms)}")

        logger.debug(f"品牌创建数据验证通过: {data.name}")

    async def _validate_update_data(self, id: UUID, data: BrandUpdateRequest, existing: Brand) -> None:
        """验证品牌更新数据

        Args:
            id: 品牌ID
            data: 更新数据
            existing: 现有品牌记录

        Raises:
            ValidationError: 验证失败
        """
        # 检查品牌名称是否重复（排除自身）
        if data.name and data.name != existing.name:
            if await self.dao.exists(name=data.name):
                raise ValidationError(f"品牌名称 {data.name} 已存在")

        # 检查平台类型是否重复（排除自身）
        if data.platform_type and data.platform_type != existing.platform_type:
            if await self.dao.exists(platform_type=data.platform_type):
                raise ValidationError(f"平台类型 {data.platform_type} 已存在")

        # 验证平台类型格式
        if data.platform_type:
            allowed_platforms = [
                "hp_comware",
                "huawei_vrp",
                "cisco_iosxe",
                "cisco_iosxr",
                "cisco_nxos",
                "juniper_junos",
            ]
            if data.platform_type not in allowed_platforms:
                raise ValidationError(f"不支持的平台类型，支持的类型: {', '.join(allowed_platforms)}")

        logger.debug(f"品牌更新数据验证通过: {existing.name} -> {data.name or existing.name}")

    async def _validate_delete(self, id: UUID, existing: Brand) -> None:
        """验证品牌删除操作

        Args:
            id: 品牌ID
            existing: 现有品牌记录

        Raises:
            ValidationError: 验证失败
        """
        # 暂时跳过删除验证
        # 在实际项目中，这里应该检查关联的设备型号和设备
        logger.debug(f"品牌删除验证通过: {existing.name}")

    def _build_filters(self, query_params: BrandQueryParams) -> dict[str, Any]:
        """构建品牌查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = super()._build_filters(query_params)

        # 按品牌名称过滤
        if query_params.name:
            filters["name__icontains"] = query_params.name

        # 按平台类型过滤
        if query_params.platform_type:
            filters["platform_type"] = query_params.platform_type

        # 按是否有设备过滤
        if query_params.has_devices is not None:
            if query_params.has_devices:
                # 有设备的品牌
                filters["device_models__devices__isnull"] = False
            else:
                # 没有设备的品牌
                filters["device_models__devices__isnull"] = True

        return filters

    def _get_prefetch_related(self) -> list[str]:
        """获取需要预加载的关联字段

        Returns:
            预加载字段列表
        """
        return ["device_models", "device_models__devices"]

    async def get_brand_stats(self, id: UUID) -> BrandStatsResponse:
        """获取品牌统计信息

        Args:
            id: 品牌ID

        Returns:
            品牌统计响应

        Raises:
            NotFoundError: 品牌不存在
        """
        try:
            # 获取品牌基本信息
            brand = await self.get_by_id(id)

            # 暂时设置默认统计值
            # 在实际项目中，应该查询关联的设备型号和设备数据
            total_models = 0
            total_devices = 0
            online_devices = 0
            recent_operations = 0

            return BrandStatsResponse(
                id=brand.id,
                name=brand.name,
                platform_type=brand.platform_type,
                total_models=total_models,
                total_devices=total_devices,
                online_devices=online_devices,
                recent_operations=recent_operations,
                created_at=brand.created_at,
                updated_at=brand.updated_at,
                is_deleted=brand.is_deleted,
                description=getattr(brand, "description", ""),
            )

        except Exception as e:
            logger.error(f"获取品牌 {id} 统计信息失败: {e}")
            raise

    async def search_by_name(self, name_keyword: str) -> list[BrandListResponse]:
        """根据名称关键字搜索品牌

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的品牌列表
        """
        try:
            filters = {"name__icontains": name_keyword, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"按名称搜索品牌失败，关键字: {name_keyword}, 错误: {e}")
            raise

    async def get_brand_by_name(self, name: str) -> BrandListResponse | None:
        """根据名称获取品牌

        Args:
            name: 品牌名称

        Returns:
            品牌响应或None
        """
        try:
            # 使用基础方法查询
            brands = await self.dao.list_by_filters({"name": name, "is_deleted": False})
            if not brands:
                return None

            return self.response_schema.model_validate(brands[0])

        except Exception as e:
            logger.error(f"根据名称获取品牌失败，名称: {name}, 错误: {e}")
            raise

    async def get_brand_by_platform_type(self, platform_type: str) -> BrandListResponse | None:
        """根据平台类型获取品牌

        Args:
            platform_type: 平台类型

        Returns:
            品牌响应或None
        """
        try:
            # 使用基础方法查询
            brands = await self.dao.list_by_filters({"platform_type": platform_type, "is_deleted": False})
            if not brands:
                return None

            return self.response_schema.model_validate(brands[0])

        except Exception as e:
            logger.error(f"根据平台类型获取品牌失败，平台类型: {platform_type}, 错误: {e}")
            raise

    async def get_brands_by_platform_type(self, platform_type: str) -> list[BrandListResponse]:
        """根据平台类型获取品牌列表

        Args:
            platform_type: 平台类型

        Returns:
            品牌列表
        """
        try:
            filters = {"platform_type": platform_type, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"根据平台类型获取品牌列表失败，平台类型: {platform_type}, 错误: {e}")
            raise

    async def get_supported_platforms(self) -> list[str]:
        """获取支持的平台类型列表

        Returns:
            平台类型列表
        """
        return ["hp_comware", "huawei_vrp", "cisco_iosxe", "cisco_iosxr", "cisco_nxos", "juniper_junos"]

    async def update_platform_type(self, id: UUID, platform_type: str) -> BrandListResponse:
        """更新品牌平台类型

        Args:
            id: 品牌ID
            platform_type: 新的平台类型

        Returns:
            更新后的品牌响应
        """
        try:
            # 验证平台类型
            supported_platforms = await self.get_supported_platforms()
            if platform_type not in supported_platforms:
                raise ValidationError(f"不支持的平台类型，支持的类型: {', '.join(supported_platforms)}")

            update_data = BrandUpdateRequest(platform_type=platform_type)
            return await self.update(id, update_data)

        except Exception as e:
            logger.error(f"更新品牌 {id} 平台类型失败: {e}")
            raise
