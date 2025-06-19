"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: run.py
@DateTime: 2025/06/16 23:26:59
@Docs: 主程序
"""

import uvicorn

from app.core.config import settings


def main():
    """主函数"""

    # 启动FastAPI应用
    uvicorn.run(
        "app.main:app",  # 使用导入字符串而不是应用对象
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),  # 转换为小写字符串
        reload=settings.DEBUG,  # 开发模式下启用热重载
    )


if __name__ == "__main__":
    main()
