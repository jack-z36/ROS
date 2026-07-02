---
title: "Python: 表示一个坐标系的结构体rm_pose_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/pose/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 表示一个坐标系的结构体rm\_pose\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `position` | [rm\_position\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/position/) | 位置，单位：m。 |
| `quaternion` | [rm\_quat\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/quat/) | 四元数。 |
| `euler` | [rm\_euler\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/euler/) | 欧拉角，单位：rad。 |

## 成员函数

```python
rm_ctypes_wrap.rm_pose_t.to_dict(self, recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。