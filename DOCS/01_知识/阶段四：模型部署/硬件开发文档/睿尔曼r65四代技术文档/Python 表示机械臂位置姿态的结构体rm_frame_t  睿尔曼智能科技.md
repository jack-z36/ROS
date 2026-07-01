---
title: "Python: 表示机械臂位置姿态的结构体rm_frame_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/frame/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 表示机械臂位置姿态的结构体rm\_frame\_t

## 构造函数

```python
rm_frame_t.__init__(self,str  frame_name = None,tuple[float, float, float, float, float, float]  pose = None,float  payload = None,float  x = None,float  y = None,float  z = None)
```

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `frame_name` | `bytes` | 坐标系名称，不超过10个字符（包括结尾的null字节）。 |
| `pose` | [`rm_pose_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) | 坐标系位姿，包含位置和姿态信息。 |
| `payload` | `float` | 坐标系末端负载重量，单位：kg。 |
| `x` | `float` | 坐标系末端负载质心位置x轴坐标。 |
| `y` | `float` | 坐标系末端负载质心位置y轴坐标。 |
| `z` | `float` | 坐标系末端负载质心位置z轴坐标。 |

## 返回值

| 参数 | 类型 |
| --- | --- |
| `ValueError` | 如果frame\_name的长度超过10个字符。 |
| `ValueError` | 如果 pose 不是包含6个浮点数的元组，表示(x, y, z, rx, ry, rz)。 |

## 成员函数

```python
dict[str, any] Robotic_Arm.rm_ctypes_wrap.rm_frame_t.to_dictionary(self)
```

将rm\_frame\_t对象转换为字典表现形式。