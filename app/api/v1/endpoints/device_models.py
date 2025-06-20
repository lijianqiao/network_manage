"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_models.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备型号管理API端点
"""

import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_device_model_service
from app.core.exceptions import (
    BadRequestException,
    NotFoundError,
    ValidationError,
)
from app.schemas.base import SuccessResponse
from app.schemas.device_model import (
    DeviceModelCreateRequest,
    DeviceModelListResponse,
    DeviceModelPaginationResponse,
    DeviceModelQueryParams,
    DeviceModelUpdateRequest,
)
from app.services.device_model_service import DeviceModelService
from app.utils.device_model_import_export import DeviceModelImportExport
from app.utils.logger import logger

router = APIRouter(prefix="/device-models", tags=["设备型号管理"])


@router.post(
    "/",
    response_model=DeviceModelListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建设备型号",
)
async def create_device_model(
    device_model_data: DeviceModelCreateRequest,
    service: DeviceModelService = Depends(get_device_model_service),
) -> DeviceModelListResponse:
    """创建设备型号"""
    try:
        device_model = await service.create(device_model_data)
        return device_model
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
            detail=f"创建设备型号失败: {str(e)}",
        ) from e


@router.get(
    "/{device_model_id}",
    response_model=DeviceModelListResponse,
    summary="获取设备型号详情",
)
async def get_device_model(
    device_model_id: UUID,
    service: DeviceModelService = Depends(get_device_model_service),
) -> DeviceModelListResponse:
    """获取设备型号详情"""
    try:
        device_model = await service.get_by_id(device_model_id)
        return device_model
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备型号不存在: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备型号失败: {str(e)}",
        ) from e


@router.put(
    "/{device_model_id}",
    response_model=DeviceModelListResponse,
    summary="更新设备型号",
)
async def update_device_model(
    device_model_id: UUID,
    device_model_data: DeviceModelUpdateRequest,
    service: DeviceModelService = Depends(get_device_model_service),
) -> DeviceModelListResponse:
    """更新设备型号"""
    try:
        device_model = await service.update(device_model_id, device_model_data)
        return device_model
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备型号不存在: {e.message}",
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
            detail=f"更新设备型号失败: {str(e)}",
        ) from e


@router.delete(
    "/{device_model_id}",
    response_model=SuccessResponse,
    summary="删除设备型号",
    description="删除指定设备型号",
)
async def delete_device_model(
    device_model_id: UUID,
    soft_delete: bool = Query(True, description="是否软删除"),
    service: DeviceModelService = Depends(get_device_model_service),
) -> SuccessResponse:
    """删除设备型号"""
    try:
        result = await service.delete(device_model_id, soft_delete=soft_delete)
        logger.info(f"成功删除设备型号: {device_model_id}")
        return result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备型号不存在: {e.message}",
        ) from e
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"业务逻辑错误: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除设备型号失败: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=DeviceModelPaginationResponse,
    summary="分页查询设备型号",
)
async def list_device_models(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: str | None = Query(None, description="型号名称筛选"),
    brand_id: UUID | None = Query(None, description="品牌ID筛选"),
    service: DeviceModelService = Depends(get_device_model_service),
) -> DeviceModelPaginationResponse:
    """分页查询设备型号列表"""
    try:
        query_params = DeviceModelQueryParams(
            page=page,
            page_size=page_size,
            name=name,
            brand_id=brand_id,
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
            detail=f"查询设备型号失败: {str(e)}",
        ) from e


@router.get(
    "/stats/count",
    response_model=dict[str, int],
    summary="统计设备型号数量",
)
async def get_device_models_count(
    service: DeviceModelService = Depends(get_device_model_service),
) -> dict[str, int]:
    """获取设备型号统计数量"""
    try:
        total_count = await service.count()
        return {"total": total_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"统计设备型号失败: {str(e)}",
        ) from e


@router.get(
    "/brand/{brand_id}",
    response_model=DeviceModelPaginationResponse,
    summary="根据品牌获取设备型号",
)
async def get_device_models_by_brand(
    brand_id: UUID,
    service: DeviceModelService = Depends(get_device_model_service),
) -> DeviceModelPaginationResponse:
    """根据品牌ID获取设备型号列表"""
    try:
        query_params = DeviceModelQueryParams(page=1, page_size=1000, brand_id=brand_id)
        result = await service.list_with_pagination(query_params)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询设备型号失败: {str(e)}",
        ) from e


@router.get(
    "/template",
    summary="下载设备型号导入模板",
    description="下载设备型号数据导入模板文件",
)
async def download_device_model_template():
    """下载设备型号导入模板"""
    try:
        device_model_import_export = DeviceModelImportExport()
        excel_data = await device_model_import_export.export_template()

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=device_model_template.xlsx"},
        )
    except Exception as e:
        logger.error(f"下载设备型号模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载模板失败: {str(e)}",
        ) from e


@router.post(
    "/import",
    summary="导入设备型号数据",
    description="从Excel文件导入设备型号数据",
)
async def import_device_models(
    file: UploadFile = File(..., description="要导入的Excel文件"),
):
    """导入设备型号数据"""
    try:
        device_model_import_export = DeviceModelImportExport()

        # 验证文件类型
        if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传Excel文件（.xlsx或.xls格式）")

        # 执行导入
        result = await device_model_import_export.import_data(file)

        return SuccessResponse(data=result, message="设备型号数据导入完成")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入设备型号数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}",
        ) from e


@router.get(
    "/export",
    summary="导出设备型号数据",
    description="导出设备型号数据到Excel文件",
)
async def export_device_models():
    """导出设备型号数据"""
    try:
        device_model_import_export = DeviceModelImportExport()
        excel_data = await device_model_import_export.export_data()

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=device_models_export.xlsx"},
        )
    except Exception as e:
        logger.error(f"导出设备型号数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}",
        ) from e


@router.get(
    "/fields",
    summary="获取设备型号字段信息",
    description="获取设备型号模型的字段信息，用于前端动态生成表单",
)
async def get_device_model_fields():
    """获取设备型号字段信息"""
    try:
        device_model_import_export = DeviceModelImportExport()
        fields = device_model_import_export.get_field_info()

        return SuccessResponse(data=fields, message="获取字段信息成功")
    except Exception as e:
        logger.error(f"获取设备型号字段信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字段信息失败: {str(e)}",
        ) from e
