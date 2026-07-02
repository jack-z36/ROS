---
title: "Python: 动作信息结构体rm_tool_action_info_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/actioninfo/"
author:
published: 2025-10-09
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 动作信息结构体rm\_tool\_action\_info\_t

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `int` | 动作名称。 |
| `hand_pos` | `int` | 动作位置。 |
| `hand_angle` | `int` | 动作角度。 |

## 成员函数

```
rm_ctypes_wrap.rm_tool_action_info_t .to_dict(self, recurse=True):
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。