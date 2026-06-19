---
title: "C、C++: 通讯内容配置communicationConfig | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/communicationConfig/"
author:
published: 2025-05-19
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 通讯内容配置communicationConfig

机械臂控制器可通过网口、RS232-USB 接口和 RS485 接口与用户通信，本接口为配置响应的通信模式。

## 获取有线网卡信息rm\_get\_wired\_net()

获取有线网卡信息，未连接有线网卡则会返回无效数据。

- **方法原型：**
```c
int rm_get_wired_net(rm_robot_handle * handle,char * ip,char * mask,char * mac)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `ip` | 输入参数 | 网络地址。 |
| `mask` | 输入参数 | 子网掩码。 |
| `mac` | 输入参数 | MAC地址。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//查询有线网卡网络信息
char ip[128];
char mask[128];
char mac[128];
ret = rm_get_wired_net(robot_handle,ip,mask,mac);
```

## 恢复网络出厂设置rm\_set\_net\_default()

- **方法原型：**
```c
int rm_set_net_default(rm_robot_handle * handle)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
//恢复网络出厂设置
ret = rm_set_net_default(robot_handle);
```