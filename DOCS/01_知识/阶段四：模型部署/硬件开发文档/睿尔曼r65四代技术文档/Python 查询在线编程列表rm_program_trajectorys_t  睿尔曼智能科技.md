---
title: "Python: 查询在线编程列表rm_program_trajectorys_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/programTrajectorys/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 查询在线编程列表rm\_program\_trajectorys\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int` | 页码。 |
| `page_size` | `int` | 每页大小。 |
| `list_size` | `int` | 返回总数量。 |
| `vague_search` | `bytes` | 模糊搜索字符串。 |
| `trajectory_list` | `list` | 符合的在线编程列表（包含 [rm\_trajectory\_data\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/trajectoryData/) 结构体的数组）。 |

## 成员函数

```python
rm_ctypes_wrap.rm_program_trajectorys_t.to_dict(self, recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段