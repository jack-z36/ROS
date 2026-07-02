---
title: "Python: 表示欧拉角的结构体rm_euler_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/euler/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 表示欧拉角的结构体rm\_euler\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `rx` | `float` | 绕X轴旋转的角度，单位：rad。 |
| `ry` | `float` | 绕Y轴旋转的角度，单位：rad。 |
| `rz` | `float` | 绕Z轴旋转的角度，单位：rad。 |

## 成员函数

```python
rm_ctypes_wrap.rm_euler_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。