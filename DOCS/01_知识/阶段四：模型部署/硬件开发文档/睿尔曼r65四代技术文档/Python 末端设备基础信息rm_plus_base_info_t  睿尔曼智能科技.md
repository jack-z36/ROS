---
title: "Python: 末端设备基础信息rm_plus_base_info_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/rmPlusBaseInfo/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 末端设备基础信息rm\_plus\_base\_info\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `manu` | c\_char \* 10 | 设备厂家 |
| `type` | c\_int | 设备类型 |
| `hv` | c\_char \* int(10) | 硬件版本 |
| `sv` | c\_char \* int(10) | 软件版本 |
| `bv` | c\_char \* int(10) | boot版本 |
| `id` | c\_int | 设备ID |
| `dof` | c\_int | 自由度 |
| `check` | c\_int | 自检开关 |
| `bee` | c\_int | 蜂鸣器开关 |
| `force` | c\_bool | 力控支持 |
| `touch` | c\_bool | 触觉支持 |
| `touch_num` | c\_int | 触觉个数 |
| `touch_sw` | c\_int | 触觉开关 |
| `hand` | c\_int | 手方向 |
| `pos_up` | c\_int \* 12 | 位置上限 |
| `pos_low` | c\_int \* 12 | 位置下限 |
| `angle_up` | c\_int \* 12 | 角度上限 |
| `angle_low` | c\_int \* 12 | 角度下限 |
| `speed_up` | c\_int \* 12 | 速度上限 |
| `speed_low` | c\_int \* 12 | 速度下限 |
| `force_up` | c\_int \* 12 | 力上限 |
| `force_low` | c\_int \* 12 | 力下限 |

## 成员函数

```python
rm_plus_base_info_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。