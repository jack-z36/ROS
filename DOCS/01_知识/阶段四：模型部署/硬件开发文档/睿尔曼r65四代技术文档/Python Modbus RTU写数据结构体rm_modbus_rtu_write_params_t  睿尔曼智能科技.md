---
title: "Python: Modbus RTU写数据结构体rm_modbus_rtu_write_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/modbuswrite/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## Modbus RTU写数据结构体rm\_modbus\_rtu\_write\_params\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int` | 数据起始地址。 |
| `device` | `int` | 外设设备地址。 |
| `type` | `int` | 0-控制器端modbus主机；1-工具端modbus主机。 |
| `num` | `int` | 写入的数据的数量，数据长度不超过100。 |
| `data` | `int` | 写入的数据，数据长度不超过100。 |