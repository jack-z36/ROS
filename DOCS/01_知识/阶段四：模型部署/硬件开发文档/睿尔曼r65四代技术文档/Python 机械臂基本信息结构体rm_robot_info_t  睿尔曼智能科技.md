---
title: "Python: 机械臂基本信息结构体rm_robot_info_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/robotInfo/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂基本信息结构体rm\_robot\_info\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `arm_dof` | `int` | 机械臂的自由度数量。 |
| `arm_model` | `int` | 机械臂型号。 |
| `force_type` | `int` | 机械臂末端力控类型。 |
| `robot_controller_version` | `int` | 控制器版本参数，其中：4-四代控制器，3-三代控制器。 |

## 成员函数

```python
rm_ctypes_wrap.rm_robot_info_t.to_dictionary(self)
```

将int类型数据转化为字符串，并输出结果为字典。

**返回值：** dict: 包含机械臂自由度'arm\_dof'、型号'arm\_model'、末端力控版本'force\_type'值的字典。