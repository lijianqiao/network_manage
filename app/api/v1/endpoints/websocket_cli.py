"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: websocket_cli.py
@DateTime: 2025/06/26 16:00:00
@Docs: WebSocket CLI交互API端点
"""

import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.network_automation.websocket_cli_manager import websocket_cli_manager
from app.utils.logger import logger

router = APIRouter(prefix="/ws", tags=["WebSocket CLI"])


@router.websocket("/cli/{host}")
async def websocket_cli_endpoint(
    websocket: WebSocket,
    host: str,
    session_id: str = Query(default_factory=lambda: str(uuid.uuid4())),
):
    """WebSocket CLI交互端点

    Args:
        websocket: WebSocket连接
        host: 设备IP地址或主机名
        session_id: 会话ID（可选，自动生成）
    """
    await websocket.accept()

    try:
        # 创建CLI会话 - 使用host作为设备标识
        session = await websocket_cli_manager.create_session_by_host(session_id, host, websocket)

        # 发送欢迎消息
        welcome_message = {
            "type": "welcome",
            "data": {
                "session_id": session_id,
                "host": host,
                "message": f"WebSocket CLI连接已建立，准备连接到 {host}",
            },
            "timestamp": datetime.now().isoformat(),
        }
        await websocket.send_text(json.dumps(welcome_message))

        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message_data = json.loads(data)

                await _handle_cli_message(session, message_data)

            except WebSocketDisconnect:
                logger.info(f"WebSocket CLI客户端断开连接: {session_id}")
                break
            except Exception as e:
                # 检查是否是连接关闭相关的异常
                if "WebSocket" in str(e) and ("disconnect" in str(e).lower() or "close" in str(e).lower()):
                    logger.info(f"WebSocket连接已关闭: {session_id}")
                    break
                elif isinstance(e, json.JSONDecodeError):
                    try:
                        await _send_error_message(websocket, "消息格式错误", "无法解析JSON消息")
                    except Exception:
                        logger.debug(f"无法发送错误消息，连接可能已断开: {session_id}")
                        break
                else:
                    logger.error(f"处理CLI消息异常: {e}")
                    try:
                        await _send_error_message(websocket, "处理消息异常", str(e))
                    except Exception:
                        logger.debug(f"无法发送错误消息，连接可能已断开: {session_id}")
                        break
                    break

    except Exception as e:
        logger.error(f"WebSocket CLI连接异常: {e}")
    finally:
        # 清理会话
        await websocket_cli_manager.handle_websocket_disconnect(session_id)


async def _handle_cli_message(session, message_data: dict[str, Any]):
    """处理CLI消息"""
    message_type = message_data.get("type", "")

    if message_type == "connect":
        # 处理连接请求
        connection_data = message_data.get("data", {})
        credentials = {
            "username": connection_data.get("username"),
            "password": connection_data.get("password"),
            "enable_password": connection_data.get("enable_password"),
        }
        # 移除None值
        credentials = {k: v for k, v in credentials.items() if v is not None}

        await session.connect_device(credentials if credentials else None)

    elif message_type == "command":
        # 处理命令执行请求
        command = message_data.get("command", "")
        timeout = message_data.get("timeout", 30)

        if not command.strip():
            await session._send_error("命令为空", "请输入要执行的命令")
            return

        await session.execute_command(command, timeout)

    elif message_type == "status":
        # 处理状态查询请求
        status = await session.get_status()
        status_message = {"type": "status", "data": status, "timestamp": datetime.now().isoformat()}
        await session.websocket.send_text(json.dumps(status_message))

    elif message_type == "disconnect":
        # 处理断开连接请求
        reason = message_data.get("reason", "用户主动断开")
        await session.disconnect(reason)

    elif message_type == "ping":
        # 处理心跳请求
        pong_message = {
            "type": "pong",
            "data": {"timestamp": datetime.now().isoformat()},
            "timestamp": datetime.now().isoformat(),
        }
        await session.websocket.send_text(json.dumps(pong_message))

    else:
        await session._send_error("未知消息类型", f"不支持的消息类型: {message_type}")


async def _send_error_message(websocket: WebSocket, error: str, detail: str = ""):
    """发送错误消息到WebSocket"""
    try:
        error_message = {
            "type": "error",
            "error": error,
            "data": {"detail": detail},
            "timestamp": datetime.now().isoformat(),
        }
        await websocket.send_text(json.dumps(error_message))
    except Exception as e:
        logger.debug(f"发送错误消息失败: {e}")


@router.get("/cli/sessions", summary="获取CLI会话状态")
async def get_cli_sessions_status() -> dict[str, Any]:
    """获取所有CLI会话的状态信息"""
    try:
        return await websocket_cli_manager.get_sessions_status()
    except Exception as e:
        logger.error(f"获取CLI会话状态失败: {e}")
        return {"error": str(e)}


@router.delete("/cli/sessions/{session_id}", summary="关闭CLI会话")
async def close_cli_session(session_id: str) -> dict[str, Any]:
    """关闭指定的CLI会话"""
    try:
        await websocket_cli_manager.remove_session(session_id)
        return {"message": f"会话 {session_id} 已关闭"}
    except Exception as e:
        logger.error(f"关闭CLI会话失败: {e}")
        return {"error": str(e)}


@router.get("/cli/terminal", response_class=HTMLResponse, summary="网络终端界面")
async def cli_terminal_page():
    """提供专业的网络设备终端界面（类似CRT）"""
    try:
        # 读取静态HTML文件
        import os
        from pathlib import Path

        # 多种方式计算项目根目录
        current_file = Path(__file__).resolve()

        # 方式1: 从当前文件向上4级目录
        project_root_1 = current_file.parent.parent.parent.parent

        # 方式2: 从工作目录
        project_root_2 = Path.cwd()

        # 方式3: 通过环境变量或配置
        project_root_3 = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))

        # 尝试的路径列表
        possible_paths = [
            project_root_1 / "static" / "html" / "terminal.html",
            project_root_2 / "static" / "html" / "terminal.html",
            project_root_3 / "static" / "html" / "terminal.html",
            Path("d:/Projects/network_manage/static/html/terminal.html"),  # 绝对路径兜底
        ]

        logger.info(f"当前文件路径: {current_file}")
        logger.info(f"工作目录: {Path.cwd()}")

        html_file = None
        for i, path in enumerate(possible_paths, 1):
            logger.info(f"尝试路径 {i}: {path}, 存在: {path.exists()}")
            if path.exists():
                html_file = path
                break

        if html_file and html_file.exists():
            with open(html_file, encoding="utf-8") as f:
                content = f.read()
                logger.info(f"成功读取HTML文件: {html_file}, 大小: {len(content)} 字符")
                return HTMLResponse(content=content)
        else:
            # 返回调试信息页面
            debug_info = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>文件未找到 - 调试信息</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .debug-section {{ margin: 15px 0; padding: 10px; border: 1px solid #ddd; }}
                        .path-item {{ margin: 5px 0; padding: 5px; background: #f5f5f5; }}
                    </style>
                </head>
                <body>
                    <h1>终端界面文件未找到</h1>
                    <div class="debug-section">
                        <h2>路径信息：</h2>
                        <div class="path-item"><strong>当前文件:</strong> {current_file}</div>
                        <div class="path-item"><strong>工作目录:</strong> {Path.cwd()}</div>
                    </div>
                    <div class="debug-section">
                        <h2>尝试的路径：</h2>
            """

            for i, path in enumerate(possible_paths, 1):
                status = "✓ 存在" if path.exists() else "✗ 不存在"
                debug_info += f'<div class="path-item">{i}. {path} - {status}</div>'

            debug_info += """
                    </div>
                    <div class="debug-section">
                        <h2>建议解决方案：</h2>
                        <ul>
                            <li>确保 static/html/terminal.html 文件存在于项目根目录</li>
                            <li>检查文件权限是否正确</li>
                            <li>确保从项目根目录启动应用程序</li>
                            <li>或者设置 PROJECT_ROOT 环境变量</li>
                        </ul>
                    </div>
                </body>
            </html>
            """

            return HTMLResponse(content=debug_info)

    except Exception as e:
        logger.error(f"加载终端界面失败: {e}")
        error_html = f"""
        <!DOCTYPE html>
        <html>
            <head><title>加载错误</title></head>
            <body>
                <h1>加载终端界面失败</h1>
                <p><strong>错误:</strong> {e}</p>
                <p>请检查服务器日志获取更多信息</p>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html)


@router.get("/cli/demo", response_class=HTMLResponse, summary="CLI交互演示页面")
async def cli_demo_page():
    """简单的CLI交互演示页面（向后兼容）"""
    return HTMLResponse(
        content="""
    <html>
        <head><title>重定向到新终端</title></head>
        <body>
            <script>
                window.location.href = '/api/ws/cli/terminal';
            </script>
            <p>正在重定向到新的终端界面...</p>
            <p>如果没有自动重定向，请<a href="/api/ws/cli/terminal">点击这里</a></p>
        </body>
    </html>
    """
    )
