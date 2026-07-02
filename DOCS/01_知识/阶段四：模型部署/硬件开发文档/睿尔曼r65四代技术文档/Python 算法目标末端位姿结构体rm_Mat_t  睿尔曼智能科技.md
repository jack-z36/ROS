---
title: "Python: 算法目标末端位姿结构体rm_Mat_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/algorithmTargetEndEffectorPose/"
author:
published: 2025-12-23
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 算法目标末端位姿结构体rm\_Mat\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `row` | `int` | 矩阵有效行数（≤18）。 |
| `col` | `int` | 矩阵有效列数（≤18）。 |
| `data` | `float data[18][18]` | 18x18浮点数组（存储矩阵数据，超出有效行列的部分默认0）。 |