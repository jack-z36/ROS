---
title: "Python: 机械臂当前状态的结构体rm_current_arm_state_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/currentArmState/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂当前状态的结构体rm\_current\_arm\_state\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `pose` | [`rm_pose_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/pose/) | 机械臂的当前位姿信息。 |
| `joint` | `List[float]` | 机械臂当前关节角度，单位：°。 |
| `err` | [`rm_err_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/err/) | 错误代码。 |

注意

- 这些字段通常由外部系统或硬件提供，并通过适当的接口填充。
- 在处理错误代码时，请参考相关的错误代码文档或枚举。

## 成员函数

```python
rm_ctypes_wrap.rm_current_arm_state_t.to_dictionary(self,arm_dof)
```