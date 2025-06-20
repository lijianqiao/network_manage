"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: devices.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备管理API端点
"""

import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_device_service
from app.core.exceptions import (
    BadRequestException,
    NotFoundError,
    ValidationError,
)
from app.models.network_models import Device, DeviceTypeEnum
from app.schemas.base import SuccessResponse
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceListResponse,
    DevicePaginationResponse,
    DeviceQueryParams,
    DeviceUpdateRequest,
)
from app.services.device_service import DeviceService
from app.utils.logger import logger
from app.utils.universal_import_export import get_import_export_tool

router = APIRouter(prefix="/devices", tags=["设备管理"])


@router.post(
    "/",
    response_model=DeviceListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建设备",
)
async def create_device(
    device_data: DeviceCreateRequest,
    service: DeviceService = Depends(get_device_service),
) -> DeviceListResponse:
    """创建设备"""
    try:
        device = await service.create(device_data)
        return device
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
            detail=f"创建设备失败: {str(e)}",
        ) from e


@router.get(
    "/{device_id}",
    response_model=DeviceListResponse,
    summary="获取设备详情",
)
async def get_device(
    device_id: UUID,
    service: DeviceService = Depends(get_device_service),
) -> DeviceListResponse:
    """获取设备详情"""
    try:
        device = await service.get_by_id(device_id)
        return device
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备不存在: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备失败: {str(e)}",
        ) from e


@router.put(
    "/{device_id}",
    response_model=DeviceListResponse,
    summary="更新设备",
)
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdateRequest,
    service: DeviceService = Depends(get_device_service),
) -> DeviceListResponse:
    """更新设备"""
    try:
        device = await service.update(device_id, device_data)
        return device
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备不存在: {e.message}",
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
            detail=f"更新设备失败: {str(e)}",
        ) from e


@router.delete(
    "/{device_id}",
    response_model=SuccessResponse,
    summary="删除设备",
    description="删除指定设备",
)
async def delete_device(
    device_id: UUID,
    soft_delete: bool = Query(True, description="是否软删除"),
    service: DeviceService = Depends(get_device_service),
) -> SuccessResponse:
    """删除设备"""
    try:
        result = await service.delete(device_id, soft_delete=soft_delete)
        logger.info(f"成功删除设备: {device_id}")
        return result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备不存在: {e.message}",
        ) from e
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"业务逻辑错误: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除设备失败: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=DevicePaginationResponse,
    summary="分页查询设备",
)
async def list_devices(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: str | None = Query(None, description="设备名称筛选"),
    ip_address: str | None = Query(None, description="IP地址筛选"),
    device_type: DeviceTypeEnum | None = Query(None, description="设备类型筛选"),
    region_id: UUID | None = Query(None, description="区域ID筛选"),
    device_group_id: UUID | None = Query(None, description="设备组ID筛选"),
    service: DeviceService = Depends(get_device_service),
) -> DevicePaginationResponse:
    """分页查询设备列表"""
    try:
        query_params = DeviceQueryParams(
            page=page,
            page_size=page_size,
            name=name,
            ip_address=ip_address,
            device_type=device_type,
            region_id=region_id,
            device_group_id=device_group_id,
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
            detail=f"查询设备失败: {str(e)}",
        ) from e


@router.get(
    "/stats/count",
    response_model=dict[str, int],
    summary="统计设备数量",
)
async def get_devices_count(
    service: DeviceService = Depends(get_device_service),
) -> dict[str, int]:
    """获取设备统计数量"""
    try:
        total_count = await service.count()
        return {"total": total_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"统计设备失败: {str(e)}",
        ) from e


@router.get(
    "/region/{region_id}",
    response_model=DevicePaginationResponse,
    summary="根据区域获取设备",
)
async def get_devices_by_region(
    region_id: UUID,
    service: DeviceService = Depends(get_device_service),
) -> DevicePaginationResponse:
    """根据区域ID获取设备列表"""
    try:
        query_params = DeviceQueryParams(page=1, page_size=1000, region_id=region_id)
        result = await service.list_with_pagination(query_params)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询设备失败: {str(e)}",
        ) from e


@router.get(
    "/group/{device_group_id}",
    response_model=DevicePaginationResponse,
    summary="根据设备组获取设备",
)
async def get_devices_by_group(
    device_group_id: UUID,
    service: DeviceService = Depends(get_device_service),
) -> DevicePaginationResponse:
    """根据设备组ID获取设备列表"""
    try:
        query_params = DeviceQueryParams(page=1, page_size=1000, device_group_id=device_group_id)
        result = await service.list_with_pagination(query_params)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询设备失败: {str(e)}",
        ) from e


@router.get("/export/template", summary="下载设备导入模板")
async def download_device_template():
    """下载设备导入模板 - 使用通用工具"""
    try:
        # 获取通用导入导出工具
        tool = await get_import_export_tool(Device)

        # 生成模板
        excel_data = await tool.export_template()
        filename = tool.get_filename("template")

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"下载设备模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载模板失败: {str(e)}",
        ) from e


@router.get("/export/data", summary="导出设备数据")
async def export_device_data():
    """导出设备数据 - 使用通用工具"""
    try:
        # 获取通用导入导出工具
        tool = await get_import_export_tool(Device)

        # 导出数据
        excel_data = await tool.export_data()
        filename = tool.get_filename("export")

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"导出设备数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出数据失败: {str(e)}",
        ) from e


@router.post("/import", summary="导入设备数据")
async def import_device_data(
    file: UploadFile = File(..., description="Excel文件"),
):
    """导入设备数据 - 使用通用工具"""
    try:
        # 验证文件类型
        if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传Excel文件（.xlsx或.xls格式）")

        # 获取通用导入导出工具
        tool = await get_import_export_tool(Device)

        # 执行导入
        result = await tool.import_data(file)

        return SuccessResponse(data=result, message="设备数据导入完成")
        return {
            "message": "导入完成",
            "total_rows": result["total_rows"],
            "success_count": result["success_count"],
            "error_count": result["error_count"],
            "errors": result["errors"],
        }
    except Exception as e:
        logger.error(f"导入设备数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导入失败: {str(e)}",
        ) from e


@router.get("/import/field-info", summary="获取设备字段信息")
async def get_device_field_info():
    """获取设备字段信息 - 使用通用工具"""
    try:
        # 获取通用导入导出工具
        tool = await get_import_export_tool(Device)

        # 获取字段信息
        field_info = tool.get_field_info()

        return SuccessResponse(data=field_info, message="获取字段信息成功")
    except Exception as e:
        logger.error(f"获取字段信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字段信息失败: {str(e)}",
        ) from e
