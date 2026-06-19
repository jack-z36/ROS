---
title: "Python: 动力学版本信息的结构体rm_dynamic_version_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/dynamicVersion/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 动力学版本信息的结构体rm\_dynamic\_version\_t

## 属性

| 属性名 | 类型 | 说明 |
| --- | --- | --- |
| `model_version` | `bytes` | 动力学模型版本号。 |

## 成员函数

```python
rm_ctypes_wrap.rm_dynamic_version_t.to_dict(self, recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。