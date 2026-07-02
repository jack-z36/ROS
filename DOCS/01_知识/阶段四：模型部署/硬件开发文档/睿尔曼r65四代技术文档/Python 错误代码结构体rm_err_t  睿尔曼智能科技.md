---
title: "Python: 错误代码结构体rm_err_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/err/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 错误代码结构体rm\_err\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `err_len` | `uint8_t` | 错误代码个数。 |
| `err` | `int` | 错误代码数组,不超过 10 个字节，支持字母、数字、下划线。 |

## 成员函数

```python
rm_ctypes_wrap.rm_err_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。