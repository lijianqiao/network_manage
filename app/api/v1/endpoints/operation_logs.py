"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_logs.py
@DateTime: 2025/06/20 00:00:00
@Docs: 操作日志管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_operation_log_service
from app.core.exceptions import (
    BadRequestException,
    NotFoundError,
    ValidationError,
)
from app.models.network_models import OperationStatusEnum
from app.schemas.operation_log import (
    OperationLogCreateRequest,
    OperationLogListResponse,
    OperationLogPaginationResponse,
    OperationLogQueryParams,
)
from app.services.operation_log_service import OperationLogService

router = APIRouter(prefix="/operation-logs", tags=["操作日志管理"])


@router.post(
    "/",
    response_model=OperationLogListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建操作日志",
)
async def create_operation_log(
    log_data: OperationLogCreateRequest,
    service: OperationLogService = Depends(get_operation_log_service),
) -> OperationLogListResponse:
    """创建操作日志"""
    try:
        log = await service.create(log_data)
        return log
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
            detail=f"创建操作日志失败: {str(e)}",
        ) from e


@router.get(
    "/{log_id}",
    response_model=OperationLogListResponse,
    summary="获取操作日志详情",
)
async def get_operation_log(
    log_id: UUID,
    service: OperationLogService = Depends(get_operation_log_service),
) -> OperationLogListResponse:
    """获取操作日志详情"""
    try:
        log = await service.get_by_id(log_id)
        return log
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"操作日志不存在: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取操作日志失败: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=OperationLogPaginationResponse,
    summary="分页查询操作日志",
)
async def list_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    operation_status: OperationStatusEnum | None = Query(None, description="操作状态筛选"),
    device_id: UUID | None = Query(None, description="设备ID筛选"),
    executed_by: str | None = Query(None, description="操作员筛选"),
    service: OperationLogService = Depends(get_operation_log_service),
) -> OperationLogPaginationResponse:
    """分页查询操作日志列表"""
    try:
        query_params = OperationLogQueryParams(
            page=page,
            page_size=page_size,
            status=operation_status,
            device_id=device_id,
            executed_by=executed_by,
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
            detail=f"查询操作日志失败: {str(e)}",
        ) from e


@router.get(
    "/stats/count",
    response_model=dict[str, int],
    summary="统计操作日志数量",
)
async def get_operation_logs_count(
    service: OperationLogService = Depends(get_operation_log_service),
) -> dict[str, int]:
    """获取操作日志统计数量"""
    try:
        total_count = await service.count()
        return {"total": total_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"统计操作日志失败: {str(e)}",
        ) from e


@router.get(
    "/device/{device_id}",
    response_model=OperationLogPaginationResponse,
    summary="根据设备获取操作日志",
)
async def get_operation_logs_by_device(
    device_id: UUID,
    service: OperationLogService = Depends(get_operation_log_service),
) -> OperationLogPaginationResponse:
    """根据设备ID获取操作日志列表"""
    try:
        query_params = OperationLogQueryParams(page=1, page_size=1000, device_id=device_id)
        result = await service.list_with_pagination(query_params)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询操作日志失败: {str(e)}",
        ) from e


@router.get(
    "/stats/summary",
    response_model=dict[str, int],
    summary="获取操作日志统计摘要",
)
async def get_operation_logs_summary(
    service: OperationLogService = Depends(get_operation_log_service),
) -> dict[str, int]:
    """获取操作日志统计摘要"""
    try:
        # 这里可以添加更详细的统计逻辑
        total_count = await service.count()
        return {
            "total": total_count,
            "today": 0,  # 今日操作数
            "success": 0,  # 成功操作数
            "failed": 0,  # 失败操作数
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取操作日志统计失败: {str(e)}",
        ) from e
