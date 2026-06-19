---
title: "Python: udp推送的灵巧手状态rm_udp_hand_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/udpHandState/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## udp推送的灵巧手状态rm\_udp\_hand\_state\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `hand_pos` | `List[int]` | 表示灵巧手位置 |
| `hand_angle` | `List[int]` | 表示灵巧手角度 |
| `hand_force` | `List[int]` | 表示灵巧手自由度力，单位mN |
| `hand_state` | `List[int]` | 表示灵巧手当前状态，由灵巧手厂商定义状态含义。 |
| `hand_err` | `int` | 表示灵巧手系统错误，由灵巧手厂商定义错误含义，例如因时错误码如下：1表示有错误，0表示无错误 |