---
title: "Python: 轨迹列表结构体rm_trajectory_list_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/trajectoryinfolist/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 轨迹列表结构体rm\_trajectory\_list\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int` | 页码。 |
| `page_size` | `int` | 每页大小。 |
| `total_size` | `int` | 列表长度。 |
| `vague_search` | `char` | 模糊搜索。 |
| `list_len` | `int` | 返回符合的轨迹列表长度。 |
| `tra_list` | `rm_trajectory_info_t` | 返回符合的轨迹列表。 |

*可以跳转 [rm\_trajectory\_info\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/trajectoryinfo/) 查阅结构体详细描述。*