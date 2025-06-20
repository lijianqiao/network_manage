"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_service.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备服务层实现
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationError
from app.models.network_models import Device, DeviceStatusEnum
from app.repositories.device_dao import DeviceDAO
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceListResponse,
    DeviceQueryParams,
    DeviceUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.logger import logger


class DeviceService(
    BaseService[Device, DeviceCreateRequest, DeviceUpdateRequest, DeviceListResponse, DeviceQueryParams]
):
    """设备服务层

    提供设备相关的业务逻辑处理，包括：
    - 设备的CRUD操作
    - 设备状态管理
    - 设备组关联管理
    - 设备配置管理
    """

    def __init__(self, dao: DeviceDAO):
        """初始化设备服务

        Args:
            dao: 设备数据访问对象
        """
        super().__init__(dao=dao, response_schema=DeviceListResponse, entity_name="设备")

    async def _validate_create_data(self, data: DeviceCreateRequest) -> None:
        """验证设备创建数据

        Args:
            data: 设备创建数据

        Raises:
            ValidationError: 验证失败
        """
        # 检查设备IP是否重复
        if await self.dao.exists(ip_address=data.ip_address):
            raise ValidationError(f"IP地址 {data.ip_address} 已被其他设备使用")

        # 检查设备名称是否重复
        if await self.dao.exists(name=data.name):
            raise ValidationError(f"设备名称 {data.name} 已存在")

        # 验证设备品牌和型号是否存在
        # 这里可以添加对model_id的验证逻辑

        logger.debug(f"设备创建数据验证通过: {data.name}")

    async def _validate_update_data(self, id: UUID, data: DeviceUpdateRequest, existing: Device) -> None:
        """验证设备更新数据

        Args:
            id: 设备ID
            data: 更新数据
            existing: 现有设备记录

        Raises:
            ValidationError: 验证失败
        """
        # 检查IP地址是否重复（排除自身）
        if data.ip_address and data.ip_address != existing.ip_address:
            if await self.dao.exists(ip_address=data.ip_address):
                raise ValidationError(f"IP地址 {data.ip_address} 已被其他设备使用")

        # 检查设备名称是否重复（排除自身）
        if data.name and data.name != existing.name:
            if await self.dao.exists(name=data.name):
                raise ValidationError(f"设备名称 {data.name} 已存在")

        logger.debug(f"设备更新数据验证通过: {existing.name} -> {data.name or existing.name}")

    async def _validate_delete(self, id: UUID, existing: Device) -> None:
        """验证设备删除操作

        Args:
            id: 设备ID
            existing: 现有设备记录

        Raises:
            ValidationError: 验证失败
        """
        # 检查设备是否在线，如果在线则不允许删除
        if hasattr(existing, "status") and existing.status == "online":
            raise ValidationError(f"设备 {existing.name} 当前在线，无法删除")

        # 检查是否有相关的配置快照或模板，可以选择是否阻止删除
        # 这里可以添加更多的业务逻辑验证

        logger.debug(f"设备删除验证通过: {existing.name}")

    def _build_filters(self, query_params: DeviceQueryParams) -> dict[str, Any]:
        """构建设备查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = super()._build_filters(query_params)

        # 按区域过滤
        if query_params.region_id:
            filters["region_id"] = query_params.region_id

        # 按设备组过滤
        if query_params.device_group_id:
            filters["device_group_id"] = query_params.device_group_id

        # 按设备状态过滤
        if query_params.status:
            filters["status"] = query_params.status

        # 按设备类型过滤
        if query_params.device_type:
            filters["device_type"] = query_params.device_type

        # 按IP地址模糊搜索
        if query_params.ip_address:
            filters["ip_address__icontains"] = query_params.ip_address

        # 按设备名称过滤
        if query_params.name:
            filters["name__icontains"] = query_params.name

        # 按品牌名称过滤
        if query_params.brand_name:
            filters["model__brand__name__icontains"] = query_params.brand_name

        # 按密码类型过滤
        if query_params.is_dynamic_password is not None:
            filters["is_dynamic_password"] = query_params.is_dynamic_password

        # 按是否有序列号过滤
        if query_params.has_serial_number is not None:
            if query_params.has_serial_number:
                filters["serial_number__isnull"] = False
            else:
                filters["serial_number__isnull"] = True

        # 重写通用搜索逻辑，支持设备名称和IP地址搜索
        if query_params.search:
            # 移除父类添加的name__icontains过滤器
            filters.pop("name__icontains", None)
            # 这里应该使用OR查询，但需要在DAO层处理
            # 暂时只搜索名称
            filters["name__icontains"] = query_params.search

        return filters

    def _get_prefetch_related(self) -> list[str]:
        """获取需要预加载的关联字段

        Returns:
            预加载字段列表
        """
        return ["region", "device_group", "model", "model__brand"]

    async def get_devices_by_group(self, group_id: UUID) -> list[DeviceListResponse]:
        """根据设备组ID获取设备列表

        Args:
            group_id: 设备组ID

        Returns:
            设备响应列表
        """
        try:
            filters = {"device_group_id": group_id, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"获取设备组 {group_id} 的设备列表失败: {e}")
            raise

    async def get_devices_by_status(self, status: str) -> list[DeviceListResponse]:
        """根据状态获取设备列表

        Args:
            status: 设备状态

        Returns:
            设备响应列表
        """
        try:
            filters = {"status": status, "is_deleted": False}
            return await self.list_all(filters=filters)

        except Exception as e:
            logger.error(f"获取状态为 {status} 的设备列表失败: {e}")
            raise

    async def update_device_status(self, id: UUID, status: DeviceStatusEnum) -> DeviceListResponse:
        """更新设备状态

        Args:
            id: 设备ID
            status: 新状态

        Returns:
            更新后的设备响应
        """
        try:
            # 构造状态更新数据
            update_data = DeviceUpdateRequest(status=status)
            return await self.update(id, update_data)

        except Exception as e:
            logger.error(f"更新设备 {id} 状态为 {status} 失败: {e}")
            raise
