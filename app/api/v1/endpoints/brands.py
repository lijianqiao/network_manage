"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: brands.py
@DateTime: 2025/06/20 00:00:00
@Docs: 品牌管理API端点
"""

import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_brand_service
from app.schemas.base import SuccessResponse
from app.schemas.brand import (
    BrandCreateRequest,
    BrandListResponse,
    BrandPaginationResponse,
    BrandQueryParams,
    BrandStatsResponse,
    BrandUpdateRequest,
)
from app.services.brand_service import BrandService
from app.utils.brand_import_export import BrandImportExport
from app.utils.logger import logger

router = APIRouter(prefix="/brands", tags=["品牌管理"])


@router.post(
    "/",
    response_model=BrandListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建品牌",
    description="创建新的设备品牌",
)
async def create_brand(
    brand_data: BrandCreateRequest,
    brand_service: BrandService = Depends(get_brand_service),
) -> BrandListResponse:
    """创建品牌"""
    try:
        brand = await brand_service.create(brand_data)
        logger.info(f"成功创建品牌: {brand.name}")
        return brand
    except Exception as e:
        logger.error(f"创建品牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建品牌失败: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=BrandPaginationResponse,
    summary="查询品牌列表",
    description="分页查询品牌列表，支持多种过滤条件",
)
async def list_brands(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: str = Query(None, description="品牌名称搜索"),
    platform_type: str = Query(None, description="平台类型搜索"),
    brand_service: BrandService = Depends(get_brand_service),
) -> BrandPaginationResponse:
    """查询品牌列表"""
    try:
        query_params = BrandQueryParams(
            page=page,
            page_size=page_size,
            name=name,
            platform_type=platform_type,
        )
        result = await brand_service.list_with_pagination(query_params)
        return result
    except Exception as e:
        logger.error(f"查询品牌列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询品牌列表失败: {str(e)}",
        ) from e


@router.get(
    "/{brand_id}",
    response_model=BrandListResponse,
    summary="获取品牌详情",
    description="根据品牌ID获取品牌详细信息",
)
async def get_brand(
    brand_id: UUID,
    brand_service: BrandService = Depends(get_brand_service),
) -> BrandListResponse:
    """获取品牌详情"""
    try:
        brand = await brand_service.get_by_id(brand_id)
        return brand
    except Exception as e:
        logger.error(f"获取品牌详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"品牌不存在或获取失败: {str(e)}",
        ) from e


@router.put(
    "/{brand_id}",
    response_model=BrandListResponse,
    summary="更新品牌",
    description="更新品牌信息",
)
async def update_brand(
    brand_id: UUID,
    brand_data: BrandUpdateRequest,
    brand_service: BrandService = Depends(get_brand_service),
) -> BrandListResponse:
    """更新品牌"""
    try:
        brand = await brand_service.update(brand_id, brand_data)
        logger.info(f"成功更新品牌: {brand_id}")
        return brand
    except Exception as e:
        logger.error(f"更新品牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新品牌失败: {str(e)}",
        ) from e


@router.delete(
    "/{brand_id}",
    response_model=SuccessResponse,
    summary="删除品牌",
    description="删除指定品牌",
)
async def delete_brand(
    brand_id: UUID,
    soft_delete: bool = Query(True, description="是否软删除"),
    brand_service: BrandService = Depends(get_brand_service),
) -> SuccessResponse:
    """删除品牌"""
    try:
        result = await brand_service.delete(brand_id, soft_delete=soft_delete)
        logger.info(f"成功删除品牌: {brand_id}")
        return result
    except Exception as e:
        logger.error(f"删除品牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"删除品牌失败: {str(e)}",
        ) from e


@router.get(
    "/{brand_id}/stats",
    response_model=BrandStatsResponse,
    summary="获取品牌统计",
    description="获取品牌下设备和型号统计信息",
)
async def get_brand_stats(
    brand_id: UUID,
    brand_service: BrandService = Depends(get_brand_service),
) -> BrandStatsResponse:
    """获取品牌统计"""
    try:
        stats = await brand_service.get_brand_stats(brand_id)
        return stats
    except Exception as e:
        logger.error(f"获取品牌统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取品牌统计失败: {str(e)}",
        ) from e


@router.get(
    "/template",
    summary="下载品牌导入模板",
    description="下载品牌数据导入模板文件",
)
async def download_brand_template():
    """下载品牌导入模板"""
    try:
        brand_import_export = BrandImportExport()
        excel_data = await brand_import_export.export_template()

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=brand_template.xlsx"},
        )
    except Exception as e:
        logger.error(f"下载品牌模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载模板失败: {str(e)}",
        ) from e


@router.post(
    "/import",
    summary="导入品牌数据",
    description="从Excel文件导入品牌数据",
)
async def import_brands(
    file: UploadFile = File(..., description="要导入的Excel文件"),
):
    """导入品牌数据"""
    try:
        brand_import_export = BrandImportExport()

        # 验证文件类型
        if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请上传Excel文件（.xlsx或.xls格式）"
            )  # 执行导入
        result = await brand_import_export.import_data(file)

        return SuccessResponse(data=result, message="品牌数据导入完成")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入品牌数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}",
        ) from e


@router.get(
    "/export",
    summary="导出品牌数据",
    description="导出品牌数据到Excel文件",
)
async def export_brands():
    """导出品牌数据"""
    try:
        brand_import_export = BrandImportExport()
        excel_data = await brand_import_export.export_data()

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=brands_export.xlsx"},
        )
    except Exception as e:
        logger.error(f"导出品牌数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}",
        ) from e


@router.get(
    "/fields",
    summary="获取品牌字段信息",
    description="获取品牌模型的字段信息，用于前端动态生成表单",
)
async def get_brand_fields():
    """获取品牌字段信息"""
    try:
        brand_import_export = BrandImportExport()
        fields = brand_import_export.get_field_info()

        return SuccessResponse(data=fields, message="获取字段信息成功")
    except Exception as e:
        logger.error(f"获取品牌字段信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字段信息失败: {str(e)}",
        ) from e
