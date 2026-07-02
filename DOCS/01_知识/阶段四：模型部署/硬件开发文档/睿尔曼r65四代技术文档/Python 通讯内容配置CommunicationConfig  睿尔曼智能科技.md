---
title: "Python: 通讯内容配置CommunicationConfig | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/communicationConfig/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 通讯内容配置CommunicationConfig

机械臂控制器可通过网口、RS232-USB 接口和 RS485 接口与用户通信，用户使用时无需切换，可使用上述任一接口， 控制器收到指令后，若指令格式正确，则会通过相同的接口反馈数据。下面是配置通讯内容 `CommunicationConfig` 的详细成员函数说明，包含了方法原型、参数说明、返回值说明和使用示例。

## 获取有线网卡信息rm\_get\_wired\_net()

未连接有线网卡则会返回无效数据。

- **方法原型：**
```python
rm_get_wired_net(self) -> dict[str, any]:
```
- **返回值:**  
	`dict[str,any]`: 包含以下键值的字典
1. 'return\_code' (int): 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 网络地址

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| ip | `str` | 网络地址 |
| mask | `str` | 子网掩码 |
| mac | `str` | MAC地址 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_wired_net())

arm.rm_delete_robot_arm()
```

## 恢复网络出厂设置rm\_set\_net\_default()

- **方法原型：**
```python
rm_set_net_default(self) -> int:
```
- **返回值:**  
	函数执行的状态码：

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_net_default())

arm.rm_delete_robot_arm()
```