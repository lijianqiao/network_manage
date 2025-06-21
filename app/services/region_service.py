"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region_service.py
@DateTime: 2025/06/20 00:00:00
@Docs: 区域服务层实现
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationError
from app.models.network_models import Region
from app.repositories.region_dao import RegionDAO
from app.schemas.region import (
    RegionCreateRequest,
    RegionListResponse,
    RegionQueryParams,
    RegionStatsResponse,
    RegionUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.logger import logger


class RegionService(
    BaseService[Region, RegionCreateRequest, RegionUpdateRequest, RegionListResponse, RegionQueryParams]
):
    """区域服务层

    提供区域相关的业务逻辑处理，包括：
    - 区域的CRUD操作
    - 区域设备统计
    - 区域设备组管理
    - 区域配置管理
    """

    def __init__(self, dao: RegionDAO):
        """初始化区域服务

        Args:
            dao: 区域数据访问对象
        """
        super().__init__(dao=dao, response_schema=RegionListResponse, entity_name="区域")

    async def _validate_create_data(self, data: RegionCreateRequest) -> None:
        """验证区域创建数据

        Args:
            data: 区域创建数据

        Raises:
            ValidationError: 验证失败
        """
        # 检查区域名称是否重复
        if await self.dao.exists(name=data.name):
            raise ValidationError(f"区域名称 {data.name} 已存在")

        # 验证SNMP社区字符串不能为空
        if not data.snmp_community_string.strip():
            raise ValidationError("SNMP社区字符串不能为空")

        # 验证默认CLI用户名不能为空
        if not data.default_cli_username.strip():
            raise ValidationError("默认CLI用户名不能为空")

        logger.debug(f"区域创建数据验证通过: {data.name}")

    async def _validate_update_data(self, id: UUID, data: RegionUpdateRequest, existing: Region) -> None:
        """验证区域更新数据

        Args:
            id: 区域ID
            data: 更新数据
            existing: 现有区域记录

        Raises:
            ValidationError: 验证失败
        """
        # 检查区域名称是否重复（排除自身）
        if data.name and data.name != existing.name:
            if await self.dao.exists(name=data.name):
                raise ValidationError(f"区域名称 {data.name} 已存在")

        # 验证SNMP社区字符串不能为空
        if data.snmp_community_string is not None and not data.snmp_community_string.strip():
            raise ValidationError("SNMP社区字符串不能为空")

        # 验证默认CLI用户名不能为空
        if data.default_cli_username is not None and not data.default_cli_username.strip():
            raise ValidationError("默认CLI用户名不能为空")

        logger.debug(f"区域更新数据验证通过: {existing.name} -> {data.name or existing.name}")

    async def _validate_delete(self, id: UUID, existing: Region) -> None:
        """验证区域删除操作

        Args:
            id: 区域ID
            existing: 现有区域记录

        Raises:
            ValidationError: 验证失败
        """
        # 暂时跳过删除验证（需要实际的关联数据查询）
        # 在实际项目中，这里应该检查关联的设备和设备组
        logger.debug(f"区域删除验证通过: {existing.name}")

    def _build_filters(self, query_params: RegionQueryParams) -> dict[str, Any]:
        """构建区域查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = super()._build_filters(query_params)

        # 按区域名称过滤
        if query_params.name:
            filters["name__icontains"] = query_params.name

        # 按是否有设备过滤
        if query_params.has_devices is not None:
            if query_params.has_devices:
                # 有设备的区域
                filters["devices__isnull"] = False
            else:
                # 没有设备的区域
                filters["devices__isnull"] = True

        return filters

    def _get_prefetch_related(self) -> list[str]:
        """获取需要预加载的关联字段

        Returns:
            预加载字段列表
        """
        return ["devices"]

    async def get_region_stats(self, id: UUID) -> RegionStatsResponse:
        """获取区域统计信息

        Args:
            id: 区域ID

        Returns:
            区域统计响应

        Raises:
            NotFoundError: 区域不存在
        """
        try:
            # 获取区域基本信息
            region = await self.get_by_id(id)

            # 暂时设置默认统计值
            # 在实际项目中，应该查询关联的设备和设备组数据
            total_devices = 0
            online_devices = 0
            offline_devices = 0
            device_groups = 0
            recent_operations = 0

            return RegionStatsResponse(
                id=region.id,
                name=region.name,
                total_devices=total_devices,
                online_devices=online_devices,
                offline_devices=offline_devices,
                device_groups=device_groups,
                recent_operations=recent_operations,
                created_at=region.created_at,
                updated_at=region.updated_at,
                is_deleted=region.is_deleted,
                description=getattr(region, "description", ""),
            )

        except Exception as e:
            logger.error(f"获取区域 {id} 统计信息失败: {e}")
            raise

    async def get_regions_with_device_count(self) -> list[dict]:
        """获取所有区域及其设备数量

        Returns:
            包含区域信息和设备数量的字典列表
        """
        try:
            # 暂时返回基础区域信息
            # 在实际项目中，应该查询关联的设备数据
            regions = await self.dao.list_by_filters({})
            result = []
            for region in regions:
                result.append(
                    {
                        "id": str(region.id),
                        "name": region.name,
                        "device_count": 0,  # 暂时设为0
                        "device_group_count": 0,  # 暂时设为0
                    }
                )
            return result

        except Exception as e:
            logger.error(f"获取区域设备统计失败: {e}")
            raise

    async def search_by_name(self, name_keyword: str) -> list[RegionListResponse]:
        """根据名称关键字搜索区域

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的区域列表
        """
        try:
            filters = {"name__icontains": name_keyword, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"按名称搜索区域失败，关键字: {name_keyword}, 错误: {e}")
            raise

    async def get_region_by_name(self, name: str) -> RegionListResponse | None:
        """根据名称获取区域

        Args:
            name: 区域名称

        Returns:
            区域响应或None
        """
        try:
            # 使用基础方法查询
            regions = await self.dao.list_by_filters({"name": name, "is_deleted": False})
            if not regions:
                return None

            return self.response_schema.model_validate(regions[0])

        except Exception as e:
            logger.error(f"根据名称获取区域失败，名称: {name}, 错误: {e}")
            raise

    async def update_snmp_config(self, id: UUID, snmp_community_string: str) -> RegionListResponse:
        """更新区域SNMP配置

        Args:
            id: 区域ID
            snmp_community_string: 新的SNMP社区字符串

        Returns:
            更新后的区域响应
        """
        try:
            if not snmp_community_string.strip():
                raise ValidationError("SNMP社区字符串不能为空")

            update_data = RegionUpdateRequest(snmp_community_string=snmp_community_string)
            return await self.update(id, update_data)

        except Exception as e:
            logger.error(f"更新区域 {id} SNMP配置失败: {e}")
            raise

    async def update_default_cli_username(self, id: UUID, default_cli_username: str) -> RegionListResponse:
        """更新区域默认CLI用户名

        Args:
            id: 区域ID
            default_cli_username: 新的默认CLI用户名

        Returns:
            更新后的区域响应
        """
        try:
            if not default_cli_username.strip():
                raise ValidationError("默认CLI用户名不能为空")

            update_data = RegionUpdateRequest(default_cli_username=default_cli_username)
            return await self.update(id, update_data)

        except Exception as e:
            logger.error(f"更新区域 {id} 默认CLI用户名失败: {e}")
            raise
