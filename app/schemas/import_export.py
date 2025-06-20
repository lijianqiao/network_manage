"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: import_export.py
@DateTime: 2025/06/20 14:00:00
@Docs: 导入导出相关Schema定义
"""

from typing import Any

from pydantic import BaseModel, Field


class ImportResultResponse(BaseModel):
    """导入结果响应Schema"""

    total_rows: int = Field(..., description="总行数")
    success_count: int = Field(..., description="成功导入数量")
    error_count: int = Field(..., description="失败导入数量")
    errors: list[str] = Field(default_factory=list, description="错误信息列表")


class ExportRequest(BaseModel):
    """导出请求Schema"""

    model_name: str = Field(..., description="模型名称", examples=["region", "brand", "device_model"])


class ImportRequest(BaseModel):
    """导入请求Schema"""

    model_name: str = Field(..., description="模型名称", examples=["region", "brand", "device_model"])
    create_missing_fk: bool = Field(default=True, description="是否自动创建缺失的外键记录")


class SupportedModelsResponse(BaseModel):
    """支持的模型列表响应Schema"""

    models: dict[str, dict[str, Any]] = Field(..., description="支持的模型及其字段信息")
