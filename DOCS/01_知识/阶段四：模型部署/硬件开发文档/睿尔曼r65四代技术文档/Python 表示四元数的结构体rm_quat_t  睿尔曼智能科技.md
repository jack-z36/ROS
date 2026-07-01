---
title: "Python: 表示四元数的结构体rm_quat_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/quat/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 表示四元数的结构体rm\_quat\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `w` | `float` | 四元数的实部（scalar part），通常用于表示旋转的角度和方向。 |
| `x` | `float` | 四元数的虚部中的第一个分量（vector part）。 |
| `y` | `float` | 四元数的虚部中的第二个分量。 |
| `z` | `float` | 四元数的虚部中的第三个分量。 |

## 成员函数

```python
rm_ctypes_wrap.rm_quat_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。