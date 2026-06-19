---
title: "Python: 关节配置JointConfigSettings | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/jointsConfig/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 关节配置JointConfigSettings

可用于配置关节的速度、加速度、限位、使能、零位、清除错误等。下面是关节配置 `JointConfigSettings` 的详细成员函数说明，包含了方法原型、参数说明、返回值说明和使用示例。

## 设置指定关节的最大速度rm\_set\_joint\_max\_speed()

- **方法原型：**
```python
rm_set_joint_max_speed(self, joint_num: int, speed: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `speed` | `float` | 关节的最大转速，单位为度每秒(°/s)，定义了关节在运动时所能达到的最大速度。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_max_speed(1, 180))

arm.rm_delete_robot_arm()
```

## 设置关节最大加速度rm\_set\_joint\_max\_acc()

- **方法原型：**
```python
rm_set_joint_max_acc(self, joint_num: int, acc: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `acc` | `float` | 关节最大加速度，单位：°/s²，定义了关节在运动时所能达到的最大加速度。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_max_acc(1, 600))

arm.rm_delete_robot_arm()
```

## 设置关节最小位置限位rm\_set\_joint\_min\_pos()

- **方法原型：**
```python
rm_set_joint_min_pos(self, joint_num: int, min_pos: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `min_pos` | `float` | 关节最小位置，单位：°。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_min_pos(1, -178))

arm.rm_delete_robot_arm()
```

## 设置关节最大位置限位rm\_set\_joint\_max\_pos()

- **方法原型：**
```python
rm_set_joint_max_pos(self, joint_num: int, max_pos: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `max_pos` | `float` | 关节最大位置，单位：°。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_max_pos(1, 178))

arm.rm_delete_robot_arm()
```

## 设置指定关节最大速度rm\_set\_joint\_drive\_max\_speed()

- **方法原型：**
```python
rm_set_joint_drive_max_speed(self, joint_num: int, speed: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `speed` | `float` | 关节的最大转速，单位为度每秒(°/s)，定义了关节在运动时所能达到的最大速度。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_drive_max_speed(1, 180))

arm.rm_delete_robot_arm()
```

## 设置指定关节最大加速度rm\_set\_joint\_drive\_max\_acc()

- **方法原型：**
```python
rm_set_joint_drive_max_acc(self, joint_num: int, acc: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `acc` | `float` | 关节最大加速度，单位：°/s²。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_drive_max_acc(1, 600))

arm.rm_delete_robot_arm()
```

## 设置指定关节最小限位(驱动器)rm\_set\_joint\_drive\_min\_pos()

- **方法原型：**
```python
rm_set_joint_drive_min_pos(self, joint_num: int, min_pos: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `min_pos` | `float` | 关节最小位置，单位：°。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_drive_min_pos(1, -178))

arm.rm_delete_robot_arm()
```

## 设置指定关节最大限位(驱动器)rm\_set\_joint\_drive\_max\_pos()

- **方法原型：**
```python
rm_set_joint_drive_max_pos(self, joint_num: int, max_pos: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `max_pos` | `float` | 关节最大位置，单位：°。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_drive_max_pos(1, 178))

arm.rm_delete_robot_arm()
```

## 设置指定关节使能状态rm\_set\_joint\_en\_state()

- **方法原型：**
```python
rm_set_joint_en_state(self, joint_num: int, en_state: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |
| `en_state` | `int` | 1：上使能 0：掉使能。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_en_state(1, 1))

arm.rm_delete_robot_arm()
```

## 指定关节当前位置为零位rm\_set\_joint\_zero\_pos()

- **方法原型：**
```python
rm_set_joint_zero_pos(self, joint_num: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_zero_pos(1))

arm.rm_delete_robot_arm()
```

## 清除指定关节错误代码rm\_set\_joint\_clear\_err()

- **方法原型：**
```python
rm_set_joint_clear_err(self, joint_num: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `int` | 关节的序号，取值范围为1到7，表示机械臂上不同关节的编号。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_joint_clear_err(1))

arm.rm_delete_robot_arm()
```

## 一键设置关节限位rm\_auto\_set\_joint\_limit()

- **方法原型：**
```python
rm_auto_set_joint_limit(self, mode: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int` | 1-正式模式，各关节限位为规格参数中的软限位和硬件限位。 |

- **返回值:**  
	int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_auto_set_joint_limit(1))

arm.rm_delete_robot_arm()
```