---
title: "Python: 力位混合控制参数结构体rm_force_position_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/forcePosition/"
author:
published: 2025-05-28
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 力位混合控制参数结构体rm\_force\_position\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int` | 0-工作坐标系力控，1-工具坐标系力控； |
| `control_mode` | `int` | 6个方向（Fx Fy Fz Mx My Mz）的模式 0-固定模式 1-浮动模式 2-弹簧模式 3-运动模式 4-力跟踪模式 8-力跟踪+姿态自适应模式（模式8只对工具坐标系的Fz方向有效）； |
| `desired_force` | `int` | 力控轴维持的期望力/力矩，力控轴的力控模式为力跟踪模式时，期望力/力矩设置才会生效 ，单位N/Nm。 |
| `limit_vel` | `int` | 力控轴的最大线速度和最大角速度限制，只对开启力控方向生效。（x、y、z）轴的最大线速度，单位为m/s，（rx、ry、rz）轴的最大角速度单位为°/s |