---
title: "Python: 末端生态协议配置RmPlusConfig | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/rmplus/"
author:
published: 2025-10-10
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 末端生态协议配置RmPlusConfig

## 读取末端设备基础信息(末端生态协议支持)rm\_get\_rm\_plus\_base\_info()

- **方法原型：**
```python
rm_get_rm_plus_base_info(self) -> tuple[int,dict[str, any]]:
```
- **返回值:**

`tuple[int,dict[str, any]]`: 包含两个元素的元组。

1. 函数执行的状态码：0成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。
2. 末端设备基础信息：
	- `dict[str, any]` 末端设备基础信息字典，键为rm\_plus\_base\_info\_t结构体的字段名称。
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E) 

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)  

# 读取末端设备基础信息
tag, base_info = arm.rm_get_rm_plus_base_info()
print(tag, base_info)
# 断开所有连接，销毁线程
RoboticArm.rm_destroy()
```

## 读取末端设备实时信息(末端生态协议支持)rm\_get\_rm\_plus\_state\_info()

- **方法原型：**
```python
rm_get_rm_plus_state_info(self) -> tuple[int, dict[str, any]]:
```
- **返回值:**

`tuple[int, dict[str, any]]`: 包含两个元素的元组。

1. 函数执行的状态码：0成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。
2. 末端设备实时信息：
	- `dict[str, any]` 末端设备实时信息字典，键为rm\_plus\_state\_info\_t结构体的字段名称。
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

# 读取末端设备实时信息
tag, state_info = arm.rm_get_rm_plus_state_info()
print(tag, state_info)
# 断开所有连接，销毁线程
RoboticArm.rm_destroy()
```