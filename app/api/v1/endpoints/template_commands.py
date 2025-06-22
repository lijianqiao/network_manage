"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: template_commands.py
@DateTime: 2025-06-22
@Docs: 模板命令API端点
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.config_template import (
    TemplateCommandCreateRequest,
    TemplateCommandResponse,
    TemplateCommandUpdateRequest,
)
from app.services.template_command_service import TemplateCommandService
from app.utils.logger import logger

router = APIRouter(prefix="/template-commands", tags=["模板命令管理"])


@router.post(
    "/",
    response_model=TemplateCommandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建模板命令",
    description="为指定配置模板和品牌创建Jinja2模板命令",
)
async def create_template_command(
    command_data: TemplateCommandCreateRequest,
) -> TemplateCommandResponse:
    """创建模板命令"""
    service = TemplateCommandService()

    try:
        result = await service.create_command(command_data)
        return result
    except Exception as e:
        logger.error(f"创建模板命令失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/{command_id}",
    response_model=TemplateCommandResponse,
    summary="获取模板命令详情",
    description="获取指定模板命令的详细信息",
)
async def get_template_command_detail(
    command_id: UUID,
) -> TemplateCommandResponse:
    """获取模板命令详情"""
    service = TemplateCommandService()

    try:
        result = await service.get_command_detail(command_id)
        return result
    except Exception as e:
        logger.error(f"获取模板命令详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "不存在" in str(e) else status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.put(
    "/{command_id}",
    response_model=TemplateCommandResponse,
    summary="更新模板命令",
    description="更新指定模板命令的信息",
)
async def update_template_command(
    command_id: UUID,
    update_data: TemplateCommandUpdateRequest,
) -> TemplateCommandResponse:
    """更新模板命令"""
    service = TemplateCommandService()

    try:
        result = await service.update_command(command_id, update_data)
        return result
    except Exception as e:
        logger.error(f"更新模板命令失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "不存在" in str(e) else status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete(
    "/{command_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除模板命令",
    description="删除指定的模板命令",
)
async def delete_template_command(
    command_id: UUID,
):
    """删除模板命令"""
    service = TemplateCommandService()

    try:
        await service.delete_command(command_id)
        return {"message": "模板命令删除成功"}
    except Exception as e:
        logger.error(f"删除模板命令失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "不存在" in str(e) else status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/template/{template_id}",
    response_model=list[TemplateCommandResponse],
    summary="根据模板获取命令",
    description="获取指定配置模板的所有模板命令",
)
async def get_commands_by_template(
    template_id: UUID,
) -> list[TemplateCommandResponse]:
    """根据配置模板ID获取所有模板命令"""
    service = TemplateCommandService()

    try:
        result = await service.get_commands_by_template(template_id)
        return result
    except Exception as e:
        logger.error(f"根据模板获取命令失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/brand/{brand_id}",
    response_model=list[TemplateCommandResponse],
    summary="根据品牌获取命令",
    description="获取指定品牌的所有模板命令",
)
async def get_commands_by_brand(
    brand_id: UUID,
) -> list[TemplateCommandResponse]:
    """根据品牌ID获取所有模板命令"""
    service = TemplateCommandService()

    try:
        result = await service.get_commands_by_brand(brand_id)
        return result
    except Exception as e:
        logger.error(f"根据品牌获取命令失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/validate-jinja",
    summary="验证Jinja2模板语法",
    description="验证Jinja2模板的语法正确性并提取变量",
)
async def validate_jinja_syntax(
    jinja_content: str = Query(..., description="Jinja2模板内容"),
) -> dict:
    """验证Jinja2模板语法"""
    service = TemplateCommandService()

    try:
        result = await service.validate_jinja_syntax(jinja_content)
        return result
    except Exception as e:
        logger.error(f"验证Jinja2模板语法失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
