---
title: "Python: 机械臂运动参数配置ArmTipVelocityParameters | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/tipVelocityParameters/"
author:
published: 2025-10-10
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 机械臂运动参数配置ArmTipVelocityParameters

可用于设置、获取机械臂运动参数。下面是机械臂运动参数 `ArmTipVelocityParameters` 的详细成员函数说明，包含了方法原型、参数说明、返回值说明和使用示例。

## 设置机械臂末端最大线速度rm\_set\_arm\_max\_line\_speed()

- **方法原型：**
```python
rm_set_arm_max_line_speed(self, speed: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `speed` | `float` | 末端最大线速度，单位m/s。 |

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

print(arm.rm_set_arm_max_line_speed(0.25))

arm.rm_delete_robot_arm()
```

## 设置机械臂末端最大线加速度rm\_set\_arm\_max\_line\_acc()

- **方法原型：**
```python
rm_set_arm_max_line_acc(self, acc: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `acc` | `float` | 末端最大线加速度，单位m/s^2。 |

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

print(arm.rm_set_arm_max_line_acc(1.6))

arm.rm_delete_robot_arm()
```

## 设置机械臂末端最大角速度rm\_set\_arm\_max\_angular\_speed()

- **方法原型：**
```python
rm_set_arm_max_angular_speed(self, speed: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `speed` | `float` | 末端最大角速度，单位rad/s。 |

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

print(arm.rm_set_arm_max_angular_speed(0.6))

arm.rm_delete_robot_arm()
```

## 设置机械臂末端最大角加速度rm\_set\_arm\_max\_angular\_acc()

- **方法原型：**
```python
rm_set_arm_max_angular_acc(self, acc: float) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `acc` | `float` | 末端最大角加速度，单位rad/s^2 |

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

print(arm.rm_set_arm_max_angular_acc(4))

arm.rm_delete_robot_arm()
```

## 设置机械臂末端参数为默认值rm\_set\_arm\_tcp\_init()

- **方法原型：**
```python
rm_set_arm_tcp_init(self) -> int:
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

# 初始化机械臂参数，机械臂的末端参数恢复到默认值。默认参数为：
# 末端线速度：0.1m/s末端线加速度：0.5m/s²
# 末端角速度：0.2rad/s末端角加速度：1rad/s²
print(arm.rm_set_arm_tcp_init())

arm.rm_delete_robot_arm()
```

## 设置碰撞防护等级rm\_set\_collision\_state()

- **方法原型：**
```python
rm_set_collision_state(self, stage: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `stage` | `int` | 等级：0~8，0-无碰撞，8-碰撞最灵敏。 |

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

# 设置机械臂碰撞防护等级为1
print(arm.rm_set_collision_state(1))

arm.rm_delete_robot_arm()
```

## 查询碰撞防护等级rm\_get\_collision\_stage()

- **方法原型：**
```python
rm_get_collision_stage(self) -> tuple[int, int]:
```
- **返回值:**  
	`tuple[int,int]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 碰撞等级

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| 0～8 | `int` | 等级：0~8，0-无碰撞，8-碰撞最灵敏。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_collision_stage())

arm.rm_delete_robot_arm()
```

## 获取机械臂末端最大线速度rm\_get\_arm\_max\_line\_speed()

- **方法原型：**
```python
rm_get_arm_max_line_speed(self) -> tuple[int, float]:
```
- **返回值:**  
	`tuple[int,int]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂末端最大线速度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `float` | 末端最大线速度，单位m/s。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_arm_max_line_speed())

arm.rm_delete_robot_arm()
```

## 获取机械臂末端最大线加速度rm\_get\_arm\_max\_line\_acc()

- **方法原型：**
```python
rm_get_arm_max_line_acc(self) -> tuple[int, float]:
```
- **返回值:**  
	`tuple[int,float]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 机械臂末端最大线加速度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `float` | 末端最大线加速度，单位m/s^2。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_arm_max_line_acc())

arm.rm_delete_robot_arm()
```

## 获取机械臂末端最大角速度rm\_get\_arm\_max\_angular\_speed()

- **方法原型：**
```python
rm_get_arm_max_angular_speed(self) -> tuple[int, float]:
```
- **返回值:**  
	`tuple[int,float]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

1. 机械臂末端最大角速度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `float` | 末端最大角速度，单位rad/s。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_arm_max_angular_speed())

arm.rm_delete_robot_arm()
```

## 获取机械臂末端最大角加速度rm\_get\_arm\_max\_angular\_acc()

- **方法原型：**
```python
rm_get_arm_max_angular_speed(self) -> tuple[int, float]:
```
- **返回值:**  
	`tuple[int,float]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

1. 机械臂末端最大角加速度

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `float` | 末端最大角加速度，单位rad/s^2。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_arm_max_angular_acc())

arm.rm_delete_robot_arm()
```

## 设置机械臂DH参数rm\_set\_DH\_data()

- **方法原型：**
```python
rm_set_DH_data(self, dh_data: rm_dh_t) -> int:
```

*可以跳转 [rm\_dh\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/dh/) 查阅结构体详细描述。*

- **参数说明：**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `dh_data` | `rm_dh_t` | 设置当前DH参数。 |

- **返回值：**  
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

# 设置机械臂当前DH参数（仅作示例，根据实际dh参数修改）
dh_data = rm_dh_t(a=[0, 0, 0, 0, 0, 0], d=[0, 0, 0, 0, 0, 0], alpha=[0, 0, 0, 0, 0, 0], offset=[0, 0, 0, 0, 0, 0])
print(arm.rm_set_DH_data(dh_data))

arm.rm_delete_robot_arm()
```

## 获取机械臂DH参数rm\_get\_DH\_data()

- **方法原型：**
```python
rm_get_DH_data(self) -> tuple[int, rm_dh_t]:
```

*可以跳转 [rm\_dh\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/dh/) 查阅结构体详细描述。*

- **返回值：**  
	`tuple[int,rm_dh_t]`: 包含两个元素的元组。
1. 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. DH参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `rm_dh_t` | 机械臂当前DH参数。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

[ret, dh] = arm.rm_get_DH_data()
print(dh.to_dict())

arm.rm_delete_robot_arm()
```

## 恢复机械臂默认DH参数rm\_set\_DH\_data\_default()

- **方法原型：**
```python
rm_set_DH_data_default(self) -> int:
```
- **返回值：**  
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

# 设置机械臂末端参数为默认值
print(arm.rm_set_DH_data_default())

arm.rm_delete_robot_arm()
```

## 设置避奇异模式rm\_set\_avoid\_singularity\_mode

注意

设置避奇异模式的接口仅支持六自由度机械臂。

- **方法原型** ：
```python
rm_set_avoid_singularity_mode(self, mode: int) -> int:
```
- **参数说明** ：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int` | 避奇异模式：0-不规避奇异点，1-规避奇异点。 |

- **返回值** ：

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_set_avoid_singularity_mode(0))

arm.rm_delete_robot_arm()
```

## 获取避奇异模式rm\_get\_avoid\_singularity\_mode

- **方法原型** ：
```python
rm_get_avoid_singularity_mode(self) -> tuple[int, int]:
```
- **返回值** ：

tuple：包含两个元素的元组。

1. int: 函数执行的状态码，0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |

2. int：当前避奇异模式。0-不规避奇异点，1-规避奇异点
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_avoid_singularity_mode())

arm.rm_delete_robot_arm()
```