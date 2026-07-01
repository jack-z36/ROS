---
title: "Python: 系统配置ControllerConfig | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/controllerConfig/"
author:
published: 2026-03-30
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 系统配置ControllerConfig

可用于系统配置（机械臂状态、电源）等。下面是系统配置 `ControllerConfig` 的详细成员函数说明，包含了方法原型、参数说明、返回值说明和使用示例。

## 获取控制器状态rm\_get\_controller\_state()

- **方法原型：**
```python
rm_get_controller_state(self) -> dict[str, any]:
```
- **返回值:**  
	`dict[str,any]`: 包含以下键值的字典。
1. int: 函数执行的状态码。

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 系统状态

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `voltage` | `float` | 返回的电压 |
| `current` | `float` | 返回的电流 |
| `temperature` | `float` | 返回的温度 |
| `sys_err` | `int` | 系统运行错误代码 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_controller_state())

arm.rm_delete_robot_arm()
```

## 设置机械臂电源rm\_set\_arm\_power()

- **方法原型：**
```python
rm_set_arm_power(self, power: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `power` | `int` | 1-上电状态，0 断电状态 |

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

# 机械臂上电
print(arm.rm_set_arm_power(1))

arm.rm_delete_robot_arm()
```

## 读取机械臂电源状态rm\_get\_arm\_power\_state()

- **方法原型：**
```python
rm_get_arm_power_state(self) -> tuple[int, int]:
```
- **返回值:**  
	`tuple[int, int]`: 包含两个元素的元组
1. int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂电源状态

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `int` | 获取到的机械臂电源状态，1-上电状态，0 断电状态 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_arm_power_state())

arm.rm_delete_robot_arm()
```

## 读取控制器的累计运行时间rm\_get\_system\_runtime()

- **方法原型：**
```python
rm_get_system_runtime(self) -> dict[str, any]:
```
- **返回值:**  
	`tuple[int, int]`: 包含两个元素的元组
1. int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 控制器运行时间

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `day` | `int` | 读取到的时间 |
| `hour` | `int` | 读取到的时间 |
| `min` | `int` | 读取到的时间 |
| `sec` | `int` | 读取到的时间 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_system_runtime())

arm.rm_delete_robot_arm()
```

## 清零控制器的累计运行时间rm\_clear\_system\_runtime()

- **方法原型：**
```python
rm_clear_system_runtime(self) -> int:
```
- **返回值:**  
	函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_clear_system_runtime())

arm.rm_delete_robot_arm()
```

## 读取关节的累计转动角度rm\_get\_joint\_odom()

- **方法原型：**
```python
rm_get_joint_odom(self) -> tuple[int, list[float]]:
```
- **返回值:**  
	`tuple[int, list[float]]`: 包含两个元素的元组。
1. int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节累计的转动角度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[float]` | 各关节累计的转动角度 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_odom())

arm.rm_delete_robot_arm()
```

## 清零关节累计转动的角度rm\_clear\_joint\_odom()

- **方法原型：**
```python
int rm_clear_joint_odom(self) -> int:
```
- **返回值:**  
	函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_clear_joint_odom())

arm.rm_delete_robot_arm()
```

## 读取机械臂软件信息rm\_get\_arm\_software\_info()

- **方法原型：**
```python
rm_get_arm_software_info(self) -> tuple[int, dict[str, any]]:
```
- **返回值:**  
	`tuple[int, dict[str,any]]`: 包含两个元素的元组
1. int: 函数执行的状态码
	0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。
2. 机械臂软件版本信息
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| `rm_arm_software_version_t` | `dict[str,any]` | 机械臂软件版本信息字典，键为rm\_arm\_software\_version\_t结构体的字段名称 |
	*可以跳转 [rm\_arm\_software\_version\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/armSoftwareVersion/) 查阅结构体详细描述。*
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_arm_software_info())

arm.rm_delete_robot_arm()
```

## 配置有线网口IP地址rm\_set\_netip()

- **方法原型：**
```python
rm_set_NetIP(self, ip: str, netmask: str, gw: str) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `ip` | `str` | 有线网口 IP 地址。 |
| `netmask` | `str` | 有线网口子网掩码。 |
| `gw` | `str` | 有线网口网关地址。 |

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

# 配置机械臂IP地址为"192.168.1.19"
print(arm.rm_set_netip("192.168.1.19", "255.255.255.0", "192.168.1.1"))

arm.rm_delete_robot_arm()
```

## 清除系统错误rm\_clear\_system\_err()

- **方法原型：**
```python
rm_clear_system_err(self) -> int:
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

print(arm.rm_clear_system_err())

arm.rm_delete_robot_arm()
```

## 设置Web服务器使能状态rm\_set\_webserver\_enabled

- **方法原型：**
```python
rm_set_webserver_enabled(self, enable: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `enable` | `int` | Web服务器使能状态（默认状态为使能）：非0代表使能，0代表禁使能。 |

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

print(arm.rm_set_webserver_enabled(0))

arm.rm_delete_robot_arm()
```

## 获取Web服务器使能状态rm\_get\_webserver\_enabled

- **方法原型：**
```python
rm_get_webserver_enabled(self) -> tuple[int, int]:
```
- **返回值:**
	tuple\[int,int\]: 包含两个元素的元组。
	- int: 函数执行的状态码。0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。
		- int: 返回Web服务器使能状态(默认状态是使能)，非0代表使能，0代表禁使能。
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
print(arm.rm_get_webserver_enabled())

arm.rm_delete_robot_arm()
```