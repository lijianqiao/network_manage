"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: common_utils.py
@DateTime: 2025/01/20 16:30:00
@Docs: 通用工具函数 - 消除代码重复，提供常用功能
"""

import hashlib
import time
from datetime import datetime
from typing import Any


def calculate_hash(content: str, algorithm: str = "md5") -> str:
    """
    计算内容哈希值

    Args:
        content: 要计算哈希的内容
        algorithm: 哈希算法（md5, sha1, sha256）

    Returns:
        哈希值字符串
    """
    if algorithm == "md5":
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(content.encode("utf-8")).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")


def format_duration(seconds: float) -> str:
    """
    格式化时长为可读字符串

    Args:
        seconds: 秒数

    Returns:
        格式化的时长字符串
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}m{remaining_seconds:.0f}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h{remaining_minutes:.0f}m"


def format_size(bytes_size: int) -> str:
    """
    格式化字节大小为可读字符串

    Args:
        bytes_size: 字节数

    Returns:
        格式化的大小字符串
    """
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f}KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f}MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f}GB"


def timestamp_to_datetime(timestamp: float) -> datetime:
    """
    时间戳转换为datetime对象

    Args:
        timestamp: Unix时间戳

    Returns:
        datetime对象
    """
    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime) -> float:
    """
    datetime对象转换为时间戳

    Args:
        dt: datetime对象

    Returns:
        Unix时间戳
    """
    return dt.timestamp()


def safe_get_nested_value(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    """
    安全获取嵌套字典的值

    Args:
        data: 字典数据
        keys: 键路径列表
        default: 默认值

    Returns:
        获取到的值或默认值
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def merge_dicts(*dicts: dict[str, Any]) -> dict[str, Any]:
    """
    合并多个字典

    Args:
        *dicts: 要合并的字典

    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def filter_none_values(data: dict[str, Any]) -> dict[str, Any]:
    """
    过滤字典中的None值

    Args:
        data: 输入字典

    Returns:
        过滤后的字典
    """
    return {k: v for k, v in data.items() if v is not None}


def chunk_list(lst: list[Any], chunk_size: int) -> list[list[Any]]:
    """
    将列表分块

    Args:
        lst: 输入列表
        chunk_size: 块大小

    Returns:
        分块后的列表
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def calculate_percentage(part: float, total: float) -> float:
    """
    计算百分比

    Args:
        part: 部分值
        total: 总值

    Returns:
        百分比（0-100）
    """
    if total == 0:
        return 0.0
    return (part / total) * 100


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 输入字符串
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def validate_ip_address(ip: str) -> bool:
    """
    验证IP地址格式

    Args:
        ip: IP地址字符串

    Returns:
        是否为有效IP地址
    """
    import ipaddress

    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    import re

    # 移除或替换非法字符
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # 移除连续的下划线
    sanitized = re.sub(r"_+", "_", sanitized)
    # 移除开头和结尾的下划线和空格
    sanitized = sanitized.strip("_ ")
    return sanitized


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间
        backoff: 退避倍数
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception from None

        return wrapper

    return decorator


def async_retry_on_exception(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    异步重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间
        backoff: 退避倍数
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            import asyncio

            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception from None

        return wrapper

    return decorator


class Timer:
    """简单的计时器类"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None

    def stop(self):
        """停止计时"""
        if self.start_time is None:
            raise ValueError("计时器尚未启动")
        self.end_time = time.time()

    @property
    def elapsed(self) -> float:
        """获取经过的时间"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

    @property
    def elapsed_formatted(self) -> str:
        """获取格式化的经过时间"""
        return format_duration(self.elapsed)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def create_error_response(error: Exception, include_traceback: bool = False) -> dict[str, Any]:
    """
    创建标准化的错误响应

    Args:
        error: 异常对象
        include_traceback: 是否包含堆栈跟踪

    Returns:
        错误响应字典
    """
    response = {"success": False, "error": str(error), "error_type": error.__class__.__name__, "timestamp": time.time()}

    if include_traceback:
        import traceback

        response["traceback"] = traceback.format_exc()

    return response


def create_success_response(data: Any = None, message: str = "操作成功") -> dict[str, Any]:
    """
    创建标准化的成功响应

    Args:
        data: 返回数据
        message: 成功消息

    Returns:
        成功响应字典
    """
    response = {"success": True, "message": message, "timestamp": time.time()}

    if data is not None:
        response["data"] = data

    return response
