---
title: "JSON协议：系统指令集 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/json/systemConfig/"
author:
published: 2025-10-16
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 系统指令集

## 电源控制

### 控制上电与断电set\_arm\_power

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_arm_power` | `string` | 控制机械臂上电、断电。 |
| `arm_power` | `int` | 上电状态1-上电0-断电。 |

- **代码示例**

**输入**

说明：控制机械臂上电。

```json
{"command":"set_arm_power","arm_power":1}
```

**输出**

```json
{
    "command": "set_arm_power",
    "arm_power": true
}
```

### 读取电源状态get\_arm\_power\_state

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_arm_power_state` | `string` | 查询机械臂电源状态。 |

- **代码示例**

**输入**

说明：查询机械臂电源状态。

```json
{"command":"get_arm_power_state"}
```

**输出**

上电状态（1-上电状态，0断电状态）。

```json
{
    "command":"get_arm_power_state",
    "power_state": 1
}
```

## 紧急停止

### 设置机械臂急停状态set\_arm\_emergency\_stop

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_arm_emergency_stop` | `string` | 设置机械臂型号。 |
| `emergency_stop` | `bool` | `true` ：进入急停状态， `false` ：关闭急停状态。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_state` | `bool` | `true` ：成功， `false` ：失败 |

- **代码示例**

**输入**

设置机械臂进入急停状态。

```json
{ "command":"set_arm_emergency_stop","emergency_stop":true}
```

**输出**

设置成功：

```json
{
    "command":"set_arm_emergency_stop",
    "set_state":true
}
```

设置失败：

```json
{
    "command":"set_arm_emergency_stop",
    "set_state":false
}
```

## 版本信息

### 查询软件版本get\_arm\_software\_info

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_arm_software_info` | `string` | 查询机械臂软件信息。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| Product\_version | `string` | 机械臂型号。 |
| algorithm\_info | `object` | 算法库信息，其中version代表版本号。 |
| communication\_info | `object` | communication层软件信息，其中build\_time代表编译时间，version代表版本号。 |
| ctrl\_info | `object` | ctrl层软件信息，其中build\_time代表编译时间，version代表版本号。 |
| program\_info | `object` | program层软件信息，其中build\_time代表编译时间，version代表版本号。 |
| robot\_controller\_version | `string` | 机械臂控制器版本信息。 |

- **代码示例**

**输入**

查询机械臂软件信息。

```json
{"command":"get_arm_software_info"}
```

**输出**

```json
{
  "Product_version": "RM65-6FB",
  "algorithm_info": {
    "version": "1.5.5-c0d52d18"
  },
  "command": "arm_software_info",
  "communication_info": {
    "build_time": "2025-06-23 14:14:59",
    "version": "V1.0.4.t9"
  },
  "ctrl_info": {
    "build_time": "2025-06-23 14:14:59",
    "version": "V1.0.4.t9"
  },
  "program_info": {
    "build_time": "2025-06-23 14:14:59",
    "version": "V1.0.4.t9"
  },
  "robot_controller_version": "4.0"
}
```

### 查询关节软件版本号get\_joint\_software\_version

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_joint_software_version` | `string` | 获取关节软件版本号。 |

- **代码示例**

**输入** ：

```json
{"command":"get_joint_software_version"}
```

**输出** ：

当前关节的版本号分别为：Vd5.1.0、Vd5.1.0、Vd5.1.0、Vd5.1.0、Vd5.1.0、Ve5.1.0。

```json
{
    "command": "get_joint_software_version",
    "version": [
        "Vd5.1.0",
        "Vd5.1.0",
        "Vd5.1.0",
        "Vd5.1.0",
        "Vd5.1.0",
        "Ve5.1.0"
    ]
}
```

### 查询末端接口板软件版本号get\_tool\_software\_version

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_tool_software_version` | `string` | 获取末端接口板软件版本号。 |

- **代码示例**

**输入**

```json
{"command":"get_tool_software_version"}
```

**输出** 当前末端接口板的版本号为V1.9.3。

```json
{
    "command": "get_tool_software_version",
    "version": "V1.9.3"
}
```

## 累计数据

### 读取控制器的累计运行时间get\_system\_runtime

查询控制器自出厂以来，累计的运行时间。

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_system_runtime` | `string` | 查询控制器累计的运行时间。 |

- **代码示例**

**输入**

说明：查询系统运行时间。

```json
{"command":"get_system_runtime"}
```

**输出**

若系统正常，则返回运行时间。

```json
{
    "command": "get_system_runtime",
    "day": 0,
    "hour": 0,
    "min": 0,
    "sec": 0
}
```

### 清零控制器的累计运行时间clear\_system\_runtime

清零控制器自出厂以来，累计的运行时间。

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `clear_system_runtime` | `string` | 清零控制器累计的运行时间。 |

- **代码示例**

**输入**

说明：清零系统运行时间。

```json
{"command":"clear_system_runtime"}
```

**输出**  
清除成功（true-清除成功，false-清除失败）。

```json
{
    "command": "clear_system_runtime",
    "clear_state": true
}
```

### 读取关节的累计转动角度get\_joint\_odom

查询各关节自出厂以来，累计的转动角度。

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_joint_odom` | `string` | 查询各关节的累计转动角度。 |

- **代码示例**

**输入**

说明：查询关节的累计转动角度。

```json
{"command":"get_joint_odom"}
```

**输出**

若指令正确，返回六自由度各关节累计的转动角度。

```json
{
    "command": "get_joint_odom",
    "motor_output_power1": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "motor_output_power2": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "motor_output_power3": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "motor_output_power4": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "motor_output_power5": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "motor_output_power6": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "odom": [0, 0, 0, 0, 0, 0, 0]
}
```

若指令正确，返回七自由度各关节累计的转动角度。

```json
{
    "command": "get_joint_odom",
    "motor_output_power1": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "motor_output_power2": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "motor_output_power3": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "motor_output_power4": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "motor_output_power5": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "motor_output_power6": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "motor_output_power7": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "odom": [259, 227, 0, 421, 6, 675, 539]
}
```

### 清零关节的累计转动角度clear\_joint\_odom

清零各关节自出厂以来，累计的转动角度。

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `clear_joint_odom` | `string` | 清零关节累计转动的角度。 |

- **代码示例**

**输入**

说明：清零关节累计转动的角度。

```json
{"command":"clear_joint_odom"}
```

**输出** 清除成功（true-清除成功，false-清除失败）。

```json
{
    "command": "clear_joint_odom",
    "clear_state": true
}
```