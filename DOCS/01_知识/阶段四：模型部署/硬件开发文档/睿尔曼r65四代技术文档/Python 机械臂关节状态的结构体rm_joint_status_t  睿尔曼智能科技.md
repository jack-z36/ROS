---
title: "Python: 机械臂关节状态的结构体rm_joint_status_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/jointStatus/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂关节状态的结构体rm\_joint\_status\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `joint_current` | `List[float]` | 关节电流，单位mA，精度：0.001mA。 |
| `joint_en_flag` | `List[bool]` | 当前关节使能状态 ，1为上使能，0为掉使能。 |
| `joint_err_code` | `List[uint16_t]` | 当前关节错误码。 |
| `joint_position` | `List[float]` | 关节角度，单位°，精度：0.001°。 |
| `joint_temperature` | `List[float]` | 当前关节温度，精度0.001℃。 |
| `joint_voltage` | `List[float]` | 当前关节电压，精度0.001V。 |
| `joint_speed` | `List[float]` | 当前关节速度，精度0.01RPM。 |