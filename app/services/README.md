# 服务层基类使用指南

## 概述

`BaseService` 是网络设备自动化管理系统的服务层基类，提供了通用的CRUD业务逻辑、分页查询、批量操作、数据验证、日志记录等功能。

## 特性

- ✅ 完整的CRUD操作（创建、读取、更新、删除）
- ✅ 分页查询支持
- ✅ 批量操作（批量创建、更新、删除）
- ✅ 数据验证钩子方法
- ✅ 操作日志记录集成
- ✅ 异常处理与业务异常转换
- ✅ 软删除支持
- ✅ 关联数据预加载
- ✅ 灵活的查询过滤构建

## 基本用法

### 1. 定义Schema

首先需要定义相应的Pydantic Schema：

```python
from app.schemas.base import BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema, BaseQueryParams

class DeviceCreateSchema(BaseCreateSchema):
    name: str
    ip_address: str
    device_type: str

class DeviceUpdateSchema(BaseUpdateSchema):
    name: str | None = None
    ip_address: str | None = None
    status: str | None = None

class DeviceResponse(BaseResponseSchema):
    name: str
    ip_address: str
    device_type: str
    status: str

class DeviceQueryParams(BaseQueryParams):
    status: str | None = None
    device_type: str | None = None
```

### 2. 继承BaseService

```python
from app.services.base_service import BaseService

class DeviceService(BaseService[Device, DeviceCreateSchema, DeviceUpdateSchema, DeviceResponse, DeviceQueryParams]):
    def __init__(self, dao: DeviceDAO):
        super().__init__(dao=dao, response_schema=DeviceResponse, entity_name="设备")
```

### 3. 重写验证钩子

```python
async def _validate_create_data(self, data: DeviceCreateSchema) -> None:
    # 检查IP地址是否重复
    if await self.dao.exists(ip_address=data.ip_address):
        raise ValidationError(f"IP地址 {data.ip_address} 已被其他设备使用")

async def _validate_update_data(self, id: UUID, data: DeviceUpdateSchema, existing: Device) -> None:
    # 检查IP地址是否重复（排除自身）
    if data.ip_address and data.ip_address != existing.ip_address:
        if await self.dao.exists(ip_address=data.ip_address):
            raise ValidationError(f"IP地址 {data.ip_address} 已被其他设备使用")

async def _validate_delete(self, id: UUID, existing: Device) -> None:
    # 检查设备是否在线
    if existing.status == "online":
        raise ValidationError(f"设备 {existing.name} 当前在线，无法删除")
```

### 4. 自定义查询过滤

```python
def _build_filters(self, query_params: DeviceQueryParams) -> dict[str, Any]:
    filters = super()._build_filters(query_params)
    
    # 按状态过滤
    if query_params.status:
        filters["status"] = query_params.status
    
    # 按设备类型过滤
    if query_params.device_type:
        filters["device_type"] = query_params.device_type
    
    return filters
```

### 5. 设置预加载字段

```python
def _get_prefetch_related(self) -> list[str]:
    return ["brand", "model", "group", "region"]
```

## API方法

### 基础CRUD操作

```python
# 创建
device = await device_service.create(device_data)

# 根据ID获取
device = await device_service.get_by_id(device_id)

# 分页查询
result = await device_service.list_with_pagination(query_params)

# 获取所有
devices = await device_service.list_all(filters={"status": "online"})

# 更新
updated_device = await device_service.update(device_id, update_data)

# 删除（默认软删除）
result = await device_service.delete(device_id)

# 物理删除
result = await device_service.delete(device_id, soft_delete=False)
```

### 批量操作

```python
# 批量创建
bulk_create_request = BulkCreateRequest(items=[device1_data, device2_data])
result = await device_service.bulk_create(bulk_create_request)

# 批量更新
bulk_update_request = BulkUpdateRequest(
    ids=[id1, id2], 
    update_data={"status": "maintenance"}
)
result = await device_service.bulk_update(bulk_update_request)

# 批量删除
bulk_delete_request = BulkDeleteRequest(ids=[id1, id2], soft_delete=True)
result = await device_service.bulk_delete(bulk_delete_request)
```

### 辅助方法

```python
# 检查是否存在
exists = await device_service.exists(ip_address="192.168.1.1")

# 统计数量
count = await device_service.count(status="online")
```

## 异常处理

服务层会自动处理并转换异常：

- `IntegrityError` → `DuplicateError`
- `DoesNotExist` → `NotFoundError`
- 其他异常 → `BusinessError`

## 日志记录

所有操作都会自动记录日志：

- 使用 `@operation_log` 装饰器记录操作日志
- 使用 `logger` 记录执行日志
- 支持操作参数和结果的记录

## 分页响应格式

```python
{
    "data": [/* 数据列表 */],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "pages": 5,
        "has_next": true,
        "has_prev": false
    }
}
```

## 批量操作响应格式

```python
{
    "success": true,
    "message": "批量创建设备完成",
    "total": 10,
    "success_count": 8,
    "failed_count": 2,
    "failed_items": [
        {
            "index": 3,
            "data": {/* 失败的数据 */},
            "error": "IP地址已存在"
        }
    ]
}
```

## 最佳实践

1. **继承时指定正确的泛型类型**：确保类型提示正确
2. **重写验证方法**：实现业务特定的验证逻辑
3. **自定义查询过滤**：支持复杂的查询需求
4. **设置预加载字段**：优化数据库查询性能
5. **异常处理**：使用适当的业务异常类型
6. **日志记录**：记录关键操作和错误信息

## 扩展示例

```python
class DeviceService(BaseService[Device, DeviceCreateSchema, DeviceUpdateSchema, DeviceResponse, DeviceQueryParams]):
    
    def __init__(self, dao: DeviceDAO):
        super().__init__(dao=dao, response_schema=DeviceResponse, entity_name="设备")
    
    # 添加业务特定方法
    async def get_online_devices(self) -> list[DeviceResponse]:
        """获取所有在线设备"""
        return await self.list_all(filters={"status": "online"})
    
    async def update_device_status(self, device_id: UUID, status: str) -> DeviceResponse:
        """更新设备状态"""
        update_data = DeviceUpdateSchema(status=status)
        return await self.update(device_id, update_data)
```

## 注意事项

1. 确保DAO层已正确实现对应的方法
2. Schema类型需要正确继承基础Schema类
3. 异常处理要符合系统的异常体系
4. 操作日志依赖于操作上下文的正确设置
5. 软删除功能需要模型支持`is_deleted`字段
