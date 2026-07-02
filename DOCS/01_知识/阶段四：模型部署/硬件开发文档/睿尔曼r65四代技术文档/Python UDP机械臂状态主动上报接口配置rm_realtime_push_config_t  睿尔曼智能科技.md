---
title: "Python: UDP机械臂状态主动上报接口配置rm_realtime_push_config_t | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/struct/realtimePushConfig/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## UDP机械臂状态主动上报接口配置rm\_realtime\_push\_config\_t

## 属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `cycle` | `int` | 广播周期，5ms的倍数。 |
| `enable` | `bool` | 使能，是否主动上报。 |
| `port` | `int` | 广播的端口号。 |
| `force_coordinate` | `int` | 系统外受力数据的坐标系（力传感器版本支持）。 0：传感器坐标系；1：当前工作坐标系；2：当前工具坐标系。 |
| `ip` | `bytes` | 自定义的上报目标IP地址。 |
| `custom_config` | [`rm_udp_custom_config_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/udpCustomConfig/) | 自定义上报项。 |

## 构造函数

```python
rm_ctypes_wrap.rm_realtime_push_config_t.__init__(self,int  cycle = None,bool  enable = None,int  port = None,int  force_coordinate = None,str  ip = None, custom_config:rm_udp_custom_config_t = None)
```

UDP机械臂状态主动上报接口配置构造函数。

## 参数说明

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `cycle` | `int`, `optional` | 广播周期，5ms的倍数。Defaults to None。 |
| `enable` | `bool`, `optional` | 使能，是否主动上报。Defaults to None。 |
| `port` | `int`, `optional` | 广播的端口号。Defaults to None。 |
| `force_coordinate` | `int`, `optional` | 系统外受力数据的坐标系（力传感器版本支持）。 0：传感器坐标系；1：当前工作坐标系；2：当前工具坐标系。 |
| `ip` | `str`, `optional` | 自定义的上报目标IP地址。Defaults to None。 |
| `custom_config` | [`rm_udp_custom_config_t`](https://develop.realman-robotics.com/robot4th/apipython/struct/udpCustomConfig/), `optional` | 自定义上报项。Defaults to None。 |

## 成员函数

```python
rm_realtime_push_config_t.to_dict(self,recurse = True)
```

将类的变量返回为字典，如果recurse为True，则递归处理ctypes结构字段。