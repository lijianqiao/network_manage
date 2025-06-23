# TextFSM解析器依赖安装指南

## 必需依赖

为了启用TextFSM结构化解析功能，需要安装以下依赖：

```bash
# 安装TextFSM和NTC-Templates
pip install textfsm ntc-templates

# 如果需要Scrapli-Community支持
pip install scrapli-community
```

## 支持的设备品牌

目前支持以下主流设备品牌：

- **Cisco**: cisco_ios, cisco_nxos, cisco_iosxr
- **Huawei**: huawei_vrp  
- **H3C**: hp_comware

## 使用说明

### 1. 基础TextFSM解析

```python
from app.network_automation.parsers.textfsm_parser import TextFSMParser

parser = TextFSMParser()
result = parser.parse_command_output(
    command_output=device_output,
    command="show version",
    brand="cisco"
)
```

### 2. Scrapli-Community增强解析

```python
from app.network_automation.enhanced_connection_manager import EnhancedConnectionManager

manager = EnhancedConnectionManager()
# 使用parsed=True参数自动解析输出
response = await conn.send_command("show version", parsed=True)
```

## 注意事项

1. **模板覆盖**: NTC-Templates项目包含大量但不是全部的命令模板
2. **品牌映射**: 确保设备品牌信息正确设置在数据库中
3. **回退机制**: 如果解析失败，会返回原始输出和错误信息
4. **性能**: TextFSM解析比TTP更成熟，模板更丰富

## 彻底移除的TTP组件

为了简化架构并专注于TextFSM解析，已彻底移除以下TTP相关组件：

### 已删除的文件
- `app/network_automation/parsers/ttp_parser.py` - TTP解析器主文件
- `app/network_automation/parsers/brand_detector.py` - 品牌检测器
- `app/network_automation/parsers/template_manager.py` - 模板管理器  
- `app/network_automation/parsers/result_formatter.py` - 结果格式化器
- `app/network_automation/templates/` - 整个TTP模板目录
  - `templates/cisco/show_version.ttp`
  - `templates/cisco/show_interface.ttp`
  - `templates/huawei/show_version.ttp`
  - `templates/huawei/show_interface.ttp`
  - `templates/h3c/show_version.ttp`
  - `templates/h3c/show_interface.ttp`

### 依赖清理
- 从`requirements.txt`中移除`ttp`依赖
- 添加`textfsm`和`ntc-templates`依赖
- 添加`scrapli-community`支持

### 代码更新
- `network_tasks.py`中的解析调用已切换为TextFSM
- `parsers/__init__.py`只导出TextFSMParser
- 移除所有TTP相关导入和引用

## 迁移优势

1. **更成熟的生态**: NTC-Templates拥有更丰富的命令模板库
2. **更好的维护**: TextFSM有活跃的社区支持和持续更新
3. **简化架构**: 减少了品牌检测、模板管理等复杂组件
4. **标准化**: 使用业界标准的解析方案
