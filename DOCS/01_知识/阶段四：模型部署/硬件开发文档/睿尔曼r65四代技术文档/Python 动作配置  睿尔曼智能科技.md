---
title: "Python: 动作配置 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/toolActionConfig/"
author:
published: 2025-10-10
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 动作配置

支持进行动作的相关配置，包括查询、运行、删除、保存和更新等操作。

## 查询动作列表 rm\_get\_tool\_action\_list

- **方法原型：**
```python
rm_get_tool_action_list(self, page_num: int, page_size: int, vague_search: str) -> tuple[int, dict[str, any]]:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int` | 页码。 |
| `page_size` | `int` | 每页大小。 |
| `vague_search` | `str` | 模糊搜索。 |

- **返回值:**

tuple\[int, dict\[str,any\]\]: 包含两个元素的元组。

1. int：函数执行的状态码：
	| 参数 | 说明 |
	| --- | --- |
	| 0 | 成功。 |
	| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
	| \-1 | 数据发送失败，通信过程中出现问题。 |
	| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
	| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
	| \-4 | 三代控制器不支持该接口。 |
2. dict\[str,any\] 获取到的动作列表字典，键为 `rm_tool_action_list_t` 结构体的字段名称。
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *
 
# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)
 
ret, list = arm.rm_get_tool_action_list(1, 20, None)
print("tool action list")
print("total_size:", list['total_size'])
THRESHOLD = 1000000
for i, action in enumerate(list['act_list']):
    print(f"action {i + 1}:")
    print(f"name: {action['name'].decode('utf-8')}" if isinstance(action['name'], bytes) else f"name: {action['name']}")

    has_valid_pos = any(pos != THRESHOLD for pos in action['hand_pos'][:100])
    has_valid_angle = any(angle != THRESHOLD for angle in action['hand_angle'][:100])

    if has_valid_pos:
        print("handpos: [", ", ".join(str(pos) for pos in action['hand_pos'][:100] if pos != THRESHOLD), "]")

    if has_valid_angle:
        print("handangle: [", ", ".join(str(angle) for angle in action['hand_angle'][:100] if angle != THRESHOLD), "]")

    print("--------------------")
 
arm.rm_delete_robot_arm()
```

## 运行指定末端动作 rm\_run\_tool\_action

- **方法原型：**
```python
rm_run_tool_action(self, action_name: str) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `action_name` | `str` | 末端动作名称。 |

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口。 |
| \-5 | 当前到位设备校验失败，即当前到位设备不为末端工具动作。 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_run_tool_action("1"))

arm.rm_delete_robot_arm()
```

## 删除指定末端动作 rm\_delete\_tool\_action

- **方法原型：**
```python
rm_delete_tool_action(self, action_name: str) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `action_name` | `str` | 末端动作名称。 |

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_delete_tool_action("p"))

arm.rm_delete_robot_arm()
```

## 保存动作到控制器 rm\_save\_tool\_action

- **方法原型：**
```python
rm_save_tool_action(self, action_name: str, selected_array: list, array_size: int, array_type: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `action_name` | `str` | 末端动作名称。 |
| `selected_array` | `list` | 保存数组的值。 |
| `array_size` | `int` | 保存数组的大小。 |
| `array_type` | `int` | 保存数字的类型（0-表示保存类型为hand\_pos， 1-表示保存类型为hand\_angle） |

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_save_tool_action("12", [1, 1, 1, 1, 1, 1] , 6 , 0))

arm.rm_delete_robot_arm()
```

## 更新动作到控制器 rm\_update\_tool\_action

- **方法原型：**
```python
rm_update_tool_action(self, action_name: str, new_name: str, selected_array: list[int], array_size: int, array_type: int) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `action_name` | `str` | 末端动作名称。 |
| `new_name` | `str` | 更新后的末端动作名称。 |
| `selected_array` | `list[int]` | 保存数组的值。 |
| `array_size` | `int` | 保存数组的大小。 |
| `array_type` | `int` | 保存数字的类型（0-表示保存类型为hand\_pos。 1-表示保存类型为hand\_angle） |

- **返回值:**

| 参数 | 说明 |
| --- | --- |
| 0 | 成功。 |
| 1 | 控制器返回false，传递参数错误或机械臂状态发生错误。 |
| \-1 | 数据发送失败，通信过程中出现问题。 |
| \-2 | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 |
| \-3 | 返回值解析失败，接收到的数据格式不正确或不完整。 |
| \-4 | 三代控制器不支持该接口 |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

print(arm.rm_update_tool_action("121", "12", [2, 1, 1, 1, 1, 1 ] , 6 , 1))

arm.rm_delete_robot_arm()
```