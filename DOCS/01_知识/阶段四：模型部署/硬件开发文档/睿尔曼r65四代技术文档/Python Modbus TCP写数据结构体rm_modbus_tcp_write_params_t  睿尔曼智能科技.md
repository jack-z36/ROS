---
title: "Python: Modbus TCP写数据结构体rm_modbus_tcp_write_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/modbustcpswrite/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## Modbus TCP写数据结构体rm\_modbus\_tcp\_write\_params\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int` | 数据起始地址。 |
| `master_name` | `char` | Modbus TCP主站名称。 |
| `ip` | `char` | 主机IP地址。 |
| `port` | `int` | 主机端口号。 |
| `num` | `int` | 写入数据的数量，数据长度不超过100。 |
| `data` | `int` | 写入的数据，数据长度不超过100。 |