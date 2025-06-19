"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: middleware.py
@DateTime: 2025/03/08 04:40:00
@Docs: 应用程序中间件
"""

import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.utils.logger import logger


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志

        Args:
            request (Request): 请求对象
            call_next (Callable): 下一个中间件

        Returns:
            Response: 响应对象
        """
        # 记录请求开始时间
        start_time = time.time()

        # 获取请求信息
        # 获取或生成请求ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else ""

        # 记录请求日志
        logger.info(f"Request started: {method} {url} from {client_host} [ID: {request_id}]")

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应日志
            logger.info(
                f"Request completed: {method} {url} [ID: {request_id}] "
                f"- Status: {response.status_code} - Time: {process_time:.4f}s"
            )

            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)

            return response
        except Exception as e:
            # 记录错误日志
            logger.error(f"Request failed: {method} {url} [ID: {request_id}] - Error: {str(e)}")
            # 重新抛出异常，让异常处理中间件处理
            raise


def setup_middlewares(app: FastAPI) -> None:
    """设置中间件

    Args:
        app (FastAPI): FastAPI应用实例
    """
    # CORS中间件
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],  # 生产环境中建议指定具体方法，例如: ["GET", "POST", "PUT", "DELETE"]
            allow_headers=["*"],  # 生产环境中建议指定具体头部，例如: ["Content-Type", "Authorization"]
        )

    # Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 请求日志中间件
    app.add_middleware(RequestLoggerMiddleware)

    # 可以根据需要添加更多中间件，如：
    # - TrustedHostMiddleware：限制请求的主机
    # - HTTPSRedirectMiddleware：强制使用HTTPS
    # - AuthenticationMiddleware：认证中间件
    # - SessionMiddleware：会话中间件
