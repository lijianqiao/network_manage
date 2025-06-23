"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: credential_manager.py
@DateTime: 2025/06/23 00:00:00
@Docs: 设备连接凭据管理器
"""

from uuid import UUID

from app.models.network_models import Device
from app.utils.logger import logger
from app.utils.password_encryption import decrypt_password, is_encrypted_password


class CredentialManager:
    """凭据管理器

    管理设备连接的账号密码逻辑：
    - 支持动态密码输入（OTP）
    - 支持Enable密码处理
    - 实现凭据优先级决策
    """

    def __init__(self):
        """初始化凭据管理器"""
        # OTP密码缓存（一次性使用后立即清除）
        self._otp_cache: dict[str, str] = {}

    async def resolve_device_credentials(
        self, device: Device, user_provided_credentials: dict[str, str] | None = None
    ) -> dict[str, str]:
        """解析设备连接凭据

        Args:
            device: 设备对象
            user_provided_credentials: 用户提供的凭据
                格式: {
                    "username": "用户名",
                    "password": "密码",
                    "enable_password": "Enable密码"
                }

        Returns:
            解析后的凭据字典
            格式: {
                "hostname": "设备IP",
                "username": "用户名",
                "password": "密码",
                "enable_password": "Enable密码",
                "platform": "设备平台",
                "port": 22
            }

        Raises:
            ValueError: 当无法获取必要凭据时
        """
        try:
            # 预加载关联数据
            await device.fetch_related("region", "model__brand")

            credentials = {
                "hostname": device.ip_address,
                "port": 22,  # 默认SSH端口
                "platform": device.model.brand.platform_type,
            }

            # 解析用户名
            username = self._resolve_username(device, user_provided_credentials)
            credentials["username"] = username

            # 解析密码
            password = await self._resolve_password(device, user_provided_credentials)
            credentials["password"] = password

            # 解析Enable密码
            enable_password = await self._resolve_enable_password(device, user_provided_credentials)
            if enable_password:
                credentials["enable_password"] = enable_password

            logger.info(f"成功解析设备凭据: {device.ip_address} (用户: {username})")
            return credentials

        except Exception as e:
            logger.error(f"解析设备凭据失败 {device.ip_address}: {e}")
            raise

    def _resolve_username(self, device: Device, user_credentials: dict[str, str] | None) -> str:
        """解析用户名

        优先级：
        1. 用户请求中提供
        2. 设备配置的固定账号
        3. 区域默认账号

        Args:
            device: 设备对象
            user_credentials: 用户提供的凭据

        Returns:
            用户名

        Raises:
            ValueError: 当无法获取用户名时
        """
        # 1. 用户请求中提供
        if user_credentials and user_credentials.get("username"):
            return user_credentials["username"]

        # 2. 设备配置的固定账号
        if not device.is_dynamic_password and device.cli_username:
            return device.cli_username

        # 3. 区域默认账号
        if device.region and device.region.default_cli_username:
            return device.region.default_cli_username

        raise ValueError(f"无法获取设备 {device.ip_address} 的登录用户名")

    async def _resolve_password(self, device: Device, user_credentials: dict[str, str] | None) -> str:
        """解析密码

        优先级：
        1. 用户请求中提供（OTP或固定密码）
        2. 设备数据库中存储的固定密码
        3. 提示用户输入OTP密码

        Args:
            device: 设备对象
            user_credentials: 用户提供的凭据

        Returns:
            密码

        Raises:
            ValueError: 当无法获取密码时
        """
        # 1. 用户请求中提供
        if user_credentials and user_credentials.get("password"):
            password = user_credentials["password"]

            # 如果是动态密码设备，将OTP密码缓存（一次性使用）
            if device.is_dynamic_password:
                cache_key = f"otp_{device.id}"
                self._otp_cache[cache_key] = password
                logger.debug(f"缓存设备 {device.ip_address} 的OTP密码")

            return password

        # 2. 设备数据库中存储的固定密码
        if not device.is_dynamic_password and device.cli_password_encrypted:
            try:
                if is_encrypted_password(device.cli_password_encrypted):
                    password = decrypt_password(device.cli_password_encrypted)
                    logger.debug(f"使用设备 {device.ip_address} 的存储密码")
                    return password
                else:
                    # 如果密码未加密，直接返回（兼容旧数据）
                    logger.warning(f"设备 {device.ip_address} 的密码未加密，建议重新保存")
                    return device.cli_password_encrypted
            except Exception as e:
                logger.error(f"解密设备 {device.ip_address} 密码失败: {e}")

        # 3. 动态密码设备需要用户输入OTP
        if device.is_dynamic_password:
            raise ValueError("无法获取连接密码。该设备使用动态密码，请提供一次性OTP密码。")

        # 4. 固定密码设备但未配置密码
        raise ValueError(f"设备 {device.ip_address} 未配置登录密码，请提供密码或在设备设置中配置。")

    async def _resolve_enable_password(self, device: Device, user_credentials: dict[str, str] | None) -> str | None:
        """解析Enable密码

        优先级：
        1. 用户请求中提供
        2. 设备配置的enable密码
        3. 区域默认enable密码

        Args:
            device: 设备对象
            user_credentials: 用户提供的凭据

        Returns:
            Enable密码（可能为None）
        """
        # 1. 用户请求中提供
        if user_credentials and user_credentials.get("enable_password"):
            return user_credentials["enable_password"]

        # 2. 设备配置的enable密码
        if device.enable_password_encrypted:
            try:
                if is_encrypted_password(device.enable_password_encrypted):
                    enable_password = decrypt_password(device.enable_password_encrypted)
                    logger.debug(f"使用设备 {device.ip_address} 的存储Enable密码")
                    return enable_password
                else:
                    # 如果密码未加密，直接返回（兼容旧数据）
                    logger.warning(f"设备 {device.ip_address} 的Enable密码未加密，建议重新保存")
                    return device.enable_password_encrypted
            except Exception as e:
                logger.error(f"解密设备 {device.ip_address} Enable密码失败: {e}")

        # 3. 区域默认enable密码（如果实现了的话）
        # 注意：当前数据模型中区域表没有default_enable_password字段
        # 如果需要可以扩展Region模型

        return None

    def clear_otp_cache(self, device_id: UUID) -> int:
        """清除OTP密码缓存

        Args:
            device_id: 设备ID

        Returns:
            清除的缓存数量
        """
        cache_key = f"otp_{device_id}"
        if cache_key in self._otp_cache:
            del self._otp_cache[cache_key]
            logger.debug(f"已清除设备 {device_id} 的OTP密码缓存")
            return 1
        return 0

    def clear_all_otp_passwords(self) -> int:
        """清除所有OTP密码缓存

        Returns:
            清除的缓存数量
        """
        count = len(self._otp_cache)
        self._otp_cache.clear()
        logger.debug(f"已清除所有OTP密码缓存，共 {count} 个")
        return count

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """验证凭据格式

        Args:
            credentials: 凭据字典

        Returns:
            是否有效
        """
        required_fields = ["hostname", "username", "password", "platform"]

        for field in required_fields:
            if field not in credentials or not credentials[field]:
                logger.error(f"凭据缺少必要字段: {field}")
                return False

        return True

    async def get_connection_info(self, device_id: UUID) -> dict[str, str | bool]:
        """获取设备连接信息（不包含敏感信息）

        Args:
            device_id: 设备ID

        Returns:
            连接信息字典
        """
        try:
            device = await Device.get(id=device_id).prefetch_related("region", "model__brand")

            return {
                "hostname": device.ip_address,
                "username": (
                    device.cli_username
                    if not device.is_dynamic_password
                    else device.region.default_cli_username
                    if device.region
                    else "未配置"
                ),
                "password_type": "动态密码(OTP)" if device.is_dynamic_password else "固定密码",
                "has_enable_password": bool(device.enable_password_encrypted),
                "platform": device.model.brand.platform_type,
                "is_dynamic_password": device.is_dynamic_password,
            }

        except Exception as e:
            logger.error(f"获取设备连接信息失败 {device_id}: {e}")
            raise

    def get_credential_requirements(self, device: Device) -> dict[str, bool]:
        """获取设备凭据需求

        Args:
            device: 设备对象

        Returns:
            凭据需求字典
        """
        return {
            "requires_username": not (device.cli_username or device.region.default_cli_username),
            "requires_password": device.is_dynamic_password or not device.cli_password_encrypted,
            "requires_enable_password": False,  # Enable密码通常是可选的
            "is_dynamic_password": device.is_dynamic_password,
        }


# 全局凭据管理器实例
credential_manager = CredentialManager()
