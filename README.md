# FastAPI 基础项目骨架

这是一个用于快速构建 FastAPI 项目的基础骨架模板，避免重复造轮子。包含了 FastAPI 项目开发中的核心基础组件。

## 功能特性

- 🚀 **FastAPI** - 现代化的 Python Web 框架，自动生成 API 文档
- 🗄️ **Tortoise ORM** - 异步 ORM，支持读写分离
- ⚙️ **完整配置管理** - 基于 Pydantic 的环境配置
- 📝 **日志系统** - 基于 Loguru 的结构化日志
- 🚨 **异常处理** - 统一的 API 异常处理机制
- � **中间件系统** - 请求日志、CORS、压缩等中间件
- ⚡ **生命周期管理** - 应用启动和关闭事件处理
- 🔧 **UV 包管理** - 使用 UV 进行快速包管理
- 🐍 **Python 3.13** - 支持最新 Python 版本

## 项目结构

```
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── api/                    # API 路由
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/                   # 核心组件
│   │   ├── config.py          # 配置管理
│   │   ├── events.py          # 应用生命周期
│   │   ├── exceptions.py      # 异常处理
│   │   └── middleware.py      # 中间件
│   ├── db/                     # 数据库相关
│   │   ├── connection.py      # 数据库连接
│   │   └── router.py          # 读写分离路由
│   ├── models/                 # 数据模型
│   ├── schemas/                # Pydantic 模式
│   ├── services/               # 业务逻辑
│   └── utils/
│       └── logger.py          # 日志管理
├── logs/                       # 日志文件
├── pyproject.toml             # UV 项目配置
├── uv.lock                    # UV 锁定文件
└── README.md
```

## 快速开始

### 前置条件

- **Python 3.13+**
- **UV** - 现代化的 Python 包管理器

如果还没有安装 UV，请运行：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 安装依赖

```bash
# 克隆项目
git clone https://gitee.com/lijianqiao/fastapi_base_template.git
cd fastapi_base_template

# 安装依赖
uv sync
```

### 环境配置

创建 `.env` 文件并配置环境变量：

```bash
# 应用配置
APP_NAME=网络监控系统
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# 服务器配置
HOST=127.0.0.1
PORT=8000

# 安全配置
SECRET_KEY=your-secret-key-here

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 日志配置
LOG_LEVEL=INFO

# CORS 配置
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 运行应用

```bash
# 开发模式运行
uv run python run.py

# 或者直接运行 FastAPI 应用
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

访问应用：
- API 文档：http://127.0.0.1:8000/api/docs
- ReDoc 文档：http://127.0.0.1:8000/api/redoc

## 核心组件说明

### 1. 配置管理 (`app/core/config.py`)

基于 Pydantic Settings 的配置管理系统，支持：
- 环境变量自动加载
- 类型验证和转换
- 多环境配置支持
- 嵌套配置结构

### 2. 数据库集成 (`app/db/`)

- **connection.py**: Tortoise ORM 连接配置
- **router.py**: 读写分离路由器（为高级用法预留）

### 3. 日志系统 (`app/utils/logger.py`)

基于 Loguru 的日志管理：
- 控制台和文件双重输出
- 自动日志轮转和压缩
- 结构化日志格式
- 函数调用装饰器

### 4. 异常处理 (`app/core/exceptions.py`)

统一的异常处理机制：
- 自定义异常类
- 全局异常处理器
- 标准化错误响应格式

### 5. 中间件 (`app/core/middleware.py`)

预配置的中间件栈：
- 请求日志中间件
- CORS 跨域处理
- Gzip 压缩
- 请求追踪

### 6. 生命周期管理 (`app/core/events.py`)

应用生命周期事件处理：
- 数据库连接初始化
- Redis 连接管理
- 优雅的启动和关闭

## 开发指南

### 添加新的 API 端点

1. 在 `app/api/v1/endpoints/` 目录下创建新的路由文件
2. 在相应的 `__init__.py` 中注册路由
3. 创建对应的 Pydantic 模式（`app/schemas/`）
4. 实现业务逻辑（`app/services/`）

### 数据库模型

在 `app/models/` 目录下创建 Tortoise ORM 模型：

```python
# 示例
from tortoise.models import Model
from tortoise import fields

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "users"
```

### 环境管理

项目支持多环境配置：
- `development`: 开发环境
- `testing`: 测试环境  
- `production`: 生产环境

通过 `ENVIRONMENT` 环境变量控制。

## 生产部署

### 使用 UV 构建

```bash
# 构建生产环境
uv sync --no-dev

# 运行生产服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker 部署（可选）

如需 Docker 部署，可以创建如下 `Dockerfile`：

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# 安装 UV
RUN pip install uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --no-dev

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 注意事项

1. **安全配置**: 生产环境务必修改 `SECRET_KEY` 等敏感配置
2. **数据库迁移**: 使用 Aerich 进行数据库版本管理
3. **日志管理**: 生产环境建议配置日志收集系统
4. **监控**: 建议添加应用性能监控和健康检查

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目骨架。


