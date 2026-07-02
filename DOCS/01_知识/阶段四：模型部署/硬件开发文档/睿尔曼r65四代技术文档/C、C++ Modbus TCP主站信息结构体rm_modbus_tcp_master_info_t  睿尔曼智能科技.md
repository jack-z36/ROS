---
title: "C、C++: Modbus TCP主站信息结构体rm_modbus_tcp_master_info_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/modbustcpmaster/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
[Skip to content](#VPContent)

## Modbus TCP主站信息结构体rm\_modbus\_tcp\_master\_info\_t

## 类成员变量说明

### Modbus TCP主站名称master\_name

```
char rm_modbus_tcp_master_info_t::master_name[20]
```

### 主站IP地址ip

```
char rm_modbus_tcp_master_info_t::ip[16]
```

### 主站端口号port

```
int rm_modbus_tcp_master_info_t::port
```