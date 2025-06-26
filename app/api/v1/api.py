"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: api.py
@DateTime: 2025/06/20 00:00:00
@Docs: API路由汇总模块
"""

from fastapi import APIRouter

from app.api.v1.endpoints.advanced_network_operations import router as advanced_operations_router
from app.api.v1.endpoints.brands import router as brands_router
from app.api.v1.endpoints.config_templates import router as config_templates_router
from app.api.v1.endpoints.device_connection_status import router as connection_status_router
from app.api.v1.endpoints.device_groups import router as device_groups_router
from app.api.v1.endpoints.device_models import router as device_models_router
from app.api.v1.endpoints.devices import router as devices_router
from app.api.v1.endpoints.network_automation import router as automation_router
from app.api.v1.endpoints.operation_logs import router as operation_logs_router
from app.api.v1.endpoints.parser_management import router as parser_management_router
from app.api.v1.endpoints.performance_management import router as performance_router
from app.api.v1.endpoints.regions import router as regions_router
from app.api.v1.endpoints.template_commands import router as template_commands_router
from app.api.v1.endpoints.universal_import_export import router as import_export_router
from app.api.v1.endpoints.websocket_cli import router as websocket_cli_router

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

# 配置模板系统路由
api_router.include_router(config_templates_router)
api_router.include_router(template_commands_router)

# 凭据管理与连接状态路由
api_router.include_router(connection_status_router)

# 网络自动化路由
api_router.include_router(automation_router)

# 解析器管理路由
api_router.include_router(parser_management_router)

# 性能管理路由
api_router.include_router(performance_router)

# 高级网络操作路由
api_router.include_router(advanced_operations_router)

# WebSocket CLI交互路由
api_router.include_router(websocket_cli_router)
