# 🌐 网络设备自动化管理平台

基于 FastAPI + Scrapli + Nornir 构建的企业级网络设备自动化管理平台，支持多厂商网络设备的统一管理、配置部署、监控运维和批量操作。

## 🚀 核心功能特性

### 🔧 网络自动化核心
- **多厂商支持** - Cisco、华为、H3C、Juniper等主流设备
- **批量操作** - 支持设备、区域、分组的批量任务执行
- **配置管理** - 配置备份、部署、差异对比、自动回滚
- **模板系统** - Jinja2配置模板 + TextFSM输出解析
- **连接池管理** - 异步连接池、并发控制、资源优化
- **凭据管理** - 动态密码、OTP、Enable密码统一管理

### 🏗️ 技术架构特性
- 🚀 **FastAPI** - 现代化异步Web框架，自动生成API文档
- 🗄️ **Tortoise ORM** - 异步ORM，支持PostgreSQL数据库
- 🌐 **Scrapli** - 专业网络设备SSH/Telnet连接驱动
- ⚡ **Nornir** - 网络自动化任务调度框架
- 📝 **结构化日志** - 基于Loguru的网络操作审计日志
- � **安全加密** - Fernet密码加密、凭据安全管理
- 🔧 **现代工具链** - UV包管理 + Python 3.13

## 📁 项目结构

```
network_manage/
├── app/                        # 应用核心代码
│   ├── main.py                # FastAPI应用入口
│   ├── api/v1/endpoints/      # API路由端点
│   │   ├── network_automation.py    # 网络自动化API
│   │   ├── devices.py         # 设备管理API
│   │   ├── regions.py         # 区域管理API
│   │   └── ...               # 其他业务API
│   ├── core/                  # 核心组件
│   │   ├── config.py         # 环境配置管理
│   │   ├── credential_manager.py # 凭据管理器
│   │   ├── exceptions.py     # 自定义异常
│   │   └── dependencies.py   # 依赖注入
│   ├── network_automation/    # 🌟 网络自动化核心模块
│   │   ├── connection_manager.py     # Scrapli连接管理
│   │   ├── inventory_manager.py      # 动态设备清单
│   │   ├── task_executor.py          # Nornir任务执行器
│   │   ├── network_tasks.py          # 网络任务函数
│   │   ├── config_diff_manager.py    # 配置差异管理
│   │   ├── config_rollback_manager.py # 配置回滚管理
│   │   └── parsers/                  # 解析器模块
│   │       ├── hybrid_parser.py      # 混合TextFSM解析器
│   │       └── custom_template_manager.py # 自定义模板管理
│   ├── models/                # 数据模型
│   │   └── network_models.py  # 网络设备数据模型
│   ├── schemas/               # Pydantic模型
│   │   └── network_automation.py # 网络自动化Schema
│   ├── services/              # 业务服务层
│   │   └── network_automation_service.py # 网络自动化服务
│   ├── repositories/          # 数据访问层
│   └── utils/                 # 工具模块
│       └── logger.py         # 网络操作专用日志
├── templates/textfsm/         # TextFSM解析模板
├── logs/                      # 系统日志文件
├── docs/                      # 📚 项目文档
│   ├── 网络设备自动化平台设计方案.md
│   ├── 网络自动化第三阶段完成报告.md
│   └── API_README.md
├── tests/                     # 测试文件
├── migrations/                # 数据库迁移
├── pyproject.toml            # UV项目配置
└── README.md
```

## 🚀 快速开始

### 📋 环境要求

- **Python 3.13+**
- **PostgreSQL 12+** - 主数据库
- **Redis 6+** - 缓存（可选）
- **UV** - 现代化Python包管理器

### 🔧 安装UV包管理器

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 📥 项目部署

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd network_manage

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库等信息

# 4. 初始化数据库
uv run python init_db.py

# 5. 初始化模板数据
uv run python init_templates.py

# 6. 启动应用
uv run python run.py
```

### ⚙️ 环境配置

创建 `.env` 文件并配置以下环境变量：

```bash
# 应用配置
APP_NAME=网络设备自动化管理平台
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# 服务器配置
HOST=127.0.0.1
PORT=8010

# 安全配置
SECRET_KEY=your-very-secure-secret-key-here

# PostgreSQL数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=network_admin
DB_PASSWORD=your_secure_password
DB_NAME=network_manage

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 网络自动化配置
MAX_CONCURRENT_CONNECTIONS=30  # 最大并发连接数
CONNECTION_TIMEOUT=30          # 连接超时时间（秒）
COMMAND_TIMEOUT=60            # 命令执行超时时间（秒）

# 日志配置
LOG_LEVEL=INFO
LOG_ROTATION=10MB             # 日志轮转大小
LOG_RETENTION=30days          # 日志保留时间

# CORS配置
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 🌐 访问应用

启动成功后，您可以访问：

- **API交互文档**: http://127.0.0.1:8010/api/docs (Swagger UI)
- **API规范文档**: http://127.0.0.1:8010/api/redoc (ReDoc)
- **健康检查**: http://127.0.0.1:8010/health

## 🎯 主要API端点

### 网络自动化核心API

```bash
# Ping连通性测试
POST /api/automation/ping

# 执行单条命令
POST /api/automation/command

# 批量执行命令
POST /api/automation/commands

# 配置备份
POST /api/automation/backup

# 配置部署
POST /api/automation/deploy

# 模板渲染
POST /api/automation/template

# 设备信息获取
POST /api/automation/device-info

# 健康检查
POST /api/automation/health-check

# 连接池状态
GET /api/automation/connection-stats
```

### 设备管理API

```bash
# 设备CRUD操作
GET    /api/devices          # 获取设备列表
POST   /api/devices          # 创建设备
GET    /api/devices/{id}     # 获取设备详情
PUT    /api/devices/{id}     # 更新设备
DELETE /api/devices/{id}     # 删除设备

# 区域和分组管理
GET    /api/regions          # 区域管理
GET    /api/device-groups    # 设备分组管理
GET    /api/brands           # 设备品牌管理
```

## 🏗️ 核心架构组件

### 1. 网络自动化引擎 (`app/network_automation/`)

**🔌 Scrapli连接管理器**
- 支持SSH/Telnet多协议连接
- 异步连接池，最大50并发连接
- 自动平台检测（Cisco、华为、H3C等）
- 连接超时和重试机制

**📋 Nornir任务执行器**
- 动态主机清单构建
- 批量任务并发执行
- 支持设备/区域/分组多维度操作
- 结果聚合和错误处理

**🔄 配置管理系统**
- 配置备份和版本管理
- 配置差异对比分析
- 自动回滚机制
- 变更风险评估

### 2. 解析器系统 (`app/network_automation/parsers/`)

**🔍 混合TextFSM解析器**
- 自定义模板优先策略
- NTC-Templates标准库支持
- 正则表达式回退解析
- 多厂商解析规则适配

### 3. 数据管理层 (`app/models/` & `app/repositories/`)

**📊 数据模型设计**
- 区域(Region) → 设备分组(DeviceGroup) → 设备(Device)
- 配置模板(ConfigTemplate) → 模板命令(TemplateCommand)
- 操作日志(OperationLog) → 审计追踪

### 4. 服务层架构 (`app/services/`)

**🔧 业务逻辑封装**
- 网络自动化服务 (NetworkAutomationService)
- 凭据管理服务 (CredentialManager)
- 统一异常处理和日志记录

### 5. API层设计 (`app/api/v1/endpoints/`)

**🌐 RESTful API接口**
- 标准化请求/响应模型
- 依赖注入的服务调用
- 自动API文档生成

## 🔧 开发指南

### 添加新设备支持

1. **扩展品牌映射** (`app/network_automation/parsers/hybrid_parser.py`)
```python
self.brand_mapping_strategies = {
    "your_vendor": ["platform_name", "fallback_platform"],
}
```

2. **添加自定义解析模板** (`templates/textfsm/`)
```bash
# 创建设备专用模板
templates/textfsm/custom/your_vendor_show_version.textfsm
```

### 创建网络自动化任务

```python
# app/network_automation/network_tasks.py
def custom_task(task: Task, **kwargs) -> Result:
    """自定义网络任务"""
    try:
        host = task.host
        # 任务逻辑实现
        return Result(host=task.host, result=result_data)
    except Exception as e:
        return Result(host=task.host, failed=True, exception=e)
```

### 扩展API端点

1. **创建Schema模型** (`app/schemas/`)
```python
class CustomRequest(TaskRequest):
    custom_param: str = Field(..., description="自定义参数")
```

2. **实现服务层逻辑** (`app/services/`)
3. **添加API端点** (`app/api/v1/endpoints/`)

### 数据库模型扩展

```python
# app/models/network_models.py
class CustomModel(BaseModel):
    name = fields.CharField(max_length=100, unique=True)
    # 添加字段定义
    
    class Meta:
        table = "custom_models"
```

## 🚀 生产部署

### 📦 Docker部署（推荐）

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装UV
RUN pip install uv

# 复制项目文件
COPY . .

# 安装Python依赖
RUN uv sync --no-dev

# 暴露端口
EXPOSE 8010

# 启动应用
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  network-manage:
    build: .
    ports:
      - "8010:8010"
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./templates:/app/templates

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: network_manage
      POSTGRES_USER: network_admin
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 🏭 生产环境配置

```bash
# 1. 设置生产环境变量
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY="your-production-secret-key"

# 2. 使用生产级WSGI服务器
uv run gunicorn app.main:app -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8010 \
  --timeout 120 \
  --keepalive 5

# 3. 配置Nginx反向代理
# /etc/nginx/sites-available/network-manage
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔐 安全最佳实践

### 凭据安全
- **密码加密**: 使用Fernet对称加密存储设备密码
- **动态密码**: 支持OTP一次性密码，使用后立即清除
- **Enable密码**: 独立管理设备Enable提权密码
- **密钥轮换**: 定期更新加密密钥

### 网络安全
- **连接加密**: 所有设备连接使用SSH加密传输
- **超时控制**: 设置连接和命令执行超时时间
- **并发限制**: 限制同时连接数，防止设备过载
- **失败重试**: 智能重试机制，避免账户锁定

### API安全
- **CORS配置**: 严格控制跨域访问源
- **输入验证**: Pydantic模型严格验证API输入
- **异常处理**: 统一异常处理，防止信息泄露
- **审计日志**: 记录所有网络操作和API调用

## 📚 文档资源

- **📖 设计文档**: `docs/网络设备自动化平台设计方案.md`
- **🚀 开发报告**: `docs/网络自动化第三阶段完成报告.md` 
- **🔧 API文档**: `docs/API_README.md`
- **📝 使用指南**: `docs/通用导入导出工具使用指南.md`
- **⚡ 性能优化**: `docs/性能优化完成报告.md`

## 🧪 测试

```bash
# 运行单元测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_network_automation.py -v

# 生成测试覆盖率报告
uv run pytest --cov=app tests/ --cov-report=html
```

## 🤝 贡献指南

1. **Fork项目** 并创建功能分支
2. **编写代码** 遵循项目编码规范
3. **添加测试** 确保新功能有测试覆盖
4. **更新文档** 包括API文档和使用说明
5. **提交PR** 详细描述变更内容

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 📞 技术支持

- **问题反馈**: 请在GitHub Issues中提交问题
- **功能请求**: 欢迎提交功能改进建议
- **技术交流**: 加入项目讨论群组

---

**🌟 如果这个项目对您有帮助，请给我们一个Star！**


