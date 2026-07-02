---
title: "Python: 读写外设数据参数结构体rm_peripheral_read_write_params_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/peripheralReadWriteParams/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 读写外设数据参数结构体rm\_peripheral\_read\_write\_params\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `port` | `int` | 通讯端口0-控制器RS485端口，1-末端接口板RS485接口，3-控制器ModbusTCP设备。 |
| `address` | `int` | 数据起始地址。 |
| `device` | `int` | 外设设备地址。 |
| `num` | `int` | 数据数量。 |

## 构造函数

```python
rm_ctypes_wrap.rm_peripheral_read_write_params_t.__init__(self, port = None, address = None, device = None, num = None)
```

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `port` | `int, optional` | 通讯端口，0-控制器RS485端口，1-末端接口板RS485接口，3-控制器ModbusTCP设备，默认为 None。 |
| `address` | `int, optional` | 数据起始地址，默认为 None。 |
| `device` | `int, optional` | 外设设备地址，默认为 None。 |
| `num` | `int, optional` | 数据数量，默认为 None。 |