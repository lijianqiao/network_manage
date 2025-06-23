"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: credential_service.py
@DateTime: 2025/06/23 00:00:00
@Docs: 凭据服务层 - 管理设备认证凭据的业务逻辑
"""

from typing import Any
from uuid import UUID

from app.core.credential_manager import CredentialManager
from app.core.exceptions import BusinessError
from app.repositories.device_dao import DeviceDAO
from app.utils.logger import logger
from app.utils.password_encryption import encrypt_password


class CredentialService:
    """凭据服务层

    提供设备连接凭据的管理和解析功能
    """

    def __init__(self):
        self.device_dao = DeviceDAO()
        self.credential_manager = CredentialManager()

    async def resolve_device_credentials(
        self, device_id: UUID, user_credentials: dict[str, str] | None = None, enable_otp: bool = False
    ) -> dict[str, Any]:
        """解析设备连接凭据

        Args:
            device_id: 设备ID
            user_credentials: 用户提供的临时凭据
            enable_otp: 是否启用OTP模式

        Returns:
            解析后的凭据信息

        Raises:
            BusinessError: 设备不存在或凭据解析失败
        """
        try:
            # 获取设备信息
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessError(f"设备不存在: {device_id}")

            # 解析凭据
            resolved_credentials = await self.credential_manager.resolve_device_credentials(
                device=device, user_provided_credentials=user_credentials
            )

            logger.info(f"成功解析设备 {device.name} 的连接凭据")

            return {
                "device_id": str(device_id),
                "device_name": device.name,
                "ip_address": device.ip_address,
                "credentials": resolved_credentials,
                "otp_enabled": enable_otp,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"解析设备凭据失败 - 设备ID: {device_id}, 错误: {e}")
            raise BusinessError(f"凭据解析失败: {str(e)}") from e

    async def update_device_credentials(
        self, device_id: UUID, credentials: dict[str, str], encrypt_passwords: bool = True
    ) -> dict[str, Any]:
        """更新设备凭据

        Args:
            device_id: 设备ID
            credentials: 新的凭据信息
            encrypt_passwords: 是否加密密码

        Returns:
            更新结果
        """
        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessError(f"设备不存在: {device_id}")

            # 准备更新数据
            update_data = {}

            if "username" in credentials:
                update_data["cli_username"] = credentials["username"]

            if "password" in credentials:
                password = credentials["password"]
                if encrypt_passwords and password:
                    password = encrypt_password(password)
                update_data["cli_password_encrypted"] = password

            if "enable_password" in credentials:
                enable_password = credentials["enable_password"]
                if encrypt_passwords and enable_password:
                    enable_password = encrypt_password(enable_password)
                update_data["enable_password_encrypted"] = enable_password

            # 更新设备凭据
            await self.device_dao.update_by_id(device_id, **update_data)

            logger.info(f"成功更新设备 {device.name} 的连接凭据")

            return {
                "device_id": str(device_id),
                "device_name": device.name,
                "status": "updated",
                "updated_fields": list(update_data.keys()),
            }

        except Exception as e:
            logger.error(f"更新设备凭据失败 - 设备ID: {device_id}, 错误: {e}")
            raise BusinessError(f"凭据更新失败: {str(e)}") from e

    async def validate_device_credentials(self, device_id: UUID, test_connection: bool = False) -> dict[str, Any]:
        """验证设备凭据

        Args:
            device_id: 设备ID
            test_connection: 是否测试实际连接

        Returns:
            验证结果
        """
        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessError(f"设备不存在: {device_id}")

            # 解析凭据
            credentials = await self.credential_manager.resolve_device_credentials(device)

            # 基础验证
            validation_result = {
                "device_id": str(device_id),
                "device_name": device.name,
                "has_username": bool(credentials.get("username")),
                "has_password": bool(credentials.get("password")),
                "has_enable_password": bool(credentials.get("enable_password")),
                "validation_status": "valid"
                if credentials.get("username") and credentials.get("password")
                else "incomplete",
            }

            # TODO: 如果需要测试实际连接，在第三阶段实现
            if test_connection:
                validation_result["connection_test"] = "skipped_until_stage3"

            logger.info(f"设备 {device.name} 凭据验证完成")
            return validation_result

        except Exception as e:
            logger.error(f"验证设备凭据失败 - 设备ID: {device_id}, 错误: {e}")
            raise BusinessError(f"凭据验证失败: {str(e)}") from e

    async def get_credential_summary(self) -> dict[str, Any]:
        """获取凭据管理概要统计

        Returns:
            凭据统计信息
        """
        try:
            # 获取所有设备
            devices = await self.device_dao.list_all()

            total_devices = len(devices)
            devices_with_credentials = 0
            devices_with_enable_password = 0
            encrypted_passwords = 0

            for device in devices:
                if device.cli_username and device.cli_password_encrypted:
                    devices_with_credentials += 1

                if device.enable_password_encrypted:
                    devices_with_enable_password += 1

                # 检查密码是否加密（简单判断）
                if device.cli_password_encrypted and len(device.cli_password_encrypted) > 50:
                    encrypted_passwords += 1

            return {
                "total_devices": total_devices,
                "devices_with_credentials": devices_with_credentials,
                "devices_with_enable_password": devices_with_enable_password,
                "encrypted_passwords": encrypted_passwords,
                "credential_coverage": f"{devices_with_credentials / total_devices * 100:.1f}%"
                if total_devices
                else "0%",
            }

        except Exception as e:
            logger.error(f"获取凭据统计失败: {e}")
            raise BusinessError(f"凭据统计失败: {str(e)}") from e

    async def clear_otp_cache(self, device_id: UUID | None = None) -> dict[str, Any]:
        """清除OTP缓存

        Args:
            device_id: 指定设备ID，如果为None则清除所有

        Returns:
            清除结果
        """
        try:
            # 简化版本，直接返回模拟结果
            # TODO: 在后续版本中实现真正的OTP缓存清除
            if device_id:
                logger.info(f"清除设备 {device_id} 的OTP缓存")
                cleared_count = 1
            else:
                logger.info("清除所有OTP缓存")
                cleared_count = 0  # 当前没有OTP缓存

            return {
                "cleared_count": cleared_count,
                "device_id": str(device_id) if device_id else "all",
                "status": "cleared",
            }

        except Exception as e:
            logger.error(f"清除OTP缓存失败: {e}")
            raise BusinessError(f"清除OTP缓存失败: {str(e)}") from e
