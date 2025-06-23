"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: password_encryption.py
@DateTime: 2025/06/23 00:00:00
@Docs: 密码加密管理工具
"""

import base64

from cryptography.fernet import Fernet

from app.core.config import settings
from app.utils.logger import logger


class PasswordEncryption:
    """密码加密管理器

    使用Fernet对称加密来安全存储和管理密码
    """

    def __init__(self):
        """初始化加密管理器"""
        self._fernet: Fernet | None = None
        self._key: bytes | None = None
        self._init_encryption_key()

    def _init_encryption_key(self):
        """初始化加密密钥"""
        try:
            # 从环境变量或配置文件获取加密密钥
            encryption_key = getattr(settings, "ENCRYPTION_KEY", None)

            if encryption_key:
                # 使用配置的密钥，处理SecretStr类型
                if hasattr(encryption_key, "get_secret_value"):
                    key_str = encryption_key.get_secret_value()
                else:
                    key_str = str(encryption_key)
                self._key = base64.urlsafe_b64decode(key_str.encode())
            else:
                # 生成新密钥（仅用于开发环境）
                logger.warning("未找到加密密钥配置，生成临时密钥（生产环境请配置ENCRYPTION_KEY）")
                self._key = Fernet.generate_key()
                logger.info(f"临时加密密钥: {base64.urlsafe_b64encode(self._key).decode()}")

            self._fernet = Fernet(self._key)
            logger.info("密码加密管理器初始化成功")

        except Exception as e:
            logger.error(f"密码加密管理器初始化失败: {e}")
            raise

    def generate_key(self) -> str:
        """生成新的加密密钥

        Returns:
            Base64编码的密钥字符串
        """
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()

    def encrypt_password(self, password: str) -> str:
        """加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码（Base64编码）

        Raises:
            ValueError: 当密码为空时
            Exception: 加密失败时
        """
        if not password:
            raise ValueError("密码不能为空")

        try:
            # 将密码编码为字节
            password_bytes = password.encode("utf-8")

            # 加密密码
            if self._fernet is None:
                raise Exception("加密器未初始化")
            encrypted_bytes = self._fernet.encrypt(password_bytes)

            # 返回Base64编码的加密密码
            encrypted_password = base64.urlsafe_b64encode(encrypted_bytes).decode()

            logger.debug("密码加密成功")
            return encrypted_password

        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            raise Exception(f"密码加密失败: {str(e)}") from e

    def decrypt_password(self, encrypted_password: str) -> str:
        """解密密码

        Args:
            encrypted_password: 加密的密码（Base64编码）

        Returns:
            明文密码

        Raises:
            ValueError: 当加密密码为空时
            Exception: 解密失败时
        """
        if not encrypted_password:
            raise ValueError("加密密码不能为空")

        try:
            # 解码Base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())

            # 解密密码
            if self._fernet is None:
                raise Exception("加密器未初始化")
            password_bytes = self._fernet.decrypt(encrypted_bytes)

            # 返回明文密码
            password = password_bytes.decode("utf-8")

            logger.debug("密码解密成功")
            return password

        except Exception as e:
            logger.error(f"密码解密失败: {e}")
            raise Exception(f"密码解密失败: {str(e)}") from e

    def is_encrypted(self, password: str) -> bool:
        """检查字符串是否为加密密码

        Args:
            password: 待检查的密码字符串

        Returns:
            是否为加密密码
        """
        if not password:
            return False

        try:
            # 尝试解密来判断是否为加密密码
            self.decrypt_password(password)
            return True
        except Exception:
            return False

    def secure_compare(self, password1: str, password2: str) -> bool:
        """安全比较两个密码是否相同

        Args:
            password1: 密码1（可能是明文或密文）
            password2: 密码2（可能是明文或密文）

        Returns:
            是否相同
        """
        try:
            # 如果都是加密密码，直接比较
            if self.is_encrypted(password1) and self.is_encrypted(password2):
                return password1 == password2

            # 如果都是明文密码，直接比较
            if not self.is_encrypted(password1) and not self.is_encrypted(password2):
                return password1 == password2

            # 一个是加密，一个是明文，需要解密后比较
            if self.is_encrypted(password1):
                decrypted_password1 = self.decrypt_password(password1)
                return decrypted_password1 == password2
            else:
                decrypted_password2 = self.decrypt_password(password2)
                return password1 == decrypted_password2

        except Exception as e:
            logger.error(f"密码比较失败: {e}")
            return False


# 全局密码加密管理器实例
password_encryption = PasswordEncryption()


def encrypt_password(password: str) -> str:
    """加密密码的便捷函数

    Args:
        password: 明文密码

    Returns:
        加密后的密码
    """
    return password_encryption.encrypt_password(password)


def decrypt_password(encrypted_password: str) -> str:
    """解密密码的便捷函数

    Args:
        encrypted_password: 加密的密码

    Returns:
        明文密码
    """
    return password_encryption.decrypt_password(encrypted_password)


def is_encrypted_password(password: str) -> bool:
    """检查是否为加密密码的便捷函数

    Args:
        password: 待检查的密码

    Returns:
        是否为加密密码
    """
    return password_encryption.is_encrypted(password)
