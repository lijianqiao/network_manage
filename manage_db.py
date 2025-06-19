#!/usr/bin/env python3
"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: manage_db.py
@DateTime: 2025/06/16
@Docs: 数据库管理脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.db import check_database_connection, generate_schemas
from app.utils.logger import logger


async def test_connection():
    """测试数据库连接"""
    logger.info("开始测试数据库连接...")
    is_connected = await check_database_connection()
    if is_connected:
        logger.info("✅ 数据库连接测试成功")
    else:
        logger.error("❌ 数据库连接测试失败")
    return is_connected


async def create_tables():
    """创建数据库表 (开发环境使用)"""
    logger.warning("警告: 此操作将生成数据库表结构")
    logger.warning("生产环境请使用: aerich upgrade")

    try:
        await generate_schemas()
        logger.info("✅ 数据库表结构生成成功")
    except Exception as e:
        logger.error(f"❌ 数据库表结构生成失败: {e}")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python manage_db.py test      # 测试数据库连接")
        print("  python manage_db.py create    # 创建数据库表 (开发环境)")
        return

    command = sys.argv[1]

    if command == "test":
        await test_connection()
    elif command == "create":
        await create_tables()
    else:
        logger.error(f"未知命令: {command}")


if __name__ == "__main__":
    asyncio.run(main())
