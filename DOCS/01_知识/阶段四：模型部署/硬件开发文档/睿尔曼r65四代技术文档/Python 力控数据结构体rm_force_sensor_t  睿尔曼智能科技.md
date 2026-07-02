---
title: "Python: 力控数据结构体rm_force_sensor_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/forceSensor/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 力控数据结构体rm\_force\_sensor\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `force` | `List[float]` | 当前力传感器原始数据，力的单位为N；力矩单位为Nm。 |
| `zero_force` | `List[float]` | 当前力传感器系统外受力数据，力的单位为N；力矩单位为Nm。 |
| `coordinate` | `int` | 系统外受力数据的坐标系，0为传感器坐标系，1为当前工作坐标系，2为当前工具坐标系 |