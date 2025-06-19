"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/20 00:00:00
@Docs: 模型模块初始化，导出所有模型类
"""

from .network_models import (
    # 基础模型
    BaseModel,
    Brand,
    ConfigDiff,
    ConfigSnapshot,
    ConfigTemplate,
    Device,
    DeviceConnectionStatus,
    DeviceGroup,
    DeviceModel,
    DeviceStatusEnum,
    # 枚举类
    DeviceTypeEnum,
    OperationLog,
    OperationStatusEnum,
    # 业务模型
    Region,
    RollbackOperation,
    RollbackStatusEnum,
    SnapshotTypeEnum,
    TemplateCommand,
    TemplateTypeEnum,
)

__all__ = [
    # 枚举类
    "DeviceTypeEnum",
    "DeviceStatusEnum",
    "OperationStatusEnum",
    "SnapshotTypeEnum",
    "RollbackStatusEnum",
    "TemplateTypeEnum",
    # 基础模型
    "BaseModel",
    # 业务模型
    "Region",
    "Brand",
    "DeviceModel",
    "DeviceGroup",
    "Device",
    "ConfigTemplate",
    "TemplateCommand",
    "OperationLog",
    "DeviceConnectionStatus",
    "ConfigSnapshot",
    "ConfigDiff",
    "RollbackOperation",
]
