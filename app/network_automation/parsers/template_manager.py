"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: template_manager.py
@DateTime: 2025/06/23 15:45:00
@Docs: TTP模板管理器 - 管理不同品牌设备的解析模板
"""

from pathlib import Path
from typing import Any

from app.utils.logger import logger


class TemplateManager:
    """TTP模板管理器"""

    def __init__(self, template_root: str | None = None):
        """初始化模板管理器

        Args:
            template_root: 模板根目录路径，默认为当前包下的templates目录
        """
        self.logger = logger

        # 设置模板根目录
        if template_root:
            self.template_root = Path(template_root)
        else:
            # 默认为当前包下的templates目录
            current_dir = Path(__file__).parent.parent
            self.template_root = current_dir / "templates"

        # 确保模板目录存在
        self.template_root.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"TTP模板根目录: {self.template_root}")

        # 模板缓存
        self._template_cache = {}

        # 初始化时扫描可用模板
        self._scan_templates()

    def _scan_templates(self):
        """扫描并缓存可用的模板信息"""
        try:
            self.logger.info("开始扫描TTP模板...")
            template_info = {}

            for brand_dir in self.template_root.iterdir():
                if not brand_dir.is_dir():
                    continue

                brand = brand_dir.name.lower()
                template_info[brand] = {}

                # 扫描品牌目录下的模板文件
                for template_file in brand_dir.iterdir():
                    if template_file.suffix == ".ttp":
                        # 模板名称（不含扩展名）
                        template_name = template_file.stem
                        template_info[brand][template_name] = str(template_file)

                self.logger.debug(f"品牌 {brand} 发现 {len(template_info[brand])} 个模板")

            self._template_info = template_info
            self.logger.info(f"模板扫描完成，支持 {len(template_info)} 个品牌")

        except Exception as e:
            self.logger.error(f"扫描模板失败: {e}")
            self._template_info = {}

    def get_template_content(self, brand: str, command_type: str) -> str | None:
        """获取指定品牌和命令类型的模板内容

        Args:
            brand: 设备品牌
            command_type: 命令类型（如 show_version, show_interface 等）

        Returns:
            模板内容字符串，如果找不到则返回None
        """
        try:
            brand = brand.lower()
            cache_key = f"{brand}_{command_type}"

            # 尝试从缓存获取
            if cache_key in self._template_cache:
                return self._template_cache[cache_key]

            # 查找模板文件
            template_path = self._find_template_path(brand, command_type)
            if not template_path:
                self.logger.warning(f"未找到模板: brand={brand}, command_type={command_type}")
                return None

            # 读取模板内容
            with open(template_path, encoding="utf-8") as f:
                template_content = f.read()

            # 缓存模板内容
            self._template_cache[cache_key] = template_content
            self.logger.debug(f"加载模板成功: {template_path}")

            return template_content

        except Exception as e:
            self.logger.error(f"获取模板内容失败: {e}")
            return None

    def _find_template_path(self, brand: str, command_type: str) -> str | None:
        """查找模板文件路径

        Args:
            brand: 设备品牌
            command_type: 命令类型

        Returns:
            模板文件路径，如果找不到则返回None
        """
        # 直接查找
        if brand in self._template_info and command_type in self._template_info[brand]:
            return self._template_info[brand][command_type]

        # 模糊匹配命令类型
        if brand in self._template_info:
            for template_name, template_path in self._template_info[brand].items():
                if command_type in template_name or template_name in command_type:
                    self.logger.debug(f"使用模糊匹配模板: {template_name} for {command_type}")
                    return template_path

        return None

    def list_templates(self, brand: str | None = None) -> dict[str, Any]:
        """列出可用的模板

        Args:
            brand: 指定品牌，如果为None则列出所有品牌

        Returns:
            模板信息字典
        """
        if brand:
            brand = brand.lower()
            return {brand: self._template_info.get(brand, {})}
        else:
            return dict(self._template_info)

    def get_supported_brands(self) -> list[str]:
        """获取支持的品牌列表

        Returns:
            支持的品牌名称列表
        """
        return list(self._template_info.keys())

    def get_supported_commands(self, brand: str) -> list[str]:
        """获取指定品牌支持的命令类型

        Args:
            brand: 设备品牌

        Returns:
            支持的命令类型列表
        """
        brand = brand.lower()
        return list(self._template_info.get(brand, {}).keys())

    def has_template(self, brand: str, command_type: str) -> bool:
        """检查是否存在指定的模板

        Args:
            brand: 设备品牌
            command_type: 命令类型

        Returns:
            是否存在该模板
        """
        brand = brand.lower()
        return brand in self._template_info and command_type in self._template_info[brand]

    def reload_templates(self):
        """重新加载模板

        重新扫描模板目录并清空缓存
        """
        self.logger.info("重新加载TTP模板...")
        self._template_cache.clear()
        self._scan_templates()

    def infer_command_type(self, command: str) -> str:
        """从命令推断命令类型

        Args:
            command: 原始命令

        Returns:
            推断的命令类型
        """
        command = command.lower().strip()

        # 命令类型映射规则
        command_mappings = {
            "show version": "show_version",
            "show ver": "show_version",
            "display version": "show_version",
            "show interface": "show_interface",
            "show interfaces": "show_interface",
            "display interface": "show_interface",
            "show ip route": "show_ip_route",
            "show route": "show_ip_route",
            "display ip routing-table": "show_ip_route",
            "show vlan": "show_vlan",
            "display vlan": "show_vlan",
            "show arp": "show_arp",
            "display arp": "show_arp",
            "show mac": "show_mac",
            "show mac-address": "show_mac",
            "display mac-address": "show_mac",
        }

        # 精确匹配
        if command in command_mappings:
            return command_mappings[command]

        # 部分匹配
        for cmd_pattern, cmd_type in command_mappings.items():
            if cmd_pattern in command:
                return cmd_type

        # 默认使用命令本身（替换空格为下划线）
        return command.replace(" ", "_").replace("-", "_")

    def create_template_file(self, brand: str, command_type: str, template_content: str) -> bool:
        """创建新的模板文件

        Args:
            brand: 设备品牌
            command_type: 命令类型
            template_content: 模板内容

        Returns:
            是否创建成功
        """
        try:
            brand = brand.lower()

            # 创建品牌目录
            brand_dir = self.template_root / brand
            brand_dir.mkdir(parents=True, exist_ok=True)

            # 创建模板文件
            template_file = brand_dir / f"{command_type}.ttp"

            with open(template_file, "w", encoding="utf-8") as f:
                f.write(template_content)

            # 重新扫描模板
            self._scan_templates()

            self.logger.info(f"创建模板成功: {template_file}")
            return True

        except Exception as e:
            self.logger.error(f"创建模板失败: {e}")
            return False
