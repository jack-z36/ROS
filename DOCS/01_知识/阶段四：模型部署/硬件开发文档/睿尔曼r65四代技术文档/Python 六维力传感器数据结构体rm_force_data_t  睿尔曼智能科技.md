---
title: "Python: 六维力传感器数据结构体rm_force_data_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/forceData/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 六维力传感器数据结构体rm\_force\_data\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `force_data` | `List[float]` | 当前力传感器原始数据，力的单位为N；力矩单位为Nm。 |
| `zero_force_data` | `List[float]` | 当前力传感器系统外受力数据，力的单位为N；力矩单位为Nm。 |
| `work_zero_force_data` | `List[float]` | 当前工作坐标系下系统外受力数据，力的单位为N；力矩单位为Nm。 |
| `tool_zero_force_data` | `List[float]` | 当前工具坐标系下系统外受力数据，力的单位为N；力矩单位为Nm。 |

## 成员函数

```python
rm_ctypes_wrap.rm_force_data_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。