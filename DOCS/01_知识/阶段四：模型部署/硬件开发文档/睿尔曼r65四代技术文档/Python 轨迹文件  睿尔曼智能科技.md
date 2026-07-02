---
title: "Python: 轨迹文件 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/apipython/classes/trajectoryfile/"
author:
published: 2025-05-19
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 轨迹文件

支持进行轨迹文件管理，包括查询、运行、删除和保存等操作。

## 查询轨迹列表 rm\_get\_trajectory\_file\_list()

- **方法原型：**
```python
rm_get_trajectory_file_list(self, page_num: int, page_size: int, vague_search: str) -> tuple[int, dict[str, any]]:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int` | 页码。 |
| `page_size` | `int` | 每页大小。 |
| `vague_search` | `str` | 模糊搜索。 |

- **返回值:**

tuple\[int,dict\[str,any\]\]: 包含两个元素的元组。

1. int：函数执行的状态码：
	| 参数 | 类型 | 说明 | 处理建议 |
	| --- | --- | --- | --- |
	| 0 | `int` | 成功。 | \- |
	| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ：   ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
	| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
	| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
	| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
	| \-4 | `int` | 三代控制器不支持该接口 | \- |
2. dict\[str,any\]：拖动示教轨迹列表：
	| 参数 | 类型 | 说明 |
	| --- | --- | --- |
	| \- | `dict[str,any]` | 返回符合条件的拖动示教轨迹列表字典，键为rm\_trajectory\_list\_t结构体的字段名称。 |
	*可以跳转 [rm\_trajectory\_list\_t](https://develop.realman-robotics.com/robot4th/apipython/struct/trajectoryinfolist/) 查阅结构体详细描述。*
- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

# 查询拖动示教轨迹列表
print(arm.rm_get_trajectory_file_list(1,10,"test"))

arm.rm_delete_robot_arm()
```

## 开始运行指定轨迹 rm\_set\_run\_trajectory()

- **方法原型：**
```python
rm_set_run_trajectory(self, trajectory_name: str) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `trajectory_name` | `str` | 拖动示教轨迹名称。 |

- **返回值:**  
	函数执行的状态码：

| 参数 | 类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 0 | `int` | 成功。 | \- |
| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ：   ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-4 | `int` | 三代控制器不支持该接口 | \- |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

# 运行指定拖动示教轨迹
print(arm.rm_set_run_trajectory('test'))

arm.rm_delete_robot_arm()
```

## 删除指定轨迹文件 rm\_delete\_trajectory\_file()

- **方法原型：**
```python
rm_delete_trajectory_file(self, trajectory_name: str) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `trajectory_name` | `str` | 拖动示教轨迹名称。 |

- **返回值:**  
	函数执行的状态码：

| 参数 | 类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 0 | `int` | 成功。 | \- |
| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ：   ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-4 | `int` | 三代控制器不支持该接口 | \- |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

# 删除指定拖动示教轨迹
print(arm.rm_delete_trajectory_file('test'))

arm.rm_delete_robot_arm()
```

## 保存轨迹文件 rm\_save\_trajectory\_file()

- **方法原型：**
```python
rm_save_trajectory_file(self, trajectory_name: str) -> int:
```
- **参数说明:**

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `trajectory_name` | `str` | 拖动示教轨迹名称。 |

- **返回值:**

函数执行的状态码：

| 参数 | 类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 0 | `int` | 成功。 | \- |
| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ：   ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-4 | `int` | 三代控制器不支持该接口 | \- |

- **使用示例**
```python
from Robotic_Arm.rm_robot_interface import *

# 实例化RoboticArm类
arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)

# 创建机械臂连接，打印连接id
handle = arm.rm_create_robot_arm("192.168.1.18", 8080)
print(handle.id)

# 保存拖动示教轨迹
print(arm.rm_save_trajectory_file('test'))

arm.rm_delete_robot_arm()
```