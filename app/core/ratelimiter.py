"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: ratelimiter.py
@DateTime: 2025/06/20 09:10:58
@Docs: 简单全局IP限流中间件（每IP每分钟50次）
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import settings

# 内存限流存储（生产建议用Redis等分布式存储）
_rate_limit_data = defaultdict(list)
_rate_limit_lock = Lock()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    全局IP限流中间件，每IP每分钟最多50次
    """

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = settings.RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = settings.RATE_LIMIT_WINDOW,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        now = int(time.time())
        with _rate_limit_lock:
            timestamps = _rate_limit_data[client_ip]
            # 移除窗口外的请求
            valid_timestamps = [ts for ts in timestamps if now - ts < self.window]
            valid_timestamps.append(now)
            _rate_limit_data[client_ip] = valid_timestamps
            if len(valid_timestamps) > self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": 429,
                        "message": f"请求过于频繁，请稍后再试（每分钟限{self.max_requests}次）",
                        "success": False,
                    },
                )
        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
