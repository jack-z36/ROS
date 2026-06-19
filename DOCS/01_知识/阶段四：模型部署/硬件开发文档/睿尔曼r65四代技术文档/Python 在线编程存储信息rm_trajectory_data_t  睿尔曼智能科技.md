---
title: "Python: 在线编程存储信息rm_trajectory_data_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/trajectoryData/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 在线编程存储信息rm\_trajectory\_data\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `int` | 在线编程文件id。 |
| `size` | `int` | 文件大小。 |
| `speed` | `int` | 默认运行速度。 |
| `trajectory_name` | `int` | 文件名称。 |

## 成员函数

```python
rm_ctypes_wrap.rm_trajectory_data_t.to_dict(self, recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段