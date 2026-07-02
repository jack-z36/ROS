---
title: "Python: Modbus TCP主站列表结构体rm_modbus_tcp_master_list_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/modbustcpmasterlist/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## Modbus TCP主站列表结构体rm\_modbus\_tcp\_master\_list\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int` | 页码。 |
| `page_size` | `int` | 每页大小。 |
| `total_size` | `int` | Modbus TCP主站列表长度。 |
| `vague_search` | `char` | 模糊搜索。 |
| `list_len` | `int` | 返回符合的Modbus TCP主站列表长度。 |
| `master_list` | `rm_modbus_tcp_master_info_t` | 返回符合的Modbus TCP主站列表。 |

*可以跳转 [rm\_modbus\_tcp\_master\_info\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/modbustcpmaster/) 查阅结构体详细描述。*