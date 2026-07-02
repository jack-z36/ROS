---
title: "C、C++: Modbus RTU读数据参数结构体rm_modbus_rtu_read_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/struct/modbusread/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## Modbus RTU读数据参数结构体rm\_modbus\_rtu\_read\_params\_t

## 类成员变量说明

### 数据起始地址address

```
int rm_modbus_rtu_read_params_t::address
```

### 外设设备地址device

```
int rm_modbus_rtu_read_params_t::device
```

### Modbus主机类型type

0-控制器端modbus主机；1-工具端modbus主机。

```
int rm_modbus_rtu_read_params_t::type
```

### 数据的数量num

读取数据的数量，数据长度不超过100。

```
int rm_modbus_rtu_read_params_t::num
```