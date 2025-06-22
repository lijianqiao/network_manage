"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_templates.py
@DateTime: 2025-06-22
@Docs: 配置模板API端点
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.config_template import (
    ConfigTemplateCreateRequest,
    ConfigTemplateDetailResponse,
    ConfigTemplateQueryParams,
    ConfigTemplateResponse,
    ConfigTemplateUpdateRequest,
)
from app.services.config_template_service import ConfigTemplateService
from app.utils.logger import logger

router = APIRouter(prefix="/config-templates", tags=["配置模板管理"])


@router.post(
    "/",
    response_model=ConfigTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建配置模板",
    description="创建新的配置模板，需要唯一的模板名称",
)
async def create_config_template(
    template_data: ConfigTemplateCreateRequest,
) -> ConfigTemplateResponse:
    """创建配置模板"""
    service = ConfigTemplateService()

    try:
        result = await service.create_template(template_data)
        logger.info(f"创建配置模板成功: {template_data.name}")
        return result
    except Exception as e:
        logger.error(f"创建配置模板失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/fields",
    summary="获取字段信息",
    description="获取配置模板的字段定义和枚举值",
)
async def get_template_fields() -> dict:
    """获取字段信息"""
    try:
        from app.models.network_models import TemplateTypeEnum

        return {
            "template_types": [{"value": item.value, "label": item.value} for item in TemplateTypeEnum],
            "fields": {
                "name": {"type": "string", "required": True, "max_length": 100, "description": "模板名称"},
                "template_type": {
                    "type": "enum",
                    "required": True,
                    "options": [item.value for item in TemplateTypeEnum],
                    "description": "模板类型",
                },
                "is_active": {"type": "boolean", "required": False, "default": True, "description": "是否启用"},
                "description": {"type": "string", "required": False, "max_length": 500, "description": "模板描述"},
            },
        }
    except Exception as e:
        logger.error(f"获取字段信息失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/stats/count",
    summary="获取配置模板统计信息",
    description="获取配置模板的总数、类型分布、使用统计等信息",
)
async def get_template_statistics() -> dict:
    """获取配置模板统计信息"""
    service = ConfigTemplateService()

    try:
        result = await service.get_template_statistics()
        return result
    except Exception as e:
        logger.error(f"获取模板统计信息失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/",
    summary="分页查询配置模板",
    description="支持按名称、类型、状态等条件分页查询配置模板",
)
async def list_config_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    name: str | None = Query(None, description="模板名称过滤"),
    template_type: str | None = Query(None, description="模板类型过滤"),
    is_active: bool | None = Query(None, description="启用状态过滤"),
    brand_id: UUID | None = Query(None, description="支持品牌过滤"),
) -> dict:
    """分页查询配置模板列表"""
    service = ConfigTemplateService()

    try:
        # 转换模板类型枚举
        template_type_enum = None
        if template_type:
            from app.models.network_models import TemplateTypeEnum

            template_type_enum = TemplateTypeEnum(template_type)

        query_params = ConfigTemplateQueryParams(
            page=page,
            page_size=page_size,
            name=name,
            template_type=template_type_enum,
            is_active=is_active,
            brand_id=brand_id,
        )

        result = await service.list_with_pagination(query_params)
        return result.model_dump()
    except Exception as e:
        logger.error(f"查询配置模板列表失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/{template_id}",
    response_model=ConfigTemplateDetailResponse,
    summary="获取配置模板详情",
    description="获取指定配置模板的详细信息，包括关联的模板命令和操作记录",
)
async def get_config_template_detail(
    template_id: UUID,
) -> ConfigTemplateDetailResponse:
    """获取配置模板详情"""
    service = ConfigTemplateService()

    try:
        result = await service.get_template_detail(template_id)
        return result
    except Exception as e:
        logger.error(f"获取配置模板详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "不存在" in str(e) else status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.put(
    "/{template_id}",
    response_model=ConfigTemplateResponse,
    summary="更新配置模板",
    description="更新指定配置模板的信息",
)
async def update_config_template(
    template_id: UUID,
    update_data: ConfigTemplateUpdateRequest,
) -> ConfigTemplateResponse:
    """更新配置模板"""
    service = ConfigTemplateService()

    try:
        result = await service.update_template(template_id, update_data)
        logger.info(f"更新配置模板成功: {result.name}")
        return result
    except Exception as e:
        logger.error(f"更新配置模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "不存在" in str(e) else status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除配置模板",
    description="删除指定的配置模板，仅当无关联数据时允许删除",
)
async def delete_config_template(
    template_id: UUID,
):
    """删除配置模板"""
    service = ConfigTemplateService()
    try:
        await service.delete_template(template_id)
        logger.info(f"删除配置模板成功: {template_id}")
        return {"message": "配置模板删除成功"}

    except Exception as e:
        logger.error(f"删除配置模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "不存在" in str(e) else status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.patch(
    "/{template_id}/toggle-status",
    response_model=ConfigTemplateResponse,
    summary="切换模板状态",
    description="启用或禁用指定的配置模板",
)
async def toggle_template_status(
    template_id: UUID,
    is_active: bool = Query(..., description="新的状态"),
) -> ConfigTemplateResponse:
    """切换模板状态"""
    service = ConfigTemplateService()

    try:
        result = await service.toggle_template_status(template_id, is_active)
        status_text = "启用" if is_active else "禁用"
        logger.info(f"{status_text}配置模板成功: {result.name}")
        return result
    except Exception as e:
        logger.error(f"切换模板状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "不存在" in str(e) else status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
