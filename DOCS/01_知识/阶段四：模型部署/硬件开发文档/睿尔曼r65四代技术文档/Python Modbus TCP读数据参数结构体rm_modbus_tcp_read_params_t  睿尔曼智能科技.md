---
title: "Python: Modbus TCP读数据参数结构体rm_modbus_tcp_read_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/modbustcpread/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## Modbus TCP读数据参数结构体rm\_modbus\_tcp\_read\_params\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int` | 数据起始地址。 |
| `master_name` | `char` | Modbus TCP主站名称。 |
| `ip` | `char` | 主机IP地址。 |
| `port` | `int` | 主机端口号。 |
| `num` | `int` | 读取数据的数量，数据长度不超过100。 |