---
title: "C、C++: 末端生态协议配置RmPlusConfig | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apic/classes/rmplus/"
author:
published: 2025-10-10
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 末端生态协议配置RmPlusConfig

末端生态协议支持下的末端设备基础信息与实时信息的读取。

## 读取末端设备基础信息（末端生态协议支持）rm\_get\_rm\_plus\_base\_info()

- **方法原型：**
```c
int rm_get_rm_plus_base_info(rm_robot_handle *handle, rm_plus_base_info_t *info)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_plus\_base\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/plusBase/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `info` | 输出参数 | 末端设备基础信息。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
rm_robot_handle *handle = NULL;
handle = rm_create_robot_arm("192.168.1.18",8080);
rm_plus_base_info_t baseinfo;
int ret = rm_get_rm_plus_base_info(handle, &baseinfo);
```

## 读取末端设备实时信息（末端生态协议支持）rm\_get\_rm\_plus\_state\_info()

- **方法原型：**
```c
int rm_get_rm_plus_state_info(rm_robot_handle *handle, rm_plus_state_info_t *info)
```

*可以跳转 [rm\_robot\_handle](https://develop.realman-robotics.com/robot4th/apic/struct/robotHandle/) 和 [rm\_plus\_state\_info\_t](https://develop.realman-robotics.com/robot4th/apic/struct/plusState/) 查阅结构体详细描述。*

- **参数说明:**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `handle` | 输入参数 | 机械臂句柄。 |
| `info` | 输出参数 | 末端设备实时信息。 |

- **返回值:**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```c
rm_robot_handle *handle = NULL;
handle = rm_create_robot_arm("192.168.1.18",8080);
rm_plus_state_info_t stateinfo;
int ret = rm_get_rm_plus_state_info(handle, &stateinfo);
```