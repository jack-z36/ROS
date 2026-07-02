---
title: "Python: 机械臂全局路点结构体rm_waypoint_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/waypoint/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂全局路点结构体rm\_waypoint\_t

## 构造函数

```python
rm_ctypes_wrap.rm_waypoint_t.__init__(self, point_name: str = None, joint: list[float] = None, pose: list[float] = None, work_frame: str = None, tool_frame: str = None, time: str = ''):
```

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `point_name` | `str, optional` | 路点名称，默认为None。 |
| `joint` | `list[float], optional` | 关节角度列表，长度为7，单位：°，默认为None。 |
| `pose` | `list[float], optional` | 位姿信息，包含位置和欧拉角，默认为None。该列表应为 \[x, y, z, rx, ry, rz\] 格式，其中 \[x, y, z\] 是位置，\[rx, ry, rz\] 是欧拉角。 |
| `work_frame` | `str, optional` | 工作坐标系名称，默认为None。 |
| `tool_frame` | `str, optional` | 工具坐标系名称，默认为None。 |
| `time` | `str, optional` | 路点新增或修改时间，默认为空字符串。 |

## 成员函数

```python
rm_ctypes_wrap.rm_waypoint_t.to_dict (self)
```

将类的变量返回为字典