# H3C显示命令增强模板示例

## 1. MAC地址表模板 (h3c_display_mac-address_enhanced.textfsm)
```
Value MAC ([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})
Value VLAN (\d+)
Value TYPE (\S+)
Value PORT (\S+)
Value AGING (\S+)

Start
  ^${MAC}\s+${VLAN}\s+${TYPE}\s+${PORT}\s+${AGING} -> Record
  ^Total\s+items\s+displayed\s+=\s+\d+ -> Continue
  ^\s*$$
  ^. -> Error
```

## 2. 接口简要信息模板 (h3c_display_interface_brief_enhanced.textfsm)
```
Value INTERFACE (\S+)
Value LINK_STATUS (up|down|admin-down)
Value PROTOCOL_STATUS (up|down)
Value DESCRIPTION (.*)

Start
  ^Interface\s+Link\s+Protocol\s+Description -> Next
  ^${INTERFACE}\s+${LINK_STATUS}\s+${PROTOCOL_STATUS}\s*${DESCRIPTION} -> Record
  ^\s*$$
  ^. -> Error
```

## 3. VLAN信息模板 (h3c_display_vlan_enhanced.textfsm)
```
Value VLAN_ID (\d+)
Value VLAN_NAME (\S+)
Value STATUS (\S+)
Value PORTS (.*)

Start
  ^VLAN\s+ID:\s+${VLAN_ID} -> Continue.Record
  ^VLAN\s+Name:\s+${VLAN_NAME}
  ^VLAN\s+Status:\s+${STATUS}
  ^Tagged\s+Ports:\s*${PORTS}
  ^Untagged\s+Ports:\s*${PORTS}
  ^\s*$$
  ^. -> Error
```

## 4. ARP表模板 (h3c_display_arp_enhanced.textfsm)
```
Value IP_ADDRESS (\d+\.\d+\.\d+\.\d+)
Value MAC_ADDRESS ([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})
Value VLAN (\d+)
Value INTERFACE (\S+)
Value AGE (\d+)
Value TYPE (\S+)

Start
  ^IP\s+ADDRESS\s+MAC\s+ADDRESS\s+VLAN/VSI\s+INTERFACE\s+AGE\s+TYPE -> Next
  ^${IP_ADDRESS}\s+${MAC_ADDRESS}\s+${VLAN}/--\s+${INTERFACE}\s+${AGE}\s+${TYPE} -> Record
  ^${IP_ADDRESS}\s+${MAC_ADDRESS}\s+${VLAN}\s+${INTERFACE}\s+${AGE}\s+${TYPE} -> Record
  ^\s*$$
  ^. -> Error
```
