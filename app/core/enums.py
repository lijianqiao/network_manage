"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: enums.py
@DateTime: 2025/01/20 16:00:00
@Docs: 系统统一枚举定义
"""

from enum import Enum

# ==================== 网络自动化相关枚举 ====================


class OperationType(Enum):
    """操作类型枚举"""

    COMMAND_EXECUTION = "command_execution"
    CONFIG_DEPLOYMENT = "config_deployment"
    CONFIG_BACKUP = "config_backup"
    CONNECTIVITY_TEST = "connectivity_test"
    DEVICE_INFO_COLLECTION = "device_info_collection"
    CUSTOM = "custom"


class OperationStatus(Enum):
    """操作状态枚举"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    SUCCESS = "success"  # 执行成功
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 超时


class BatchStrategy(Enum):
    """批量策略枚举"""

    PARALLEL = "parallel"  # 并行执行
    SEQUENTIAL = "sequential"  # 顺序执行
    FAIL_FAST = "fail_fast"  # 快速失败
    CONTINUE_ON_ERROR = "continue_on_error"  # 遇错继续


# ==================== 配置管理相关枚举 ====================


class DiffType(Enum):
    """差异类型枚举"""

    ADDED = "added"  # 新增行
    REMOVED = "removed"  # 删除行
    MODIFIED = "modified"  # 修改行
    UNCHANGED = "unchanged"  # 未变化行


class DiffSeverity(Enum):
    """差异严重程度"""

    LOW = "low"  # 低风险（注释、描述等）
    MEDIUM = "medium"  # 中风险（非关键配置）
    HIGH = "high"  # 高风险（关键配置）
    CRITICAL = "critical"  # 严重风险（安全、路由等）


class SnapshotType(Enum):
    """快照类型枚举"""

    MANUAL = "manual"  # 手动快照
    AUTO_BACKUP = "auto_backup"  # 自动备份
    PRE_CHANGE = "pre_change"  # 变更前快照
    POST_CHANGE = "post_change"  # 变更后快照
    SCHEDULED = "scheduled"  # 定时快照


class RollbackStatus(Enum):
    """回滚状态枚举"""

    PENDING = "pending"  # 等待执行
    IN_PROGRESS = "in_progress"  # 执行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    PARTIAL = "partial"  # 部分成功


# ==================== 连接管理相关枚举 ====================


class ConnectionState(Enum):
    """连接状态枚举"""

    IDLE = "idle"  # 空闲
    ACTIVE = "active"  # 活跃使用中
    CHECKING = "checking"  # 健康检查中
    FAILED = "failed"  # 连接失败
    EXPIRED = "expired"  # 已过期


# ==================== 性能监控相关枚举 ====================


class AlertSeverity(Enum):
    """告警严重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """告警类型"""

    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    CONNECTION_POOL = "connection_pool"
    DEVICE_HEALTH = "device_health"


# ==================== 通用状态枚举 ====================


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class DeviceStatus(Enum):
    """设备状态枚举"""

    ONLINE = "online"
    OFFLINE = "offline"
    UNREACHABLE = "unreachable"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class LogLevel(Enum):
    """日志级别枚举"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ==================== 报告格式枚举 ====================


class ReportFormat(Enum):
    """报告格式枚举"""

    HTML = "html"
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class ExportFormat(Enum):
    """导出格式枚举"""

    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    EXCEL = "excel"
    PROMETHEUS = "prometheus"
