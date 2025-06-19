"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_log_dao.py
@DateTime: 2025-06-20
@Docs: 操作日志数据访问层实现
"""

from datetime import datetime, timedelta

from app.models.network_models import OperationLog
from app.repositories.base_dao import BaseDAO


class OperationLogDAO(BaseDAO[OperationLog]):
    """操作日志数据访问层

    继承BaseDAO，提供操作日志相关的数据访问方法
    """

    def __init__(self):
        """初始化操作日志DAO"""
        super().__init__(OperationLog)

    async def get_by_device(self, device_id: int) -> list[OperationLog]:
        """根据设备ID获取操作日志列表

        Args:
            device_id: 设备ID

        Returns:
            操作日志列表
        """
        return await self.list_by_filters(
            {"device_id": device_id}, prefetch_related=["device"], order_by=["-timestamp"]
        )

    async def get_by_status(self, status: str) -> list[OperationLog]:
        """根据操作状态获取操作日志列表

        Args:
            status: 操作状态

        Returns:
            操作日志列表
        """
        return await self.list_by_filters({"status": status}, prefetch_related=["device"], order_by=["-timestamp"])

    async def get_by_executed_by(self, executed_by: str) -> list[OperationLog]:
        """根据执行者获取操作日志列表

        Args:
            executed_by: 执行者

        Returns:
            操作日志列表
        """
        return await self.list_by_filters(
            {"executed_by": executed_by}, prefetch_related=["device"], order_by=["-timestamp"]
        )

    async def get_recent_logs(self, limit: int = 100) -> list[OperationLog]:
        """获取最近的操作日志

        Args:
            limit: 限制数量

        Returns:
            最近的操作日志列表
        """
        queryset = self.get_queryset()
        return await queryset.prefetch_related("device").order_by("-timestamp").limit(limit)

    async def get_failed_operations(self) -> list[OperationLog]:
        """获取失败的操作日志

        Returns:
            失败的操作日志列表
        """
        return await self.list_by_filters({"status": "failure"}, prefetch_related=["device"], order_by=["-timestamp"])

    async def search_by_command_executed(self, keyword: str) -> list[OperationLog]:
        """根据执行命令关键字搜索操作日志

        Args:
            keyword: 搜索关键字

        Returns:
            匹配的操作日志列表
        """
        return await self.list_by_filters(
            {"command_executed": keyword},  # 会被_apply_filters转换为模糊查询
            prefetch_related=["device"],
            order_by=["-timestamp"],
        )

    async def log_operation(
        self,
        device_id: int,
        executed_by: str,
        command_executed: str,
        output_received: str | None = None,
        status: str = "success",
        error_message: str | None = None,
        template_id: int | None = None,
        parsed_output: dict | None = None,
    ) -> OperationLog:
        """记录操作日志

        Args:
            device_id: 设备ID
            executed_by: 执行者
            command_executed: 执行的命令
            output_received: 接收的输出
            status: 操作状态
            error_message: 错误信息
            template_id: 模板ID
            parsed_output: 解析后的输出

        Returns:
            创建的操作日志
        """
        return await self.create(
            device_id=device_id,
            executed_by=executed_by,
            command_executed=command_executed,
            output_received=output_received,
            status=status,
            error_message=error_message,
            template_id=template_id,
            parsed_output=parsed_output,
            timestamp=datetime.now(),
        )

    async def paginate_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        device_id: int | None = None,
        status: str | None = None,
        executed_by: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """分页获取操作日志（性能优化版本）

        Args:
            page: 页码
            page_size: 每页大小
            device_id: 设备ID过滤
            status: 状态过滤
            executed_by: 执行者过滤
            start_date: 开始时间过滤
            end_date: 结束时间过滤

        Returns:
            分页日志列表
        """
        filters = {}
        if device_id:
            filters["device_id"] = device_id
        if status:
            filters["status"] = status
        if executed_by:
            filters["executed_by"] = executed_by
        if start_date:
            filters["timestamp__gte"] = start_date
        if end_date:
            filters["timestamp__lte"] = end_date

        return await self.paginate(
            page=page,
            page_size=page_size,
            filters=filters,
            prefetch_related=["device", "template"],
            order_by=["-timestamp"],  # 最新的在前面
        )

    async def get_logs_statistics(self) -> dict:
        """获取日志统计信息（优化版本）

        Returns:
            日志统计信息
        """
        from tortoise.functions import Count

        # 今日日志统计
        today = datetime.now().date()
        today_logs = await self.count(timestamp__gte=today)

        # 近7天日志统计
        week_ago = today - timedelta(days=7)
        week_logs = await self.count(timestamp__gte=week_ago)

        # 按状态统计
        status_stats = await self.get_count_by_status("status")

        # 按设备统计Top10
        device_stats = await (
            self.model.all()
            .group_by("device_id")
            .annotate(count=Count("id"))
            .prefetch_related("device")
            .order_by("-count")
            .limit(10)
            .values("device__name", "count")
        )

        return {
            "today_logs": today_logs,
            "week_logs": week_logs,
            "by_status": status_stats,
            "top_devices": device_stats,
        }

    async def bulk_update_logs(self, updates: list[dict]) -> int:
        """批量更新操作日志

        Args:
            updates: 更新数据列表

        Returns:
            更新的记录数量
        """
        return await self.bulk_update(updates, key_field="id")

    async def get_recent_failed_logs(self, limit: int = 20) -> list:
        """获取最近的失败日志（优化版本）

        Args:
            limit: 限制数量

        Returns:
            最近的失败日志列表
        """
        return await self.list_by_filters(
            filters={"status": "failure"}, prefetch_related=["device"], order_by=["-timestamp"]
        )

    async def search_logs_by_command(self, keyword: str, page: int = 1, page_size: int = 20) -> dict:
        """根据命令内容搜索日志（分页）

        Args:
            keyword: 搜索关键字
            page: 页码
            page_size: 每页大小

        Returns:
            分页搜索结果
        """
        filters = {"command_executed": keyword}

        return await self.paginate(
            page=page, page_size=page_size, filters=filters, prefetch_related=["device"], order_by=["-timestamp"]
        )
