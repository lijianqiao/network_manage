"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_groups.py
@DateTime: 2025/06/20 00:00:00
@Docs: 设备组管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_device_group_service
from app.core.exceptions import (
    BadRequestException,
    NotFoundError,
    ValidationError,
)
from app.schemas.device_group import (
    DeviceGroupCreateRequest,
    DeviceGroupListResponse,
    DeviceGroupPaginationResponse,
    DeviceGroupQueryParams,
    DeviceGroupUpdateRequest,
)
from app.services.device_group_service import DeviceGroupService

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
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除设备组",
)
async def delete_device_group(
    device_group_id: UUID,
    service: DeviceGroupService = Depends(get_device_group_service),
) -> None:
    """删除设备组"""
    try:
        await service.delete(device_group_id)
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
    region_id: UUID | None = Query(None, description="区域ID筛选"),
    service: DeviceGroupService = Depends(get_device_group_service),
) -> DeviceGroupPaginationResponse:
    """分页查询设备组列表"""
    try:
        query_params = DeviceGroupQueryParams(
            page=page,
            page_size=page_size,
            name=name,
            region_id=region_id,
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
    "/region/{region_id}",
    response_model=DeviceGroupPaginationResponse,
    summary="根据区域获取设备组",
)
async def get_device_groups_by_region(
    region_id: UUID,
    service: DeviceGroupService = Depends(get_device_group_service),
) -> DeviceGroupPaginationResponse:
    """根据区域ID获取设备组列表"""
    try:
        query_params = DeviceGroupQueryParams(page=1, page_size=1000, region_id=region_id)
        result = await service.list_with_pagination(query_params)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询设备组失败: {str(e)}",
        ) from e
