"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_log_service.py
@DateTime: 2025/06/20 00:00:00
@Docs: 操作日志服务层实现
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationError
from app.models.network_models import OperationLog, OperationStatusEnum
from app.repositories.operation_log_dao import OperationLogDAO
from app.schemas.base import BaseUpdateSchema
from app.schemas.operation_log import (
    OperationLogCreateRequest,
    OperationLogListResponse,
    OperationLogQueryParams,
    OperationLogStatsResponse,
)
from app.services.base_service import BaseService
from app.utils.logger import logger


class OperationLogUpdateRequest(BaseUpdateSchema):
    """操作日志更新请求

    注意：操作日志作为审计记录，通常不允许更新
    此类仅为满足BaseService类型要求而存在
    """

    pass


class OperationLogService(
    BaseService[
        OperationLog,
        OperationLogCreateRequest,
        OperationLogUpdateRequest,
        OperationLogListResponse,
        OperationLogQueryParams,
    ]
):
    """操作日志服务层

    提供操作日志相关的业务逻辑处理，包括：
    - 操作日志的创建和查询
    - 日志统计分析
    - 日志清理和归档
    - 设备操作历史追踪
    """

    def __init__(self, dao: OperationLogDAO):
        """初始化操作日志服务

        Args:
            dao: 操作日志数据访问对象
        """
        super().__init__(dao=dao, response_schema=OperationLogListResponse, entity_name="操作日志")

    async def _validate_create_data(self, data: OperationLogCreateRequest) -> None:
        """验证操作日志创建数据

        Args:
            data: 操作日志创建数据

        Raises:
            ValidationError: 验证失败
        """
        # 验证设备ID和模板ID至少有一个不为空
        if not data.device_id and not data.template_id:
            raise ValidationError("设备ID和模板ID至少需要指定一个")

        # 验证操作状态
        valid_statuses = [status.value for status in OperationStatusEnum]
        if data.status not in valid_statuses:
            raise ValidationError(f"无效的操作状态: {data.status}")

        # 如果状态为失败，必须提供错误信息
        if data.status == OperationStatusEnum.FAILURE and not data.error_message:
            raise ValidationError("操作失败时必须提供错误信息")

        logger.debug(f"操作日志创建数据验证通过: 设备ID={data.device_id}, 状态={data.status}")

    def _build_filters(self, query_params: OperationLogQueryParams) -> dict[str, Any]:
        """构建操作日志查询过滤条件

        Args:
            query_params: 查询参数

        Returns:
            过滤条件字典
        """
        filters = super()._build_filters(query_params)

        # 按设备ID过滤
        if query_params.device_id:
            filters["device_id"] = str(query_params.device_id)

        # 按模板ID过滤
        if query_params.template_id:
            filters["template_id"] = str(query_params.template_id)

        # 按操作状态过滤
        if query_params.status:
            filters["status"] = query_params.status

        # 按操作者过滤
        if query_params.executed_by:
            filters["executed_by__icontains"] = query_params.executed_by

        # 按时间范围过滤
        if query_params.start_time:
            filters["created_at__gte"] = query_params.start_time

        if query_params.end_time:
            filters["created_at__lte"] = query_params.end_time

        # 按是否有错误过滤
        if query_params.has_error is not None:
            if query_params.has_error:
                filters["error_message__isnull"] = False
            else:
                filters["error_message__isnull"] = True  # 按命令内容搜索
        if query_params.command_contains:
            filters["command_executed__icontains"] = query_params.command_contains

        return filters

    def _get_prefetch_related(self) -> list[str]:
        """获取需要预加载的关联字段

        Returns:
            预加载字段列表
        """
        return ["device", "template"]

    async def create_operation_log(
        self,
        device_id: UUID | None = None,
        template_id: UUID | None = None,
        command: str | None = None,
        output: str | None = None,
        parsed_output: dict | None = None,
        status: OperationStatusEnum = OperationStatusEnum.SUCCESS,
        error_message: str | None = None,
        executed_by: str | None = None,
    ) -> OperationLogListResponse:
        """创建操作日志

        Args:
            device_id: 设备ID
            template_id: 模板ID
            command: 执行的命令
            output: 设备输出
            parsed_output: 解析后的输出
            status: 操作状态
            error_message: 错误信息
            executed_by: 操作者

        Returns:
            创建的操作日志响应
        """
        try:
            log_data = OperationLogCreateRequest(
                device_id=device_id,
                template_id=template_id,
                command_executed=command,
                output_received=output,
                parsed_output=parsed_output,
                status=status,
                error_message=error_message,
                executed_by=executed_by,
            )

            return await self.create(log_data)

        except Exception as e:
            logger.error(f"创建操作日志失败: {e}")
            raise

    async def get_device_operation_history(
        self, device_id: UUID, days: int = 30, status: OperationStatusEnum | None = None
    ) -> list[OperationLogListResponse]:
        """获取设备操作历史

        Args:
            device_id: 设备ID
            days: 查询天数
            status: 操作状态过滤

        Returns:
            操作日志列表
        """
        try:
            start_time = datetime.now() - timedelta(days=days)
            filters = {
                "device_id": str(device_id),
                "created_at__gte": start_time,
                "is_deleted": False,
            }

            if status:
                filters["status"] = status

            logs = await self.dao.list_by_filters(filters)
            # 按创建时间倒序排列
            logs.sort(key=lambda x: x.created_at, reverse=True)

            return [self.response_schema.model_validate(log) for log in logs]

        except Exception as e:
            logger.error(f"获取设备 {device_id} 操作历史失败: {e}")
            raise

    async def get_operation_stats(self, days: int = 7) -> OperationLogStatsResponse:
        """获取操作统计信息

        Args:
            days: 统计天数

        Returns:
            操作统计响应
        """
        try:
            start_time = datetime.now() - timedelta(days=days)
            base_filters = {"created_at__gte": start_time, "is_deleted": False}

            # 统计各种状态的操作数量
            total_operations = await self.dao.count(**base_filters)
            success_operations = await self.dao.count(**base_filters, status=OperationStatusEnum.SUCCESS)
            failed_operations = await self.dao.count(**base_filters, status=OperationStatusEnum.FAILURE)
            pending_operations = await self.dao.count(**base_filters, status=OperationStatusEnum.PENDING)

            # 计算成功率
            success_rate = (success_operations / total_operations * 100) if total_operations > 0 else 0

            # 获取今日、本周、本月的操作统计
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            month_start = today_start.replace(day=1)

            today_operations = await self.dao.count(created_at__gte=today_start, is_deleted=False)
            week_operations = await self.dao.count(created_at__gte=week_start, is_deleted=False)
            month_operations = await self.dao.count(created_at__gte=month_start, is_deleted=False)

            from uuid import uuid4

            return OperationLogStatsResponse(
                id=uuid4(),  # 为统计响应生成临时ID
                total_operations=total_operations,
                success_operations=success_operations,
                failed_operations=failed_operations,
                pending_operations=pending_operations,
                success_rate=round(success_rate, 2),
                today_operations=today_operations,
                week_operations=week_operations,
                month_operations=month_operations,
                top_devices=[],  # 暂时为空，可后续实现
                top_templates=[],  # 暂时为空，可后续实现
                top_operators=[],  # 暂时为空，可后续实现
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_deleted=False,
                description=f"最近 {days} 天的操作统计",
            )

        except Exception as e:
            logger.error(f"获取操作统计失败: {e}")
            raise

    async def get_failed_operations(self, days: int = 7) -> list[OperationLogListResponse]:
        """获取失败的操作列表

        Args:
            days: 查询天数

        Returns:
            失败操作列表
        """
        try:
            start_time = datetime.now() - timedelta(days=days)
            filters = {
                "status": OperationStatusEnum.FAILURE,
                "created_at__gte": start_time,
                "is_deleted": False,
            }

            logs = await self.dao.list_by_filters(filters)
            # 按创建时间倒序排列
            logs.sort(key=lambda x: x.created_at, reverse=True)

            return [self.response_schema.model_validate(log) for log in logs]

        except Exception as e:
            logger.error(f"获取失败操作列表失败: {e}")
            raise

    async def search_by_command(self, command_keyword: str, days: int = 30) -> list[OperationLogListResponse]:
        """根据命令关键字搜索操作日志

        Args:
            command_keyword: 命令关键字
            days: 搜索天数范围

        Returns:
            匹配的操作日志列表
        """
        try:
            start_time = datetime.now() - timedelta(days=days)
            filters = {
                "command_executed__icontains": command_keyword,
                "created_at__gte": start_time,
                "is_deleted": False,
            }

            logs = await self.dao.list_by_filters(filters)
            # 按创建时间倒序排列
            logs.sort(key=lambda x: x.created_at, reverse=True)

            return [self.response_schema.model_validate(log) for log in logs]

        except Exception as e:
            logger.error(f"按命令搜索操作日志失败，关键字: {command_keyword}, 错误: {e}")
            raise

    async def cleanup_old_logs(self, days: int = 90) -> dict:
        """清理旧的操作日志

        Args:
            days: 保留天数，超过此天数的日志将被清理

        Returns:
            清理结果
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)

            # 统计要清理的日志数量
            count_to_delete = await self.dao.count(created_at__lt=cutoff_time, is_deleted=False)

            if count_to_delete == 0:
                return {"deleted_count": 0, "message": f"没有超过 {days} 天的操作日志需要清理"}

            # 获取要删除的日志ID
            old_logs = await self.dao.list_by_filters({"created_at__lt": cutoff_time, "is_deleted": False})
            deleted_count = 0  # 逐个删除
            for log in old_logs:
                await self.dao.delete_by_id(log.id)
                deleted_count += 1

            logger.info(f"清理了 {deleted_count} 条超过 {days} 天的操作日志")

            return {
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_time.strftime("%Y-%m-%d"),
                "message": f"成功清理 {deleted_count} 条操作日志",
            }

        except Exception as e:
            logger.error(f"清理操作日志失败: {e}")
            raise

    async def get_top_error_messages(self, days: int = 7, limit: int = 10) -> list[dict]:
        """获取最常见的错误信息

        Args:
            days: 统计天数
            limit: 返回数量限制

        Returns:
            错误信息统计列表
        """
        try:
            start_time = datetime.now() - timedelta(days=days)

            # 获取失败的操作日志
            failed_logs = await self.dao.list_by_filters(
                {
                    "status": OperationStatusEnum.FAILURE,
                    "created_at__gte": start_time,
                    "is_deleted": False,
                    "error_message__isnull": False,
                }
            )

            # 统计错误信息出现次数
            error_counts = {}
            for log in failed_logs:
                if log.error_message:
                    error_msg = log.error_message.strip()
                    error_counts[error_msg] = error_counts.get(error_msg, 0) + 1

            # 按出现次数排序
            sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)

            # 返回前N条
            return [{"error_message": error_msg, "count": count} for error_msg, count in sorted_errors[:limit]]

        except Exception as e:
            logger.error(f"获取错误信息统计失败: {e}")
            raise

    async def get_operation_trend(self, days: int = 30) -> list[dict]:
        """获取操作趋势数据

        Args:
            days: 统计天数

        Returns:
            每日操作趋势列表
        """
        try:
            start_time = datetime.now() - timedelta(days=days)

            # 获取指定时间范围内的所有日志
            logs = await self.dao.list_by_filters(
                {
                    "created_at__gte": start_time,
                    "is_deleted": False,
                }
            )

            # 按日期分组统计
            daily_stats = {}
            for log in logs:
                date_str = log.created_at.strftime("%Y-%m-%d")
                if date_str not in daily_stats:
                    daily_stats[date_str] = {"total": 0, "success": 0, "failed": 0}

                daily_stats[date_str]["total"] += 1
                if log.status == OperationStatusEnum.SUCCESS:
                    daily_stats[date_str]["success"] += 1
                elif log.status == OperationStatusEnum.FAILURE:
                    daily_stats[date_str]["failed"] += 1

            # 生成完整的日期序列
            result = []
            current_date = start_time.date()
            end_date = datetime.now().date()

            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                stats = daily_stats.get(date_str, {"total": 0, "success": 0, "failed": 0})
                success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0

                result.append(
                    {
                        "date": date_str,
                        "total_count": stats["total"],
                        "success_count": stats["success"],
                        "failed_count": stats["failed"],
                        "success_rate": round(success_rate, 2),
                    }
                )

                current_date += timedelta(days=1)

            return result

        except Exception as e:
            logger.error(f"获取操作趋势失败: {e}")
            raise
