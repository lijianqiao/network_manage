"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_groups.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备组管理API端点
"""

import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_device_group_service
from app.core.exceptions import (
    BadRequestException,
    NotFoundError,
    ValidationError,
)
from app.models.network_models import DeviceGroup
from app.schemas.base import SuccessResponse
from app.schemas.device_group import (
    DeviceGroupCreateRequest,
    DeviceGroupListResponse,
    DeviceGroupPaginationResponse,
    DeviceGroupQueryParams,
    DeviceGroupUpdateRequest,
)
from app.services.device_group_service import DeviceGroupService
from app.utils.logger import logger
from app.utils.universal_import_export import get_import_export_tool

router = APIRouter(prefix="/device-groups", tags=["设备组管理"])


@router.post(
    "/",
    response_model=DeviceGroupListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建设备组",
)
async def create_device_group(
    device_group_data: DeviceGroupCreateRequest,
    service: DeviceGroupService = Depends(get_device_group_service),
) -> DeviceGroupListResponse:
    """创建设备组"""
    try:
        device_group = await service.create(device_group_data)
        return device_group
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"数据验证失败: {e.message}",
        ) from e
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"业务逻辑错误: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建设备组失败: {str(e)}",
        ) from e


@router.get(
    "/{device_group_id}",
    response_model=DeviceGroupListResponse,
    summary="获取设备组详情",
)
async def get_device_group(
    device_group_id: UUID,
    service: DeviceGroupService = Depends(get_device_group_service),
) -> DeviceGroupListResponse:
    """获取设备组详情"""
    try:
        device_group = await service.get_by_id(device_group_id)
        return device_group
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备组不存在: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备组失败: {str(e)}",
        ) from e


@router.put(
    "/{device_group_id}",
    response_model=DeviceGroupListResponse,
    summary="更新设备组",
)
async def update_device_group(
    device_group_id: UUID,
    device_group_data: DeviceGroupUpdateRequest,
    service: DeviceGroupService = Depends(get_device_group_service),
) -> DeviceGroupListResponse:
    """更新设备组"""
    try:
        device_group = await service.update(device_group_id, device_group_data)
        return device_group
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备组不存在: {e.message}",
        ) from e
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"数据验证失败: {e.message}",
        ) from e
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"业务逻辑错误: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新设备组失败: {str(e)}",
        ) from e


@router.delete(
    "/{device_group_id}",
    response_model=SuccessResponse,
    summary="删除设备组",
    description="删除指定设备组",
)
async def delete_device_group(
    device_group_id: UUID,
    soft_delete: bool = Query(True, description="是否软删除"),
    service: DeviceGroupService = Depends(get_device_group_service),
) -> SuccessResponse:
    """删除设备组"""
    try:
        result = await service.delete(device_group_id, soft_delete=soft_delete)
        logger.info(f"成功删除设备组: {device_group_id}")
        return result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备组不存在: {e.message}",
        ) from e
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"业务逻辑错误: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除设备组失败: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=DeviceGroupPaginationResponse,
    summary="分页查询设备组",
)
async def list_device_groups(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: str | None = Query(None, description="设备组名称筛选"),
    service: DeviceGroupService = Depends(get_device_group_service),
) -> DeviceGroupPaginationResponse:
    """分页查询设备组列表"""
    try:
        query_params = DeviceGroupQueryParams(
            page=page,
            page_size=page_size,
            name=name,
        )

        result = await service.list_with_pagination(query_params)
        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"参数验证失败: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询设备组失败: {str(e)}",
        ) from e


@router.get(
    "/stats/count",
    response_model=dict[str, int],
    summary="统计设备组数量",
)
async def get_device_groups_count(
    service: DeviceGroupService = Depends(get_device_group_service),
) -> dict[str, int]:
    """获取设备组统计数量"""
    try:
        total_count = await service.count()
        return {"total": total_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"统计设备组失败: {str(e)}",
        ) from e


@router.get(
    "/template",
    summary="下载设备分组导入模板",
    description="下载设备分组数据导入模板文件",
)
async def download_device_group_template():
    """下载设备分组导入模板"""
    try:
        tool = await get_import_export_tool(DeviceGroup)
        excel_data = await tool.export_template()

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=device_group_template.xlsx"},
        )
    except Exception as e:
        logger.error(f"下载设备分组模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载模板失败: {str(e)}",
        ) from e


@router.post(
    "/import",
    summary="导入设备分组数据",
    description="从Excel文件导入设备分组数据",
)
async def import_device_groups(
    file: UploadFile = File(..., description="要导入的Excel文件"),
):
    """导入设备分组数据"""
    try:
        tool = await get_import_export_tool(DeviceGroup)

        # 验证文件类型
        if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传Excel文件（.xlsx或.xls格式）")

        # 执行导入
        result = await tool.import_data(file)

        return SuccessResponse(data=result, message="设备分组数据导入完成")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入设备分组数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}",
        ) from e


@router.get(
    "/export",
    summary="导出设备分组数据",
    description="导出设备分组数据到Excel文件",
)
async def export_device_groups():
    """导出设备分组数据"""
    try:
        tool = await get_import_export_tool(DeviceGroup)
        excel_data = await tool.export_data()

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=device_groups_export.xlsx"},
        )
    except Exception as e:
        logger.error(f"导出设备分组数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}",
        ) from e


@router.get(
    "/fields",
    summary="获取设备分组字段信息",
    description="获取设备分组模型的字段信息，用于前端动态生成表单",
)
async def get_device_group_fields():
    """获取设备分组字段信息"""
    try:
        tool = await get_import_export_tool(DeviceGroup)
        fields = tool.get_field_info()

        return SuccessResponse(data=fields, message="获取字段信息成功")
    except Exception as e:
        logger.error(f"获取设备分组字段信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字段信息失败: {str(e)}",
        ) from e
