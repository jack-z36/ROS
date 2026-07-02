---
title: "Python: 机械臂状态查询ArmState | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/armState/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂状态查询ArmState

可用于机械臂状态获取。下面是机械臂状态获取 `ArmState` 的详细成员函数说明，包含了方法原型、参数说明、返回值说明和使用示例。

## 获取机械臂当前状态rm\_get\_current\_arm\_state()

- **方法原型：**
```python
rm_get_current_arm_state(self) -> tuple[int, dict[str, any]]:
```
- **返回值:**  
	`tuple[int, dict[str,any]]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂当前状态

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `rm_current_arm_state_t` | `dict` | 机械臂当前状态字典，键为rm\_current\_arm\_state\_t的参数名。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_current_arm_state())

arm.rm_delete_robot_arm()
```

## 获取关节当前温度rm\_get\_current\_joint\_temperature()

- **方法原型：**
```python
rm_get_current_joint_temperature(self) -> tuple[int, list[float]]:
```
- **返回值:**  
	`tuple[int, list[float]]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂关节温度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[float]` | 关节1~7温度数组，单位：℃ |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_current_joint_temperature())

arm.rm_delete_robot_arm()
```

## 获取关节当前电流rm\_get\_current\_joint\_current()

- **方法原型：**
```python
rm_get_current_joint_current(self) -> tuple[int, list[float]]:
```
- **返回值:**  
	`tuple[int, list[float]]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂关节电流

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[float]` | 关节1~7电流数组，单位：mA |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_current_joint_current())

arm.rm_delete_robot_arm()
```

## 获取关节当前电压rm\_get\_current\_joint\_voltage()

- **方法原型：**
```python
rm_get_current_joint_voltage(self) -> tuple[int, list[float]]:
```
- **返回值:**  
	`tuple[int, list[float]]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂关节电压

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[float]` | 关节1~7电压数组，单位：V |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_current_joint_voltage())

arm.rm_delete_robot_arm()
```

## 设置机械臂的初始位置角度rm\_set\_init\_pose()

- **方法原型：**
```python
int rm_set_init_pose(self, joint: list[float]) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| joint | `list[float]` | 机械臂初始位置关节角度数组 |

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

print(arm.rm_set_init_pose())

arm.rm_delete_robot_arm()
```

## 获取机械臂初始位置角度rm\_get\_init\_pose()

- **方法原型：**
```python
rm_get_init_pose(self) -> tuple[int, list[float]]:
```
- **返回值:**  
	`tuple[int, list[float]]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂初始位置关节角度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[float]` | 机械臂初始位置关节角度数组，单位：°度 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_init_pose())

arm.rm_delete_robot_arm()
```

## 获取当前关节角度rm\_get\_joint\_degree()

- **方法原型：**
```python
rm_get_joint_degree(self) -> tuple[int, list[float]]:
```
- **返回值:**  
	`tuple[int, list[float]]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂初始位置关节角度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[float]` | 机械臂初始位置关节角度数组，单位：°度 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_degree())

arm.rm_delete_robot_arm()
```

## 获取机械臂所有状态信息rm\_get\_arm\_all\_state()

- **方法原型：**
```python
rm_get_arm_all_state(self) -> tuple[int, dict[str, any]]:
```
- **返回值:**  
	`tuple[int, dict[str, any]]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂所有状态信息

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `rm_arm_all_state_t` | `dict` | 机械臂所有状态信息字典，键为rm\_arm\_all\_state\_t的参数名。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_arm_all_state())

arm.rm_delete_robot_arm()
```

## 查询控制器RS485模式rm\_get\_controller\_rs485\_mode()

- **方法原型：**
```python
rm_get_controller_rs485_mode(self) -> dict[str, any]:
```
- **返回值:**  
	`dict[str, any]`: 包含以下键值的字典
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂状态模式

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| mode | `int` | 0-代表默认 RS485 串行通讯，1-代表 modbus-RTU 主站模式，2-代表 modbus-RTU 从站模式。 |

3. 波特率

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| baudrate | `int` | 波特率 |

4. Timeout

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| timeout | `int` | modbus 协议超时时间，单位 100ms，仅在 modbus-RTU 模式下提供此字段 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_controller_rs485_mode())

arm.rm_delete_robot_arm()
```

## 查询工具端 RS485 模式rm\_get\_tool\_rs485\_mode()

- **方法原型：**
```python
rm_get_tool_rs485_mode(self) -> dict[str, any]:
```
- **返回值:**  
	`dict[str, any]`: 包含以下键值的字典
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂状态模式

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int` | 0-代表默认 RS485 串行通讯，1-代表 modbus-RTU 主站模式。 |

3. 波特率

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `baudrate` | `int` | 波特率 |

4. Timeout

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `timeout` | `int` | modbus 协议超时时间，单位 100ms，仅在 modbus-RTU 模式下提供此字段 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_tool_rs485_mode())

arm.rm_delete_robot_arm()
```