"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_rollback_manager.py
@DateTime: 2025/01/20 15:00:00
@Docs: 配置回滚管理器 - 提供配置快照、回滚、版本管理等功能
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.enums import RollbackStatus, SnapshotType
from app.network_automation.config_diff_manager import config_diff_manager
from app.network_automation.high_performance_connection_manager import high_performance_connection_manager
from app.utils.logger import logger


@dataclass
class ConfigSnapshot:
    """配置快照"""

    snapshot_id: str
    device_id: str
    device_ip: str
    device_name: str | None
    snapshot_type: SnapshotType
    config_content: str
    config_hash: str
    created_at: float
    created_by: str
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def created_datetime(self) -> datetime:
        """创建时间（datetime格式）"""
        return datetime.fromtimestamp(self.created_at)

    @property
    def config_size(self) -> int:
        """配置大小（字节）"""
        return len(self.config_content.encode("utf-8"))


@dataclass
class RollbackPlan:
    """回滚计划"""

    plan_id: str
    device_id: str
    device_ip: str
    source_snapshot_id: str
    target_snapshot_id: str
    rollback_type: str  # "full" 或 "partial"
    rollback_commands: list[str]
    estimated_duration: float
    risk_level: str
    created_at: float
    created_by: str
    description: str | None = None

    @property
    def created_datetime(self) -> datetime:
        """创建时间（datetime格式）"""
        return datetime.fromtimestamp(self.created_at)


@dataclass
class RollbackExecution:
    """回滚执行记录"""

    execution_id: str
    plan_id: str
    device_id: str
    device_ip: str
    status: RollbackStatus
    start_time: float | None = None
    end_time: float | None = None
    duration: float | None = None
    executed_commands: list[str] = field(default_factory=list)
    failed_commands: list[str] = field(default_factory=list)
    error_message: str | None = None
    rollback_result: dict[str, Any] | None = None

    @property
    def start_datetime(self) -> datetime | None:
        """开始时间（datetime格式）"""
        return datetime.fromtimestamp(self.start_time) if self.start_time else None

    @property
    def end_datetime(self) -> datetime | None:
        """结束时间（datetime格式）"""
        return datetime.fromtimestamp(self.end_time) if self.end_time else None


class ConfigRollbackManager:
    """配置回滚管理器"""

    def __init__(self):
        # 内存存储（生产环境应使用数据库）
        self.snapshots: dict[str, ConfigSnapshot] = {}
        self.rollback_plans: dict[str, RollbackPlan] = {}
        self.rollback_executions: dict[str, RollbackExecution] = {}

        # 设备快照索引
        self.device_snapshots: dict[str, list[str]] = {}

        # 配置分类规则（用于生成回滚命令）
        self.config_rules = {
            "interface": {
                "add_pattern": r"^interface\s+(.+)",
                "remove_command": "no interface {interface}",
                "modify_commands": ["shutdown", "no shutdown", "ip address", "description"],
            },
            "vlan": {
                "add_pattern": r"^vlan\s+(\d+)",
                "remove_command": "no vlan {vlan_id}",
                "modify_commands": ["name", "state"],
            },
            "access_list": {
                "add_pattern": r"^access-list\s+(.+)",
                "remove_command": "no access-list {acl_name}",
                "modify_commands": ["permit", "deny"],
            },
            "route": {
                "add_pattern": r"^ip\s+route\s+(.+)",
                "remove_command": "no ip route {route}",
                "modify_commands": [],
            },
        }

    async def create_snapshot(
        self, device_data: dict[str, Any], snapshot_type: SnapshotType, created_by: str, description: str | None = None
    ) -> ConfigSnapshot:
        """
        创建配置快照

        Args:
            device_data: 设备数据
            snapshot_type: 快照类型
            created_by: 创建者
            description: 描述

        Returns:
            配置快照
        """
        device_id = device_data.get("device_id", "")
        device_ip = device_data.get("hostname", device_data.get("ip", ""))
        device_name = device_data.get("device_name", "")

        logger.info(
            f"开始创建配置快照: {device_ip}",
            device_ip=device_ip,
            device_id=device_id,
            snapshot_type=snapshot_type.value,
            created_by=created_by,
        )

        try:
            # 获取当前配置
            backup_result = await high_performance_connection_manager.backup_configuration(device_data)

            if backup_result["status"] != "success":
                raise Exception(f"配置备份失败: {backup_result.get('error', 'Unknown error')}")

            config_content = backup_result["config_content"]

            # 计算配置哈希
            from app.utils.common_utils import calculate_hash

            config_hash = calculate_hash(config_content)

            # 创建快照
            snapshot = ConfigSnapshot(
                snapshot_id=str(uuid.uuid4()),
                device_id=device_id,
                device_ip=device_ip,
                device_name=device_name,
                snapshot_type=snapshot_type,
                config_content=config_content,
                config_hash=config_hash,
                created_at=time.time(),
                created_by=created_by,
                description=description,
                metadata={
                    "config_size": len(config_content),
                    "backup_duration": backup_result.get("elapsed_time", 0),
                    "platform": device_data.get("platform", "unknown"),
                },
            )

            # 存储快照
            self.snapshots[snapshot.snapshot_id] = snapshot

            # 更新设备快照索引
            if device_id not in self.device_snapshots:
                self.device_snapshots[device_id] = []
            self.device_snapshots[device_id].append(snapshot.snapshot_id)

            # 保持最近的快照数量（最多保留50个）
            if len(self.device_snapshots[device_id]) > 50:
                old_snapshot_id = self.device_snapshots[device_id].pop(0)
                if old_snapshot_id in self.snapshots:
                    del self.snapshots[old_snapshot_id]

            logger.info(
                f"配置快照创建成功: {device_ip}",
                device_ip=device_ip,
                device_id=device_id,
                snapshot_id=snapshot.snapshot_id,
                config_size=snapshot.config_size,
                config_hash=config_hash[:8],
            )

            return snapshot

        except Exception as e:
            logger.error(
                f"配置快照创建失败: {device_ip}",
                device_ip=device_ip,
                device_id=device_id,
                error=str(e),
                error_type=e.__class__.__name__,
            )
            raise

    def get_device_snapshots(
        self, device_id: str, limit: int | None = None, snapshot_type: SnapshotType | None = None
    ) -> list[ConfigSnapshot]:
        """
        获取设备的配置快照列表

        Args:
            device_id: 设备ID
            limit: 限制数量
            snapshot_type: 快照类型过滤

        Returns:
            快照列表
        """
        if device_id not in self.device_snapshots:
            return []

        snapshot_ids = self.device_snapshots[device_id]
        snapshots = []

        for snapshot_id in reversed(snapshot_ids):  # 最新的在前
            if snapshot_id in self.snapshots:
                snapshot = self.snapshots[snapshot_id]

                # 类型过滤
                if snapshot_type and snapshot.snapshot_type != snapshot_type:
                    continue

                snapshots.append(snapshot)

                # 数量限制
                if limit and len(snapshots) >= limit:
                    break

        return snapshots

    def compare_snapshots(self, snapshot_id1: str, snapshot_id2: str) -> dict[str, Any]:
        """
        对比两个快照

        Args:
            snapshot_id1: 快照1 ID
            snapshot_id2: 快照2 ID

        Returns:
            对比结果
        """
        if snapshot_id1 not in self.snapshots or snapshot_id2 not in self.snapshots:
            raise ValueError("快照不存在")

        snapshot1 = self.snapshots[snapshot_id1]
        snapshot2 = self.snapshots[snapshot_id2]

        if snapshot1.device_id != snapshot2.device_id:
            raise ValueError("不能对比不同设备的快照")

        logger.info(
            "开始对比配置快照", device_ip=snapshot1.device_ip, snapshot1_id=snapshot_id1, snapshot2_id=snapshot_id2
        )

        # 使用配置差异管理器进行对比
        diff_result = config_diff_manager.compare_configs(
            source_config=snapshot1.config_content,
            target_config=snapshot2.config_content,
            source_name=f"Snapshot {snapshot1.snapshot_id[:8]} ({snapshot1.created_datetime.strftime('%Y-%m-%d %H:%M:%S')})",
            target_name=f"Snapshot {snapshot2.snapshot_id[:8]} ({snapshot2.created_datetime.strftime('%Y-%m-%d %H:%M:%S')})",
        )

        return {
            "snapshot1": {
                "id": snapshot1.snapshot_id,
                "created_at": snapshot1.created_at,
                "type": snapshot1.snapshot_type.value,
                "hash": snapshot1.config_hash,
            },
            "snapshot2": {
                "id": snapshot2.snapshot_id,
                "created_at": snapshot2.created_at,
                "type": snapshot2.snapshot_type.value,
                "hash": snapshot2.config_hash,
            },
            "diff_result": diff_result,
            "comparison_summary": {
                "total_changes": diff_result.added_lines + diff_result.removed_lines + diff_result.modified_lines,
                "change_percentage": diff_result.change_percentage,
                "has_critical_changes": diff_result.has_critical_changes,
                "risk_level": diff_result.risk_assessment.get("overall_risk", "unknown"),
            },
        }

    def create_rollback_plan(
        self,
        device_id: str,
        target_snapshot_id: str,
        created_by: str,
        description: str | None = None,
        rollback_type: str = "full",
    ) -> RollbackPlan:
        """
        创建回滚计划

        Args:
            device_id: 设备ID
            target_snapshot_id: 目标快照ID
            created_by: 创建者
            description: 描述
            rollback_type: 回滚类型（full/partial）

        Returns:
            回滚计划
        """
        if target_snapshot_id not in self.snapshots:
            raise ValueError("目标快照不存在")

        target_snapshot = self.snapshots[target_snapshot_id]

        if target_snapshot.device_id != device_id:
            raise ValueError("快照设备ID不匹配")

        # 获取当前快照（最新的）
        current_snapshots = self.get_device_snapshots(device_id, limit=1)
        if not current_snapshots:
            raise ValueError("设备没有当前快照")

        current_snapshot = current_snapshots[0]

        logger.info(
            f"开始创建回滚计划: {target_snapshot.device_ip}",
            device_ip=target_snapshot.device_ip,
            device_id=device_id,
            target_snapshot_id=target_snapshot_id,
            rollback_type=rollback_type,
        )

        # 生成回滚命令
        rollback_commands = self._generate_rollback_commands(
            current_snapshot.config_content, target_snapshot.config_content, rollback_type
        )

        # 评估风险和预估时间
        risk_level = self._assess_rollback_risk(rollback_commands)
        estimated_duration = self._estimate_rollback_duration(rollback_commands)

        # 创建回滚计划
        plan = RollbackPlan(
            plan_id=str(uuid.uuid4()),
            device_id=device_id,
            device_ip=target_snapshot.device_ip,
            source_snapshot_id=current_snapshot.snapshot_id,
            target_snapshot_id=target_snapshot_id,
            rollback_type=rollback_type,
            rollback_commands=rollback_commands,
            estimated_duration=estimated_duration,
            risk_level=risk_level,
            created_at=time.time(),
            created_by=created_by,
            description=description,
        )

        # 存储计划
        self.rollback_plans[plan.plan_id] = plan

        logger.info(
            f"回滚计划创建成功: {target_snapshot.device_ip}",
            device_ip=target_snapshot.device_ip,
            plan_id=plan.plan_id,
            commands_count=len(rollback_commands),
            risk_level=risk_level,
            estimated_duration=estimated_duration,
        )

        return plan

    async def execute_rollback(
        self, plan_id: str, device_data: dict[str, Any], dry_run: bool = False
    ) -> RollbackExecution:
        """
        执行回滚计划

        Args:
            plan_id: 回滚计划ID
            device_data: 设备数据
            dry_run: 是否为试运行

        Returns:
            回滚执行记录
        """
        if plan_id not in self.rollback_plans:
            raise ValueError("回滚计划不存在")

        plan = self.rollback_plans[plan_id]

        logger.info(
            f"开始执行回滚: {plan.device_ip}",
            device_ip=plan.device_ip,
            plan_id=plan_id,
            dry_run=dry_run,
            commands_count=len(plan.rollback_commands),
        )

        # 创建执行记录
        execution = RollbackExecution(
            execution_id=str(uuid.uuid4()),
            plan_id=plan_id,
            device_id=plan.device_id,
            device_ip=plan.device_ip,
            status=RollbackStatus.IN_PROGRESS,
            start_time=time.time(),
        )

        # 存储执行记录
        self.rollback_executions[execution.execution_id] = execution

        try:
            if dry_run:
                # 试运行模式，只验证命令
                logger.info(f"回滚试运行完成: {plan.device_ip}")
                execution.status = RollbackStatus.SUCCESS
                execution.rollback_result = {
                    "dry_run": True,
                    "commands_to_execute": plan.rollback_commands,
                    "estimated_duration": plan.estimated_duration,
                }
            else:
                # 实际执行回滚
                if len(plan.rollback_commands) == 1:
                    # 单个命令，使用send_command
                    result = await high_performance_connection_manager.execute_command(
                        device_data, plan.rollback_commands[0]
                    )

                    if result["status"] == "success":
                        execution.executed_commands = plan.rollback_commands
                        execution.status = RollbackStatus.SUCCESS
                    else:
                        execution.failed_commands = plan.rollback_commands
                        execution.status = RollbackStatus.FAILED
                        execution.error_message = result.get("error", "Command execution failed")

                    execution.rollback_result = result
                else:
                    # 多个命令，使用send_commands
                    result = await high_performance_connection_manager.execute_commands(
                        device_data, plan.rollback_commands
                    )

                    successful_commands = [
                        cmd["command"] for cmd in result.get("commands_detail", []) if cmd["status"] == "success"
                    ]
                    failed_commands = [
                        cmd["command"] for cmd in result.get("commands_detail", []) if cmd["status"] == "failed"
                    ]

                    execution.executed_commands = successful_commands
                    execution.failed_commands = failed_commands

                    if result.get("successful_commands", 0) == len(plan.rollback_commands):
                        execution.status = RollbackStatus.SUCCESS
                    elif result.get("successful_commands", 0) > 0:
                        execution.status = RollbackStatus.PARTIAL
                    else:
                        execution.status = RollbackStatus.FAILED
                        execution.error_message = "All commands failed"

                    execution.rollback_result = result

        except Exception as e:
            execution.status = RollbackStatus.FAILED
            execution.error_message = str(e)

            logger.error(
                f"回滚执行失败: {plan.device_ip}",
                device_ip=plan.device_ip,
                plan_id=plan_id,
                error=str(e),
                error_type=e.__class__.__name__,
            )

        finally:
            execution.end_time = time.time()
            if execution.start_time is not None and execution.end_time is not None:
                execution.duration = execution.end_time - execution.start_time
            else:
                execution.duration = None

            logger.info(
                f"回滚执行完成: {plan.device_ip}",
                device_ip=plan.device_ip,
                plan_id=plan_id,
                execution_id=execution.execution_id,
                status=execution.status.value,
                duration=execution.duration,
                executed_commands=len(execution.executed_commands),
                failed_commands=len(execution.failed_commands),
            )

        return execution

    def _generate_rollback_commands(self, current_config: str, target_config: str, rollback_type: str) -> list[str]:
        """生成回滚命令"""
        # 使用配置差异管理器分析差异
        diff_result = config_diff_manager.compare_configs(
            source_config=current_config, target_config=target_config, source_name="Current", target_name="Target"
        )

        rollback_commands = []

        # 根据差异生成回滚命令
        for section in diff_result.sections:
            for line in section.lines:
                if line.diff_type.value == "removed":
                    # 目标配置中删除的行，需要添加回来
                    rollback_commands.append(line.content.strip())
                elif line.diff_type.value == "added":
                    # 目标配置中新增的行，需要删除
                    no_command = self._generate_no_command(line.content.strip())
                    if no_command:
                        rollback_commands.append(no_command)

        # 如果没有生成具体命令，使用完整配置替换
        if not rollback_commands and rollback_type == "full":
            # 这里可以实现完整配置替换的逻辑
            # 例如：copy running-config startup-config 等
            rollback_commands = [
                "! Full configuration rollback",
                "! This would require platform-specific implementation",
            ]

        return rollback_commands

    def _generate_no_command(self, command: str) -> str | None:
        """生成no命令"""
        command = command.strip()

        # 如果已经是no命令，则返回原命令（去掉no）
        if command.startswith("no "):
            return command[3:]

        # 否则添加no前缀
        return f"no {command}"

    def _assess_rollback_risk(self, commands: list[str]) -> str:
        """评估回滚风险"""
        global re
        high_risk_patterns = [r"no\s+interface", r"no\s+ip\s+route", r"no\s+router", r"shutdown", r"no\s+access-list"]

        medium_risk_patterns = [r"no\s+vlan", r"no\s+switchport", r"description"]

        high_risk_count = 0
        medium_risk_count = 0

        for command in commands:
            command_lower = command.lower()

            for pattern in high_risk_patterns:
                import re

                if re.search(pattern, command_lower):
                    high_risk_count += 1
                    break
            else:
                for pattern in medium_risk_patterns:
                    if re.search(pattern, command_lower):
                        medium_risk_count += 1
                        break

        if high_risk_count > 0:
            return "high"
        elif medium_risk_count > 5:
            return "medium"
        elif medium_risk_count > 0:
            return "low"
        else:
            return "minimal"

    def _estimate_rollback_duration(self, commands: list[str]) -> float:
        """预估回滚时间"""
        # 基础时间：连接建立等
        base_time = 10.0

        # 每个命令的平均执行时间
        command_time = 2.0

        # 复杂命令的额外时间
        complex_commands = ["interface", "router", "access-list", "crypto"]

        total_time = base_time

        for command in commands:
            total_time += command_time

            # 检查是否为复杂命令
            for complex_cmd in complex_commands:
                if complex_cmd in command.lower():
                    total_time += 5.0  # 额外5秒
                    break

        return total_time

    def get_rollback_history(self, device_id: str, limit: int | None = None) -> list[RollbackExecution]:
        """获取设备的回滚历史"""
        executions = []

        for execution in self.rollback_executions.values():
            if execution.device_id == device_id:
                executions.append(execution)

        # 按时间倒序排列
        executions.sort(key=lambda x: x.start_time or 0, reverse=True)

        if limit:
            executions = executions[:limit]

        return executions

    def get_snapshot(self, snapshot_id: str) -> ConfigSnapshot | None:
        """获取快照"""
        return self.snapshots.get(snapshot_id)

    def get_rollback_plan(self, plan_id: str) -> RollbackPlan | None:
        """获取回滚计划"""
        return self.rollback_plans.get(plan_id)

    def get_rollback_execution(self, execution_id: str) -> RollbackExecution | None:
        """获取回滚执行记录"""
        return self.rollback_executions.get(execution_id)


# 全局配置回滚管理器实例
config_rollback_manager = ConfigRollbackManager()
