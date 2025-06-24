"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: advanced_network_operations.py
@DateTime: 2025/01/20 15:30:00
@Docs: 高级网络操作API端点 - 配置差异对比、批量操作、回滚系统
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.core.enums import SnapshotType
from app.network_automation.batch_operation_manager import batch_operation_manager
from app.network_automation.config_diff_manager import config_diff_manager
from app.network_automation.config_rollback_manager import config_rollback_manager
from app.schemas.advanced_operations import (
    BatchOperationProgress,
    BatchOperationRequest,
    BatchOperationResponse,
    ConfigCompareRequest,
    ConfigCompareResponse,
    CreateRollbackPlanRequest,
    CreateSnapshotRequest,
    ExecuteRollbackRequest,
    RollbackPlanResponse,
    SnapshotResponse,
)
from app.utils.logger import logger

router = APIRouter(prefix="/advanced", tags=["高级网络操作"])


# ==================== 配置差异对比端点 ====================


@router.post("/config/compare", response_model=ConfigCompareResponse, summary="配置差异对比")
async def compare_configs(request: ConfigCompareRequest):
    """
    对比两个配置文件的差异

    功能特性：
    - 智能配置分类和风险评估
    - 详细的差异分析和统计
    - 自动生成优化建议
    - 支持多种网络设备配置格式
    """
    try:
        logger.info(
            "开始配置差异对比",
            source_name=request.source_name,
            target_name=request.target_name,
            source_length=len(request.source_config),
            target_length=len(request.target_config),
        )

        # 执行配置对比
        diff_result = config_diff_manager.compare_configs(
            source_config=request.source_config,
            target_config=request.target_config,
            source_name=request.source_name,
            target_name=request.target_name,
            context_lines=request.context_lines,
        )

        # 构建响应
        response = ConfigCompareResponse(
            source_name=diff_result.source_name,
            target_name=diff_result.target_name,
            total_lines=diff_result.total_lines,
            added_lines=diff_result.added_lines,
            removed_lines=diff_result.removed_lines,
            modified_lines=diff_result.modified_lines,
            change_percentage=diff_result.change_percentage,
            has_critical_changes=diff_result.has_critical_changes,
            summary=diff_result.summary,
            risk_assessment=diff_result.risk_assessment,
            recommendations=diff_result.recommendations,
        )

        logger.info(
            "配置差异对比完成",
            source_name=request.source_name,
            target_name=request.target_name,
            change_percentage=diff_result.change_percentage,
            has_critical_changes=diff_result.has_critical_changes,
        )

        return response

    except Exception as e:
        logger.error(f"配置差异对比失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"配置差异对比失败: {str(e)}"
        ) from e


@router.post("/config/compare/report", summary="生成配置差异报告")
async def generate_config_diff_report(
    request: ConfigCompareRequest, format: str = Query("html", description="报告格式", enum=["html", "text"])
):
    """
    生成配置差异报告

    支持格式：
    - html: HTML格式报告，适合浏览器查看
    - text: 文本格式报告，适合命令行查看
    """
    try:
        # 执行配置对比
        diff_result = config_diff_manager.compare_configs(
            source_config=request.source_config,
            target_config=request.target_config,
            source_name=request.source_name,
            target_name=request.target_name,
            context_lines=request.context_lines,
        )

        # 生成报告
        if format == "html":
            report_content = config_diff_manager.generate_html_report(diff_result)
            media_type = "text/html"
        else:
            report_content = config_diff_manager.generate_text_report(diff_result)
            media_type = "text/plain"

        from fastapi.responses import Response

        return Response(
            content=report_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=config_diff_report.{format}"},
        )

    except Exception as e:
        logger.error(f"生成配置差异报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"生成配置差异报告失败: {str(e)}"
        ) from e


# ==================== 批量操作端点 ====================


@router.post("/batch/execute", response_model=BatchOperationResponse, summary="执行批量操作")
async def execute_batch_operation(request: BatchOperationRequest, background_tasks: BackgroundTasks):
    """
    执行批量网络操作

    支持的操作类型：
    - command_execution: 批量命令执行
    - config_deployment: 批量配置部署
    - config_backup: 批量配置备份
    - connectivity_test: 批量连通性测试
    - device_info_collection: 批量设备信息收集

    执行策略：
    - parallel: 并行执行（默认）
    - sequential: 顺序执行
    - fail_fast: 快速失败
    - continue_on_error: 遇错继续
    """
    try:
        # 操作类型和策略已经在schema中验证

        logger.info(
            "开始批量操作",
            operation_type=request.operation_type,
            device_count=len(request.devices),
            strategy=request.strategy,
        )

        # 创建进度跟踪函数
        from app.network_automation.batch_operation_manager import (
            BatchOperationProgress as BatchOperationProgressInternal,
        )

        def progress_callback(progress: BatchOperationProgressInternal):
            logger.debug(
                "批量操作进度更新",
                completion_percentage=progress.completion_percentage,
                successful_devices=progress.successful_devices,
                failed_devices=progress.failed_devices,
            )

        # 执行批量操作（异步生成器）
        batch_generator = batch_operation_manager.execute_batch_operation(
            devices=request.devices,
            operation_type=request.operation_type,
            operation_params=request.operation_params,
            strategy=request.strategy,
            max_retries=request.max_retries,
            timeout_per_device=request.timeout_per_device,
            progress_callback=progress_callback,
        )

        # 获取初始结果
        batch_result = await batch_generator.__anext__()

        # 在后台继续执行
        async def continue_batch_execution():
            try:
                async for _ in batch_generator:
                    # 这里可以添加实时更新逻辑，如WebSocket推送
                    pass
            except Exception as e:
                logger.error(f"批量操作后台执行异常: {e}")

        background_tasks.add_task(continue_batch_execution)

        # 构建响应
        progress_schema = BatchOperationProgress(
            total_devices=batch_result.progress.total_devices,
            completed_devices=batch_result.progress.completed_devices,
            successful_devices=batch_result.progress.successful_devices,
            failed_devices=batch_result.progress.failed_devices,
            pending_devices=batch_result.progress.pending_devices,
            running_devices=batch_result.progress.running_devices,
            completion_percentage=batch_result.progress.completion_percentage,
            success_rate=batch_result.progress.success_rate,
        )
        response = BatchOperationResponse(
            batch_id=batch_result.batch_id,
            operation_type=batch_result.operation_type,
            strategy=batch_result.strategy,
            total_devices=batch_result.progress.total_devices,
            status="running" if not batch_result.is_completed else "completed",
            progress=progress_schema,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量操作执行失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量操作执行失败: {str(e)}"
        ) from e


@router.get("/batch/{batch_id}/status", summary="获取批量操作状态")
async def get_batch_operation_status(batch_id: str):
    """获取批量操作的当前状态和进度"""
    try:
        batch_result = batch_operation_manager.get_batch_status(batch_id)

        if not batch_result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"批量操作不存在: {batch_id}")

        return {
            "batch_id": batch_result.batch_id,
            "operation_type": batch_result.operation_type.value,
            "strategy": batch_result.strategy.value,
            "is_completed": batch_result.is_completed,
            "is_successful": batch_result.is_successful,
            "progress": {
                "total_devices": batch_result.progress.total_devices,
                "completed_devices": batch_result.progress.completed_devices,
                "successful_devices": batch_result.progress.successful_devices,
                "failed_devices": batch_result.progress.failed_devices,
                "completion_percentage": batch_result.progress.completion_percentage,
                "success_rate": batch_result.progress.success_rate,
            },
            "summary": batch_result.summary,
            "errors": batch_result.errors[-10:] if batch_result.errors else [],  # 最近10个错误
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批量操作状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取批量操作状态失败: {str(e)}"
        ) from e


@router.post("/batch/{batch_id}/cancel", summary="取消批量操作")
async def cancel_batch_operation(batch_id: str):
    """取消正在执行的批量操作"""
    try:
        success = batch_operation_manager.cancel_batch_operation(batch_id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"批量操作不存在或已完成: {batch_id}")

        return {"message": f"批量操作已取消: {batch_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消批量操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"取消批量操作失败: {str(e)}"
        ) from e


# ==================== 配置快照端点 ====================


@router.post("/snapshot/create", response_model=SnapshotResponse, summary="创建配置快照")
async def create_config_snapshot(request: CreateSnapshotRequest):
    """
    创建设备配置快照

    快照类型：
    - manual: 手动快照
    - auto_backup: 自动备份
    - pre_change: 变更前快照
    - post_change: 变更后快照
    - scheduled: 定时快照
    """
    try:
        # 验证快照类型
        try:
            snapshot_type = SnapshotType(request.snapshot_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的快照类型: {request.snapshot_type}"
            ) from e

        # 创建快照
        snapshot = await config_rollback_manager.create_snapshot(
            device_data=request.device_data,
            snapshot_type=snapshot_type,
            created_by="api_user",  # 这里应该从认证信息获取
            description=request.description,
        )

        # 构建响应
        response = SnapshotResponse(
            snapshot_id=snapshot.snapshot_id,
            device_id=snapshot.device_id,
            device_ip=snapshot.device_ip,
            snapshot_type=snapshot.snapshot_type,
            config_size=snapshot.config_size,
            config_hash=snapshot.config_hash,
            created_at=snapshot.created_at,
            created_by=snapshot.created_by,
            description=snapshot.description,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建配置快照失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建配置快照失败: {str(e)}"
        ) from e


@router.get("/snapshot/device/{device_id}", summary="获取设备快照列表")
async def get_device_snapshots(
    device_id: str,
    limit: int | None = Query(None, description="限制数量", ge=1, le=100),
    snapshot_type: str | None = Query(None, description="快照类型过滤"),
):
    """获取指定设备的配置快照列表"""
    try:
        # 验证快照类型（如果提供）
        snapshot_type_enum = None
        if snapshot_type:
            try:
                snapshot_type_enum = SnapshotType(snapshot_type)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的快照类型: {snapshot_type}"
                ) from e

        # 获取快照列表
        snapshots = config_rollback_manager.get_device_snapshots(
            device_id=device_id, limit=limit, snapshot_type=snapshot_type_enum
        )

        # 构建响应
        response_snapshots = []
        for snapshot in snapshots:
            response_snapshots.append(
                {
                    "snapshot_id": snapshot.snapshot_id,
                    "device_id": snapshot.device_id,
                    "device_ip": snapshot.device_ip,
                    "snapshot_type": snapshot.snapshot_type.value,
                    "config_size": snapshot.config_size,
                    "config_hash": snapshot.config_hash,
                    "created_at": snapshot.created_at,
                    "created_by": snapshot.created_by,
                    "description": snapshot.description,
                }
            )

        return {"device_id": device_id, "total_snapshots": len(response_snapshots), "snapshots": response_snapshots}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备快照列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备快照列表失败: {str(e)}"
        ) from e


@router.get("/snapshot/{snapshot_id}/compare/{target_snapshot_id}", summary="对比两个快照")
async def compare_snapshots(snapshot_id: str, target_snapshot_id: str):
    """对比两个配置快照的差异"""
    try:
        comparison_result = config_rollback_manager.compare_snapshots(
            snapshot_id1=snapshot_id, snapshot_id2=target_snapshot_id
        )

        return comparison_result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"快照对比失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"快照对比失败: {str(e)}") from e


# ==================== 配置回滚端点 ====================


@router.post("/rollback/plan", response_model=RollbackPlanResponse, summary="创建回滚计划")
async def create_rollback_plan(request: CreateRollbackPlanRequest):
    """
    创建配置回滚计划

    回滚类型：
    - full: 完整回滚
    - partial: 部分回滚
    """
    try:
        # 创建回滚计划
        plan = config_rollback_manager.create_rollback_plan(
            device_id=request.device_id,
            target_snapshot_id=request.target_snapshot_id,
            created_by="api_user",  # 这里应该从认证信息获取
            description=request.description,
            rollback_type=request.rollback_type,
        )

        # 构建响应
        response = RollbackPlanResponse(
            plan_id=plan.plan_id,
            device_id=plan.device_id,
            device_ip=plan.device_ip,
            target_snapshot_id=plan.target_snapshot_id,
            rollback_type=plan.rollback_type,
            commands_count=len(plan.rollback_commands),
            estimated_duration=plan.estimated_duration,
            risk_level=plan.risk_level,
            created_at=plan.created_at,
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"创建回滚计划失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建回滚计划失败: {str(e)}"
        ) from e


@router.post("/rollback/execute", summary="执行回滚计划")
async def execute_rollback_plan(request: ExecuteRollbackRequest):
    """执行配置回滚计划"""
    try:
        # 执行回滚
        execution = await config_rollback_manager.execute_rollback(
            plan_id=request.plan_id, device_data=request.device_data, dry_run=request.dry_run
        )

        # 构建响应
        return {
            "execution_id": execution.execution_id,
            "plan_id": execution.plan_id,
            "device_id": execution.device_id,
            "device_ip": execution.device_ip,
            "status": execution.status.value,
            "start_time": execution.start_time,
            "end_time": execution.end_time,
            "duration": execution.duration,
            "executed_commands": len(execution.executed_commands),
            "failed_commands": len(execution.failed_commands),
            "error_message": execution.error_message,
            "dry_run": request.dry_run,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"执行回滚计划失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"执行回滚计划失败: {str(e)}"
        ) from e


@router.get("/rollback/device/{device_id}/history", summary="获取设备回滚历史")
async def get_device_rollback_history(
    device_id: str, limit: int | None = Query(None, description="限制数量", ge=1, le=100)
):
    """获取指定设备的回滚历史记录"""
    try:
        executions = config_rollback_manager.get_rollback_history(device_id=device_id, limit=limit)

        # 构建响应
        response_executions = []
        for execution in executions:
            response_executions.append(
                {
                    "execution_id": execution.execution_id,
                    "plan_id": execution.plan_id,
                    "status": execution.status.value,
                    "start_time": execution.start_time,
                    "end_time": execution.end_time,
                    "duration": execution.duration,
                    "executed_commands": len(execution.executed_commands),
                    "failed_commands": len(execution.failed_commands),
                    "error_message": execution.error_message,
                }
            )

        return {"device_id": device_id, "total_executions": len(response_executions), "executions": response_executions}

    except Exception as e:
        logger.error(f"获取设备回滚历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备回滚历史失败: {str(e)}"
        ) from e
