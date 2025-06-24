"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: custom_template_manager.py
@DateTime: 2025/06/24 16:00:00
@Docs: 自定义TextFSM模板管理器
"""

import re
from pathlib import Path
from typing import Any

from app.utils.logger import logger

try:
    import textfsm

    TEXTFSM_AVAILABLE = True
except ImportError:
    textfsm = None
    TEXTFSM_AVAILABLE = False


class CustomTemplateManager:
    """自定义TextFSM模板管理器"""

    def __init__(self, custom_template_dir: str | None = None):
        """初始化自定义模板管理器

        Args:
            custom_template_dir: 自定义模板目录路径，如果未指定则使用默认路径
        """
        self.logger = logger

        # 设置模板目录
        if custom_template_dir:
            self.template_dir = Path(custom_template_dir)
        else:
            # 默认使用项目根目录下的templates/textfsm
            project_root = Path(__file__).parent.parent.parent.parent
            self.template_dir = project_root / "templates" / "textfsm"

        # 确保目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 自定义模板索引文件
        self.custom_index_file = self.template_dir / "custom_index"

        # 内存中的模板索引缓存
        self._template_cache: dict[str, dict[str, Any]] = {}
        self._load_custom_templates()

        self.logger.info(f"自定义模板管理器初始化完成，模板目录: {self.template_dir}")

    def _load_custom_templates(self) -> None:
        """加载自定义模板索引"""
        try:
            if self.custom_index_file.exists():
                with open(self.custom_index_file, encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue

                        try:
                            parts = [part.strip() for part in line.split(",")]
                            if len(parts) >= 4:
                                template_file, hostname_pattern, platform, command_pattern = parts[:4]

                                # 构建完整的模板文件路径
                                template_path = self.template_dir / template_file
                                if template_path.exists():
                                    key = f"{platform}_{command_pattern}"
                                    self._template_cache[key] = {
                                        "template_file": str(template_path),
                                        "hostname_pattern": hostname_pattern,
                                        "platform": platform,
                                        "command_pattern": command_pattern,
                                        "source": "custom",
                                    }
                        except Exception as e:
                            self.logger.warning(f"解析自定义模板索引第{line_num}行失败: {str(e)}")

            self.logger.info(f"加载了 {len(self._template_cache)} 个自定义模板")

        except Exception as e:
            self.logger.error(f"加载自定义模板索引失败: {str(e)}")

    def find_custom_template(self, platform: str, command: str, hostname: str = ".*") -> str | None:
        """查找匹配的自定义模板

        Args:
            platform: 设备平台
            command: 命令
            hostname: 主机名（可选）

        Returns:
            模板文件路径，如果没找到返回None
        """
        best_match = None
        best_score = 0

        for template_info in self._template_cache.values():
            try:
                # 检查平台匹配
                if template_info["platform"].lower() != platform.lower():
                    continue

                # 检查主机名匹配
                hostname_pattern = template_info["hostname_pattern"]
                if hostname_pattern != ".*" and not re.match(hostname_pattern, hostname):
                    continue

                # 检查命令匹配
                command_pattern = template_info["command_pattern"]
                # 处理类似 "di[[splay]] v[[lan]]" 的模式
                expanded_pattern = self._expand_command_pattern(command_pattern)

                if re.search(expanded_pattern, command, re.IGNORECASE):
                    # 计算匹配分数（更精确的匹配得分更高）
                    score = len(command_pattern)
                    if score > best_score:
                        best_score = score
                        best_match = template_info["template_file"]

            except Exception as e:
                self.logger.debug(f"模板匹配检查失败: {str(e)}")
                continue

        return best_match

    def _expand_command_pattern(self, pattern: str) -> str:
        """展开命令模式，处理 [[]] 语法

        例如: "di[[splay]] v[[lan]]" -> "di(s(p(l(a(y)?)?)?)?)?\\s+v(l(a(n)?)?)?"
        """
        try:
            # 处理 [[]] 括号内的可选匹配
            def replace_brackets(match):
                content = match.group(1)
                # 构建递归可选模式
                result = content[0]
                for char in content[1:]:
                    result = f"{result}({char}({result[len(result) - len(char) :]})?)?".replace("()?", "?")
                return result

            # 替换所有 [[...]] 模式
            expanded = re.sub(r"\[\[([^]]+)]]", replace_brackets, pattern)

            # 处理空格
            expanded = re.sub(r"\s+", r"\\s+", expanded)

            return expanded

        except Exception:
            # 如果展开失败，返回简化的模式
            return pattern.replace("[[", "").replace("]]", "").replace(" ", r"\s+")

    def parse_with_custom_template(self, output: str, template_path: str) -> list[dict[str, Any]] | None:
        """使用自定义模板解析输出

        Args:
            output: 命令输出
            template_path: 模板文件路径

        Returns:
            解析结果，失败返回None
        """
        if not TEXTFSM_AVAILABLE:
            self.logger.error("TextFSM不可用")
            return None

        try:
            if textfsm is None:
                self.logger.error("TextFSM模块未正确导入")
                return None
            with open(template_path, encoding="utf-8") as template_file:
                template = textfsm.TextFSM(template_file)
                parsed_data = template.ParseText(output)

                # 转换为字典格式
                if parsed_data and template.header:
                    result = []
                    for row in parsed_data:
                        row_dict = {}
                        for i, value in enumerate(row):
                            if i < len(template.header):
                                row_dict[template.header[i].lower()] = value
                        result.append(row_dict)
                    return result

        except Exception as e:
            self.logger.error(f"使用自定义模板解析失败: {str(e)}")

        return None

    def add_custom_template(
        self,
        template_name: str,
        platform: str,
        command_pattern: str,
        template_content: str,
        hostname_pattern: str = ".*",
    ) -> bool:
        """添加自定义模板

        Args:
            template_name: 模板名称
            platform: 设备平台
            command_pattern: 命令模式
            template_content: 模板内容
            hostname_pattern: 主机名模式

        Returns:
            添加是否成功
        """
        try:
            # 创建模板文件
            template_file = self.template_dir / "custom" / f"{template_name}.textfsm"
            template_file.parent.mkdir(parents=True, exist_ok=True)

            with open(template_file, "w", encoding="utf-8") as f:
                f.write(template_content)

            # 更新索引文件
            index_entry = f"custom/{template_name}.textfsm, {hostname_pattern}, {platform}, {command_pattern}\n"

            with open(self.custom_index_file, "a", encoding="utf-8") as f:
                f.write(index_entry)

            # 更新缓存
            key = f"{platform}_{command_pattern}"
            self._template_cache[key] = {
                "template_file": str(template_file),
                "hostname_pattern": hostname_pattern,
                "platform": platform,
                "command_pattern": command_pattern,
                "source": "custom",
            }

            self.logger.info(f"成功添加自定义模板: {template_name}")
            return True

        except Exception as e:
            self.logger.error(f"添加自定义模板失败: {str(e)}")
            return False

    def remove_custom_template(self, template_name: str) -> bool:
        """删除自定义模板

        Args:
            template_name: 模板名称

        Returns:
            删除是否成功
        """
        try:
            # 删除模板文件
            template_file = self.template_dir / "custom" / f"{template_name}.textfsm"
            if template_file.exists():
                template_file.unlink()

            # 重新构建索引文件（去除对应条目）
            if self.custom_index_file.exists():
                lines = []
                with open(self.custom_index_file, encoding="utf-8") as f:
                    for line in f:
                        if not line.startswith(f"custom/{template_name}.textfsm"):
                            lines.append(line)

                with open(self.custom_index_file, "w", encoding="utf-8") as f:
                    f.writelines(lines)

            # 重新加载缓存
            self._template_cache.clear()
            self._load_custom_templates()

            self.logger.info(f"成功删除自定义模板: {template_name}")
            return True

        except Exception as e:
            self.logger.error(f"删除自定义模板失败: {str(e)}")
            return False

    def list_custom_templates(self) -> list[dict[str, Any]]:
        """列出所有自定义模板

        Returns:
            模板信息列表
        """
        templates = []
        for info in self._template_cache.values():
            templates.append(
                {
                    "template_name": Path(info["template_file"]).stem,
                    "platform": info["platform"],
                    "command_pattern": info["command_pattern"],
                    "hostname_pattern": info["hostname_pattern"],
                    "template_path": info["template_file"],
                    "source": info["source"],
                }
            )

        return templates

    def validate_template(self, template_content: str) -> tuple[bool, str]:
        """验证模板语法

        Args:
            template_content: 模板内容

        Returns:
            (是否有效, 错误信息)
        """
        if not TEXTFSM_AVAILABLE or textfsm is None:
            return False, "TextFSM不可用"

        try:
            # 创建临时模板进行验证
            import io

            template_io = io.StringIO(template_content)
            if textfsm is not None:
                textfsm.TextFSM(template_io)
                return True, "模板语法有效"
            else:
                return False, "TextFSM模块未正确导入"

        except Exception as e:
            return False, f"模板语法错误: {str(e)}"

    def get_template_stats(self) -> dict[str, Any]:
        """获取模板统计信息

        Returns:
            统计信息字典
        """
        platforms = {}
        total_templates = len(self._template_cache)

        for info in self._template_cache.values():
            platform = info["platform"]
            platforms[platform] = platforms.get(platform, 0) + 1

        return {
            "total_templates": total_templates,
            "platforms_supported": list(platforms.keys()),
            "platform_counts": platforms,
            "template_directory": str(self.template_dir),
            "textfsm_available": TEXTFSM_AVAILABLE,
        }


# 全局自定义模板管理器实例
custom_template_manager = CustomTemplateManager()
