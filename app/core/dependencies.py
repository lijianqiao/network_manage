"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: dependencies.py
@DateTime: 2025/06/20 00:00:00
@Docs: 服务依赖注入容器
"""

from functools import lru_cache

from app.repositories.brand_dao import BrandDAO
from app.repositories.device_dao import DeviceDAO
from app.repositories.device_group_dao import DeviceGroupDAO
from app.repositories.device_model_dao import DeviceModelDAO
from app.repositories.operation_log_dao import OperationLogDAO
from app.repositories.region_dao import RegionDAO
from app.services.brand_service import BrandService
from app.services.device_group_service import DeviceGroupService
from app.services.device_model_service import DeviceModelService
from app.services.device_service import DeviceService

# from app.services.import_export_service import ImportExportService
from app.services.operation_log_service import OperationLogService
from app.services.region_service import RegionService


class ServiceContainer:
    """服务容器，管理所有服务实例"""

    def __init__(self):
        """初始化服务容器"""
        self._dao_instances = {}
        self._service_instances = {}

    def get_region_dao(self) -> RegionDAO:
        """获取区域DAO实例"""
        if "region_dao" not in self._dao_instances:
            self._dao_instances["region_dao"] = RegionDAO()
        return self._dao_instances["region_dao"]

    def get_brand_dao(self) -> BrandDAO:
        """获取品牌DAO实例"""
        if "brand_dao" not in self._dao_instances:
            self._dao_instances["brand_dao"] = BrandDAO()
        return self._dao_instances["brand_dao"]

    def get_device_model_dao(self) -> DeviceModelDAO:
        """获取设备型号DAO实例"""
        if "device_model_dao" not in self._dao_instances:
            self._dao_instances["device_model_dao"] = DeviceModelDAO()
        return self._dao_instances["device_model_dao"]

    def get_device_group_dao(self) -> DeviceGroupDAO:
        """获取设备组DAO实例"""
        if "device_group_dao" not in self._dao_instances:
            self._dao_instances["device_group_dao"] = DeviceGroupDAO()
        return self._dao_instances["device_group_dao"]

    def get_device_dao(self) -> DeviceDAO:
        """获取设备DAO实例"""
        if "device_dao" not in self._dao_instances:
            self._dao_instances["device_dao"] = DeviceDAO()
        return self._dao_instances["device_dao"]

    def get_operation_log_dao(self) -> OperationLogDAO:
        """获取操作日志DAO实例"""
        if "operation_log_dao" not in self._dao_instances:
            self._dao_instances["operation_log_dao"] = OperationLogDAO()
        return self._dao_instances["operation_log_dao"]

    def get_region_service(self) -> RegionService:
        """获取区域服务实例"""
        if "region_service" not in self._service_instances:
            self._service_instances["region_service"] = RegionService(self.get_region_dao())
        return self._service_instances["region_service"]

    def get_brand_service(self) -> BrandService:
        """获取品牌服务实例"""
        if "brand_service" not in self._service_instances:
            self._service_instances["brand_service"] = BrandService(self.get_brand_dao())
        return self._service_instances["brand_service"]

    def get_device_model_service(self) -> DeviceModelService:
        """获取设备型号服务实例"""
        if "device_model_service" not in self._service_instances:
            self._service_instances["device_model_service"] = DeviceModelService(self.get_device_model_dao())
        return self._service_instances["device_model_service"]

    def get_device_group_service(self) -> DeviceGroupService:
        """获取设备组服务实例"""
        if "device_group_service" not in self._service_instances:
            self._service_instances["device_group_service"] = DeviceGroupService(self.get_device_group_dao())
        return self._service_instances["device_group_service"]

    def get_device_service(self) -> DeviceService:
        """获取设备服务实例"""
        if "device_service" not in self._service_instances:
            self._service_instances["device_service"] = DeviceService(self.get_device_dao())
        return self._service_instances["device_service"]

    def get_operation_log_service(self) -> OperationLogService:
        """获取操作日志服务实例"""
        if "operation_log_service" not in self._service_instances:
            self._service_instances["operation_log_service"] = OperationLogService(self.get_operation_log_dao())
        return self._service_instances["operation_log_service"]

    # def get_import_export_service(self) -> ImportExportService:
    #     """获取导入导出服务实例"""
    #     if "import_export_service" not in self._service_instances:
    #         self._service_instances["import_export_service"] = ImportExportService()
    #     return self._service_instances["import_export_service"]


# 全局服务容器实例
@lru_cache
def get_service_container() -> ServiceContainer:
    """获取服务容器单例"""
    return ServiceContainer()


# FastAPI依赖注入函数
def get_region_service() -> RegionService:
    """获取区域服务依赖"""
    return get_service_container().get_region_service()


def get_brand_service() -> BrandService:
    """获取品牌服务依赖"""
    return get_service_container().get_brand_service()


def get_device_model_service() -> DeviceModelService:
    """获取设备型号服务依赖"""
    return get_service_container().get_device_model_service()


def get_device_group_service() -> DeviceGroupService:
    """获取设备组服务依赖"""
    return get_service_container().get_device_group_service()


def get_device_service() -> DeviceService:
    """获取设备服务依赖"""
    return get_service_container().get_device_service()


def get_operation_log_service() -> OperationLogService:
    """获取操作日志服务依赖"""
    return get_service_container().get_operation_log_service()


# def get_import_export_service() -> ImportExportService:
#     """获取导入导出服务依赖"""
#     return get_service_container().get_import_export_service()
