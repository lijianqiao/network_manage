"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_template_service.py
@DateTime: 2025-06-22
@Docs: 配置模板服务层实现
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import DuplicateError, NotFoundError, ValidationError
from app.models.network_models import ConfigTemplate
from app.repositories.config_template_dao import ConfigTemplateDAO
from app.schemas.base import SuccessResponse
from app.schemas.config_template import (
    ConfigTemplateCreateRequest,
    ConfigTemplateDetailResponse,
    ConfigTemplateQueryParams,
    ConfigTemplateResponse,
    ConfigTemplateUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.logger import logger
from app.utils.operation_logger import operation_log


class ConfigTemplateService(
    BaseService[
        ConfigTemplate,
        ConfigTemplateCreateRequest,
        ConfigTemplateUpdateRequest,
        ConfigTemplateResponse,
        ConfigTemplateQueryParams,
    ]
):
    """配置模板服务层

    提供配置模板的业务逻辑处理，包括：
    - 模板的CRUD操作
    - 唯一性验证
    - 状态管理
    - 统计信息
    - 模板命令管理
    """

    def __init__(self):
        """初始化配置模板服务"""
        self.dao = ConfigTemplateDAO()
        super().__init__(dao=self.dao, response_schema=ConfigTemplateResponse, entity_name="配置模板")

    async def _validate_create_data(self, data: ConfigTemplateCreateRequest) -> None:
        """验证创建数据

        Args:
            data: 创建数据

        Raises:
            DuplicateError: 模板名称已存在
            ValidationError: 数据验证失败
        """
        # 检查模板名称唯一性
        if await self.dao.check_name_exists(data.name):
            raise DuplicateError(f"配置模板名称 '{data.name}' 已存在")

        # 验证模板名称格式
        if not data.name.strip():
            raise ValidationError("模板名称不能为空")

        # 这里可以添加其他业务规则验证
        logger.debug(f"配置模板创建数据验证通过: {data.name}")

    async def _validate_update_data(
        self, id: UUID, data: ConfigTemplateUpdateRequest, existing: ConfigTemplate | None = None
    ) -> None:
        """验证更新数据

        Args:
            id: 模板ID
            data: 更新数据
            existing: 现有实体（可选）

        Raises:
            DuplicateError: 模板名称已存在
            ValidationError: 数据验证失败
        """
        if data.name and await self.dao.check_name_exists(data.name, exclude_id=id):
            raise DuplicateError(f"配置模板名称 '{data.name}' 已存在")

    def _prepare_create_data(self, data: ConfigTemplateCreateRequest) -> dict[str, Any]:
        """准备创建数据

        Args:
            data: 创建数据

        Returns:
            处理后的数据字典
        """
        return {
            "name": data.name.strip(),
            "template_type": data.template_type,
            "is_active": data.is_active,
            "description": getattr(data, "description", None),
        }

    def _build_filters(self, query_params: ConfigTemplateQueryParams) -> dict[str, Any]:
        """构建查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = {}

        if query_params.name:
            filters["name__icontains"] = query_params.name
        if query_params.template_type:
            filters["template_type"] = query_params.template_type
        if query_params.is_active is not None:
            filters["is_active"] = query_params.is_active

        return filters

    def _build_order_by(self, query_params: ConfigTemplateQueryParams) -> list[str]:
        """构建排序条件

        Args:
            query_params: 查询参数

        Returns:
            排序字段列表
        """
        order_by = ["template_type", "name"]

        if hasattr(query_params, "order_by") and query_params.order_by:
            order_by = [query_params.order_by]

        return order_by

    @operation_log("创建配置模板", auto_save=True, include_args=True)
    async def create_template(self, data: ConfigTemplateCreateRequest) -> ConfigTemplateResponse:
        """创建配置模板

        Args:
            data: 创建数据

        Returns:
            创建的模板响应
        """
        return await self.create(data)

    @operation_log("获取配置模板详情", auto_save=False)
    async def get_template_detail(self, template_id: UUID) -> ConfigTemplateDetailResponse:
        """获取配置模板详情（包含关联信息）

        Args:
            template_id: 模板ID

        Returns:
            模板详情响应
        """
        try:
            template = await self.dao.get_by_id(template_id)
            if not template:
                raise NotFoundError("配置模板不存在")

            # 基础信息
            response_data = {
                "id": template.id,
                "name": template.name,
                "template_type": template.template_type,
                "is_active": template.is_active,
                "description": getattr(template, "description", None),
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "command_count": 0,
                "supported_brands": [],
                "usage_count": 0,
                "template_commands": [],
                "recent_operations": [],
            }

            # TODO: 获取关联的模板命令
            # template_commands = await self._get_template_commands(template_id)
            # response_data["template_commands"] = template_commands
            # response_data["command_count"] = len(template_commands)

            # TODO: 获取支持的品牌列表
            # supported_brands = await self._get_supported_brands(template_id)
            # response_data["supported_brands"] = supported_brands

            # TODO: 获取使用次数和最近操作
            # usage_info = await self._get_usage_info(template_id)
            # response_data.update(usage_info)

            return ConfigTemplateDetailResponse(**response_data)

        except Exception as e:
            logger.error(f"获取配置模板详情失败: {e}")
            raise

    @operation_log("更新配置模板", auto_save=True, include_args=True)
    async def update_template(self, template_id: UUID, data: ConfigTemplateUpdateRequest) -> ConfigTemplateResponse:
        """更新配置模板

        Args:
            template_id: 模板ID
            data: 更新数据

        Returns:
            更新后的模板响应
        """  # 验证更新数据
        await self._validate_update_data(template_id, data)

        # 准备更新数据
        update_data = {}
        if data.name:
            update_data["name"] = data.name.strip()
        if data.template_type:
            update_data["template_type"] = data.template_type
        if data.is_active is not None:
            update_data["is_active"] = data.is_active
        if hasattr(data, "description") and data.description is not None:
            update_data["description"] = data.description

        # 执行更新
        updated_template = await self.dao.update_by_id(template_id, **update_data)
        if not updated_template:
            raise NotFoundError("配置模板不存在")

        logger.info(f"更新配置模板成功: {template_id}")
        return ConfigTemplateResponse.model_validate(updated_template)

    @operation_log("删除配置模板", auto_save=True, include_args=True)
    async def delete_template(self, template_id: UUID) -> SuccessResponse:
        """删除配置模板

        Args:
            template_id: 模板ID

        Returns:
            删除成功响应
        """
        # 检查模板是否存在
        template = await self.dao.get_by_id(template_id)
        if not template:
            raise NotFoundError("配置模板不存在")

        # TODO: 检查是否有关联的模板命令或操作记录
        # if await self._has_dependencies(template_id):
        #     raise ValidationError("配置模板正在使用中，无法删除")

        # 执行删除
        await self.dao.delete_by_id(template_id)

        logger.info(f"删除配置模板成功: {template_id}")
        return SuccessResponse(message="删除配置模板成功")

    @operation_log("切换配置模板状态", auto_save=True, include_args=True)
    async def toggle_template_status(self, template_id: UUID, is_active: bool) -> ConfigTemplateResponse:
        """切换配置模板状态

        Args:
            template_id: 模板ID
            is_active: 新的状态

        Returns:
            更新后的模板响应
        """
        updated_template = await self.dao.update_by_id(template_id, is_active=is_active)
        if not updated_template:
            raise NotFoundError("配置模板不存在")

        status_text = "启用" if is_active else "禁用"
        logger.info(f"{status_text}配置模板成功: {template_id}")

        return ConfigTemplateResponse.model_validate(updated_template)

    async def list_templates_by_type(self, template_type: str) -> list[ConfigTemplateResponse]:
        """根据类型获取配置模板列表

        Args:
            template_type: 模板类型

        Returns:
            模板列表
        """
        templates = await self.dao.get_by_template_type(template_type)
        return [ConfigTemplateResponse.model_validate(template) for template in templates]

    async def get_active_templates(self) -> list[ConfigTemplateResponse]:
        """获取活跃的配置模板列表

        Returns:
            活跃模板列表
        """
        templates = await self.dao.get_active_templates()
        return [ConfigTemplateResponse.model_validate(template) for template in templates]

    async def search_templates(self, keyword: str) -> list[ConfigTemplateResponse]:
        """搜索配置模板

        Args:
            keyword: 搜索关键字

        Returns:
            匹配的模板列表
        """
        templates = await self.dao.search_by_name(keyword)
        return [ConfigTemplateResponse.model_validate(template) for template in templates]

    async def get_template_statistics(self) -> dict[str, Any]:
        """获取配置模板统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = await self.dao.get_templates_statistics()

            # 添加额外的统计信息
            stats.update(
                {
                    "templates_with_commands": 0,  # TODO: 实现
                    "avg_commands_per_template": 0.0,  # TODO: 实现
                    "most_used_template": None,  # TODO: 实现
                    "recently_created": 0,  # TODO: 实现最近创建的模板数量
                }
            )

            logger.debug(f"获取配置模板统计信息: {stats}")
            return stats

        except Exception as e:
            logger.error(f"获取配置模板统计信息失败: {e}")
            raise

    async def bulk_toggle_status(self, template_ids: list[UUID], is_active: bool) -> dict[str, Any]:
        """批量切换模板状态

        Args:
            template_ids: 模板ID列表
            is_active: 新状态

        Returns:
            批量操作结果
        """
        try:
            # 转换UUID为int（如果需要）
            int_ids = [int(str(template_id).replace("-", ""), 16) for template_id in template_ids]

            updated_count = await self.dao.bulk_toggle_status(int_ids, is_active)

            status_text = "启用" if is_active else "禁用"
            logger.info(f"批量{status_text}配置模板完成: {updated_count}个")

            return {
                "success": True,
                "updated_count": updated_count,
                "message": f"成功{status_text}{updated_count}个配置模板",
            }

        except Exception as e:
            logger.error(f"批量切换配置模板状态失败: {e}")
            raise

    # 获取模板字段信息（用于前端动态表单）
    def get_template_fields(self) -> dict[str, Any]:
        """获取配置模板字段信息

        Returns:
            字段信息字典
        """
        from app.models.network_models import TemplateTypeEnum

        return {
            "fields": {
                "name": {
                    "type": "string",
                    "required": True,
                    "max_length": 100,
                    "label": "模板名称",
                    "placeholder": "请输入模板名称",
                },
                "template_type": {
                    "type": "enum",
                    "required": True,
                    "options": [{"value": t.value, "label": t.value} for t in TemplateTypeEnum],
                    "label": "模板类型",
                },
                "description": {
                    "type": "text",
                    "required": False,
                    "max_length": 500,
                    "label": "模板描述",
                    "placeholder": "请输入模板描述",
                },
                "is_active": {"type": "boolean", "default": True, "label": "是否启用"},
            },
            "validation_rules": {
                "name": ["required", "unique", "max:100"],
                "template_type": ["required", "enum"],
                "description": ["max:500"],
            },
        }
