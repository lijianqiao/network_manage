"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: high_performance_connection_manager.py
@DateTime: 2025/01/20 13:00:00
@Docs: 高性能连接管理器 - 集成高级连接池和性能监控
"""

import time
from typing import Any

from app.core.exceptions import CommandExecutionError, DeviceAuthenticationError, DeviceConnectionError
from app.network_automation.advanced_connection_pool import advanced_connection_pool
from app.network_automation.performance_monitor import performance_monitor
from app.utils.logger import logger
from app.utils.network_logger import log_command_execution, log_command_execution_result, log_network_operation


class HighPerformanceConnectionManager:
    """高性能连接管理器

    集成高级连接池、性能监控、动态并发控制等功能
    """

    def __init__(self):
        self.pool = advanced_connection_pool
        self.monitor = performance_monitor
        self._started = False

    async def start(self) -> None:
        """启动连接管理器"""
        if self._started:
            return

        self._started = True
        await self.pool.start()
        await self.monitor.start()

        logger.info("高性能连接管理器已启动")

    async def stop(self) -> None:
        """停止连接管理器"""
        if not self._started:
            return

        self._started = False
        await self.pool.stop()
        await self.monitor.stop()

        logger.info("高性能连接管理器已停止")

    @log_network_operation("connectivity_test", include_args=False)
    async def test_connectivity(self, host_data: dict[str, Any]) -> dict[str, Any]:
        """测试设备连通性"""
        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id")
        start_time = time.time()

        try:
            async with self.pool.get_connection(host_data) as conn:
                # 发送简单命令测试连接
                logger.debug(f"发送测试命令到 {device_ip}")
                response = await conn.send_command("show version", strip_prompt=False)

                end_time = time.time()
                duration = end_time - start_time

                # 记录性能指标
                self.monitor.record_operation(
                    operation_type="connectivity_test",
                    device_ip=device_ip,
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                )

                result = {
                    "hostname": device_ip,
                    "status": "success",
                    "message": "设备连通性正常",
                    "response_time": round(duration, 3),
                    "platform_detected": getattr(conn, "platform", "unknown"),
                    "response_length": len(response.result) if hasattr(response, "result") else 0,
                }

                logger.info(
                    f"连通性测试成功: {device_ip}",
                    device_ip=device_ip,
                    device_id=device_id,
                    response_time=duration,
                    platform=result["platform_detected"],
                )

                return result

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # 记录性能指标
            self.monitor.record_operation(
                operation_type="connectivity_test",
                device_ip=device_ip,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )

            logger.warning(
                f"连通性测试失败 {device_ip}: {e}",
                device_ip=device_ip,
                device_id=device_id,
                error=str(e),
                response_time=duration,
            )

            return {
                "hostname": device_ip,
                "status": "failed",
                "message": f"连通性测试失败: {str(e)}",
                "error": str(e),
                "response_time": round(duration, 3),
                "error_type": type(e).__name__,
            }

    @log_network_operation("command_execution", include_args=False)
    async def execute_command(self, host_data: dict[str, Any], command: str) -> dict[str, Any]:
        """执行单条命令"""
        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id")
        start_time = time.time()

        # 记录命令执行开始
        log_command_execution(device_ip, command, device_id)

        try:
            async with self.pool.get_connection(host_data) as conn:
                logger.info(f"执行命令: {command}", device_ip=device_ip, device_id=device_id, command=command)

                response = await conn.send_command(command)
                end_time = time.time()
                duration = end_time - start_time

                # 记录性能指标
                self.monitor.record_operation(
                    operation_type="command_execution",
                    device_ip=device_ip,
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                )

                # 记录命令执行结果
                log_command_execution_result(
                    device_ip=device_ip, command=command, success=True, duration=duration, device_id=device_id
                )

                result = {
                    "hostname": device_ip,
                    "command": command,
                    "status": "success",
                    "output": response.result,
                    "elapsed_time": round(duration, 3),
                }

                logger.info(
                    f"命令执行成功: {command}",
                    device_ip=device_ip,
                    device_id=device_id,
                    command=command,
                    duration=duration,
                    output_length=len(response.result),
                )

                return result

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # 记录性能指标
            self.monitor.record_operation(
                operation_type="command_execution",
                device_ip=device_ip,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )

            # 记录命令执行结果
            log_command_execution_result(
                device_ip=device_ip,
                command=command,
                success=False,
                duration=duration,
                error=str(e),
                device_id=device_id,
            )

            logger.error(
                f"命令执行失败: {command}",
                device_ip=device_ip,
                device_id=device_id,
                command=command,
                error=str(e),
                error_type=e.__class__.__name__,
                duration=duration,
            )

            # 根据错误类型抛出相应异常
            if isinstance(e, DeviceConnectionError | DeviceAuthenticationError):
                raise
            else:
                raise CommandExecutionError(
                    message=f"命令执行失败: {command}",
                    detail=str(e),
                    device_id=device_id,
                    device_ip=device_ip,
                    command=command,
                    error_output=str(e),
                ) from e

    @log_network_operation("batch_command_execution", include_args=False)
    async def execute_commands(self, host_data: dict[str, Any], commands: list[str]) -> dict[str, Any]:
        """执行多条命令 - 使用Scrapli原生send_commands方法"""
        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id")
        total_start_time = time.time()

        try:
            async with self.pool.get_connection(host_data) as conn:
                logger.info(
                    f"使用send_commands批量执行 {len(commands)} 条命令",
                    device_ip=device_ip,
                    device_id=device_id,
                    commands_count=len(commands),
                )

                # 使用Scrapli原生的send_commands方法
                responses = await conn.send_commands(commands)

                total_end_time = time.time()
                total_duration = total_end_time - total_start_time

                # 处理响应结果
                results = []
                successful_commands = 0

                for i, response in enumerate(responses):
                    command = commands[i] if i < len(commands) else f"command_{i}"

                    if response.failed:
                        # 记录失败的命令
                        self.monitor.record_operation(
                            operation_type="command_execution",
                            device_ip=device_ip,
                            device_id=device_id,
                            start_time=total_start_time,
                            end_time=total_end_time,
                            success=False,
                            error_type="CommandFailed",
                            error_message=getattr(response, "error", "Command execution failed"),
                        )

                        results.append(
                            {
                                "command": command,
                                "status": "failed",
                                "output": "",
                                "error": getattr(response, "error", "Command execution failed"),
                                "elapsed_time": response.elapsed_time if hasattr(response, "elapsed_time") else 0,
                            }
                        )
                    else:
                        # 记录成功的命令
                        self.monitor.record_operation(
                            operation_type="command_execution",
                            device_ip=device_ip,
                            device_id=device_id,
                            start_time=total_start_time,
                            end_time=total_end_time,
                            success=True,
                        )

                        successful_commands += 1
                        results.append(
                            {
                                "command": command,
                                "status": "success",
                                "output": response.result,
                                "elapsed_time": response.elapsed_time if hasattr(response, "elapsed_time") else 0,
                            }
                        )

                # 记录批量操作的性能指标
                self.monitor.record_operation(
                    operation_type="batch_command_execution",
                    device_ip=device_ip,
                    device_id=device_id,
                    start_time=total_start_time,
                    end_time=total_end_time,
                    success=successful_commands > 0,
                )

                logger.info(
                    f"批量命令执行完成: {successful_commands}/{len(commands)} 成功",
                    device_ip=device_ip,
                    device_id=device_id,
                    successful_commands=successful_commands,
                    failed_commands=len(commands) - successful_commands,
                    total_duration=total_duration,
                )

                return {
                    "hostname": device_ip,
                    "total_commands": len(commands),
                    "successful_commands": successful_commands,
                    "failed_commands": len(commands) - successful_commands,
                    "total_time": round(total_duration, 3),
                    "commands_detail": results,
                }

        except Exception as e:
            total_end_time = time.time()
            total_duration = total_end_time - total_start_time

            # 记录批量操作失败
            self.monitor.record_operation(
                operation_type="batch_command_execution",
                device_ip=device_ip,
                device_id=device_id,
                start_time=total_start_time,
                end_time=total_end_time,
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )

            logger.error(
                f"批量命令执行失败 {device_ip}: {e}",
                device_ip=device_ip,
                device_id=device_id,
                commands_count=len(commands),
                error=str(e),
                duration=total_duration,
            )

            return {
                "hostname": device_ip,
                "total_commands": len(commands),
                "successful_commands": 0,
                "failed_commands": len(commands),
                "total_time": round(total_duration, 3),
                "error": str(e),
                "error_type": type(e).__name__,
                "commands_detail": [{"command": cmd, "status": "failed", "error": str(e)} for cmd in commands],
            }

    @log_network_operation("device_facts_collection", include_args=False)
    async def get_device_facts(self, host_data: dict[str, Any]) -> dict[str, Any]:
        """获取设备基础信息"""
        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id")
        start_time = time.time()

        try:
            async with self.pool.get_connection(host_data) as conn:
                # 尝试获取设备版本信息
                version_response = await conn.send_command("show version")

                facts = {
                    "hostname": device_ip,
                    "platform": getattr(conn, "platform", "unknown"),
                    "version_output": version_response.result,
                    "status": "success",
                }

                # 尝试获取更多信息（根据平台）
                try:
                    platform = host_data.get("platform", "").lower()
                    if "cisco" in platform:
                        inventory_response = await conn.send_command("show inventory")
                        facts["inventory"] = inventory_response.result
                    elif "huawei" in platform:
                        system_response = await conn.send_command("display device")
                        facts["system_info"] = system_response.result
                    elif "h3c" in platform or "comware" in platform:
                        device_response = await conn.send_command("display device")
                        facts["device_info"] = device_response.result
                except Exception as extra_info_error:
                    logger.debug(f"获取额外设备信息失败 {device_ip}: {extra_info_error}")

                end_time = time.time()

                # 记录性能指标
                self.monitor.record_operation(
                    operation_type="device_facts_collection",
                    device_ip=device_ip,
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                )

                return facts

        except Exception as e:
            end_time = time.time()

            # 记录性能指标
            self.monitor.record_operation(
                operation_type="device_facts_collection",
                device_ip=device_ip,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )

            logger.error(f"获取设备信息失败 {device_ip}: {e}")
            return {
                "hostname": device_ip,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    @log_network_operation("config_backup", include_args=False)
    async def backup_configuration(self, host_data: dict[str, Any]) -> dict[str, Any]:
        """备份设备配置"""
        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id")
        start_time = time.time()

        try:
            async with self.pool.get_connection(host_data) as conn:
                # 根据平台选择配置命令
                platform = getattr(conn, "platform", "").lower()
                if "cisco" in platform:
                    config_command = "show running-config"
                elif "huawei" in platform:
                    config_command = "display current-configuration"
                elif "h3c" in platform or "comware" in platform:
                    config_command = "display current-configuration"
                else:
                    config_command = "show running-config"  # 默认

                response = await conn.send_command(config_command)
                end_time = time.time()
                duration = end_time - start_time

                # 记录性能指标
                self.monitor.record_operation(
                    operation_type="config_backup",
                    device_ip=device_ip,
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                )

                return {
                    "hostname": device_ip,
                    "status": "success",
                    "config_content": response.result,
                    "config_size": len(response.result),
                    "elapsed_time": round(duration, 3),
                }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # 记录性能指标
            self.monitor.record_operation(
                operation_type="config_backup",
                device_ip=device_ip,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )

            logger.error(f"配置备份失败 {device_ip}: {e}")
            return {
                "hostname": device_ip,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "elapsed_time": round(duration, 3),
            }

    def get_connection_stats(self) -> dict[str, Any]:
        """获取连接池统计信息"""
        pool_stats = self.pool.get_stats()
        performance_summary = self.monitor.get_performance_summary()

        return {
            **pool_stats,
            "performance_summary": performance_summary,
            "manager_info": {
                "manager_type": "HighPerformanceConnectionManager",
                "features": ["高级连接池", "动态并发控制", "性能监控", "健康检查", "连接复用"],
            },
        }

    def get_device_performance(self, device_ip: str, device_id: str | None = None) -> dict[str, Any] | None:
        """获取设备性能详情"""
        return self.monitor.get_device_details(device_ip, device_id)

    def get_device_recommendations(self, device_ip: str, device_id: str | None = None) -> list[str]:
        """获取设备优化建议"""
        return self.monitor.get_device_recommendations(device_ip, device_id)

    @log_network_operation("config_deployment", include_args=False)
    async def send_config(self, host_data: dict[str, Any], config: str) -> dict[str, Any]:
        """发送单个配置 - 使用Scrapli原生send_config方法"""
        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id")
        start_time = time.time()

        try:
            async with self.pool.get_connection(host_data) as conn:
                logger.info("发送配置到设备", device_ip=device_ip, device_id=device_id, config_length=len(config))

                # 使用Scrapli原生的send_config方法
                response = await conn.send_config(config)

                end_time = time.time()
                duration = end_time - start_time

                # 记录性能指标
                self.monitor.record_operation(
                    operation_type="config_deployment",
                    device_ip=device_ip,
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time,
                    success=not response.failed,
                )

                if response.failed:
                    logger.error(
                        f"配置发送失败: {device_ip}",
                        device_ip=device_ip,
                        device_id=device_id,
                        error=getattr(response, "error", "Configuration failed"),
                        duration=duration,
                    )

                    return {
                        "hostname": device_ip,
                        "status": "failed",
                        "error": getattr(response, "error", "Configuration failed"),
                        "elapsed_time": round(duration, 3),
                    }
                else:
                    logger.info(
                        f"配置发送成功: {device_ip}", device_ip=device_ip, device_id=device_id, duration=duration
                    )

                    return {
                        "hostname": device_ip,
                        "status": "success",
                        "output": response.result,
                        "elapsed_time": round(duration, 3),
                    }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # 记录性能指标
            self.monitor.record_operation(
                operation_type="config_deployment",
                device_ip=device_ip,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )

            logger.error(
                f"配置发送异常: {device_ip}",
                device_ip=device_ip,
                device_id=device_id,
                error=str(e),
                error_type=e.__class__.__name__,
                duration=duration,
            )

            return {
                "hostname": device_ip,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "elapsed_time": round(duration, 3),
            }

    @log_network_operation("batch_config_deployment", include_args=False)
    async def send_configs(self, host_data: dict[str, Any], configs: list[str]) -> dict[str, Any]:
        """发送多个配置 - 使用Scrapli原生send_configs方法"""
        device_ip = host_data.get("hostname") or ""
        device_id = host_data.get("device_id")
        start_time = time.time()

        try:
            async with self.pool.get_connection(host_data) as conn:
                logger.info(
                    f"批量发送 {len(configs)} 个配置",
                    device_ip=device_ip,
                    device_id=device_id,
                    configs_count=len(configs),
                )

                # 使用Scrapli原生的send_configs方法
                responses = await conn.send_configs(configs)

                end_time = time.time()
                duration = end_time - start_time

                # 处理响应结果
                results = []
                successful_configs = 0

                for i, response in enumerate(responses):
                    config_name = f"config_{i + 1}"

                    if response.failed:
                        # 记录失败的配置
                        self.monitor.record_operation(
                            operation_type="config_deployment",
                            device_ip=device_ip,
                            device_id=device_id,
                            start_time=start_time,
                            end_time=end_time,
                            success=False,
                            error_type="ConfigFailed",
                            error_message=getattr(response, "error", "Configuration failed"),
                        )

                        results.append(
                            {
                                "config": config_name,
                                "status": "failed",
                                "output": "",
                                "error": getattr(response, "error", "Configuration failed"),
                                "elapsed_time": response.elapsed_time if hasattr(response, "elapsed_time") else 0,
                            }
                        )
                    else:
                        # 记录成功的配置
                        self.monitor.record_operation(
                            operation_type="config_deployment",
                            device_ip=device_ip,
                            device_id=device_id,
                            start_time=start_time,
                            end_time=end_time,
                            success=True,
                        )

                        successful_configs += 1
                        results.append(
                            {
                                "config": config_name,
                                "status": "success",
                                "output": response.result,
                                "elapsed_time": response.elapsed_time if hasattr(response, "elapsed_time") else 0,
                            }
                        )

                # 记录批量操作的性能指标
                self.monitor.record_operation(
                    operation_type="batch_config_deployment",
                    device_ip=device_ip,
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time,
                    success=successful_configs > 0,
                )

                logger.info(
                    f"批量配置发送完成: {successful_configs}/{len(configs)} 成功",
                    device_ip=device_ip,
                    device_id=device_id,
                    successful_configs=successful_configs,
                    failed_configs=len(configs) - successful_configs,
                    total_duration=duration,
                )

                return {
                    "hostname": device_ip,
                    "total_configs": len(configs),
                    "successful_configs": successful_configs,
                    "failed_configs": len(configs) - successful_configs,
                    "total_time": round(duration, 3),
                    "configs_detail": results,
                }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # 记录批量操作失败
            self.monitor.record_operation(
                operation_type="batch_config_deployment",
                device_ip=device_ip,
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_type=e.__class__.__name__,
                error_message=str(e),
            )

            logger.error(
                f"批量配置发送失败 {device_ip}: {e}",
                device_ip=device_ip,
                device_id=device_id,
                configs_count=len(configs),
                error=str(e),
                duration=duration,
            )

            return {
                "hostname": device_ip,
                "total_configs": len(configs),
                "successful_configs": 0,
                "failed_configs": len(configs),
                "total_time": round(duration, 3),
                "error": str(e),
                "error_type": type(e).__name__,
                "configs_detail": [
                    {"config": f"config_{i + 1}", "status": "failed", "error": str(e)} for i in range(len(configs))
                ],
            }


# 全局高性能连接管理器实例
high_performance_connection_manager = HighPerformanceConnectionManager()
