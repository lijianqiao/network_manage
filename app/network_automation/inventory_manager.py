"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: inventory_manager.py
@DateTime: 2025/06/23 11:00:00
@Docs: Nornir动态主机清单管理器 - 从数据库构建设备清单
"""

from typing import Any
from uuid import UUID

from nornir.core.inventory import Group, Groups, Host, Hosts, Inventory

from app.core.credential_manager import CredentialManager
from app.models.network_models import Device
from app.utils.logger import logger


class DynamicInventoryManager:
    """动态主机清单管理器

    从数据库中构建Nornir Inventory，而非静态YAML文件
    """

    def __init__(self, credential_manager: CredentialManager):
        """初始化清单管理器

        Args:
            credential_manager: 凭据管理器实例
        """
        self.credential_manager = credential_manager

    async def create_inventory_from_devices(
        self, device_ids: list[UUID], runtime_credentials: dict[str, Any] | None = None
    ) -> Inventory:
        """从设备ID列表创建动态清单

        Args:
            device_ids: 设备ID列表
            runtime_credentials: 运行时凭据（用户输入的OTP等）

        Returns:
            构建完成的Nornir Inventory对象

        Raises:
            ValueError: 当设备不存在或凭据解析失败时
        """
        if not device_ids:
            raise ValueError("设备ID列表不能为空")

        # 查询设备信息（包含关联的区域、品牌等）
        devices = (
            await Device.filter(id__in=device_ids).prefetch_related("region", "model__brand", "device_group").all()
        )

        if len(devices) != len(device_ids):
            found_ids = {device.id for device in devices}
            missing_ids = set(device_ids) - found_ids
            raise ValueError(f"设备不存在: {missing_ids}")

        # 创建主机和分组
        hosts = {}
        groups = {}

        for device in devices:
            try:  # 解析设备凭据
                credentials = await self.credential_manager.resolve_device_credentials(
                    device=device, user_provided_credentials=runtime_credentials
                )

                # 设备分组名称（按区域分组）
                group_name = f"region_{device.region.name}"

                # 创建主机对象 - 只包含Nornir Host支持的标准参数
                host_params = {
                    "hostname": credentials["hostname"],
                    "username": credentials["username"],
                    "password": credentials["password"],
                    "platform": credentials["platform"],
                    "port": credentials.get("port", 22),
                    "groups": [group_name],
                }

                # 添加enable密码（如果有）
                if credentials.get("enable_password"):
                    host_params["enable_password"] = credentials["enable_password"]

                # 准备自定义数据（通过data参数传递）
                custom_data = {
                    # 设备元数据
                    "device_id": str(device.id),
                    "device_name": device.name,
                    "device_type": device.device_type.value,
                    "region_name": device.region.name,
                    "brand_name": device.model.brand.name,
                    "model_name": device.model.name,
                    "group_name": device.device_group.name,
                    # Scrapli连接配置
                    "timeout_socket": 30,
                    "timeout_transport": 60,
                    # 原始凭据信息（供任务使用）
                    "credentials": credentials,
                }

                # 通过data参数传递自定义数据
                host_params["data"] = custom_data

                hosts[device.name] = Host(name=device.name, **host_params)

                # 创建区域分组（如果还没有）
                if group_name not in groups:
                    # 准备分组自定义数据
                    group_custom_data = {
                        "region_id": str(device.region.id),
                        "snmp_community": device.region.snmp_community_string,
                        "default_username": device.region.default_cli_username,
                    }
                    groups[group_name] = Group(name=group_name, data=group_custom_data)

                logger.debug(f"已添加设备到清单: {device.name} ({device.ip_address})")

            except Exception as e:
                logger.error(f"创建设备 {device.name} 的清单项失败: {e}")
                raise ValueError(f"设备 {device.name} 凭据解析失败: {str(e)}") from e  # 创建并返回Inventory

        inventory = Inventory(hosts=Hosts(hosts), groups=Groups(groups))
        logger.info(f"成功创建动态清单，包含 {len(hosts)} 台设备，{len(groups)} 个分组")

        return inventory

    async def create_inventory_from_region(
        self, region_id: UUID, runtime_credentials: dict[str, Any] | None = None
    ) -> Inventory:
        """从区域创建设备清单

        Args:
            region_id: 区域ID
            runtime_credentials: 运行时凭据

        Returns:
            区域内所有设备的清单
        """
        # 查询区域内的所有设备
        devices = (
            await Device.filter(region_id=region_id).prefetch_related("region", "model__brand", "device_group").all()
        )

        if not devices:
            raise ValueError(f"区域 {region_id} 中没有设备")

        device_ids = [device.id for device in devices]
        return await self.create_inventory_from_devices(device_ids, runtime_credentials)

    async def create_inventory_from_group(
        self, group_id: UUID, runtime_credentials: dict[str, Any] | None = None
    ) -> Inventory:
        """从设备分组创建设备清单

        Args:
            group_id: 设备分组ID
            runtime_credentials: 运行时凭据

        Returns:
            分组内所有设备的清单
        """
        # 查询分组内的所有设备
        devices = (
            await Device.filter(device_group_id=group_id)
            .prefetch_related("region", "model__brand", "device_group")
            .all()
        )

        if not devices:
            raise ValueError(f"设备分组 {group_id} 中没有设备")

        device_ids = [device.id for device in devices]
        return await self.create_inventory_from_devices(device_ids, runtime_credentials)

    def validate_inventory(self, inventory: Inventory) -> dict[str, Any]:
        """验证清单的有效性

        Args:
            inventory: 要验证的清单

        Returns:
            验证结果统计
        """
        validation_result = {
            "total_hosts": len(inventory.hosts),
            "total_groups": len(inventory.groups),
            "hosts_with_credentials": 0,
            "hosts_without_credentials": 0,
            "platform_distribution": {},
            "region_distribution": {},
        }

        for host in inventory.hosts.values():
            # 检查凭据完整性
            has_credentials = bool(host.username and host.password and host.hostname and host.platform)

            if has_credentials:
                validation_result["hosts_with_credentials"] += 1
            else:
                validation_result["hosts_without_credentials"] += 1

            # 统计平台分布
            platform = getattr(host, "platform", "unknown")
            validation_result["platform_distribution"][platform] = (
                validation_result["platform_distribution"].get(platform, 0) + 1
            )  # 统计区域分布
            host_data = getattr(host, "data", {})
            region = host_data.get("region_name", "unknown")
            validation_result["region_distribution"][region] = (
                validation_result["region_distribution"].get(region, 0) + 1
            )

        logger.info(f"清单验证完成: {validation_result}")
        return validation_result
