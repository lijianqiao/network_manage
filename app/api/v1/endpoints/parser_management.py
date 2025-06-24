"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: parser_management.py
@DateTime: 2025/06/24 14:30:00
@Docs: 解析器管理API端点
"""

from typing import Any

from fastapi import APIRouter

from app.network_automation.parsers.hybrid_parser import hybrid_parser
from app.utils.logger import logger

router = APIRouter(prefix="/parser", tags=["解析器管理"])


@router.get("/strategies", summary="获取解析策略信息")
async def get_parsing_strategies() -> dict[str, Any]:
    """获取解析器支持的策略和品牌信息"""
    try:
        return await hybrid_parser.get_parsing_strategies()
    except Exception as e:
        logger.error(f"获取解析策略失败: {e}")
        return {"error": str(e)}


@router.post("/test", summary="测试解析功能")
async def test_parser(test_data: dict[str, Any]) -> dict[str, Any]:
    """测试解析器功能

    Args:
        test_data: 测试数据，格式:
        {
            "command_output": "命令输出文本",
            "command": "命令",
            "brand": "设备品牌"
        }
    """
    try:
        required_fields = ["command_output", "command", "brand"]
        for field in required_fields:
            if field not in test_data:
                return {"error": f"缺少必需字段: {field}"}

        result = hybrid_parser.parse_command_output(
            command_output=test_data["command_output"],
            command=test_data["command"],
            brand=test_data["brand"],
            use_ntc_first=test_data.get("use_ntc_first", True),
        )

        return result

    except Exception as e:
        logger.error(f"测试解析失败: {e}")
        return {"error": str(e)}


@router.post("/batch-test", summary="批量测试解析功能")
async def batch_test_parser(test_samples: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """批量测试解析器功能

    Args:
        test_samples: 测试样本，格式:
        {
            "command_name": {
                "output": "命令输出文本",
                "brand": "设备品牌"
            }
        }
    """
    try:
        # 转换格式以适配测试方法
        formatted_samples = {}
        for command, sample in test_samples.items():
            if "output" not in sample or "brand" not in sample:
                continue
            formatted_samples[command] = sample

        results = hybrid_parser.test_parsing(formatted_samples)
        return {
            "total_tests": len(formatted_samples),
            "successful_parses": sum(1 for r in results.values() if r.get("success")),
            "failed_parses": sum(1 for r in results.values() if not r.get("success")),
            "results": results,
        }

    except Exception as e:
        logger.error(f"批量测试解析失败: {e}")
        return {"error": str(e)}


@router.get("/sample-data", summary="获取测试样本数据")
async def get_sample_data() -> dict[str, Any]:
    """获取用于测试的样本数据"""
    sample_data = {
        "h3c_mac_address": {
            "output": """MAC-Address    VLAN   Type      Port                 Aging
0001-0203-0405    1      Dynamic   GigabitEthernet1/0/1    300
0001-0203-0406    10     Dynamic   GigabitEthernet1/0/2    300
0001-0203-0407    20     Dynamic   GigabitEthernet1/0/3    300
Total items displayed = 3""",
            "brand": "h3c",
        },
        "h3c_interface_brief": {
            "output": """Interface                   Link       Protocol   Description
GigabitEthernet1/0/1       up         up         To_Switch_01
GigabitEthernet1/0/2       down       down
GigabitEthernet1/0/3       up         up         To_Server_01
Vlan-interface1            up         up         Management""",
            "brand": "h3c",
        },
        "huawei_arp": {
            "output": """IP ADDRESS      MAC ADDRESS     VLAN/VSI      INTERFACE
10.1.1.1        0001-0203-0405  1/--          GE1/0/1
10.1.1.2        0001-0203-0406  1/--          GE1/0/2
10.1.1.3        0001-0203-0407  1/--          GE1/0/3""",
            "brand": "huawei",
        },
        "cisco_mac_table": {
            "output": """Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0001.0203.0405    DYNAMIC     Gi0/1
  10    0001.0203.0406    DYNAMIC     Gi0/2
  20    0001.0203.0407    DYNAMIC     Gi0/3
Total Mac Addresses for this criterion: 3""",
            "brand": "cisco",
        },
    }

    return {
        "description": "测试样本数据，可用于验证解析器功能",
        "samples": sample_data,
        "usage": "使用 /parser/batch-test 端点测试这些样本",
    }


# 自定义模板管理端点
@router.get("/custom-templates", summary="列出所有自定义模板")
async def list_custom_templates() -> dict[str, Any]:
    """列出所有自定义模板"""
    try:
        from app.network_automation.parsers.custom_template_manager import custom_template_manager

        templates = custom_template_manager.list_custom_templates()
        stats = custom_template_manager.get_template_stats()

        return {"templates": templates, "statistics": stats}
    except Exception as e:
        logger.error(f"列出自定义模板失败: {e}")
        return {"error": str(e)}


@router.post("/custom-templates", summary="添加自定义模板")
async def add_custom_template(template_data: dict[str, Any]) -> dict[str, Any]:
    """添加自定义模板

    Args:
        template_data: 模板数据，格式:
        {
            "template_name": "模板名称",
            "platform": "设备平台",
            "command_pattern": "命令模式",
            "template_content": "TextFSM模板内容",
            "hostname_pattern": "主机名模式（可选）"
        }
    """
    try:
        from app.network_automation.parsers.custom_template_manager import custom_template_manager

        required_fields = ["template_name", "platform", "command_pattern", "template_content"]
        for field in required_fields:
            if field not in template_data:
                return {"error": f"缺少必需字段: {field}"}

        # 验证模板语法
        is_valid, error_msg = custom_template_manager.validate_template(template_data["template_content"])
        if not is_valid:
            return {"error": f"模板语法验证失败: {error_msg}"}

        # 添加模板
        success = custom_template_manager.add_custom_template(
            template_name=template_data["template_name"],
            platform=template_data["platform"],
            command_pattern=template_data["command_pattern"],
            template_content=template_data["template_content"],
            hostname_pattern=template_data.get("hostname_pattern", ".*"),
        )

        if success:
            return {"message": "自定义模板添加成功", "template_name": template_data["template_name"]}
        else:
            return {"error": "添加自定义模板失败"}

    except Exception as e:
        logger.error(f"添加自定义模板失败: {e}")
        return {"error": str(e)}


@router.delete("/custom-templates/{template_name}", summary="删除自定义模板")
async def remove_custom_template(template_name: str) -> dict[str, Any]:
    """删除指定的自定义模板"""
    try:
        from app.network_automation.parsers.custom_template_manager import custom_template_manager

        success = custom_template_manager.remove_custom_template(template_name)

        if success:
            return {"message": f"自定义模板 '{template_name}' 删除成功"}
        else:
            return {"error": f"删除自定义模板 '{template_name}' 失败"}

    except Exception as e:
        logger.error(f"删除自定义模板失败: {e}")
        return {"error": str(e)}


@router.post("/custom-templates/validate", summary="验证模板语法")
async def validate_template_syntax(template_data: dict[str, str]) -> dict[str, Any]:
    """验证TextFSM模板语法

    Args:
        template_data: {"template_content": "TextFSM模板内容"}
    """
    try:
        from app.network_automation.parsers.custom_template_manager import custom_template_manager

        if "template_content" not in template_data:
            return {"error": "缺少template_content字段"}

        is_valid, error_msg = custom_template_manager.validate_template(template_data["template_content"])

        return {"valid": is_valid, "message": error_msg}

    except Exception as e:
        logger.error(f"验证模板语法失败: {e}")
        return {"error": str(e)}


@router.post("/custom-templates/test", summary="测试自定义模板")
async def test_custom_template(test_data: dict[str, Any]) -> dict[str, Any]:
    """测试自定义模板解析

    Args:
        test_data: 测试数据，格式:
        {
            "template_content": "TextFSM模板内容",
            "command_output": "命令输出文本"
        }"""
    try:
        import os
        import tempfile

        from app.network_automation.parsers.custom_template_manager import custom_template_manager

        required_fields = ["template_content", "command_output"]
        for field in required_fields:
            if field not in test_data:
                return {"error": f"缺少必需字段: {field}"}

        # 验证模板语法
        is_valid, error_msg = custom_template_manager.validate_template(test_data["template_content"])
        if not is_valid:
            return {"error": f"模板语法验证失败: {error_msg}"}

        # 创建临时模板文件进行测试
        with tempfile.NamedTemporaryFile(mode="w", suffix=".textfsm", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(test_data["template_content"])
            tmp_file_path = tmp_file.name

        try:
            # 使用自定义模板解析
            parsed_data = custom_template_manager.parse_with_custom_template(test_data["command_output"], tmp_file_path)

            return {
                "success": parsed_data is not None,
                "data": parsed_data if parsed_data else [],
                "data_count": len(parsed_data) if parsed_data else 0,
            }

        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        logger.error(f"测试自定义模板失败: {e}")
        return {"error": str(e)}
