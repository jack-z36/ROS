---
title: "Python: 机械臂所有状态参数结构体rm_arm_all_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/armAllState/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂所有状态参数结构体rm\_arm\_all\_state\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `joint_current` | `List[float]` | 关节电流，单位mA。 |
| `joint_en_flag` | `List[int]` | 关节使能状态。 |
| `joint_temperature` | `List[float]` | 关节温度,单位℃。 |
| `joint_voltage` | `List[float]` | 关节电压，单位V。 |
| `joint_err_code` | `List[int]` | 关节错误码。 |
| `err` | [`rm_err_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/err/) | 错误代码。 |

## 成员函数

```python
rm_ctypes_wrap.rm_arm_all_state_t.to_dictionary(self)
```