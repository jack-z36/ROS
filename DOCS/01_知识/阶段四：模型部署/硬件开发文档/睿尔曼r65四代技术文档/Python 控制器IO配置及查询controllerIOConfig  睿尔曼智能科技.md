---
title: "Python: 控制器IO配置及查询controllerIOConfig | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/controllerIOConfig/"
author:
published: 2025-06-30
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 控制器IO配置及查询controllerIOConfig

可用于IO控制。下面是控制器端IO控制 `controllerIOConfig` 的详细成员函数说明，包含了方法原型、参数说明、返回值说明和使用示例。

**控制器端IO** 机械臂控制器提供IO端口，用于与外部设备交互。数量和分类如下所示：

| 类型 | 数量 | 说明 |
| --- | --- | --- |
| 数字IO | 4路 | 可配置为0-24V；DO/DI复用； |

---

## 配置IO模式rm\_set\_io\_mode()

- **方法原型：**
```python
rm_set_io_mode(self, io_num: int, io_mode: int, io_speed: int=0, io_speed_mode: int=0) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `io_num` | `int` | IO 端口号，范围：1~4。 |
| `io_mode` | `int` | 模式   0-通用输入模式；   1-通用输出模式；   2-输入开始功能复用模式；   3-输入暂停功能复用模式；   4-输入继续功能复用模式；   5-输入急停功能复用模式；   6-输入进入电流环拖动复用模式；   7-输入进入力只动位置拖动模式（六维力版本可配置）；   8-输入进入力只动姿态拖动模式（六维力版本可配置）；   9-输入进入力位姿结合拖动复用模式（六维力版本可配置）；   10-输入外部轴最大软限位复用模式（外部轴模式可配置）；   11-输入外部轴最小软限位复用模式（外部轴模式可配置）；   12-输入初始位姿功能复用模式；   13-输出碰撞功能复用模式；   14-实时调速功能复用模式 |
| `io_speed` | int | 速度取值范围0-100 |
| `io_speed_mode` | int | 模式取值范围1或2。   1-单次触发模式，当IO拉低速度设置为speed参数值，IO恢复高电平速度设置为初始值。   2-连续触发模式，IO拉低速度设置为speed参数值，IO恢复高电平速度维持当前值。   （io\_mode为14时生效） |

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

# 设置IO 1通道为通用输出模式
print(arm.rm_set_io_mode(1, 1))
print(arm.rm_set_io_mode(2, 14,50,2))
arm.rm_delete_robot_arm()
```

## 设置数字IO输出rm\_set\_do\_state()

- **方法原型：**
```python
rm_set_do_state(self, io_num: int, state: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `io_num` | `str` | IO 端口号，范围：1~4 |
| `state` | `int` | IO 状态，1-输出高，0-输出低 |

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

# 设置IO 1通道输出高
print(arm.rm_set_do_state(1, 1))

arm.rm_delete_robot_arm()
```

## 获取数字 IO 状态rm\_get\_io\_state()

- **方法原型：**
```python
rm_get_io_state(self, io_num: int) -> dict[str, any]:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `io_num` | `str` | IO 端口号，范围：1~4 |

- **返回值:**  
	`dict[str,any]`: 包含以下键值的字典。
1. **int: 函数执行的状态码**

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. **IO 状态和模式**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `IO_state` | `int` | IO 状态。 |
| `io_mode` | `int` | 模式   0-通用输入模式   1-通用输出模式   2-输入开始功能复用模式   3-输入暂停功能复用模式   4-输入继续功能复用模式   5-输入急停功能复用模式   6-输入进入电流环拖动复用模式   7-输入进入力只动位置拖动模式（六维力版本可配置）   8-输入进入力只动姿态拖动模式（六维力版本可配置）   9-输入进入力位姿结合拖动复用模式（六维力版本可配置）   10-输入外部轴最大软限位复用模式（外部轴模式可配置）   11-输入外部轴最小软限位复用模式（外部轴模式可配置）   12-输入初始位姿功能复用模式；   13-输出碰撞功能复用模式；   14-实时调速功能复用模式 |
| `io_speed` | int | 速度取值范围0-100 |
| `io_speed_mode` | int | 模式取值范围1或2。   1-单次触发模式，当IO拉低速度设置为speed参数值，IO恢复高电平速度设置为初始值。   2-连续触发模式，IO拉低速度设置为speed参数值，IO恢复高电平速度维持当前值。   （io\_mode为14时生效） |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

# 获取IO 1通道状态
print(arm.rm_get_io_state(1))

arm.rm_delete_robot_arm()
```

## 获取所有 IO 输入状态rm\_get\_io\_input()

- **方法原型：**
```python
rm_get_io_input(self) -> tuple[int, list[int]]:
```
- **返回值:**  
	`tuple[int, list[int]]`: 包含两个元素的元组。
1. int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 4 路数字输入状态列表

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[int]` | 4路数字输入状态列表，1：高，0：低，-1：该端口不是输入模式 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

# 获取IO输入状态
print(arm.rm_get_io_input())

arm.rm_delete_robot_arm()
```

## 获取所有 IO 输出状态rm\_get\_io\_output()

- **方法原型：**
```python
rm_get_io_output(self) -> tuple[int, list[int]]:
```
- **返回值:**  
	`tuple[int, list[int]]`: 包含两个元素的元组。
1. int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 4 路数字输出状态列表

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `list[int]` | 4路数字输出状态列表，1：高，0：低，-1：该端口不是输出模式 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_io_output())

arm.rm_delete_robot_arm()
```

## 设置控制器电源输出rm\_set\_voltage()

- **方法原型：**
```python
rm_set_voltage(self, voltage_type: int, start_enable: bool) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `voltage_type` | `int` | 电源输出类型，0：0V，2：12V，3：24V。 |
| `start_enable` | `bool` | `true` 代表开机启动时即输出此配置电压， `false` 代表取消开机启动即配置电压。 |

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

# 设置控制器电源输出24V
print(arm.rm_set_voltage(3, true))

arm.rm_delete_robot_arm()
```

## 获取控制器电源输出类rm\_get\_voltage()

- **方法原型：**
```python
rm_get_voltage(self) -> tuple[int, int]:
```
- **返回值:**  
	`tuple[int, int]`
1. int: 函数执行的状态码

0代表成功，其他错误码请参考 [API2错误代码](https://develop.realman-robotics.com/robot4th/apierrorList2/) 。

2. 电源输出类型

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| \- | `int` | 电源输出类型，0：0V，2：12V，3：24V。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_get_voltage())

arm.rm_delete_robot_arm()
```