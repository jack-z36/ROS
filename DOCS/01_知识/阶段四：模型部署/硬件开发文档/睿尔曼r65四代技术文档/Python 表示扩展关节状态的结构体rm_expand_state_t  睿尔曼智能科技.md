---
title: "Python: 表示扩展关节状态的结构体rm_expand_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/expandState/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 表示扩展关节状态的结构体rm\_expand\_state\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `pos` | `int` | 扩展关节角度，单位度，精度 0.001°(若为升降机构高度，则s单位：mm，精度：1mm，范围：0 ~2300)。 |
| `current` | `int` | 驱动电流，单位：mA，精度：1mA。 |
| `err_flag` | `int` | 驱动错误代码，错误代码类型参考关节错误代码。 |
| `mode` | `int` | 当前工作状态：   0：空闲；   1：正方向速度运动；   2：正方向位置运动；   3：负方向速度运动；   4：负方向位置运动。 |

## 成员函数

```python
rm_ctypes_wrap.rm_expand_state_t.to_dict (self, recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段