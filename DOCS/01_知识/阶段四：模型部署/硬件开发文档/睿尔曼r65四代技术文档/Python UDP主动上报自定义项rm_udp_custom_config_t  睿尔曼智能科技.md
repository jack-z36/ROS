---
title: "Python: UDP主动上报自定义项rm_udp_custom_config_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/udpCustomConfig/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## UDP主动上报自定义项rm\_udp\_custom\_config\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `joint_speed` | `int` | 关节速度。1：上报；0：关闭上报；-1：不设置，保持之前的状态 |
| `lift_state` | `int` | 升降关节信息。1：上报；0：关闭上报；-1：不设置，保持之前的状态 |
| `expand_state` | `int` | 扩展关节信息（升降关节和扩展关节为二选一，优先显示升降关节）1：上报；0：关闭上报；-1：不设置，保持之前的状态 |
| `arm_current_status` | `int` | 机械臂当前状态。1：上报；0：关闭上报；-1：不设置，保持之前的状态 |
| `hand_state` | `int` | 灵巧手状态。1：上报；0：关闭上报；-1：不设置，保持之前的状态 |
| `aloha_state` | `int` | aloha主臂状态。1：上报；0：关闭上报；-1：不设置，保持之前的状态 |
| `plus_base` | `int` | 末端设备基础信息。1：上报；0：关闭上报；-1：不设置，保持之前的状态 |
| `plus_state` | `int` | 末端设备实时信息。1：上报；0：关闭上报；-1：不设置，保持之前的状态 |

## 成员函数

```python
rm_ctypes_wrap.rm_udp_custom_config_t.to_dict(self, recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。