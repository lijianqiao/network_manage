"""
检查配置模板和命令数据
"""

import asyncio


async def check_template_data():
    try:
        from app.models.network_models import Brand, ConfigTemplate, TemplateCommand

        print("检查数据库中的配置模板数据...")

        # 检查品牌数据
        brands = await Brand.all()
        print(f"品牌数量: {len(brands)}")
        for brand in brands[:5]:  # 显示前5个品牌
            print(f"  - {brand.name}")

        # 检查配置模板数据
        config_templates = await ConfigTemplate.all()
        print(f"配置模板数量: {len(config_templates)}")
        for template in config_templates[:5]:  # 显示前5个模板
            print(f"  - {template.name} ({template.template_type}, active: {template.is_active})")

        # 检查模板命令数据
        template_commands = await TemplateCommand.all()
        print(f"模板命令数量: {len(template_commands)}")

        # 检查活跃的查询类型模板命令
        active_query_commands = (
            await TemplateCommand.filter(
                config_template__is_active=True, config_template__template_type="query", is_deleted=False
            )
            .prefetch_related("brand", "config_template")
            .all()
        )

        print(f"活跃的查询类型模板命令数量: {len(active_query_commands)}")

        if active_query_commands:
            print("前5个活跃的查询命令:")
            for cmd in active_query_commands[:5]:
                print(f"  - 品牌: {cmd.brand.name}, 模板: {cmd.config_template.name}")
                if cmd.jinja_content:
                    first_line = cmd.jinja_content.strip().split("\n")[0][:50]
                    print(f"    内容: {first_line}...")

        return True
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(check_template_data())
    print(f"检查结果: {'成功' if result else '失败'}")
