"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: exceptions.py
@DateTime: 2025/03/08 04:45:00
@Docs: 应用程序异常处理
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, IntegrityError

from app.core.config import settings
from app.utils.logger import logger


class APIException(Exception):
    """API异常基类"""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "服务器内部错误",
        detail: str | dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(APIException):
    """资源不存在异常"""

    def __init__(
        self,
        message: str = "请求的资源不存在",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            detail=detail,
        )


class BadRequestException(APIException):
    """错误请求异常"""

    def __init__(
        self,
        message: str = "请求参数错误",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            detail=detail,
        )


class UnauthorizedException(APIException):
    """未授权异常"""

    def __init__(
        self,
        message: str = "未授权访问",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            detail=detail,
        )


class ForbiddenException(APIException):
    """禁止访问异常"""

    def __init__(
        self,
        message: str = "禁止访问",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            detail=detail,
        )


# 服务层业务异常类
class BusinessError(APIException):
    """业务逻辑错误异常"""

    def __init__(
        self,
        message: str = "业务逻辑错误",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            detail=detail,
        )


# 网络自动化相关异常类
class NetworkDeviceException(APIException):
    """网络设备异常基类"""

    def __init__(
        self,
        message: str = "网络设备操作失败",
        detail: str | dict[str, Any] | None = None,
        device_id: str | None = None,
        device_ip: str | None = None,
    ):
        self.device_id = device_id
        self.device_ip = device_ip
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
        )


class DeviceConnectionError(NetworkDeviceException):
    """设备连接异常"""

    def __init__(
        self,
        message: str = "设备连接失败",
        detail: str | dict[str, Any] | None = None,
        device_id: str | None = None,
        device_ip: str | None = None,
        timeout: int | None = None,
    ):
        self.timeout = timeout
        super().__init__(
            message=message,
            detail=detail,
            device_id=device_id,
            device_ip=device_ip,
        )


class DeviceAuthenticationError(NetworkDeviceException):
    """设备认证异常"""

    def __init__(
        self,
        message: str = "设备认证失败",
        detail: str | dict[str, Any] | None = None,
        device_id: str | None = None,
        device_ip: str | None = None,
        username: str | None = None,
    ):
        self.username = username
        super().__init__(
            message=message,
            detail=detail,
            device_id=device_id,
            device_ip=device_ip,
        )


class CommandExecutionError(NetworkDeviceException):
    """命令执行异常"""

    def __init__(
        self,
        message: str = "命令执行失败",
        detail: str | dict[str, Any] | None = None,
        device_id: str | None = None,
        device_ip: str | None = None,
        command: str | None = None,
        error_output: str | None = None,
    ):
        self.command = command
        self.error_output = error_output
        super().__init__(
            message=message,
            detail=detail,
            device_id=device_id,
            device_ip=device_ip,
        )


class ConfigTemplateError(APIException):
    """配置模板异常"""

    def __init__(
        self,
        message: str = "配置模板错误",
        detail: str | dict[str, Any] | None = None,
        template_id: str | None = None,
        template_name: str | None = None,
    ):
        self.template_id = template_id
        self.template_name = template_name
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            detail=detail,
        )


class ConfigTemplateNotFoundError(ConfigTemplateError):
    """配置模板未找到异常"""

    def __init__(
        self,
        message: str = "配置模板未找到",
        detail: str | dict[str, Any] | None = None,
        template_id: str | None = None,
        template_name: str | None = None,
    ):
        super().__init__(
            message=message,
            detail=detail,
            template_id=template_id,
            template_name=template_name,
        )


class ConfigTemplateRenderError(ConfigTemplateError):
    """配置模板渲染异常"""

    def __init__(
        self,
        message: str = "配置模板渲染失败",
        detail: str | dict[str, Any] | None = None,
        template_id: str | None = None,
        template_name: str | None = None,
        render_variables: dict[str, Any] | None = None,
    ):
        self.render_variables = render_variables
        super().__init__(
            message=message,
            detail=detail,
            template_id=template_id,
            template_name=template_name,
        )


class ConfigDeploymentError(NetworkDeviceException):
    """配置部署异常"""

    def __init__(
        self,
        message: str = "配置部署失败",
        detail: str | dict[str, Any] | None = None,
        device_id: str | None = None,
        device_ip: str | None = None,
        config_content: str | None = None,
    ):
        self.config_content = config_content
        super().__init__(
            message=message,
            detail=detail,
            device_id=device_id,
            device_ip=device_ip,
        )


class ConfigBackupError(NetworkDeviceException):
    """配置备份异常"""

    def __init__(
        self,
        message: str = "配置备份失败",
        detail: str | dict[str, Any] | None = None,
        device_id: str | None = None,
        device_ip: str | None = None,
        backup_type: str | None = None,
    ):
        self.backup_type = backup_type
        super().__init__(
            message=message,
            detail=detail,
            device_id=device_id,
            device_ip=device_ip,
        )


class TextFSMParsingError(APIException):
    """TextFSM解析异常"""

    def __init__(
        self,
        message: str = "命令输出解析失败",
        detail: str | dict[str, Any] | None = None,
        command: str | None = None,
        brand: str | None = None,
        template_name: str | None = None,
    ):
        self.command = command
        self.brand = brand
        self.template_name = template_name
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
        )


class CredentialManagerError(APIException):
    """凭据管理异常"""

    def __init__(
        self,
        message: str = "凭据管理操作失败",
        detail: str | dict[str, Any] | None = None,
        operation: str | None = None,
    ):
        self.operation = operation
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
        )


class InventoryManagerError(APIException):
    """清单管理异常"""

    def __init__(
        self,
        message: str = "设备清单管理失败",
        detail: str | dict[str, Any] | None = None,
        operation: str | None = None,
    ):
        self.operation = operation
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
        )


class ValidationError(APIException):
    """数据验证错误异常"""

    def __init__(
        self,
        message: str = "数据验证失败",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            detail=detail,
        )


class DuplicateError(APIException):
    """数据重复异常"""

    def __init__(
        self,
        message: str = "数据重复",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            detail=detail,
        )


class NotFoundError(APIException):
    """资源不存在异常"""

    def __init__(
        self,
        message: str = "资源不存在",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            detail=detail,
        )


class ConflictException(APIException):
    """资源冲突异常"""

    def __init__(
        self,
        message: str = "资源冲突",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            detail=detail,
        )


async def network_device_exception_handler(request: Request, exc: NetworkDeviceException) -> Response:
    """网络设备异常处理器

    Args:
        request (Request): 请求对象
        exc (NetworkDeviceException): 网络设备异常

    Returns:
        Response: HTTP响应
    """
    # 构建详细的错误信息用于日志记录
    error_context = {
        "exception_type": exc.__class__.__name__,
        "message": exc.message,
        "device_id": getattr(exc, 'device_id', None),
        "device_ip": getattr(exc, 'device_ip', None),
        "command": getattr(exc, 'command', None),
        "username": getattr(exc, 'username', None),
        "timeout": getattr(exc, 'timeout', None),
        "operation": getattr(exc, 'operation', None),
    }
    
    # 过滤掉None值
    error_context = {k: v for k, v in error_context.items() if v is not None}
    
    logger.error(
        f"网络设备操作异常: {exc.message}",
        **error_context
    )
    
    # 构建响应内容
    response_content = {
        "code": exc.status_code,
        "message": exc.message,
        "detail": exc.detail,
        "error_type": "network_device_error",
    }
    
    # 在开发环境下添加更多调试信息
    if settings.DEBUG:
        response_content["debug_info"] = error_context
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
    )


async def config_template_exception_handler(request: Request, exc: ConfigTemplateError) -> Response:
    """配置模板异常处理器

    Args:
        request (Request): 请求对象
        exc (ConfigTemplateError): 配置模板异常

    Returns:
        Response: HTTP响应
    """
    error_context = {
        "exception_type": exc.__class__.__name__,
        "message": exc.message,
        "template_id": getattr(exc, 'template_id', None),
        "template_name": getattr(exc, 'template_name', None),
        "render_variables": getattr(exc, 'render_variables', None),
    }
    
    # 过滤掉None值
    error_context = {k: v for k, v in error_context.items() if v is not None}
    
    logger.error(
        f"配置模板操作异常: {exc.message}",
        **error_context
    )
    
    response_content = {
        "code": exc.status_code,
        "message": exc.message,
        "detail": exc.detail,
        "error_type": "config_template_error",
    }
    
    if settings.DEBUG:
        response_content["debug_info"] = error_context
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
    )


async def textfsm_parsing_exception_handler(request: Request, exc: TextFSMParsingError) -> Response:
    """TextFSM解析异常处理器

    Args:
        request (Request): 请求对象
        exc (TextFSMParsingError): TextFSM解析异常

    Returns:
        Response: HTTP响应
    """
    error_context = {
        "exception_type": exc.__class__.__name__,
        "message": exc.message,
        "command": getattr(exc, 'command', None),
        "brand": getattr(exc, 'brand', None),
        "template_name": getattr(exc, 'template_name', None),
    }
    
    # 过滤掉None值
    error_context = {k: v for k, v in error_context.items() if v is not None}
    
    logger.error(
        f"TextFSM解析异常: {exc.message}",
        **error_context
    )
    
    response_content = {
        "code": exc.status_code,
        "message": exc.message,
        "detail": exc.detail,
        "error_type": "textfsm_parsing_error",
    }
    
    if settings.DEBUG:
        response_content["debug_info"] = error_context
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
    )


async def api_exception_handler(request: Request, exc: APIException) -> Response:
    """API异常处理器

    Args:
        request (Request): 请求对象
        exc (APIException): API异常

    Returns:
        Response: HTTP响应
    """
    logger.error(f"API异常: {exc.message} - 详细信息: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError | PydanticValidationError
) -> Response:
    """验证异常处理器

    Args:
        request (Request): 请求对象
        exc (Union[RequestValidationError, ValidationError]): 验证异常

    Returns:
        Response: HTTP响应
    """
    error_details = []
    for error in exc.errors():
        error_details.append(
            {
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", ""),
            }
        )

    logger.error(f"验证异常: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "请求数据验证失败",
            "detail": error_details,
        },
    )


async def tortoise_not_found_exception_handler(request: Request, exc: DoesNotExist) -> Response:
    """Tortoise ORM 数据不存在异常处理器

    Args:
        request (Request): 请求对象
        exc (DoesNotExist): 数据不存在异常

    Returns:
        Response: HTTP响应
    """
    logger.error(f"数据不存在异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "code": status.HTTP_404_NOT_FOUND,
            "message": "请求的资源不存在",
            "detail": str(exc),
        },
    )


async def tortoise_integrity_error_handler(request: Request, exc: IntegrityError) -> Response:
    """Tortoise ORM 完整性约束异常处理器

    Args:
        request (Request): 请求对象
        exc (IntegrityError): 完整性约束异常

    Returns:
        Response: HTTP响应
    """
    logger.error(f"数据完整性异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": status.HTTP_409_CONFLICT,
            "message": "数据完整性约束冲突",
            "detail": str(exc),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> Response:
    """通用异常处理器

    Args:
        request (Request): 请求对象
        exc (Exception): 异常

    Returns:
        Response: HTTP响应
    """
    logger.exception(f"未处理的异常: {str(exc)}")
    error_message = "服务器内部错误"
    error_detail = None
    if settings.DEBUG:
        error_detail = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": error_message,
            "detail": error_detail,
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """设置异常处理器

    Args:
        app (FastAPI): FastAPI应用实例
    """
    # 网络自动化相关异常处理器（需要在APIException之前注册）
    app.add_exception_handler(NetworkDeviceException, network_device_exception_handler)  # type: ignore
    app.add_exception_handler(ConfigTemplateError, config_template_exception_handler)  # type: ignore
    app.add_exception_handler(TextFSMParsingError, textfsm_parsing_exception_handler)  # type: ignore
    
    # 通用异常处理器
    app.add_exception_handler(APIException, api_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(DoesNotExist, tortoise_not_found_exception_handler)  # type: ignore
    app.add_exception_handler(IntegrityError, tortoise_integrity_error_handler)  # type: ignore
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore
