"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_models.py
@DateTime: 2025/06/20 00:00:00
@Docs: 网络设备自动化平台数据模型定义
"""

import uuid
from enum import Enum

from tortoise import fields
from tortoise.models import Model


class DeviceTypeEnum(str, Enum):
    """设备类型枚举"""

    SWITCH = "switch"
    ROUTER = "router"


class DeviceStatusEnum(str, Enum):
    """设备在线状态枚举"""

    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class OperationStatusEnum(str, Enum):
    """操作执行状态枚举"""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class SnapshotTypeEnum(str, Enum):
    """配置快照类型枚举"""

    BACKUP = "backup"
    PRE_CHANGE = "pre_change"
    POST_CHANGE = "post_change"


class RollbackStatusEnum(str, Enum):
    """回滚状态枚举"""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class TemplateTypeEnum(str, Enum):
    """模板类型枚举"""

    QUERY = "query"
    CONFIG = "config"


class BaseModel(Model):
    """
    基础模型类

    所有业务模型的基类，提供通用字段：
    - id: 主键（UUID）
    - is_deleted: 软删除标记
    - description: 描述信息
    - created_at: 创建时间
    - updated_at: 更新时间
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4, description="主键")
    is_deleted = fields.BooleanField(default=False, description="软删除标记")
    description = fields.TextField(null=True, description="描述信息")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:  # type: ignore
        abstract = True


class Region(BaseModel):
    """
    区域表

    用于管理不同地区的网络设备分组：
    - name: 区域唯一名称（如"成都区域"）
    - snmp_community_string: 该区域SNMP社区字符串
    - default_cli_username: 区域内动态密码设备的默认CLI账号
    """

    name = fields.CharField(max_length=100, unique=True, description="区域唯一名称")
    snmp_community_string = fields.CharField(max_length=100, description="SNMP社区字符串")
    default_cli_username = fields.CharField(max_length=50, description="默认CLI账号名")

    class Meta:  # type: ignore
        table = "regions"
        table_description = "网络设备区域管理表"

    def __str__(self) -> str:
        return self.name


class Brand(BaseModel):
    """
    品牌表

    管理网络设备品牌信息：
    - name: 品牌唯一名称（如"H3C", "Huawei"）
    - platform_type: 对应Scrapli/Nornir的平台驱动类型
    """

    name = fields.CharField(max_length=50, unique=True, description="品牌唯一名称")
    platform_type = fields.CharField(max_length=50, unique=True, description="平台驱动类型")

    class Meta:  # type: ignore
        table = "brands"
        table_description = "网络设备品牌表"

    def __str__(self) -> str:
        return self.name


class DeviceModel(BaseModel):
    """
    设备型号表

    管理具体的设备型号信息：
    - name: 设备型号唯一名称（如"S5700", "CE12800"）
    - brand: 关联品牌表
    """

    name = fields.CharField(max_length=100, unique=True, description="设备型号唯一名称")
    brand = fields.ForeignKeyField("models.Brand", related_name="device_models", description="关联品牌")

    class Meta:  # type: ignore
        table = "device_models"
        table_description = "网络设备型号表"

    def __str__(self) -> str:
        return f"{self.brand.name} {self.name}" if hasattr(self, "brand") else self.name


class DeviceGroup(BaseModel):
    """
    设备分组表

    用于对设备进行逻辑分组：
    - name: 分组唯一名称（如"核心交换机"）
    - region: 可选关联区域
    """

    name = fields.CharField(max_length=100, unique=True, description="分组唯一名称")
    region = fields.ForeignKeyField("models.Region", related_name="device_groups", null=True, description="关联区域")

    class Meta:  # type: ignore
        table = "device_groups"
        table_description = "设备分组表"

    def __str__(self) -> str:
        return self.name


class Device(BaseModel):
    """
    设备表

    核心设备信息管理：
    - name: 设备唯一主机名
    - ip_address: 设备管理IP地址
    - region: 设备所属区域
    - device_group: 设备所属分组
    - model: 设备型号
    - device_type: 设备类型（交换机/路由器）
    - serial_number: 设备序列号
    - is_dynamic_password: 是否使用动态密码
    - cli_username: 固定CLI账号（当不使用动态密码时）
    - cli_password_encrypted: 加密存储的固定密码
    - enable_password_encrypted: 加密存储的enable密码
    - status: 设备当前在线状态
    - extra_info: 扩展信息（JSON格式）
    """

    name = fields.CharField(max_length=100, unique=True, description="设备唯一主机名")
    ip_address = fields.CharField(max_length=45, unique=True, description="设备管理IP地址")
    region = fields.ForeignKeyField("models.Region", related_name="devices", description="设备所属区域")
    device_group = fields.ForeignKeyField("models.DeviceGroup", related_name="devices", description="设备所属分组")
    model = fields.ForeignKeyField("models.DeviceModel", related_name="devices", description="设备型号")
    device_type = fields.CharEnumField(DeviceTypeEnum, description="设备类型")
    serial_number = fields.CharField(max_length=100, null=True, description="设备序列号")
    is_dynamic_password = fields.BooleanField(default=True, description="是否使用动态密码")
    cli_username = fields.CharField(max_length=50, null=True, description="固定CLI账号")
    cli_password_encrypted = fields.TextField(null=True, description="加密存储的固定密码")
    enable_password_encrypted = fields.TextField(null=True, description="加密存储的enable密码")
    status = fields.CharEnumField(DeviceStatusEnum, default=DeviceStatusEnum.UNKNOWN, description="设备在线状态")
    extra_info = fields.JSONField(null=True, description="扩展信息")

    class Meta:  # type: ignore
        table = "devices"
        table_description = "网络设备信息表"
        indexes = [
            ["ip_address", "region_id", "status"],  # 复合索引
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"


class ConfigTemplate(BaseModel):
    """
    配置模板表

    管理预设的配置和查询模板：
    - name: 模板唯一名称
    - template_type: 模板类型（查询/配置）
    - is_active: 是否启用
    """

    name = fields.CharField(max_length=100, unique=True, description="模板唯一名称")
    template_type = fields.CharEnumField(TemplateTypeEnum, description="模板类型")
    is_active = fields.BooleanField(default=True, description="是否启用")

    class Meta:  # type: ignore
        table = "config_templates"
        table_description = "配置模板表"

    def __str__(self) -> str:
        return self.name


class TemplateCommand(BaseModel):
    """
    模板命令表

    存储针对不同品牌的具体模板内容：
    - config_template: 关联配置模板
    - brand: 关联品牌
    - jinja_content: Jinja2模板内容
    - ttp_template: TTP解析模板
    - expected_params: 期望的参数列表（JSON格式）
    """

    config_template = fields.ForeignKeyField(
        "models.ConfigTemplate", related_name="template_commands", description="关联配置模板"
    )
    brand = fields.ForeignKeyField("models.Brand", related_name="template_commands", description="关联品牌")
    jinja_content = fields.TextField(description="Jinja2模板内容")
    ttp_template = fields.TextField(null=True, description="TTP解析模板")
    expected_params = fields.JSONField(null=True, description="期望的参数列表")

    class Meta:  # type: ignore
        table = "template_commands"
        table_description = "模板命令表"
        unique_together = [["config_template", "brand"]]  # 每个模板每个品牌只能有一个命令

    def __str__(self) -> str:
        return f"{self.config_template.name} - {self.brand.name}"


class OperationLog(BaseModel):
    """
    操作日志表

    记录所有设备操作的详细日志：
    - device: 关联操作的设备
    - template: 关联使用的模板
    - command_executed: 实际发送到设备的命令
    - output_received: 设备返回的原始输出
    - parsed_output: 结构化解析后的结果
    - status: 操作执行状态
    - error_message: 失败时的错误信息
    - executed_by: 操作者身份标识
    - timestamp: 操作发生时间
    """

    device = fields.ForeignKeyField("models.Device", related_name="operation_logs", null=True, description="操作的设备")
    template = fields.ForeignKeyField(
        "models.ConfigTemplate", related_name="operation_logs", null=True, description="使用的模板"
    )
    command_executed = fields.TextField(null=True, description="实际执行的命令")
    output_received = fields.TextField(null=True, description="设备返回的原始输出")
    parsed_output = fields.JSONField(null=True, description="结构化解析结果")
    status = fields.CharEnumField(OperationStatusEnum, description="操作执行状态")
    error_message = fields.TextField(null=True, description="错误信息")
    executed_by = fields.CharField(max_length=100, null=True, description="操作者身份")
    timestamp = fields.DatetimeField(auto_now_add=True, description="操作时间")

    class Meta:  # type: ignore
        table = "operation_logs"
        table_description = "操作日志表"
        indexes = [
            ["device_id", "timestamp"],  # 复合索引
        ]

    def __str__(self) -> str:
        return f"Operation {self.id} - {self.status}"


class DeviceConnectionStatus(BaseModel):
    """
    设备连接状态表

    记录设备的连接监控信息：
    - device: 关联的设备（一对一关系）
    - is_reachable: 设备是否可达
    - last_check_time: 最近检查时间
    - last_success_time: 最近成功连接时间
    - failure_count: 连续失败次数
    - failure_reason: 失败原因
    - snmp_response_time_ms: SNMP响应时间（毫秒）
    """

    device = fields.OneToOneField("models.Device", related_name="connection_status", description="关联设备")
    is_reachable = fields.BooleanField(default=False, description="设备是否可达")
    last_check_time = fields.DatetimeField(description="最近检查时间")
    last_success_time = fields.DatetimeField(null=True, description="最近成功连接时间")
    failure_count = fields.IntField(default=0, description="连续失败次数")
    failure_reason = fields.TextField(null=True, description="失败原因")
    snmp_response_time_ms = fields.IntField(null=True, description="SNMP响应时间")

    class Meta:  # type: ignore
        table = "device_connection_status"
        table_description = "设备连接状态表"
        indexes = [
            ["device_id", "last_check_time"],  # 复合索引
        ]

    def __str__(self) -> str:
        return f"{self.device.name} - {'Reachable' if self.is_reachable else 'Unreachable'}"


class ConfigSnapshot(BaseModel):
    """
    配置快照表

    存储设备配置的快照信息：
    - device: 关联的设备
    - snapshot_type: 快照类型（备份/变更前/变更后）
    - config_content: 完整配置内容
    - checksum: 配置内容的MD5校验码
    - operation_log: 关联的操作记录
    """

    device = fields.ForeignKeyField("models.Device", related_name="config_snapshots", description="关联设备")
    snapshot_type = fields.CharEnumField(SnapshotTypeEnum, description="快照类型")
    config_content = fields.TextField(description="完整配置内容")
    checksum = fields.CharField(max_length=32, description="配置MD5校验码")
    operation_log = fields.ForeignKeyField(
        "models.OperationLog", related_name="config_snapshots", null=True, description="关联操作记录"
    )

    class Meta:  # type: ignore
        table = "config_snapshots"
        table_description = "配置快照表"
        indexes = [
            ["device_id", "created_at"],  # 复合索引
        ]

    def __str__(self) -> str:
        return f"{self.device.name} - {self.snapshot_type} - {self.created_at}"


class ConfigDiff(BaseModel):
    """
    配置差异表

    存储配置变更的差异信息：
    - before_snapshot: 变更前快照
    - after_snapshot: 变更后快照
    - diff_content: 差异内容（unified diff格式）
    - added_lines: 新增行数
    - removed_lines: 删除行数
    """

    before_snapshot = fields.ForeignKeyField(
        "models.ConfigSnapshot", related_name="before_diffs", description="变更前快照"
    )
    after_snapshot = fields.ForeignKeyField(
        "models.ConfigSnapshot", related_name="after_diffs", description="变更后快照"
    )
    diff_content = fields.TextField(description="差异内容")
    added_lines = fields.IntField(description="新增行数")
    removed_lines = fields.IntField(description="删除行数")

    class Meta:  # type: ignore
        table = "config_diffs"
        table_description = "配置差异表"

    def __str__(self) -> str:
        return f"Diff: +{self.added_lines}/-{self.removed_lines}"


class RollbackOperation(BaseModel):
    """
    回滚操作表

    记录配置回滚操作的信息：
    - original_operation: 原始操作记录
    - target_snapshot: 目标回滚快照
    - rollback_status: 回滚状态
    - executed_by: 执行回滚的操作者
    - executed_at: 回滚执行时间
    """

    original_operation = fields.ForeignKeyField(
        "models.OperationLog", related_name="rollback_operations", description="原始操作记录"
    )
    target_snapshot = fields.ForeignKeyField(
        "models.ConfigSnapshot", related_name="rollback_operations", description="目标回滚快照"
    )
    rollback_status = fields.CharEnumField(RollbackStatusEnum, description="回滚状态")
    executed_by = fields.CharField(max_length=100, description="执行回滚的操作者")
    executed_at = fields.DatetimeField(description="回滚执行时间")

    class Meta:  # type: ignore
        table = "rollback_operations"
        table_description = "回滚操作表"

    def __str__(self) -> str:
        return f"Rollback {self.id} - {self.rollback_status}"
