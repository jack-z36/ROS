---
title: "Python: 动作列表结构体rm_tool_action_list_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/actionlist/"
author:
published: 2025-10-09
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 动作列表结构体rm\_tool\_action\_list\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int` | 页码。 |
| `page_size` | `int` | 每页大小。 |
| `total_size` | `int` | 列表长度。 |
| `vague_search` | `char` | 模糊搜索。 |
| `list_len` | `int` | 返回符合的动作列表长度。 |
| `act_list` | `rm_tool_action_info_t` | 返回符合的动作列表。 |

## 成员函数

```
rm_ctypes_wrap.rm_tool_action_list_t .to_dict(self, recurse=True):
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。

*可以跳转 [rm\_tool\_action\_info\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/actioninfo/) 查阅结构体详细描述。*