---
title: "Python: 复合拖动示教参数结构体rm_multi_drag_teach_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/multiDragTeach/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 复合拖动示教参数结构体rm\_multi\_drag\_teach\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `free_axes` | `List[int]` | 自由驱动方向\[x,y,z,rx,ry,rz\]，0-在参考坐标系对应方向轴上不可拖动，1-在参考坐标系对应方向轴上可拖动 |
| `frame` | `int` | 参考坐标系，0-工作坐标系 1-工具坐标系。 |
| `singular_wall` | `int` | 仅在六维力模式拖动示教中生效，用于指定是否开启拖动奇异墙，0表示关闭拖动奇异墙，1表示开启拖动奇异墙，若无配置参数，默认启动拖动奇异墙 |