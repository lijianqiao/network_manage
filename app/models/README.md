# 网络设备自动化平台数据模型

## 📋 模型概述

本项目基于设计文档实现了完整的数据模型，用于管理1000+网络设备的自动化运维任务。

## 🏗️ 模型架构

### 基础模型类 (BaseModel)
所有业务模型的基类，提供统一的基础字段：
- `id`: UUID主键
- `is_deleted`: 软删除标记
- `description`: 描述信息
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 🌍 基础数据模型

#### 1. 区域管理 (Region)
- 管理不同地区的网络设备分组
- 包含SNMP社区字符串和默认CLI账号配置

#### 2. 品牌管理 (Brand)
- 支持H3C、华为、思科等主流品牌
- 关联Scrapli/Nornir平台驱动类型

#### 3. 设备型号 (DeviceModel)  
- 具体设备型号信息
- 关联对应品牌

#### 4. 设备分组 (DeviceGroup)
- 逻辑分组管理（如核心交换机、接入交换机）
- 可关联到特定区域

#### 5. 设备信息 (Device)
- 核心设备信息管理
- 支持动态/固定密码两种认证方式
- 包含加密存储的密码和Enable密码
- 设备状态监控

### 📝 配置模板系统

#### 6. 配置模板 (ConfigTemplate)
- 预设模板管理（查询/配置类型）
- 支持启用/禁用状态

#### 7. 模板命令 (TemplateCommand)
- 针对不同品牌的具体模板内容
- 包含Jinja2模板和TTP解析模板
- 期望参数列表（JSON格式）

### 📊 监控与日志

#### 8. 操作日志 (OperationLog)
- 记录所有设备操作的详细信息
- 包含执行命令、设备输出、解析结果
- 支持操作状态跟踪

#### 9. 设备连接状态 (DeviceConnectionStatus)
- 实时设备连接监控
- 记录连接失败统计和SNMP响应时间
- 一对一关联设备

### 🔄 配置管理与回滚

#### 10. 配置快照 (ConfigSnapshot)
- 存储设备配置快照
- 支持备份、变更前、变更后三种类型
- 包含MD5校验码

#### 11. 配置差异 (ConfigDiff)
- 记录配置变更差异
- 统计新增/删除行数
- 支持unified diff格式

#### 12. 回滚操作 (RollbackOperation)
- 配置回滚操作记录
- 关联原始操作和目标快照
- 跟踪回滚状态

## 🚀 使用方法

### 1. 数据库初始化

```bash
# 初始化数据库并创建示例数据
python init_db.py --init

# 重置数据库（仅开发环境）
python init_db.py --reset
```

### 2. 导入模型

```python
from app.models import (
    Region, Brand, DeviceModel, DeviceGroup, Device,
    ConfigTemplate, TemplateCommand, OperationLog,
    DeviceConnectionStatus, ConfigSnapshot, ConfigDiff,
    RollbackOperation
)

# 导入枚举类型
from app.models import (
    DeviceTypeEnum, DeviceStatusEnum, OperationStatusEnum,
    SnapshotTypeEnum, RollbackStatusEnum, TemplateTypeEnum
)
```

### 3. 基本操作示例

```python
# 创建区域
region = await Region.create(
    name="成都区域",
    snmp_community_string="public@cd", 
    default_cli_username="admin"
)

# 创建品牌
brand = await Brand.create(
    name="H3C",
    platform_type="hp_comware"
)

# 创建设备
device = await Device.create(
    name="SW-CD-01",
    ip_address="192.168.1.100",
    region=region,
    device_type=DeviceTypeEnum.SWITCH,
    is_dynamic_password=True
)

# 查询设备及关联信息
devices = await Device.all().prefetch_related(
    "region", "device_group", "model__brand"
)

# 记录操作日志
await OperationLog.create(
    device=device,
    command_executed="display version",
    status=OperationStatusEnum.SUCCESS,
    executed_by="admin"
)
```

## 🔧 数据库迁移

### Aerich 配置
项目已配置Aerich进行数据库迁移管理：

```bash
# 初始化迁移
aerich init -t app.db.connection.TORTOISE_ORM

# 生成迁移文件
aerich init-db

# 执行迁移
aerich upgrade

# 生成新的迁移
aerich migrate
```

### 注意事项
- 生产环境请使用Aerich进行数据库迁移
- 开发环境可使用`init_db.py`快速初始化
- 所有密码字段均采用Fernet加密存储
- 建议定期备份配置快照

## 📈 性能优化

### 数据库索引
模型已配置必要的数据库索引：
- 设备表：ip_address, region_id, status复合索引
- 操作日志：device_id, timestamp复合索引  
- 设备连接状态：device_id, last_check_time索引
- 配置快照：device_id, created_at索引

### 查询优化
- 使用`prefetch_related()`预加载关联数据
- 对大数据量查询使用分页
- 配置内容采用延迟加载策略

## 🔐 安全考虑

- 所有密码字段加密存储
- 支持软删除，避免数据丢失
- 操作日志完整记录，支持审计
- Enable密码独立管理和加密
