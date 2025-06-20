"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: regions.py
@DateTime: 2025/06/20 00:00:00
@Docs: 区域管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_region_service
from app.core.exceptions import (
    BadRequestException,
    NotFoundError,
    ValidationError,
)
from app.schemas.region import (
    RegionCreateRequest,
    RegionListResponse,
    RegionPaginationResponse,
    RegionQueryParams,
    RegionUpdateRequest,
)
from app.services.region_service import RegionService

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
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除区域",
)
async def delete_region(
    region_id: UUID,
    service: RegionService = Depends(get_region_service),
) -> None:
    """删除区域"""
    try:
        await service.delete(region_id)
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
