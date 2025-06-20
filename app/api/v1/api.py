"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: api.py
@DateTime: 2025/06/20 00:00:00
@Docs: API路由汇总模块
"""

from fastapi import APIRouter

from app.api.v1.endpoints.brands import router as brands_router
from app.api.v1.endpoints.device_groups import router as device_groups_router
from app.api.v1.endpoints.device_models import router as device_models_router
from app.api.v1.endpoints.devices import router as devices_router
from app.api.v1.endpoints.import_export import router as import_export_router
from app.api.v1.endpoints.operation_logs import router as operation_logs_router
from app.api.v1.endpoints.regions import router as regions_router

# 创建API路由器
api_router = APIRouter()

# 注册所有端点路由
api_router.include_router(regions_router)
api_router.include_router(brands_router)
api_router.include_router(device_models_router)
api_router.include_router(device_groups_router)
api_router.include_router(devices_router)
api_router.include_router(operation_logs_router)
api_router.include_router(import_export_router)
