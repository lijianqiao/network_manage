"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: regions.py
@DateTime: 2025/06/20 00:00:00
@Docs: 区域管理API端点
"""

import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_region_service
from app.core.exceptions import (
    BadRequestException,
    NotFoundError,
    ValidationError,
)
from app.models.network_models import Region
from app.schemas.base import SuccessResponse
from app.schemas.region import (
    RegionCreateRequest,
    RegionListResponse,
    RegionPaginationResponse,
    RegionQueryParams,
    RegionUpdateRequest,
)
from app.services.region_service import RegionService
from app.utils.logger import logger
from app.utils.universal_import_export import get_import_export_tool

router = APIRouter(prefix="/regions", tags=["区域管理"])


@router.post(
    "/",
    response_model=RegionListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建区域",
)
async def create_region(
    region_data: RegionCreateRequest,
    service: RegionService = Depends(get_region_service),
) -> RegionListResponse:
    """创建区域"""
    try:
        region = await service.create(region_data)
        return region
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
            detail=f"创建区域失败: {str(e)}",
        ) from e


@router.get(
    "/{region_id}",
    response_model=RegionListResponse,
    summary="获取区域详情",
)
async def get_region(
    region_id: UUID,
    service: RegionService = Depends(get_region_service),
) -> RegionListResponse:
    """获取区域详情"""
    try:
        region = await service.get_by_id(region_id)
        return region
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"区域不存在: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取区域失败: {str(e)}",
        ) from e


@router.put(
    "/{region_id}",
    response_model=RegionListResponse,
    summary="更新区域",
)
async def update_region(
    region_id: UUID,
    region_data: RegionUpdateRequest,
    service: RegionService = Depends(get_region_service),
) -> RegionListResponse:
    """更新区域"""
    try:
        region = await service.update(region_id, region_data)
        return region
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"区域不存在: {e.message}",
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
            detail=f"更新区域失败: {str(e)}",
        ) from e


@router.delete(
    "/{region_id}",
    response_model=SuccessResponse,
    summary="删除区域",
    description="删除指定区域",
)
async def delete_region(
    region_id: UUID,
    soft_delete: bool = Query(True, description="是否软删除"),
    service: RegionService = Depends(get_region_service),
) -> SuccessResponse:
    """删除区域"""
    try:
        result = await service.delete(region_id, soft_delete=soft_delete)
        logger.info(f"成功删除区域: {region_id}")
        return result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"区域不存在: {e.message}",
        ) from e
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"业务逻辑错误: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除区域失败: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=RegionPaginationResponse,
    summary="分页查询区域",
)
async def list_regions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: str | None = Query(None, description="区域名称筛选"),
    has_devices: bool | None = Query(None, description="是否包含设备"),
    service: RegionService = Depends(get_region_service),
) -> RegionPaginationResponse:
    """分页查询区域列表"""
    try:
        query_params = RegionQueryParams(
            page=page,
            page_size=page_size,
            name=name,
            has_devices=has_devices,
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
            detail=f"查询区域失败: {str(e)}",
        ) from e


@router.get(
    "/stats/count",
    response_model=dict[str, int],
    summary="统计区域数量",
)
async def get_regions_count(
    service: RegionService = Depends(get_region_service),
) -> dict[str, int]:
    """获取区域统计数量"""
    try:
        total_count = await service.count()
        return {"total": total_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"统计区域失败: {str(e)}",
        ) from e


@router.get("/export/template", summary="下载区域导入模板")
async def download_region_template():
    """下载区域导入模板 - 使用通用工具"""
    try:
        # 获取通用导入导出工具
        tool = await get_import_export_tool(Region)

        # 生成模板
        excel_data = await tool.export_template()

        # 生成文件名
        filename = tool.get_filename("template")

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"下载区域模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载模板失败: {str(e)}",
        ) from e


@router.get("/export/data", summary="导出区域数据")
async def export_region_data():
    """导出区域数据 - 使用通用工具"""
    try:
        # 获取通用导入导出工具
        tool = await get_import_export_tool(Region)

        # 导出数据
        excel_data = await tool.export_data()

        # 生成文件名
        filename = tool.get_filename("export")

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"导出区域数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出数据失败: {str(e)}",
        ) from e


@router.post("/import", summary="导入区域数据")
async def import_region_data(
    file: UploadFile = File(..., description="Excel文件"),
):
    """导入区域数据 - 使用通用工具"""
    try:
        # 验证文件类型
        if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传Excel文件（.xlsx或.xls格式）")

        # 获取通用导入导出工具
        tool = await get_import_export_tool(Region)

        # 执行导入
        result = await tool.import_data(file)

        return SuccessResponse(data=result, message="区域数据导入完成")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入区域数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导入失败: {str(e)}",
        ) from e


@router.get("/import/field-info", summary="获取区域字段信息")
async def get_region_field_info():
    """获取区域字段信息 - 使用通用工具"""
    try:
        # 获取通用导入导出工具
        tool = await get_import_export_tool(Region)

        # 获取字段信息
        field_info = tool.get_field_info()

        return SuccessResponse(data=field_info, message="获取字段信息成功")
    except Exception as e:
        logger.error(f"获取字段信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字段信息失败: {str(e)}",
        ) from e
