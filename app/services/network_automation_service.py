"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_automation_service.py
@DateTime: 2025/06/23 13:30:00
@Docs: 网络自动化服务层
"""

from typing import Any

from fastapi import HTTPException, status

from app.core.credential_manager import CredentialManager
from app.network_automation.inventory_manager import DynamicInventoryManager
from app.network_automation.network_tasks import (
    backup_config_task,
    deploy_config_task,
    execute_command_task,
    get_device_info_task,
    health_check_task,
    ping_task,
    template_render_task,
)
from app.network_automation.task_executor import NetworkTaskExecutor
from app.network_automation.high_performance_connection_manager import high_performance_connection_manager
from app.schemas.network_automation import TaskRequest
from app.utils.logger import logger


class NetworkAutomationService:
    """网络自动化服务类"""

    def __init__(self, max_workers: int = 30):
        """初始化网络自动化服务

        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers
        self._credential_manager = None
        self._inventory_manager = None
        self._task_executor = None

    @property
    def credential_manager(self) -> CredentialManager:
        """获取凭据管理器"""
        if self._credential_manager is None:
            self._credential_manager = CredentialManager()
        return self._credential_manager

    @property
    def inventory_manager(self) -> DynamicInventoryManager:
        """获取动态清单管理器"""
        if self._inventory_manager is None:
            self._inventory_manager = DynamicInventoryManager(self.credential_manager)
        return self._inventory_manager

    @property
    def task_executor(self) -> NetworkTaskExecutor:
        """获取任务执行器"""
        if self._task_executor is None:
            self._task_executor = NetworkTaskExecutor(self.inventory_manager, self.max_workers)
        return self._task_executor

    def validate_task_request(self, request: TaskRequest) -> None:
        """验证任务请求参数

        Args:
            request: 任务请求对象

        Raises:
            HTTPException: 当请求参数无效时
        """
        target_count = sum([bool(request.device_ids), bool(request.region_id), bool(request.group_id)])

        if target_count != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须指定且仅指定一个目标：device_ids、region_id 或 group_id",
            )

    async def execute_task_by_request(
        self, request: TaskRequest, task_func: Any, task_kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """根据请求执行任务

        Args:
            request: 任务请求对象
            task_func: 要执行的任务函数
            task_kwargs: 任务参数

        Returns:
            任务执行结果

        Raises:
            HTTPException: 当任务执行失败时
        """
        try:
            if request.device_ids:
                return await self.task_executor.execute_task_on_devices(
                    device_ids=request.device_ids,
                    task_func=task_func,
                    task_kwargs=task_kwargs,
                    runtime_credentials=request.runtime_credentials,
                )
            elif request.region_id:
                return await self.task_executor.execute_task_on_region(
                    region_id=request.region_id,
                    task_func=task_func,
                    task_kwargs=task_kwargs,
                    runtime_credentials=request.runtime_credentials,
                )
            elif request.group_id:
                return await self.task_executor.execute_task_on_group(
                    group_id=request.group_id,
                    task_func=task_func,
                    task_kwargs=task_kwargs,
                    runtime_credentials=request.runtime_credentials,
                )
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未指定有效的执行目标")
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"任务执行失败: {str(e)}"
            ) from e

    async def ping_devices(self, request: TaskRequest) -> dict[str, Any]:
        """执行Ping连通性测试

        Args:
            request: Ping测试请求

        Returns:
            测试结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(request=request, task_func=ping_task, task_kwargs={})

    async def execute_command(self, request: TaskRequest, command: str) -> dict[str, Any]:
        """执行单条命令

        Args:
            request: 命令执行请求
            command: 要执行的命令

        Returns:
            执行结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(
            request=request, task_func=execute_command_task, task_kwargs={"command": command}
        )

    async def execute_commands(self, request: TaskRequest, commands: list[str]) -> dict[str, Any]:
        """执行多条命令

        Args:
            request: 多命令执行请求
            commands: 要执行的命令列表

        Returns:
            执行结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(
            request=request, task_func=deploy_config_task, task_kwargs={"config_commands": commands}
        )

    async def backup_configuration(self, request: TaskRequest) -> dict[str, Any]:
        """备份设备配置

        Args:
            request: 配置备份请求

        Returns:
            备份结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(request=request, task_func=backup_config_task, task_kwargs={})

    async def deploy_configuration(self, request: TaskRequest, config_commands: list[str]) -> dict[str, Any]:
        """部署配置

        Args:
            request: 配置部署请求
            config_commands: 要部署的配置命令列表

        Returns:
            部署结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(
            request=request, task_func=deploy_config_task, task_kwargs={"config_commands": config_commands}
        )

    async def render_template(
        self, request: TaskRequest, template_content: str, template_vars: dict[str, Any]
    ) -> dict[str, Any]:
        """模板渲染

        Args:
            request: 模板渲染请求
            template_content: Jinja2模板内容
            template_vars: 模板变量

        Returns:
            渲染结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(
            request=request,
            task_func=template_render_task,
            task_kwargs={"template_content": template_content, "template_vars": template_vars},
        )

    async def get_device_info(self, request: TaskRequest) -> dict[str, Any]:
        """获取设备信息

        Args:
            request: 设备信息获取请求

        Returns:
            设备信息结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(request=request, task_func=get_device_info_task, task_kwargs={})

    async def health_check(self, request: TaskRequest) -> dict[str, Any]:
        """设备健康检查

        Args:
            request: 健康检查请求

        Returns:
            健康检查结果
        """
        self.validate_task_request(request)
        return await self.execute_task_by_request(request=request, task_func=health_check_task, task_kwargs={})

    async def get_connection_stats(self) -> dict[str, Any]:
        """获取连接池统计信息

        Returns:
            连接池统计
        """
        try:
            # 启动高性能连接管理器（如果还未启动）
            if not high_performance_connection_manager._started:
                await high_performance_connection_manager.start()
            
            # 获取详细的连接池统计
            return high_performance_connection_manager.get_connection_stats()
            
        except Exception as e:
            logger.error(f"获取连接统计失败: {e}")
            # 回退到基础连接管理器
            from app.network_automation.connection_manager import connection_manager
            return connection_manager.get_connection_stats()
