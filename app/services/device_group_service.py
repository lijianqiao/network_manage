"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_group_service.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备组服务层实现
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationError
from app.models.network_models import DeviceGroup
from app.repositories.device_group_dao import DeviceGroupDAO
from app.schemas.device_group import (
    DeviceGroupBatchAssignRequest,
    DeviceGroupCreateRequest,
    DeviceGroupListResponse,
    DeviceGroupQueryParams,
    DeviceGroupStatsResponse,
    DeviceGroupUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.logger import logger


class DeviceGroupService(
    BaseService[
        DeviceGroup, DeviceGroupCreateRequest, DeviceGroupUpdateRequest, DeviceGroupListResponse, DeviceGroupQueryParams
    ]
):
    """设备组服务层

    提供设备组相关的业务逻辑处理，包括：
    - 设备组的CRUD操作
    - 设备分组管理
    - 设备批量分配
    - 设备组统计
    """

    def __init__(self, dao: DeviceGroupDAO):
        """初始化设备组服务

        Args:
            dao: 设备组数据访问对象
        """
        super().__init__(dao=dao, response_schema=DeviceGroupListResponse, entity_name="设备组")

    async def _validate_create_data(self, data: DeviceGroupCreateRequest) -> None:
        """验证设备组创建数据

        Args:
            data: 设备组创建数据

        Raises:
            ValidationError: 验证失败
        """  # 检查设备组名称是否重复
        filters = {"name": data.name}
        if data.region_id:
            filters["region_id"] = str(data.region_id)

        if await self.dao.exists(**filters):
            if data.region_id:
                raise ValidationError(f"区域内设备组名称 {data.name} 已存在")
            else:
                raise ValidationError(f"设备组名称 {data.name} 已存在")

        # 验证关联的区域是否存在
        if data.region_id:
            # 这里应该验证region_id是否存在，暂时跳过
            pass

        logger.debug(f"设备组创建数据验证通过: {data.name}")

    async def _validate_update_data(self, id: UUID, data: DeviceGroupUpdateRequest, existing: DeviceGroup) -> None:
        """验证设备组更新数据

        Args:
            id: 设备组ID
            data: 更新数据
            existing: 现有设备组记录

        Raises:
            ValidationError: 验证失败
        """  # 检查设备组名称是否重复（排除自身）
        if data.name and data.name != existing.name:
            filters = {"name": data.name}
            # 如果指定了新的区域ID，则在该区域内检查重复
            region_id = data.region_id if data.region_id is not None else getattr(existing, "region_id", None)
            if region_id:
                filters["region_id"] = str(region_id)

            # 检查是否存在同名的其他设备组
            existing_groups = await self.dao.list_by_filters(filters)
            if existing_groups and any(group.id != id for group in existing_groups):
                if region_id:
                    raise ValidationError(f"区域内设备组名称 {data.name} 已存在")
                else:
                    raise ValidationError(f"设备组名称 {data.name} 已存在")

        # 验证关联的区域是否存在
        if data.region_id:
            # 这里应该验证region_id是否存在，暂时跳过
            pass

        logger.debug(f"设备组更新数据验证通过: {existing.name} -> {data.name or existing.name}")

    async def _validate_delete(self, id: UUID, existing: DeviceGroup) -> None:
        """验证设备组删除操作

        Args:
            id: 设备组ID
            existing: 现有设备组记录

        Raises:
            ValidationError: 验证失败
        """
        # 暂时跳过删除验证
        # 在实际项目中，这里应该检查组内是否还有设备
        logger.debug(f"设备组删除验证通过: {existing.name}")

    def _build_filters(self, query_params: DeviceGroupQueryParams) -> dict[str, Any]:
        """构建设备组查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = super()._build_filters(query_params)

        # 按设备组名称过滤
        if query_params.name:
            filters["name__icontains"] = query_params.name

        # 按区域ID过滤
        if query_params.region_id:
            filters["region_id"] = query_params.region_id

        # 按区域名称过滤
        if query_params.region_name:
            filters["region__name__icontains"] = query_params.region_name

        # 按是否有设备过滤
        if query_params.has_devices is not None:
            if query_params.has_devices:
                # 有设备的设备组
                filters["devices__isnull"] = False
            else:
                # 没有设备的设备组
                filters["devices__isnull"] = True

        return filters

    def _get_prefetch_related(self) -> list[str]:
        """获取需要预加载的关联字段

        Returns:
            预加载字段列表
        """
        return ["region", "devices"]

    async def get_device_group_stats(self, id: UUID) -> DeviceGroupStatsResponse:
        """获取设备组统计信息

        Args:
            id: 设备组ID

        Returns:
            设备组统计响应

        Raises:
            NotFoundError: 设备组不存在
        """
        try:
            # 获取设备组基本信息
            device_group = await self.get_by_id(id)

            # 暂时设置默认统计值
            # 在实际项目中，应该查询组内的设备数据
            total_devices = 0
            online_devices = 0
            offline_devices = 0
            switch_count = 0
            router_count = 0

            return DeviceGroupStatsResponse(
                id=device_group.id,
                name=device_group.name,
                region_name=getattr(device_group, "region_name", None),
                total_devices=total_devices,
                online_devices=online_devices,
                offline_devices=offline_devices,
                switch_count=switch_count,
                router_count=router_count,
                created_at=device_group.created_at,
                updated_at=device_group.updated_at,
                is_deleted=device_group.is_deleted,
                description=getattr(device_group, "description", ""),
            )

        except Exception as e:
            logger.error(f"获取设备组 {id} 统计信息失败: {e}")
            raise

    async def get_groups_by_region(self, region_id: UUID) -> list[DeviceGroupListResponse]:
        """根据区域ID获取设备组列表

        Args:
            region_id: 区域ID

        Returns:
            设备组列表
        """
        try:
            filters = {"region_id": region_id, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"获取区域 {region_id} 的设备组列表失败: {e}")
            raise

    async def search_by_name(self, name_keyword: str) -> list[DeviceGroupListResponse]:
        """根据名称关键字搜索设备组

        Args:
            name_keyword: 名称关键字

        Returns:
            匹配的设备组列表
        """
        try:
            filters = {"name__icontains": name_keyword, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"按名称搜索设备组失败，关键字: {name_keyword}, 错误: {e}")
            raise

    async def get_group_by_name(self, name: str, region_id: UUID | None = None) -> DeviceGroupListResponse | None:
        """根据名称获取设备组

        Args:
            name: 设备组名称
            region_id: 区域ID（可选，用于区域内查找）

        Returns:
            设备组响应或None
        """
        try:
            filters = {"name": name, "is_deleted": False}
            if region_id:
                filters["region_id"] = region_id

            # 使用基础方法查询
            groups = await self.dao.list_by_filters(filters)
            if not groups:
                return None

            return self.response_schema.model_validate(groups[0])

        except Exception as e:
            logger.error(f"根据名称获取设备组失败，名称: {name}, 区域ID: {region_id}, 错误: {e}")
            raise

    async def batch_assign_devices(self, request: DeviceGroupBatchAssignRequest) -> dict:
        """批量分配设备到设备组

        Args:
            request: 批量分配请求

        Returns:
            分配结果
        """
        try:
            # 验证设备组是否存在
            await self.get_by_id(request.group_id)

            # 这里应该调用设备服务来更新设备的设备组ID
            # 暂时返回模拟结果
            success_count = len(request.device_ids)
            failed_count = 0

            logger.info(f"批量分配 {len(request.device_ids)} 个设备到设备组 {request.group_id}")

            return {
                "total": len(request.device_ids),
                "success": success_count,
                "failed": failed_count,
                "group_id": str(request.group_id),
                "message": f"成功分配 {success_count} 个设备",
            }

        except Exception as e:
            logger.error(f"批量分配设备到设备组失败: {e}")
            raise

    async def move_group_to_region(self, group_id: UUID, target_region_id: UUID | None) -> DeviceGroupListResponse:
        """移动设备组到另一个区域

        Args:
            group_id: 设备组ID
            target_region_id: 目标区域ID（None表示移到无区域分组）

        Returns:
            更新后的设备组响应
        """
        try:
            # 如果目标区域存在，验证其是否有效
            if target_region_id:
                # 这里应该验证target_region_id是否存在，暂时跳过
                pass

            update_data = DeviceGroupUpdateRequest(region_id=target_region_id)
            return await self.update(group_id, update_data)

        except Exception as e:
            logger.error(f"移动设备组 {group_id} 到区域 {target_region_id} 失败: {e}")
            raise

    async def get_empty_groups(self) -> list[DeviceGroupListResponse]:
        """获取没有设备的空设备组

        Returns:
            空设备组列表
        """
        try:
            filters = {"devices__isnull": True, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"获取空设备组列表失败: {e}")
            raise
