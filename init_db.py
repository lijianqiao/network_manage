"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: init_db.py
@DateTime: 2025/06/20 00:00:00
@Docs: 数据库初始化脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.db.connection import close_database, generate_schemas, init_database
from app.utils.logger import logger


async def init_database_with_sample_data():
    """初始化数据库并添加示例数据"""
    try:
        # 初始化数据库连接
        await init_database()

        # 生成数据库表结构（仅开发环境）
        if settings.IS_DEVELOPMENT:
            logger.info("开发环境：正在生成数据库表结构...")
            await generate_schemas()
        else:
            logger.warning("生产环境：请使用 Aerich 进行数据库迁移管理")

        # 导入模型类
        from app.models import (
            Brand,
            ConfigTemplate,
            DeviceGroup,
            DeviceModel,
            Region,
            TemplateTypeEnum,
        )

        # 检查是否已有数据
        existing_regions = await Region.all().count()
        if existing_regions > 0:
            logger.info("数据库已包含数据，跳过示例数据初始化")
            return

        logger.info("正在创建示例数据...")

        # 创建区域数据
        chengdu_region = await Region.create(
            name="成都区域",
            snmp_community_string="oppein@11",
            default_cli_username="opcdjr",
            description="成都地区网络设备",
        )

        beijing_region = await Region.create(  # noqa: F841
            name="无锡区域",
            snmp_community_string="oppein@16",
            default_cli_username="opwxjr",
            description="无锡地区网络设备",
        )

        # 创建品牌数据
        h3c_brand = await Brand.create(name="H3C", platform_type="hp_comware", description="华三网络设备")

        huawei_brand = await Brand.create(name="Huawei", platform_type="huawei_vrp", description="华为网络设备")

        cisco_brand = await Brand.create(name="Cisco", platform_type="cisco_iosxe", description="思科网络设备")

        # 创建设备型号
        await DeviceModel.create(name="S5700", brand=h3c_brand, description="H3C S5700系列交换机")

        await DeviceModel.create(name="CE12800", brand=huawei_brand, description="华为CE12800系列核心交换机")

        await DeviceModel.create(name="Catalyst 9300", brand=cisco_brand, description="Cisco Catalyst 9300系列交换机")

        # 创建设备分组
        core_group = await DeviceGroup.create(name="核心交换机", region=chengdu_region, description="核心网络设备")  # noqa: F841

        access_group = await DeviceGroup.create(name="接入交换机", region=chengdu_region, description="接入层网络设备")  # noqa: F841

        # 创建配置模板
        await ConfigTemplate.create(
            name="MAC地址查询", template_type=TemplateTypeEnum.QUERY, description="查询设备MAC地址表"
        )

        await ConfigTemplate.create(
            name="端口配置", template_type=TemplateTypeEnum.CONFIG, description="配置交换机端口"
        )

        await ConfigTemplate.create(name="VLAN配置", template_type=TemplateTypeEnum.CONFIG, description="配置VLAN")

        logger.info("示例数据创建完成")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        await close_database()


async def reset_database():
    """重置数据库（危险操作，仅用于开发环境）"""
    if not settings.IS_DEVELOPMENT:
        logger.error("重置数据库仅允许在开发环境执行")
        return

    try:
        await init_database()

        # 导入所有模型
        from app.models import (
            Brand,
            ConfigDiff,
            ConfigSnapshot,
            ConfigTemplate,
            Device,
            DeviceConnectionStatus,
            DeviceGroup,
            DeviceModel,
            OperationLog,
            Region,
            RollbackOperation,
            TemplateCommand,
        )

        # 按依赖关系逆序删除数据
        models_to_clear = [
            RollbackOperation,
            ConfigDiff,
            ConfigSnapshot,
            DeviceConnectionStatus,
            OperationLog,
            TemplateCommand,
            ConfigTemplate,
            Device,
            DeviceGroup,
            DeviceModel,
            Brand,
            Region,
        ]

        for model in models_to_clear:
            await model.all().delete()
            logger.info(f"已清空表: {model._meta.table}")

        logger.info("数据库重置完成")

    except Exception as e:
        logger.error(f"数据库重置失败: {e}")
        raise
    finally:
        await close_database()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("--reset", action="store_true", help="重置数据库（仅开发环境）")
    parser.add_argument("--init", action="store_true", help="初始化数据库并创建示例数据")

    args = parser.parse_args()

    if args.reset:
        print("⚠️  警告：这将删除所有数据库数据！")
        confirm = input("请输入 'yes' 确认重置数据库: ")
        if confirm.lower() == "yes":
            asyncio.run(reset_database())
        else:
            print("操作已取消")
    elif args.init:
        asyncio.run(init_database_with_sample_data())
    else:
        parser.print_help()
