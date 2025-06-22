"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: jinja_renderer.py
@DateTime: 2025-06-22
@Docs: Jinja2模板渲染工具
"""

from typing import Any

from jinja2 import Environment, StrictUndefined, meta
from jinja2.exceptions import TemplateError, TemplateSyntaxError, UndefinedError

from app.utils.logger import logger


class JinjaRenderer:
    """Jinja2模板渲染器"""

    def __init__(self):
        """初始化渲染器"""
        # 创建严格模式的Jinja2环境，未定义变量会抛出异常
        self.env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def validate_syntax(self, template_content: str) -> dict[str, Any]:
        """验证模板语法

        Args:
            template_content: 模板内容

        Returns:
            验证结果字典
        """
        try:
            # 解析模板语法
            ast = self.env.parse(template_content)

            # 提取模板中的变量
            variables = meta.find_undeclared_variables(ast)

            return {
                "is_valid": True,
                "variables": list(variables),
                "message": "模板语法验证通过",
                "error": None,
            }
        except TemplateSyntaxError as e:
            return {
                "is_valid": False,
                "variables": [],
                "message": f"模板语法错误: {e.message}",
                "error": {
                    "type": "SyntaxError",
                    "line": e.lineno,
                    "message": e.message,
                },
            }
        except Exception as e:
            return {
                "is_valid": False,
                "variables": [],
                "message": f"模板验证失败: {str(e)}",
                "error": {
                    "type": "UnknownError",
                    "message": str(e),
                },
            }

    def render_template(self, template_content: str, variables: dict[str, Any]) -> dict[str, Any]:
        """渲染模板

        Args:
            template_content: 模板内容
            variables: 模板变量

        Returns:
            渲染结果字典
        """
        try:
            # 创建模板对象
            template = self.env.from_string(template_content)

            # 渲染模板
            rendered = template.render(**variables)

            return {
                "success": True,
                "rendered_content": rendered,
                "message": "模板渲染成功",
                "error": None,
            }
        except UndefinedError as e:
            return {
                "success": False,
                "rendered_content": "",
                "message": f"模板变量未定义: {str(e)}",
                "error": {
                    "type": "UndefinedError",
                    "message": str(e),
                },
            }
        except TemplateSyntaxError as e:
            return {
                "success": False,
                "rendered_content": "",
                "message": f"模板语法错误: {e.message}",
                "error": {
                    "type": "SyntaxError",
                    "line": e.lineno,
                    "message": e.message,
                },
            }
        except TemplateError as e:
            return {
                "success": False,
                "rendered_content": "",
                "message": f"模板渲染错误: {str(e)}",
                "error": {
                    "type": "TemplateError",
                    "message": str(e),
                },
            }
        except Exception as e:
            logger.error(f"模板渲染异常: {str(e)}")
            return {
                "success": False,
                "rendered_content": "",
                "message": f"模板渲染失败: {str(e)}",
                "error": {
                    "type": "UnknownError",
                    "message": str(e),
                },
            }

    def render_commands(self, template_content: str, variables: dict[str, Any]) -> dict[str, Any]:
        """渲染命令模板（返回命令列表）

        Args:
            template_content: 模板内容
            variables: 模板变量

        Returns:
            渲染结果字典，包含命令列表
        """
        result = self.render_template(template_content, variables)

        if result["success"]:
            # 将渲染结果按行分割为命令列表
            rendered_content = result["rendered_content"]
            commands = [cmd.strip() for cmd in rendered_content.split("\n") if cmd.strip()]

            result["commands"] = commands
            result["command_count"] = len(commands)
        else:
            result["commands"] = []
            result["command_count"] = 0

        return result

    def preview_render(
        self, template_content: str, variables: dict[str, Any], max_length: int = 1000
    ) -> dict[str, Any]:
        """预览模板渲染（用于前端展示）

        Args:
            template_content: 模板内容
            variables: 模板变量
            max_length: 最大返回长度

        Returns:
            预览结果字典
        """
        result = self.render_template(template_content, variables)

        if result["success"]:
            rendered = result["rendered_content"]

            # 如果内容过长，截断并添加省略号
            if len(rendered) > max_length:
                result["rendered_content"] = rendered[:max_length] + "..."
                result["is_truncated"] = True
                result["full_length"] = len(rendered)
            else:
                result["is_truncated"] = False
                result["full_length"] = len(rendered)

        return result

    def extract_variables(self, template_content: str) -> dict[str, Any]:
        """提取模板中使用的变量

        Args:
            template_content: 模板内容

        Returns:
            变量信息字典
        """
        try:
            ast = self.env.parse(template_content)
            variables = meta.find_undeclared_variables(ast)

            return {
                "success": True,
                "variables": list(variables),
                "variable_count": len(variables),
                "message": "变量提取成功",
            }
        except Exception as e:
            return {
                "success": False,
                "variables": [],
                "variable_count": 0,
                "message": f"变量提取失败: {str(e)}",
            }

    def validate_variables(self, template_content: str, provided_variables: dict[str, Any]) -> dict[str, Any]:
        """验证提供的变量是否满足模板需求

        Args:
            template_content: 模板内容
            provided_variables: 提供的变量

        Returns:
            验证结果字典
        """
        # 提取模板需要的变量
        extract_result = self.extract_variables(template_content)

        if not extract_result["success"]:
            return extract_result

        required_vars = set(extract_result["variables"])
        provided_vars = set(provided_variables.keys())

        # 检查缺失的变量
        missing_vars = required_vars - provided_vars
        # 检查多余的变量
        extra_vars = provided_vars - required_vars

        return {
            "is_valid": len(missing_vars) == 0,
            "required_variables": list(required_vars),
            "provided_variables": list(provided_vars),
            "missing_variables": list(missing_vars),
            "extra_variables": list(extra_vars),
            "message": ("变量验证通过" if len(missing_vars) == 0 else f"缺少必需变量: {', '.join(missing_vars)}"),
        }


# 全局渲染器实例
jinja_renderer = JinjaRenderer()
