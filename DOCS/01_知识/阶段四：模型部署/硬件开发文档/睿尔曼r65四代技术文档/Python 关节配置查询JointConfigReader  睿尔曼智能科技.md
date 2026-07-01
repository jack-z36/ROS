---
title: "Python: 关节配置查询JointConfigReader | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/jointsConfigQuery/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 关节配置查询JointConfigReader

可用于查询关节、驱动器的最大速度、加速度或者限位等。下面是关节配置查询 `JointConfigReader` 的详细成员函数说明，包含了方法原型、参数说明、返回值说明和使用示例。

## 查询关节最大速度rm\_get\_joint\_max\_speed()

- **方法原型：**
```python
rm_get_joint_max_speed(self) -> tuple[int, list]:
```
- **返回值:**

`tuple[int, list]`: 包含两个元素的元组。

1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最大速度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 关节最大速度值。单位：°/s。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
print(arm.rm_get_joint_max_speed())
arm.rm_delete_robot_arm()
```

## 查询关节最大加速度rm\_get\_joint\_max\_acc()

- **方法原型：**
```python
rm_get_joint_max_acc(self) -> tuple[int, list]:
```
- **返回值:**`tuple[int, list]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最大加速度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 关节最大加速度值。单位：°/s。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
print(arm.rm_get_joint_max_acc())
arm.rm_delete_robot_arm()
```

## 查询关节最小限位rm\_get\_joint\_min\_pos()

- **方法原型：**
```python
rm_get_joint_min_pos(self) -> tuple[int, list]:
```
- **返回值:** tuple\[int, list\]: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最小限位

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 关节最小位置数组，长度与机械臂的关节数，单位：°度。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
print(arm.rm_get_joint_min_pos())
arm.rm_delete_robot_arm()
```

## 查询关节最大限位rm\_get\_joint\_max\_pos()

- **方法原型：**
```python
rm_get_joint_max_pos(self) -> tuple[int, list]:
```
- **返回值:**  
	`tuple[int, list]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最大限位

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 关节最大位置数组，长度与机械臂的关节数，单位：°度。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
print(arm.rm_get_joint_max_pos())
arm.rm_delete_robot_arm()
```

## 查询关节最大速度(驱动器)rm\_get\_joint\_drive\_max\_speed()

- **方法原型：**
```python
rm_get_joint_drive_max_speed(self) -> tuple[int, list]:
```
- **返回值:**  
	`tuple[int, list]`: 包含两个元素的元组
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最大速度（驱动器）

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 关节最大速度值 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_drive_max_speed())

arm.rm_delete_robot_arm()
```

## 查询关节最大加速度(驱动器)rm\_get\_joint\_drive\_max\_acc()

- **方法原型：**
```python
rm_get_joint_drive_max_acc(self) -> tuple[int, list]:
```
- **返回值:**  
	`tuple[int, list]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最大加速度（驱动器）

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 各关节最大加速度值 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_drive_max_acc())

arm.rm_delete_robot_arm()
```

## 查询关节最小限位(驱动器)rm\_get\_joint\_drive\_min\_pos()

- **方法原型：**
```python
rm_get_joint_drive_min_pos(self) -> tuple[int, list]:
```
- **返回值:**  
	`tuple[int, list]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最小限位（驱动器）

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 关节最小位置数组，长度与机械臂的关节数，单位：°度 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_drive_min_pos())

arm.rm_delete_robot_arm()
```

## 查询关节最大限位(驱动器)rm\_get\_joint\_drive\_max\_pos()

- **方法原型：**
```python
rm_get_joint_drive_max_pos(self) -> tuple[int, list]:
```
- **返回值:**  
	`tuple[int, list]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节最大限位（驱动器）

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 关节最大位置数组，长度与机械臂的关节数，单位：°度 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_drive_max_pos())

arm.rm_delete_robot_arm()
```

## 获取关节使能状态rm\_get\_joint\_en\_state()

- **方法原型：**
```python
rm_get_joint_en_state(self) -> tuple[int, list]:
```
- **返回值:**  
	`tuple[int, list]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节的使能状态（驱动器）

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| list | `float` | 每个关节的使能状态数组，长度为机械臂的关节数，单位：°度 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_en_state())

arm.rm_delete_robot_arm()
```

## 获取关节错误代码rm\_get\_joint\_err\_flag()

- **方法原型：**
```python
rm_get_joint_err_flag(self) -> dict[str, any]:
```
- **返回值:**  
	`tuple[int, list]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 关节错误代码

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `err_flag` | `list[float]` | 浮点数列表，表示每个关节的错误标志。   如果arm\_dof不为0，则列表长度为arm\_dof；否则，使用默认的ARM\_DOF长度。 |
| `brake_state` | `list[float]` | 浮点数列表，表示每个关节的抱闸状态。   如果arm\_dof不为0，则列表长度为arm\_dof；否则，使用默认的ARM\_DOF长度。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_joint_err_flag())

arm.rm_delete_robot_arm()
```