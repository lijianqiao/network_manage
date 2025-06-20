# 网络设备自动化管理系统 API 文档

## 已完成的功能

### 基础实体管理 API

系统提供完整的CRUD操作和分页查询功能：

1. **区域管理** (`/api/regions`)
   - POST `/api/regions` - 创建区域
   - GET `/api/regions/{region_id}` - 获取区域详情
   - PUT `/api/regions/{region_id}` - 更新区域
   - DELETE `/api/regions/{region_id}` - 删除区域
   - GET `/api/regions` - 分页查询区域
   - GET `/api/regions/stats/count` - 统计区域数量

2. **品牌管理** (`/api/brands`)
   - 完整的CRUD操作
   - 分页查询和统计

3. **设备型号管理** (`/api/device-models`)
   - 完整的CRUD操作
   - 按品牌筛选
   - 分页查询和统计

4. **设备组管理** (`/api/device-groups`)
   - 完整的CRUD操作
   - 按区域筛选
   - 分页查询和统计

5. **设备管理** (`/api/devices`)
   - 完整的CRUD操作
   - 多条件筛选（名称、IP、类型、区域、设备组）
   - 分页查询和统计

6. **操作日志** (`/api/operation-logs`)
   - 创建和查询操作日志
   - 按设备、状态、操作员筛选
   - 分页查询和统计

## 启动应用

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 访问API文档

启动应用后，可以通过以下URL访问API文档：

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## 健康检查

```bash
curl http://localhost:8000/health
```

## 技术栈

- **后端框架**: FastAPI
- **ORM**: Tortoise ORM
- **数据库**: PostgreSQL
- **校验**: Pydantic v2
- **依赖注入**: 自定义服务容器
- **异常处理**: 统一异常体系
- **日志系统**: 结构化日志

## 项目结构

```
app/
├── api/v1/endpoints/    # API端点
├── core/               # 核心模块（配置、异常、依赖注入）
├── models/             # 数据模型
├── schemas/            # 校验模型
├── services/           # 服务层
├── repositories/       # 数据访问层
└── utils/              # 工具模块
```

## 下一步开发

- [ ] 网络自动化核心功能（配置模板、配置快照、配置差异、回滚操作）
- [ ] 设备连接状态管理
- [ ] 批量操作API
- [ ] 单元测试
- [ ] 部署配置
