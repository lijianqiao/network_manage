"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config_diff_manager.py
@DateTime: 2025/01/20 14:00:00
@Docs: 配置差异对比管理器 - 提供配置对比、分析、可视化等功能
"""

import difflib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.enums import DiffSeverity, DiffType
from app.utils.logger import logger


@dataclass
class ConfigLine:
    """配置行"""

    line_number: int
    content: str
    diff_type: DiffType
    severity: DiffSeverity = DiffSeverity.LOW
    category: str | None = None
    description: str | None = None


@dataclass
class ConfigSection:
    """配置段落"""

    name: str
    start_line: int
    end_line: int
    lines: list[ConfigLine] = field(default_factory=list)
    has_changes: bool = False
    change_count: int = 0


@dataclass
class ConfigDiffResult:
    """配置差异结果"""

    source_name: str
    target_name: str
    total_lines: int
    added_lines: int
    removed_lines: int
    modified_lines: int
    unchanged_lines: int
    sections: list[ConfigSection] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    risk_assessment: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    @property
    def change_percentage(self) -> float:
        """变化百分比"""
        if self.total_lines == 0:
            return 0.0
        changed_lines = self.added_lines + self.removed_lines + self.modified_lines
        return (changed_lines / self.total_lines) * 100

    @property
    def has_critical_changes(self) -> bool:
        """是否有严重变化"""
        return any(
            line.severity == DiffSeverity.CRITICAL
            for section in self.sections
            for line in section.lines
            if line.diff_type != DiffType.UNCHANGED
        )


class ConfigDiffManager:
    """配置差异对比管理器"""

    def __init__(self):
        # 配置分类规则
        self.config_categories = {
            "interface": {
                "patterns": [r"^interface\s+", r"^\s+ip\s+address", r"^\s+shutdown"],
                "severity": DiffSeverity.HIGH,
                "description": "接口配置",
            },
            "routing": {
                "patterns": [r"^router\s+", r"^ip\s+route", r"^\s+network\s+"],
                "severity": DiffSeverity.CRITICAL,
                "description": "路由配置",
            },
            "access_control": {
                "patterns": [r"^access-list\s+", r"^ip\s+access-list", r"^\s+permit", r"^\s+deny"],
                "severity": DiffSeverity.CRITICAL,
                "description": "访问控制列表",
            },
            "vlan": {
                "patterns": [r"^vlan\s+", r"^\s+name\s+", r"^switchport\s+"],
                "severity": DiffSeverity.MEDIUM,
                "description": "VLAN配置",
            },
            "security": {
                "patterns": [r"^username\s+", r"^enable\s+secret", r"^crypto\s+", r"^aaa\s+"],
                "severity": DiffSeverity.CRITICAL,
                "description": "安全配置",
            },
            "snmp": {
                "patterns": [r"^snmp-server\s+", r"^snmp\s+"],
                "severity": DiffSeverity.MEDIUM,
                "description": "SNMP配置",
            },
            "logging": {
                "patterns": [r"^logging\s+", r"^log\s+"],
                "severity": DiffSeverity.LOW,
                "description": "日志配置",
            },
            "comment": {
                "patterns": [r"^\s*!", r"^\s*#", r"^\s*rem\s+"],
                "severity": DiffSeverity.LOW,
                "description": "注释",
            },
        }

        # 风险评估规则
        self.risk_rules = {
            "high_risk_commands": [
                "no shutdown",
                "shutdown",
                "ip route",
                "access-list",
                "username",
                "enable secret",
                "crypto",
                "router",
            ],
            "critical_sections": ["interface", "router", "access-list", "crypto", "aaa"],
        }

    def compare_configs(
        self,
        source_config: str,
        target_config: str,
        source_name: str = "Source",
        target_name: str = "Target",
        context_lines: int = 3,
    ) -> ConfigDiffResult:
        """
        对比两个配置文件

        Args:
            source_config: 源配置内容
            target_config: 目标配置内容
            source_name: 源配置名称
            target_name: 目标配置名称
            context_lines: 上下文行数

        Returns:
            配置差异结果
        """
        logger.info(f"开始配置对比: {source_name} vs {target_name}")

        # 预处理配置
        source_lines = self._preprocess_config(source_config)
        target_lines = self._preprocess_config(target_config)

        # 生成差异
        differ = difflib.unified_diff(
            source_lines, target_lines, fromfile=source_name, tofile=target_name, lineterm="", n=context_lines
        )

        # 解析差异
        diff_lines = list(differ)
        config_lines = self._parse_diff_lines(diff_lines, source_lines, target_lines)

        # 分类和分析
        sections = self._categorize_config_lines(config_lines)

        # 统计信息
        added_lines = len([line for line in config_lines if line.diff_type == DiffType.ADDED])
        removed_lines = len([line for line in config_lines if line.diff_type == DiffType.REMOVED])
        modified_lines = len([line for line in config_lines if line.diff_type == DiffType.MODIFIED])
        unchanged_lines = len([line for line in config_lines if line.diff_type == DiffType.UNCHANGED])

        # 创建结果
        result = ConfigDiffResult(
            source_name=source_name,
            target_name=target_name,
            total_lines=len(config_lines),
            added_lines=added_lines,
            removed_lines=removed_lines,
            modified_lines=modified_lines,
            unchanged_lines=unchanged_lines,
            sections=sections,
        )

        # 生成摘要和风险评估
        result.summary = self._generate_summary(result)
        result.risk_assessment = self._assess_risk(result)
        result.recommendations = self._generate_recommendations(result)

        logger.info(
            f"配置对比完成: {result.change_percentage:.1f}% 变化",
            source_name=source_name,
            target_name=target_name,
            total_lines=result.total_lines,
            added_lines=added_lines,
            removed_lines=removed_lines,
            modified_lines=modified_lines,
            change_percentage=result.change_percentage,
        )

        return result

    def _preprocess_config(self, config: str) -> list[str]:
        """预处理配置内容"""
        if not config:
            return []

        lines = config.split("\n")
        processed_lines = []

        for line in lines:
            # 移除行尾空白
            line = line.rstrip()

            # 跳过空行（可选）
            if not line:
                continue

            processed_lines.append(line)

        return processed_lines

    def _parse_diff_lines(
        self, diff_lines: list[str], source_lines: list[str], target_lines: list[str]
    ) -> list[ConfigLine]:
        """解析差异行"""
        config_lines = []
        line_number = 0

        # 如果没有差异，所有行都是未变化的
        if not diff_lines or len(diff_lines) <= 2:  # 只有文件头
            for i, line in enumerate(source_lines):
                config_lines.append(ConfigLine(line_number=i + 1, content=line, diff_type=DiffType.UNCHANGED))
            return config_lines

        # 解析unified diff格式
        for line in diff_lines:
            if line.startswith("@@"):
                # 解析行号信息
                continue
            elif line.startswith("---") or line.startswith("+++"):
                # 文件头信息
                continue
            elif line.startswith("-"):
                # 删除的行
                line_number += 1
                config_lines.append(
                    ConfigLine(
                        line_number=line_number,
                        content=line[1:],  # 移除前缀
                        diff_type=DiffType.REMOVED,
                    )
                )
            elif line.startswith("+"):
                # 添加的行
                line_number += 1
                config_lines.append(
                    ConfigLine(
                        line_number=line_number,
                        content=line[1:],  # 移除前缀
                        diff_type=DiffType.ADDED,
                    )
                )
            elif line.startswith(" "):
                # 未变化的行
                line_number += 1
                config_lines.append(
                    ConfigLine(
                        line_number=line_number,
                        content=line[1:],  # 移除前缀
                        diff_type=DiffType.UNCHANGED,
                    )
                )

        return config_lines

    def _categorize_config_lines(self, config_lines: list[ConfigLine]) -> list[ConfigSection]:
        """分类配置行"""
        sections = []
        current_section = None

        for line in config_lines:
            # 分类行
            category, severity = self._classify_line(line.content)
            line.category = category
            line.severity = severity

            # 检查是否开始新的配置段落
            if self._is_section_start(line.content):
                # 保存当前段落
                if current_section:
                    sections.append(current_section)

                # 开始新段落
                current_section = ConfigSection(
                    name=category or "unknown", start_line=line.line_number, end_line=line.line_number
                )

            # 添加行到当前段落
            if current_section:
                current_section.lines.append(line)
                current_section.end_line = line.line_number

                if line.diff_type != DiffType.UNCHANGED:
                    current_section.has_changes = True
                    current_section.change_count += 1
            else:
                # 如果没有当前段落，创建一个默认段落
                current_section = ConfigSection(
                    name="general", start_line=line.line_number, end_line=line.line_number, lines=[line]
                )

        # 添加最后一个段落
        if current_section:
            sections.append(current_section)

        return sections

    def _classify_line(self, line: str) -> tuple[str | None, DiffSeverity]:
        """分类配置行"""
        line_lower = line.lower().strip()

        for category, rules in self.config_categories.items():
            for pattern in rules["patterns"]:
                if re.match(pattern, line_lower):
                    return category, rules["severity"]

        return None, DiffSeverity.LOW

    def _is_section_start(self, line: str) -> bool:
        """判断是否是配置段落开始"""
        section_starters = [
            r"^interface\s+",
            r"^router\s+",
            r"^vlan\s+",
            r"^access-list\s+",
            r"^ip\s+access-list",
            r"^crypto\s+",
            r"^aaa\s+",
        ]

        line_lower = line.lower().strip()
        return any(re.match(pattern, line_lower) for pattern in section_starters)

    def _generate_summary(self, result: ConfigDiffResult) -> dict[str, Any]:
        """生成差异摘要"""
        summary = {
            "total_changes": result.added_lines + result.removed_lines + result.modified_lines,
            "change_percentage": result.change_percentage,
            "sections_with_changes": len([s for s in result.sections if s.has_changes]),
            "total_sections": len(result.sections),
            "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "category_breakdown": {},
        }

        # 统计严重程度分布
        for section in result.sections:
            for line in section.lines:
                if line.diff_type != DiffType.UNCHANGED:
                    summary["severity_breakdown"][line.severity.value] += 1

                    # 统计分类分布
                    if line.category:
                        if line.category not in summary["category_breakdown"]:
                            summary["category_breakdown"][line.category] = 0
                        summary["category_breakdown"][line.category] += 1

        return summary

    def _assess_risk(self, result: ConfigDiffResult) -> dict[str, Any]:
        """评估风险"""
        risk_assessment = {
            "overall_risk": "low",
            "risk_score": 0,
            "critical_changes": [],
            "high_risk_changes": [],
            "potential_issues": [],
        }

        critical_count = 0
        high_count = 0

        for section in result.sections:
            for line in section.lines:
                if line.diff_type == DiffType.UNCHANGED:
                    continue

                if line.severity == DiffSeverity.CRITICAL:
                    critical_count += 1
                    risk_assessment["critical_changes"].append(
                        {
                            "line": line.line_number,
                            "content": line.content,
                            "type": line.diff_type.value,
                            "category": line.category,
                        }
                    )
                elif line.severity == DiffSeverity.HIGH:
                    high_count += 1
                    risk_assessment["high_risk_changes"].append(
                        {
                            "line": line.line_number,
                            "content": line.content,
                            "type": line.diff_type.value,
                            "category": line.category,
                        }
                    )

        # 计算风险评分
        risk_score = critical_count * 10 + high_count * 5
        risk_assessment["risk_score"] = risk_score

        # 确定整体风险等级
        if critical_count > 0:
            risk_assessment["overall_risk"] = "critical"
        elif high_count > 5:
            risk_assessment["overall_risk"] = "high"
        elif high_count > 0:
            risk_assessment["overall_risk"] = "medium"
        else:
            risk_assessment["overall_risk"] = "low"

        return risk_assessment

    def _generate_recommendations(self, result: ConfigDiffResult) -> list[str]:
        """生成建议"""
        recommendations = []

        # 基于风险评估的建议
        if result.has_critical_changes:
            recommendations.append("⚠️ 检测到严重配置变更，建议在维护窗口期间执行")
            recommendations.append("📋 执行前请确保有完整的配置备份")
            recommendations.append("🔍 建议分段执行配置变更，便于问题定位")

        # 基于变更百分比的建议
        if result.change_percentage > 50:
            recommendations.append("📊 配置变更幅度较大，建议详细审查每项变更")
        elif result.change_percentage > 20:
            recommendations.append("📈 配置变更较多，建议重点关注关键配置项")

        # 基于配置类别的建议
        category_counts = result.summary.get("category_breakdown", {})

        if "routing" in category_counts:
            recommendations.append("🛣️ 包含路由配置变更，请确认网络连通性")

        if "security" in category_counts:
            recommendations.append("🔒 包含安全配置变更，请确认访问权限")

        if "interface" in category_counts:
            recommendations.append("🔌 包含接口配置变更，请确认物理连接")

        # 通用建议
        if not recommendations:
            recommendations.append("✅ 配置变更风险较低，可以正常执行")

        recommendations.append("📝 建议记录配置变更日志，便于后续追踪")

        return recommendations

    def generate_html_report(self, result: ConfigDiffResult) -> str:
        """生成HTML格式的差异报告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>配置差异报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
                .summary { margin: 20px 0; }
                .section { margin: 15px 0; border: 1px solid #ddd; border-radius: 5px; }
                .section-header { background-color: #e9e9e9; padding: 10px; font-weight: bold; }
                .line { padding: 5px; font-family: monospace; }
                .added { background-color: #d4edda; }
                .removed { background-color: #f8d7da; }
                .modified { background-color: #fff3cd; }
                .unchanged { background-color: #f8f9fa; }
                .critical { border-left: 4px solid #dc3545; }
                .high { border-left: 4px solid #fd7e14; }
                .medium { border-left: 4px solid #ffc107; }
                .low { border-left: 4px solid #28a745; }
                .recommendations { background-color: #e7f3ff; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>配置差异报告</h1>
                <p><strong>源配置:</strong> {source_name}</p>
                <p><strong>目标配置:</strong> {target_name}</p>
                <p><strong>生成时间:</strong> {timestamp}</p>
            </div>

            <div class="summary">
                <h2>差异摘要</h2>
                <ul>
                    <li>总行数: {total_lines}</li>
                    <li>新增行数: {added_lines}</li>
                    <li>删除行数: {removed_lines}</li>
                    <li>修改行数: {modified_lines}</li>
                    <li>变更百分比: {change_percentage:.1f}%</li>
                    <li>整体风险: {overall_risk}</li>
                </ul>
            </div>

            <div class="recommendations">
                <h2>建议</h2>
                <ul>
                    {recommendations_html}
                </ul>
            </div>

            <div class="sections">
                <h2>详细差异</h2>
                {sections_html}
            </div>
        </body>
        </html>
        """

        # 生成建议HTML
        recommendations_html = "\n".join([f"<li>{rec}</li>" for rec in result.recommendations])

        # 生成段落HTML
        sections_html = ""
        for section in result.sections:
            if not section.has_changes:
                continue

            section_html = f"""
            <div class="section">
                <div class="section-header">{section.name} (行 {section.start_line}-{section.end_line})</div>
            """

            for line in section.lines:
                if line.diff_type == DiffType.UNCHANGED:
                    continue

                css_classes = [line.diff_type.value, line.severity.value]
                section_html += f"""
                <div class="line {" ".join(css_classes)}">
                    <span class="line-number">{line.line_number}:</span>
                    <span class="content">{line.content}</span>
                </div>
                """

            section_html += "</div>"
            sections_html += section_html

        return html_template.format(
            source_name=result.source_name,
            target_name=result.target_name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_lines=result.total_lines,
            added_lines=result.added_lines,
            removed_lines=result.removed_lines,
            modified_lines=result.modified_lines,
            change_percentage=result.change_percentage,
            overall_risk=result.risk_assessment.get("overall_risk", "unknown"),
            recommendations_html=recommendations_html,
            sections_html=sections_html,
        )

    def generate_text_report(self, result: ConfigDiffResult) -> str:
        """生成文本格式的差异报告"""
        report_lines = []

        # 标题
        report_lines.append("=" * 60)
        report_lines.append("配置差异报告")
        report_lines.append("=" * 60)
        report_lines.append(f"源配置: {result.source_name}")
        report_lines.append(f"目标配置: {result.target_name}")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # 摘要
        report_lines.append("差异摘要:")
        report_lines.append("-" * 30)
        report_lines.append(f"总行数: {result.total_lines}")
        report_lines.append(f"新增行数: {result.added_lines}")
        report_lines.append(f"删除行数: {result.removed_lines}")
        report_lines.append(f"修改行数: {result.modified_lines}")
        report_lines.append(f"变更百分比: {result.change_percentage:.1f}%")
        report_lines.append(f"整体风险: {result.risk_assessment.get('overall_risk', 'unknown')}")
        report_lines.append("")

        # 建议
        report_lines.append("建议:")
        report_lines.append("-" * 30)
        for rec in result.recommendations:
            report_lines.append(f"• {rec}")
        report_lines.append("")

        # 详细差异
        report_lines.append("详细差异:")
        report_lines.append("-" * 30)

        for section in result.sections:
            if not section.has_changes:
                continue

            report_lines.append(f"\n[{section.name}] (行 {section.start_line}-{section.end_line})")

            for line in section.lines:
                if line.diff_type == DiffType.UNCHANGED:
                    continue

                prefix = {DiffType.ADDED: "+ ", DiffType.REMOVED: "- ", DiffType.MODIFIED: "~ "}.get(
                    line.diff_type, "  "
                )

                severity_marker = {
                    DiffSeverity.CRITICAL: "[!]",
                    DiffSeverity.HIGH: "[H]",
                    DiffSeverity.MEDIUM: "[M]",
                    DiffSeverity.LOW: "[L]",
                }.get(line.severity, "")

                report_lines.append(f"{prefix}{severity_marker} {line.content}")

        return "\n".join(report_lines)


# 全局配置差异管理器实例
config_diff_manager = ConfigDiffManager()
