"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/20 00:00:00
@Docs: 服务层模块初始化和统一导出
"""

from .base_service import BaseService
from .brand_service import BrandService
from .device_group_service import DeviceGroupService
from .device_model_service import DeviceModelService
from .device_service import DeviceService
from .operation_log_service import OperationLogService
from .region_service import RegionService

__all__ = [
    "BaseService",
    "RegionService",
    "BrandService",
    "DeviceGroupService",
    "DeviceModelService",
    "DeviceService",
    "OperationLogService",
]

# 服务层使用说明：
# 1. 所有服务都继承自BaseService，提供统一的CRUD操作
# 2. 严格使用项目定义的Schema进行数据验证
# 3. 集成操作日志装饰器和异常处理
# 4. 支持分页、批量操作、业务校验等功能
#
# 使用示例：
# from app.services import DeviceService
# from app.repositories.device_dao import DeviceDAO
#
# device_dao = DeviceDAO()
# device_service = DeviceService(device_dao)
#
# # 执行业务操作
# result = await device_service.create(device_data)
