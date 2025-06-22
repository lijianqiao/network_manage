"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: init_templates.py
@DateTime: 2025-06-22
@Docs: 初始化基础网络设备模板数据
"""

import asyncio

from tortoise import Tortoise

from app.core.config import settings
from app.models.network_models import Brand, ConfigTemplate, TemplateCommand, TemplateTypeEnum


async def init_brands():
    """初始化品牌数据"""
    brands_data = [
        {"name": "H3C", "platform_type": "hp_comware"},
        {"name": "Huawei", "platform_type": "huawei"},
        {"name": "Cisco", "platform_type": "cisco_iosxe"},
    ]

    brands = {}
    for brand_data in brands_data:
        brand, created = await Brand.get_or_create(
            name=brand_data["name"], defaults={"platform_type": brand_data["platform_type"]}
        )
        brands[brand.name] = brand
        if created:
            print(f"创建品牌: {brand.name}")
        else:
            print(f"品牌已存在: {brand.name}")

    return brands


async def init_config_templates():
    """初始化配置模板"""
    templates_data = [
        # 查询类模板
        {"name": "显示版本信息", "template_type": TemplateTypeEnum.QUERY},
        {"name": "显示接口状态", "template_type": TemplateTypeEnum.QUERY},
        {"name": "显示VLAN信息", "template_type": TemplateTypeEnum.QUERY},
        {"name": "显示路由表", "template_type": TemplateTypeEnum.QUERY},
        {"name": "显示ARP表", "template_type": TemplateTypeEnum.QUERY},
        {"name": "显示MAC地址表", "template_type": TemplateTypeEnum.QUERY},
        {"name": "显示系统资源", "template_type": TemplateTypeEnum.QUERY},
        {"name": "显示日志信息", "template_type": TemplateTypeEnum.QUERY},
        # 配置类模板
        {"name": "创建VLAN", "template_type": TemplateTypeEnum.CONFIG},
        {"name": "配置接口", "template_type": TemplateTypeEnum.CONFIG},
        {"name": "配置OSPF", "template_type": TemplateTypeEnum.CONFIG},
        {"name": "配置ACL", "template_type": TemplateTypeEnum.CONFIG},
        {"name": "配置静态路由", "template_type": TemplateTypeEnum.CONFIG},
    ]

    templates = {}
    for template_data in templates_data:
        template, created = await ConfigTemplate.get_or_create(name=template_data["name"], defaults=template_data)
        templates[template.name] = template
        if created:
            print(f"创建配置模板: {template.name}")
        else:
            print(f"配置模板已存在: {template.name}")

    return templates


async def init_template_commands(brands, templates):
    """初始化模板命令"""

    # 查询类模板命令
    query_commands = {
        "显示版本信息": {
            "H3C": {
                "jinja_content": "display version",
                "ttp_template": """
<group name="version_info">
H3C <device_type> Software Version <software_version>
Copyright (c) <copyright_year> New H3C Technologies Co., Ltd. All rights reserved.
<device_type> uptime is <uptime>
<device_type> <hardware_version> (Board type: <board_type>)
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display version",
                "ttp_template": """
<group name="version_info">
Huawei Versatile Routing Platform Software
VRP (R) software, Version <software_version>
Copyright (C) <copyright_year> Huawei Technologies Co., Ltd.
HUAWEI <device_type> uptime is <uptime>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show version",
                "ttp_template": """
<group name="version_info">
Cisco IOS XE Software, Version <software_version>
<device_type> uptime is <uptime>
System returned to ROM by <reload_reason>
</group>
                """.strip(),
                "expected_params": [],
            },
        },
        "显示接口状态": {
            "H3C": {
                "jinja_content": "display interface brief",
                "ttp_template": """
<group name="interfaces*">
<interface_name>\\s+<status>\\s+<protocol>\\s+<physical>\\s+<description>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display interface brief",
                "ttp_template": """
<group name="interfaces*">
<interface_name>\\s+<status>\\s+<protocol>\\s+<speed>\\s+<duplex>\\s+<description>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show interfaces status",
                "ttp_template": """
<group name="interfaces*">
<interface_name>\\s+<description>\\s+<status>\\s+<vlan>\\s+<duplex>\\s+<speed>\\s+<type>
</group>
                """.strip(),
                "expected_params": [],
            },
        },
        "显示VLAN信息": {
            "H3C": {
                "jinja_content": "display vlan brief",
                "ttp_template": """
<group name="vlans*">
<vlan_id>\\s+<name>\\s+<status>\\s+<ports>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display vlan",
                "ttp_template": """
<group name="vlans*">
VLAN ID: <vlan_id>
VLAN Name: <name>
VLAN Status: <status>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show vlan brief",
                "ttp_template": """
<group name="vlans*">
<vlan_id>\\s+<name>\\s+<status>\\s+<ports>
</group>
                """.strip(),
                "expected_params": [],
            },
        },
        "显示路由表": {
            "H3C": {
                "jinja_content": "display ip routing-table",
                "ttp_template": """
<group name="routes*">
<destination>/<mask>\\s+<next_hop>\\s+<metric>\\s+<protocol>\\s+<interface>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display ip routing-table",
                "ttp_template": """
<group name="routes*">
<destination>/<mask>\\s+<next_hop>\\s+<metric>\\s+<protocol>\\s+<interface>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show ip route",
                "ttp_template": """
<group name="routes*">
<protocol>\\s+<destination>/<mask>\\s+\\[<admin_distance>/<metric>\\]\\s+via\\s+<next_hop>,\\s+<interface>
</group>
                """.strip(),
                "expected_params": [],
            },
        },
        "显示ARP表": {
            "H3C": {
                "jinja_content": "display arp",
                "ttp_template": """
<group name="arp_entries*">
<ip_address>\\s+<mac_address>\\s+<vlan>\\s+<interface>\\s+<type>\\s+<aging>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display arp",
                "ttp_template": """
<group name="arp_entries*">
<ip_address>\\s+<mac_address>\\s+<interface>\\s+<vlan>\\s+<type>\\s+<aging>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show arp",
                "ttp_template": """
<group name="arp_entries*">
Internet\\s+<ip_address>\\s+<age>\\s+<mac_address>\\s+<type>\\s+<interface>
</group>
                """.strip(),
                "expected_params": [],
            },
        },
        "显示MAC地址表": {
            "H3C": {
                "jinja_content": "display mac-address",
                "ttp_template": """
<group name="mac_entries*">
<mac_address>\\s+<vlan>\\s+<type>\\s+<interface>\\s+<aging>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display mac-address",
                "ttp_template": """
<group name="mac_entries*">
<mac_address>\\s+<vlan>\\s+<interface>\\s+<type>\\s+<aging>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show mac address-table",
                "ttp_template": """
<group name="mac_entries*">
<vlan>\\s+<mac_address>\\s+<type>\\s+<interface>
</group>
                """.strip(),
                "expected_params": [],
            },
        },
        "显示系统资源": {
            "H3C": {
                "jinja_content": "display memory",
                "ttp_template": """
<group name="memory_info">
Memory Using Percentage Is: <memory_usage>%
</group>

<group name="cpu_info">
CPU Usage: <cpu_usage>%
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display memory && display cpu-usage",
                "ttp_template": """
<group name="memory_info">
Memory utilization: <memory_usage>%
</group>

<group name="cpu_info">
CPU utilization: <cpu_usage>%
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show processes memory && show processes cpu",
                "ttp_template": """
<group name="memory_info">
Total: <total_memory>, Used: <used_memory>, Free: <free_memory>
</group>

<group name="cpu_info">
CPU utilization for five seconds: <cpu_5s>%; one minute: <cpu_1m>%; five minutes: <cpu_5m>%
</group>
                """.strip(),
                "expected_params": [],
            },
        },
        "显示日志信息": {
            "H3C": {
                "jinja_content": "display logbuffer",
                "ttp_template": """
<group name="logs*">
<timestamp>\\s+<facility>\\s+<severity>\\s+<message>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Huawei": {
                "jinja_content": "display logbuffer",
                "ttp_template": """
<group name="logs*">
<timestamp>\\s+<facility>\\s+<severity>\\s+<message>
</group>
                """.strip(),
                "expected_params": [],
            },
            "Cisco": {
                "jinja_content": "show logging",
                "ttp_template": """
<group name="logs*">
<timestamp>: <facility>-<severity>-<message>
</group>
                """.strip(),
                "expected_params": [],
            },
        },
    }

    # 配置类模板命令
    config_commands = {
        "创建VLAN": {
            "H3C": {
                "jinja_content": """system-view
vlan {{ vlan_id }}
{% if vlan_name %} name {{ vlan_name }}{% endif %}
{% if description %} description {{ description }}{% endif %}
quit
quit""",
                "expected_params": [
                    {"name": "vlan_id", "type": "int", "required": True, "description": "VLAN ID"},
                    {"name": "vlan_name", "type": "string", "required": False, "description": "VLAN名称"},
                    {"name": "description", "type": "string", "required": False, "description": "VLAN描述"},
                ],
            },
            "Huawei": {
                "jinja_content": """system-view
vlan {{ vlan_id }}
{% if vlan_name %} name {{ vlan_name }}{% endif %}
{% if description %} description {{ description }}{% endif %}
quit
quit""",
                "expected_params": [
                    {"name": "vlan_id", "type": "int", "required": True, "description": "VLAN ID"},
                    {"name": "vlan_name", "type": "string", "required": False, "description": "VLAN名称"},
                    {"name": "description", "type": "string", "required": False, "description": "VLAN描述"},
                ],
            },
            "Cisco": {
                "jinja_content": """configure terminal
vlan {{ vlan_id }}
{% if vlan_name %} name {{ vlan_name }}{% endif %}
exit
exit""",
                "expected_params": [
                    {"name": "vlan_id", "type": "int", "required": True, "description": "VLAN ID"},
                    {"name": "vlan_name", "type": "string", "required": False, "description": "VLAN名称"},
                ],
            },
        },
        "配置接口": {
            "H3C": {
                "jinja_content": """system-view
interface {{ interface_name }}
{% if ip_address and subnet_mask %} ip address {{ ip_address }} {{ subnet_mask }}{% endif %}
{% if description %} description {{ description }}{% endif %}
{% if vlan_id %} port link-type {{ link_type | default('access') }}
 port access vlan {{ vlan_id }}{% endif %}
{% if shutdown %} shutdown{% else %} undo shutdown{% endif %}
quit
quit""",
                "expected_params": [
                    {"name": "interface_name", "type": "string", "required": True, "description": "接口名称"},
                    {"name": "ip_address", "type": "string", "required": False, "description": "IP地址"},
                    {"name": "subnet_mask", "type": "string", "required": False, "description": "子网掩码"},
                    {"name": "description", "type": "string", "required": False, "description": "接口描述"},
                    {"name": "vlan_id", "type": "int", "required": False, "description": "VLAN ID"},
                    {"name": "link_type", "type": "string", "required": False, "description": "链路类型"},
                    {"name": "shutdown", "type": "boolean", "required": False, "description": "是否关闭接口"},
                ],
            },
            "Huawei": {
                "jinja_content": """system-view
interface {{ interface_name }}
{% if ip_address and subnet_mask %} ip address {{ ip_address }} {{ subnet_mask }}{% endif %}
{% if description %} description {{ description }}{% endif %}
{% if vlan_id %} port link-type {{ link_type | default('access') }}
 port default vlan {{ vlan_id }}{% endif %}
{% if shutdown %} shutdown{% else %} undo shutdown{% endif %}
quit
quit""",
                "expected_params": [
                    {"name": "interface_name", "type": "string", "required": True, "description": "接口名称"},
                    {"name": "ip_address", "type": "string", "required": False, "description": "IP地址"},
                    {"name": "subnet_mask", "type": "string", "required": False, "description": "子网掩码"},
                    {"name": "description", "type": "string", "required": False, "description": "接口描述"},
                    {"name": "vlan_id", "type": "int", "required": False, "description": "VLAN ID"},
                    {"name": "link_type", "type": "string", "required": False, "description": "链路类型"},
                    {"name": "shutdown", "type": "boolean", "required": False, "description": "是否关闭接口"},
                ],
            },
            "Cisco": {
                "jinja_content": """configure terminal
interface {{ interface_name }}
{% if ip_address and subnet_mask %} ip address {{ ip_address }} {{ subnet_mask }}{% endif %}
{% if description %} description {{ description }}{% endif %}
{% if vlan_id and interface_name.startswith('Gi') %} switchport mode access
 switchport access vlan {{ vlan_id }}{% endif %}
{% if shutdown %} shutdown{% else %} no shutdown{% endif %}
exit
exit""",
                "expected_params": [
                    {"name": "interface_name", "type": "string", "required": True, "description": "接口名称"},
                    {"name": "ip_address", "type": "string", "required": False, "description": "IP地址"},
                    {"name": "subnet_mask", "type": "string", "required": False, "description": "子网掩码"},
                    {"name": "description", "type": "string", "required": False, "description": "接口描述"},
                    {"name": "vlan_id", "type": "int", "required": False, "description": "VLAN ID"},
                    {"name": "shutdown", "type": "boolean", "required": False, "description": "是否关闭接口"},
                ],
            },
        },
        "配置OSPF": {
            "H3C": {
                "jinja_content": """system-view
ospf {{ process_id | default(1) }}
 router-id {{ router_id }}
 area {{ area_id | default('0.0.0.0') }}
  network {{ network }} {{ wildcard_mask }} area {{ area_id | default('0.0.0.0') }}
quit
quit
quit""",
                "expected_params": [
                    {"name": "process_id", "type": "int", "required": False, "description": "OSPF进程ID"},
                    {"name": "router_id", "type": "string", "required": True, "description": "路由器ID"},
                    {"name": "area_id", "type": "string", "required": False, "description": "OSPF区域ID"},
                    {"name": "network", "type": "string", "required": True, "description": "网络地址"},
                    {"name": "wildcard_mask", "type": "string", "required": True, "description": "通配符掩码"},
                ],
            },
            "Huawei": {
                "jinja_content": """system-view
ospf {{ process_id | default(1) }}
 router-id {{ router_id }}
 area {{ area_id | default('0.0.0.0') }}
  network {{ network }} {{ wildcard_mask }}
quit
quit
quit""",
                "expected_params": [
                    {"name": "process_id", "type": "int", "required": False, "description": "OSPF进程ID"},
                    {"name": "router_id", "type": "string", "required": True, "description": "路由器ID"},
                    {"name": "area_id", "type": "string", "required": False, "description": "OSPF区域ID"},
                    {"name": "network", "type": "string", "required": True, "description": "网络地址"},
                    {"name": "wildcard_mask", "type": "string", "required": True, "description": "通配符掩码"},
                ],
            },
            "Cisco": {
                "jinja_content": """configure terminal
router ospf {{ process_id | default(1) }}
 router-id {{ router_id }}
 network {{ network }} {{ wildcard_mask }} area {{ area_id | default(0) }}
exit
exit""",
                "expected_params": [
                    {"name": "process_id", "type": "int", "required": False, "description": "OSPF进程ID"},
                    {"name": "router_id", "type": "string", "required": True, "description": "路由器ID"},
                    {"name": "area_id", "type": "string", "required": False, "description": "OSPF区域ID"},
                    {"name": "network", "type": "string", "required": True, "description": "网络地址"},
                    {"name": "wildcard_mask", "type": "string", "required": True, "description": "通配符掩码"},
                ],
            },
        },
        "配置ACL": {
            "H3C": {
                "jinja_content": """system-view
acl {{ acl_type | default('advanced') }} {{ acl_number }}
{% if permit_rule %} rule {{ rule_number | default(10) }} permit {{ protocol | default('ip') }} source {{ source_ip }} {{ source_mask | default('0.0.0.0') }} destination {{ dest_ip }} {{ dest_mask | default('0.0.0.0') }}{% endif %}
{% if deny_rule %} rule {{ rule_number | default(20) }} deny {{ protocol | default('ip') }} source {{ source_ip }} {{ source_mask | default('0.0.0.0') }} destination {{ dest_ip }} {{ dest_mask | default('0.0.0.0') }}{% endif %}
quit
quit""",
                "expected_params": [
                    {"name": "acl_type", "type": "string", "required": False, "description": "ACL类型"},
                    {"name": "acl_number", "type": "int", "required": True, "description": "ACL编号"},
                    {"name": "rule_number", "type": "int", "required": False, "description": "规则编号"},
                    {"name": "permit_rule", "type": "boolean", "required": False, "description": "是否为允许规则"},
                    {"name": "deny_rule", "type": "boolean", "required": False, "description": "是否为拒绝规则"},
                    {"name": "protocol", "type": "string", "required": False, "description": "协议类型"},
                    {"name": "source_ip", "type": "string", "required": True, "description": "源IP地址"},
                    {"name": "source_mask", "type": "string", "required": False, "description": "源IP掩码"},
                    {"name": "dest_ip", "type": "string", "required": True, "description": "目标IP地址"},
                    {"name": "dest_mask", "type": "string", "required": False, "description": "目标IP掩码"},
                ],
            },
            "Huawei": {
                "jinja_content": """system-view
acl {{ acl_number }}
{% if permit_rule %} rule {{ rule_number | default(10) }} permit {{ protocol | default('ip') }} source {{ source_ip }} {{ source_mask | default('0.0.0.0') }} destination {{ dest_ip }} {{ dest_mask | default('0.0.0.0') }}{% endif %}
{% if deny_rule %} rule {{ rule_number | default(20) }} deny {{ protocol | default('ip') }} source {{ source_ip }} {{ source_mask | default('0.0.0.0') }} destination {{ dest_ip }} {{ dest_mask | default('0.0.0.0') }}{% endif %}
quit
quit""",
                "expected_params": [
                    {"name": "acl_number", "type": "int", "required": True, "description": "ACL编号"},
                    {"name": "rule_number", "type": "int", "required": False, "description": "规则编号"},
                    {"name": "permit_rule", "type": "boolean", "required": False, "description": "是否为允许规则"},
                    {"name": "deny_rule", "type": "boolean", "required": False, "description": "是否为拒绝规则"},
                    {"name": "protocol", "type": "string", "required": False, "description": "协议类型"},
                    {"name": "source_ip", "type": "string", "required": True, "description": "源IP地址"},
                    {"name": "source_mask", "type": "string", "required": False, "description": "源IP掩码"},
                    {"name": "dest_ip", "type": "string", "required": True, "description": "目标IP地址"},
                    {"name": "dest_mask", "type": "string", "required": False, "description": "目标IP掩码"},
                ],
            },
            "Cisco": {
                "jinja_content": """configure terminal
ip access-list {{ acl_type | default('extended') }} {{ acl_name }}
{% if permit_rule %} {{ rule_number | default(10) }} permit {{ protocol | default('ip') }} {{ source_ip }} {{ source_mask | default('0.0.0.0') }} {{ dest_ip }} {{ dest_mask | default('0.0.0.0') }}{% endif %}
{% if deny_rule %} {{ rule_number | default(20) }} deny {{ protocol | default('ip') }} {{ source_ip }} {{ source_mask | default('0.0.0.0') }} {{ dest_ip }} {{ dest_mask | default('0.0.0.0') }}{% endif %}
exit
exit""",
                "expected_params": [
                    {"name": "acl_type", "type": "string", "required": False, "description": "ACL类型"},
                    {"name": "acl_name", "type": "string", "required": True, "description": "ACL名称"},
                    {"name": "rule_number", "type": "int", "required": False, "description": "规则编号"},
                    {"name": "permit_rule", "type": "boolean", "required": False, "description": "是否为允许规则"},
                    {"name": "deny_rule", "type": "boolean", "required": False, "description": "是否为拒绝规则"},
                    {"name": "protocol", "type": "string", "required": False, "description": "协议类型"},
                    {"name": "source_ip", "type": "string", "required": True, "description": "源IP地址"},
                    {"name": "source_mask", "type": "string", "required": False, "description": "源IP掩码"},
                    {"name": "dest_ip", "type": "string", "required": True, "description": "目标IP地址"},
                    {"name": "dest_mask", "type": "string", "required": False, "description": "目标IP掩码"},
                ],
            },
        },
        "配置静态路由": {
            "H3C": {
                "jinja_content": """system-view
ip route-static {{ destination_network }} {{ subnet_mask }} {{ next_hop }}{% if distance %} {{ distance }}{% endif %}
quit""",
                "expected_params": [
                    {"name": "destination_network", "type": "string", "required": True, "description": "目标网络"},
                    {"name": "subnet_mask", "type": "string", "required": True, "description": "子网掩码"},
                    {"name": "next_hop", "type": "string", "required": True, "description": "下一跳地址"},
                    {"name": "distance", "type": "int", "required": False, "description": "管理距离"},
                ],
            },
            "Huawei": {
                "jinja_content": """system-view
ip route-static {{ destination_network }} {{ subnet_mask }} {{ next_hop }}{% if distance %} preference {{ distance }}{% endif %}
quit""",
                "expected_params": [
                    {"name": "destination_network", "type": "string", "required": True, "description": "目标网络"},
                    {"name": "subnet_mask", "type": "string", "required": True, "description": "子网掩码"},
                    {"name": "next_hop", "type": "string", "required": True, "description": "下一跳地址"},
                    {"name": "distance", "type": "int", "required": False, "description": "管理距离"},
                ],
            },
            "Cisco": {
                "jinja_content": """configure terminal
ip route {{ destination_network }} {{ subnet_mask }} {{ next_hop }}{% if distance %} {{ distance }}{% endif %}
exit""",
                "expected_params": [
                    {"name": "destination_network", "type": "string", "required": True, "description": "目标网络"},
                    {"name": "subnet_mask", "type": "string", "required": True, "description": "子网掩码"},
                    {"name": "next_hop", "type": "string", "required": True, "description": "下一跳地址"},
                    {"name": "distance", "type": "int", "required": False, "description": "管理距离"},
                ],
            },
        },
    }

    # 合并所有命令
    all_commands = {**query_commands, **config_commands}

    # 创建模板命令
    created_count = 0
    for template_name, brand_commands in all_commands.items():
        if template_name not in templates:
            print(f"警告: 模板 '{template_name}' 不存在，跳过")
            continue

        template = templates[template_name]

        for brand_name, command_data in brand_commands.items():
            if brand_name not in brands:
                print(f"警告: 品牌 '{brand_name}' 不存在，跳过")
                continue

            brand = brands[brand_name]

            # 检查是否已存在
            existing = await TemplateCommand.filter(config_template=template, brand=brand).first()

            if existing:
                print(f"模板命令已存在: {template_name} - {brand_name}")
                continue

            # 创建新的模板命令
            await TemplateCommand.create(
                config_template=template,
                brand=brand,
                jinja_content=command_data["jinja_content"],
                ttp_template=command_data.get("ttp_template"),
                expected_params=command_data.get("expected_params", []),
            )

            created_count += 1
            print(f"创建模板命令: {template_name} - {brand_name}")

    print(f"总共创建了 {created_count} 个模板命令")


async def main():
    """主函数"""
    # 初始化数据库连接
    await Tortoise.init(config=settings.TORTOISE_ORM_CONFIG)

    try:
        print("开始初始化基础模板数据...")

        # 初始化品牌
        print("\n=== 初始化品牌数据 ===")
        brands = await init_brands()

        # 初始化配置模板
        print("\n=== 初始化配置模板 ===")
        templates = await init_config_templates()

        # 初始化模板命令
        print("\n=== 初始化模板命令 ===")
        await init_template_commands(brands, templates)

        print("\n初始化完成！")

    except Exception as e:
        print(f"初始化失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
