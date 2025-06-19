"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_template.py
@DateTime: 2025/06/20 00:00:00
@Docs: 配置模板相关Pydantic校验模型
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.network_models import TemplateTypeEnum
from .base import (
    BaseCreateSchema,
    BaseQueryParams,
    BaseResponseSchema,
    BaseUpdateSchema
)


class ConfigTemplateCreateRequest(BaseCreateSchema):
    """配置模板创建请求"""
    name: str = Field(min_length=1, max_length=100, description="模板名称")
    template_type: TemplateTypeEnum = Field(description="模板类型")
    is_active: bool = Field(default=True, description="是否启用")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证模板名称"""
        if not v.strip():
            raise ValueError("模板名称不能为空")
        return v.strip()


class ConfigTemplateUpdateRequest(BaseUpdateSchema):
    """配置模板更新请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="模板名称")
    template_type: Optional[TemplateTypeEnum] = Field(default=None, description="模板类型")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class ConfigTemplateResponse(BaseResponseSchema):
    """配置模板响应"""
    name: str = Field(description="模板名称")
    template_type: TemplateTypeEnum = Field(description="模板类型")
    is_active: bool = Field(description="是否启用")
    
    # 统计信息
    command_count: Optional[int] = Field(default=0, description="关联命令数量")
    supported_brands: Optional[List[str]] = Field(default=None, description="支持的品牌列表")
    usage_count: Optional[int] = Field(default=0, description="使用次数")


class ConfigTemplateListResponse(ConfigTemplateResponse):
    """配置模板列表响应（简化版）"""
    pass


class ConfigTemplateDetailResponse(ConfigTemplateResponse):
    """配置模板详情响应"""
    # 包含关联的模板命令
    template_commands: Optional[List[dict]] = Field(default=None, description="模板命令列表")
    recent_operations: Optional[List[dict]] = Field(default=None, description="最近使用记录")


class ConfigTemplateQueryParams(BaseQueryParams):
    """配置模板查询参数"""
    name: Optional[str] = Field(default=None, description="按模板名称筛选")
    template_type: Optional[TemplateTypeEnum] = Field(default=None, description="按模板类型筛选")
    is_active: Optional[bool] = Field(default=None, description="按启用状态筛选")
    brand_id: Optional[UUID] = Field(default=None, description="按支持品牌筛选")


class TemplateCommandCreateRequest(BaseCreateSchema):
    """模板命令创建请求"""
    config_template_id: UUID = Field(description="关联配置模板ID")
    brand_id: UUID = Field(description="关联品牌ID")
    jinja_content: str = Field(min_length=1, description="Jinja2模板内容")
    ttp_template: Optional[str] = Field(default=None, description="TTP解析模板")
    expected_params: Optional[Dict[str, Any]] = Field(default=None, description="期望的参数列表")
    
    @field_validator('jinja_content')
    @classmethod
    def validate_jinja_content(cls, v: str) -> str:
        """验证Jinja2模板内容"""
        if not v.strip():
            raise ValueError("Jinja2模板内容不能为空")
        # 这里可以添加Jinja2语法验证
        return v.strip()


class TemplateCommandUpdateRequest(BaseUpdateSchema):
    """模板命令更新请求"""
    jinja_content: Optional[str] = Field(default=None, min_length=1, description="Jinja2模板内容")
    ttp_template: Optional[str] = Field(default=None, description="TTP解析模板")
    expected_params: Optional[Dict[str, Any]] = Field(default=None, description="期望的参数列表")


class TemplateCommandResponse(BaseResponseSchema):
    """模板命令响应"""
    config_template_id: UUID = Field(description="配置模板ID")
    brand_id: UUID = Field(description="品牌ID")
    jinja_content: str = Field(description="Jinja2模板内容")
    ttp_template: Optional[str] = Field(description="TTP解析模板")
    expected_params: Optional[Dict[str, Any]] = Field(description="期望参数列表")
    
    # 关联信息
    config_template_name: Optional[str] = Field(default=None, description="配置模板名称")
    brand_name: Optional[str] = Field(default=None, description="品牌名称")
    brand_platform_type: Optional[str] = Field(default=None, description="平台类型")


class TemplateCommandQueryParams(BaseQueryParams):
    """模板命令查询参数"""
    config_template_id: Optional[UUID] = Field(default=None, description="按模板ID筛选")
    brand_id: Optional[UUID] = Field(default=None, description="按品牌ID筛选")
    template_name: Optional[str] = Field(default=None, description="按模板名称筛选")
    brand_name: Optional[str] = Field(default=None, description="按品牌名称筛选")


class TemplateExecuteRequest(BaseCreateSchema):
    """模板执行请求"""
    template_id: UUID = Field(description="模板ID")
    device_ids: List[UUID] = Field(min_length=1, max_length=50, description="目标设备ID列表")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模板参数")
    username: Optional[str] = Field(default=None, description="连接用户名")
    password: Optional[str] = Field(default=None, description="连接密码")
    enable_password: Optional[str] = Field(default=None, description="Enable密码")
    timeout: int = Field(default=60, ge=10, le=600, description="执行超时时间（秒）")
    save_log: bool = Field(default=True, description="是否保存操作日志")
    parse_output: bool = Field(default=True, description="是否解析输出")


class TemplateExecuteResponse(BaseResponseSchema):
    """模板执行响应"""
    template_id: UUID = Field(description="模板ID")
    template_name: str = Field(description="模板名称")
    device_id: UUID = Field(description="设备ID")
    device_name: str = Field(description="设备名称")
    rendered_commands: List[str] = Field(description="渲染后的命令")
    raw_output: List[str] = Field(description="原始输出")
    parsed_output: Optional[List[Dict[str, Any]]] = Field(default=None, description="解析后的输出")
    execution_time: float = Field(description="执行时间（秒）")
    status: str = Field(description="执行状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class TemplateBatchExecuteResponse(BaseResponseSchema):
    """批量模板执行响应"""
    template_id: UUID = Field(description="模板ID")
    template_name: str = Field(description="模板名称")
    total_devices: int = Field(description="总设备数")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    results: List[TemplateExecuteResponse] = Field(description="详细结果")


class TemplateRenderRequest(BaseCreateSchema):
    """模板渲染请求（仅渲染，不执行）"""
    template_id: UUID = Field(description="模板ID")
    brand_id: UUID = Field(description="品牌ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模板参数")


class TemplateRenderResponse(BaseResponseSchema):
    """模板渲染响应"""
    template_id: UUID = Field(description="模板ID")
    brand_id: UUID = Field(description="品牌ID")
    original_template: str = Field(description="原始模板")
    rendered_commands: List[str] = Field(description="渲染后的命令")
    parameters_used: Dict[str, Any] = Field(description="使用的参数")


class TemplateStatsResponse(BaseResponseSchema):
    """模板统计响应"""
    name: str = Field(description="模板名称")
    template_type: TemplateTypeEnum = Field(description="模板类型")
    supported_brands: List[str] = Field(description="支持的品牌")
    total_executions: int = Field(description="总执行次数")
    success_executions: int = Field(description="成功执行次数")
    success_rate: float = Field(description="成功率")
    avg_execution_time: float = Field(description="平均执行时间")
    last_used: Optional[str] = Field(default=None, description="最后使用时间")
