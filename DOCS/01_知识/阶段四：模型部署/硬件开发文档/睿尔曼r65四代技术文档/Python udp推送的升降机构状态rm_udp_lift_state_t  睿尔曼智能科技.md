---
title: "Python: udp推送的升降机构状态rm_udp_lift_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/udpLiftState/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## udp推送的升降机构状态rm\_udp\_lift\_state\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `height` | `int` | 当前升降机构高度，单位：mm，精度：1mm |
| `pos` | `float` | 当前角度 精度 0.001°，单位：° |
| `current` | `int` | 当前驱动电流，单位：mA，精度：1mA |
| `err_flag` | `int` | 驱动错误代码，错误代码类型参考关节错误代码 |
| `en_flag` | `int` | 当前关节使能状态 ，1 为上使能，0 为掉使能 |