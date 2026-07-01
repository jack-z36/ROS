---
title: "Python: 夹爪状态结构体rm_gripper_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/gripperState/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 夹爪状态结构体rm\_gripper\_state\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `enable_state` | `int` | 夹爪使能标志，0表示未使能，1表示使能。 |
| `status` | `int` | 夹爪在线状态，0表示离线，1表示在线。 |
| `error` | `int` | 夹爪错误信息，低8位表示夹爪内部的错误信息bit5-7 保留bit4 内部通bit3 驱动器bit2 过流 bit1 过温bit0 堵转。 |
| `mode` | `int` | 当前工作状态：1 夹爪张开到最大且空闲，2 夹爪闭合到最小且空闲，3 夹爪停止且空闲，4 夹爪正在闭合，5 夹爪正在张开，6 夹爪闭合过程中遇到力控停止。 |
| `current_force` | `int` | 夹爪当前的压力，单位g。 |
| `temperature` | `int` | 当前温度，单位℃。 |
| `actpos` | `int` | 夹爪开口度。 |

## 成员函数

```python
rm_ctypes_wrap.rm_gripper_state_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。