"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: template_command_service.py
@DateTime: 2025-06-22
@Docs: 模板命令服务层实现
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import DuplicateError, NotFoundError, ValidationError
from app.models.network_models import TemplateCommand
from app.repositories.template_command_dao import TemplateCommandDAO
from app.schemas.base import SuccessResponse
from app.schemas.config_template import (
    TemplateCommandCreateRequest,
    TemplateCommandQueryParams,
    TemplateCommandResponse,
    TemplateCommandUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.logger import logger
from app.utils.operation_logger import operation_log


class TemplateCommandService(
    BaseService[
        TemplateCommand,
        TemplateCommandCreateRequest,
        TemplateCommandUpdateRequest,
        TemplateCommandResponse,
        TemplateCommandQueryParams,
    ]
):
    """模板命令服务层

    提供模板命令的业务逻辑处理，包括：
    - 模板命令的CRUD操作
    - 唯一性验证
    - Jinja2语法验证
    - 按模板和品牌查询
    """

    def __init__(self):
        """初始化模板命令服务"""
        self.dao = TemplateCommandDAO()
        super().__init__(dao=self.dao, response_schema=TemplateCommandResponse, entity_name="模板命令")

    async def _validate_create_data(self, data: TemplateCommandCreateRequest) -> None:
        """验证创建数据

        Args:
            data: 创建数据

        Raises:
            DuplicateError: 模板命令组合已存在
            ValidationError: 数据验证失败
        """
        # 检查模板命令组合唯一性
        if await self.dao.check_command_exists(data.config_template_id, data.brand_id):
            raise DuplicateError("该配置模板和品牌的命令组合已存在")

        # 验证Jinja2语法
        syntax_result = await self.validate_jinja_syntax(data.jinja_content)
        if not syntax_result["is_valid"]:
            raise ValidationError(f"Jinja2模板语法错误: {syntax_result['message']}")
        logger.debug(f"模板命令创建数据验证通过: {data.config_template_id}-{data.brand_id}")

    async def _validate_update_data(
        self, id: UUID, data: TemplateCommandUpdateRequest, existing: TemplateCommand | None = None
    ) -> None:
        """验证更新数据

        Args:
            id: 命令ID
            data: 更新数据
            existing: 现有实体（可选）

        Raises:
            ValidationError: 数据验证失败
        """
        if data.jinja_content:
            # 验证Jinja2语法
            syntax_result = await self.validate_jinja_syntax(data.jinja_content)
            if not syntax_result["is_valid"]:
                raise ValidationError(f"Jinja2模板语法错误: {syntax_result['message']}")

    def _prepare_create_data(self, data: TemplateCommandCreateRequest) -> dict[str, Any]:
        """准备创建数据

        Args:
            data: 创建数据

        Returns:
            处理后的数据字典
        """
        return {
            "config_template_id": data.config_template_id,
            "brand_id": data.brand_id,
            "jinja_content": data.jinja_content.strip(),
            "ttp_template": data.ttp_template,
            "expected_params": data.expected_params or {},
        }

    def _build_filters(self, query_params: TemplateCommandQueryParams) -> dict[str, Any]:
        """构建查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = {}

        if query_params.config_template_id:
            filters["config_template_id"] = query_params.config_template_id
        if query_params.brand_id:
            filters["brand_id"] = query_params.brand_id
        if query_params.template_name:
            filters["config_template__name__icontains"] = query_params.template_name
        if query_params.brand_name:
            filters["brand__name__icontains"] = query_params.brand_name

        return filters

    def _build_order_by(self, query_params: TemplateCommandQueryParams) -> list[str]:
        """构建排序条件

        Args:
            query_params: 查询参数

        Returns:
            排序字段列表
        """
        return ["config_template__name", "brand__name"]

    def _get_prefetch_related(self) -> list[str]:
        """获取预加载关联字段

        Returns:
            预加载字段列表
        """
        return ["config_template", "brand"]

    @operation_log("创建模板命令", auto_save=True, include_args=True)
    async def create_command(self, data: TemplateCommandCreateRequest) -> TemplateCommandResponse:
        """创建模板命令

        Args:
            data: 创建数据

        Returns:
            创建的命令响应
        """
        return await self.create(data)

    @operation_log("获取模板命令详情", auto_save=False)
    async def get_command_detail(self, command_id: UUID) -> TemplateCommandResponse:
        """获取模板命令详情

        Args:
            command_id: 命令ID

        Returns:
            命令详情响应
        """
        return await self.get_by_id(command_id)

    @operation_log("更新模板命令", auto_save=True, include_args=True)
    async def update_command(self, command_id: UUID, data: TemplateCommandUpdateRequest) -> TemplateCommandResponse:
        """更新模板命令

        Args:
            command_id: 命令ID
            data: 更新数据

        Returns:
            更新后的命令响应
        """
        # 验证更新数据
        await self._validate_update_data(command_id, data)

        # 准备更新数据
        update_data = {}
        if data.jinja_content:
            update_data["jinja_content"] = data.jinja_content.strip()
        if data.ttp_template is not None:
            update_data["ttp_template"] = data.ttp_template
        if data.expected_params is not None:
            update_data["expected_params"] = data.expected_params

        # 执行更新
        updated_command = await self.dao.update_by_id(command_id, **update_data)
        if not updated_command:
            raise NotFoundError("模板命令不存在")

        logger.info(f"更新模板命令成功: {command_id}")
        return TemplateCommandResponse.model_validate(updated_command)

    @operation_log("删除模板命令", auto_save=True, include_args=True)
    async def delete_command(self, command_id: UUID) -> SuccessResponse:
        """删除模板命令

        Args:
            command_id: 命令ID

        Returns:
            删除成功响应
        """
        # 检查命令是否存在
        command = await self.dao.get_by_id(command_id)
        if not command:
            raise NotFoundError("模板命令不存在")

        # 执行删除
        await self.dao.delete_by_id(command_id)

        logger.info(f"删除模板命令成功: {command_id}")
        return SuccessResponse(message="删除模板命令成功")

    async def get_commands_by_template(self, template_id: UUID) -> list[TemplateCommandResponse]:
        """根据配置模板ID获取所有模板命令

        Args:
            template_id: 配置模板ID

        Returns:
            命令列表
        """
        commands = await self.dao.get_commands_by_template(template_id)
        return [TemplateCommandResponse.model_validate(cmd) for cmd in commands]

    async def get_commands_by_brand(self, brand_id: UUID) -> list[TemplateCommandResponse]:
        """根据品牌ID获取所有模板命令

        Args:
            brand_id: 品牌ID

        Returns:
            命令列表
        """
        commands = await self.dao.get_commands_by_brand(brand_id)
        return [TemplateCommandResponse.model_validate(cmd) for cmd in commands]

    async def validate_jinja_syntax(self, jinja_content: str) -> dict[str, Any]:
        """验证Jinja2模板语法

        Args:
            jinja_content: Jinja2模板内容

        Returns:
            验证结果字典
        """
        try:
            from jinja2 import Environment, meta

            env = Environment()
            # 解析模板语法
            ast = env.parse(jinja_content)

            # 提取模板变量
            variables = meta.find_undeclared_variables(ast)

            return {"is_valid": True, "variables": list(variables), "message": "模板语法验证通过"}
        except Exception as e:
            return {"is_valid": False, "variables": [], "message": f"模板语法错误: {str(e)}"}

    async def get_template_supported_brands(self, template_id: UUID) -> list[dict]:
        """获取模板支持的品牌列表

        Args:
            template_id: 配置模板ID

        Returns:
            品牌信息列表
        """
        return await self.dao.get_template_supported_brands(template_id)

    async def get_brand_supported_templates(self, brand_id: UUID) -> list[dict]:
        """获取品牌支持的模板列表

        Args:
            brand_id: 品牌ID

        Returns:
            模板信息列表
        """
        return await self.dao.get_brand_supported_templates(brand_id)

    async def get_commands_statistics(self) -> dict[str, Any]:
        """获取模板命令统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = await self.dao.get_commands_statistics()

            # 添加额外的统计信息
            stats.update(
                {
                    "avg_commands_per_template": 0.0,  # TODO: 计算平均值
                    "avg_commands_per_brand": 0.0,  # TODO: 计算平均值
                    "templates_with_commands": len(stats.get("by_template", [])),
                    "brands_with_commands": len(stats.get("by_brand", [])),
                }
            )

            logger.debug(f"获取模板命令统计信息: {stats}")
            return stats

        except Exception as e:
            logger.error(f"获取模板命令统计信息失败: {e}")
            raise

    async def bulk_create_commands(self, commands_data: list[dict]) -> dict[str, Any]:
        """批量创建模板命令

        Args:
            commands_data: 命令数据列表

        Returns:
            批量操作结果
        """
        try:
            created_commands = await self.dao.bulk_create_commands(commands_data)

            logger.info(f"批量创建模板命令完成: {len(created_commands)}个")

            return {
                "success": True,
                "created_count": len(created_commands),
                "message": f"成功创建{len(created_commands)}个模板命令",
            }

        except Exception as e:
            logger.error(f"批量创建模板命令失败: {e}")
            raise
