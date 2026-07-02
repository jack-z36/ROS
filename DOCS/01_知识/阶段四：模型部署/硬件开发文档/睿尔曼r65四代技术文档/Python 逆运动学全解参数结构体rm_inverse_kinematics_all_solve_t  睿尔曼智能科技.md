---
title: "Python: 逆运动学全解参数结构体rm_inverse_kinematics_all_solve_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/inverseKinematicsAllSolve/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 逆运动学全解参数结构体rm\_inverse\_kinematics\_all\_solve\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `result` | `int` | 逆解求解结果，0：成功，1：逆解失败，-1：上一时刻关节角度输入为空或超关节限位，-2：目标位姿四元数不合法。 |
| `num` | `int` | 目标位姿，根据flag的值，可以是位置+四元数或位置+欧拉角，默认为None。 |
| `q_ref` | `List[float]` | 参考关节角度，通常是当前关节角度, 单位 °。 |
| `q_solve` | `List[List[float]]` | 关节角全解, 8x8 数组, 单位 °。 |