---
title: "JSON 协议：IO配置指令集 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/json/ioConfig/"
author:
published: 2025-11-13
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## IO配置指令集

## 控制器IO

第四代控制器数量和分类如下所示：

| 类型 | 说明 |
| --- | --- |
| 数字IO：DO/DI复用 | 4路，可配置为0~24V |

### 设置数字IO模式set\_IO\_mode

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_IO_mode` | `string` | 设置数字IO模式。 |
| `IO_Num` | `int` | IO端口号，范围：1~4。 |
| `IO_mode` | `int` | 模式选择。   0-通用输入模式；   1-通用输出模式；   2-输入开始功能复用模式；   3-输入暂停功能复用模式；   4-输入继续功能复用模式；   5-输入急停功能复用模式；   6-输入进入电流环拖动复用模式；   7-输入进入力只动位置拖动模式（六维力版本可配置）；   8-输入进入力只动姿态拖动模式（六维力版本可配置）；   9-输入进入力位姿结合拖动复用模式（六维力版本可配置）；   10-输入外部轴最大软限位复用模式（扩展关节的外部轴模式可配置）；   11-输入外部轴最小软限位复用模式（扩展关节的外部轴模式可配置）；   12-输入初始位姿功能复用模式（低电平触发）；   13-输出碰撞功能复用模式（正常输出低电平，错误输出高电平）；   14-实时调速功能复用模式。 |
| `realtime_speed` | `string` | 缺省参数，当 `IO_mode` 设置为14（实时调速功能复用模式）时，设置此参数。 |
| `speed` | `int` | 设置速度，取值范围0-100。 |
| `mode` | `int` | 模式选择。   1-单次触发模式，单次触发模式下当IO拉低速度设置为speed参数值，IO恢复高电平速度设置为初始值；   2-连续触发模式，连续触发模式下IO拉低速度设置为speed参数值，IO恢复高电平速度维持当前值。   3-自定义电平速度模式，可自定义设置低电平速度与高电平速度。当IO低电平速度设置为speed参数值，IO高电平速度设置为heightSpeed参数值。 |

- **代码示例**

**输入**

设置数字IO模式。

```json
{"command":"set_IO_mode","IO_Num":1,"IO_mode":14,"realtime_speed":{"speed":50,"mode":1}}
```

**输出**

配置成功：

```json
{
    "command": "set_IO_mode",
    "set_state": true
}
```

配置失败：

```json
{
    "command": "set_IO_mode",
    "set_state": false
}
```

### 设置数字IO输出状态set\_DO\_state

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_DO_state` | `string` | 设置数字IO输出。 |
| `IO_Num` | `int` | IO端口号，范围：1~4。 |
| `state` | `int` | IO状态，1-输出高，0-输出低。 |

- **代码示例**

**输入**

```json
{"command":"set_DO_state","IO_Num":1,"state":1}
```

**输出**

配置成功：

```json
{
    "command": "set_DO_state",
    "set_state": true
}
```

配置失败：

```json
{
    "command": "set_DO_state",
    "set_state": false
}
```

### 查询数字IO状态get\_IO\_state

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_IO_state` | `string` | 获取数字IO输出。 |
| `IO_Num` | `int` | IO端口号，范围：1~4。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `IO_Num` | `int` | IO 端口号，范围：1~4。 |
| `IO_mode` | `int` | 输出设置模式。   0-通用输入模式；   1-通用输出模式；   2-输入开始功能复用模式；   3-输入暂停功能复用模式；   4-输入继续功能复用模式；   5-输入急停功能复用模式；   6-输入进入电流环拖动复用模式；   7-输入进入力只动位置拖动模式；   8-输入进入力只动姿态拖动模式；   9-输入进入力位姿结合拖动复用模式；   10-输入外部轴最大软限位复用模式；   11-输入外部轴最小软限位复用模式；   12-输入初始位姿功能复用模式；   13-输出碰撞功能复用模式；   14-实时调速功能复用模式。 |
| `IO_State` | `int` | IO状态，1-输出高，0-输出低。 |
| `realtime_speed` | `object` | 缺省参数，当 `IO_mode` 为14（实时调速功能复用模式）时，返回此参数。 |
| `speed` | `int` | 输出设置速度，取值范围0-100。 |
| `mode` | `int` | 输出设置模式。   1-单次触发模式，单次触发模式下当IO拉低速度设置为speed参数值，IO恢复高电平速度设置为初始值。   2-连续触发模式，连续触发模式下IO拉低速度设置为speed参数值，IO恢复高电平速度维持当前值。   3-自定义电平速度模式，可自定义设置低电平速度与高电平速度。当IO低电平速度设置为speed参数值，IO高电平速度设置为heightSpeed参数值。 |

- **代码示例**

**输入**

获取数字IO输出状态

```json
{"command":"get_IO_state","IO_Num":1}
```

**输出**

```json
{
    "command":"get_IO_state",
    "IO_Num": 1,
    "IO_Mode": 14,
    "IO_state": 1,
    "realtime_speed":
    {
        "speed":50,
        "mode":1
    }
}
```

### 查询所有IO输入状态get\_IO\_input

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_IO_input` | `string` | 获取所有IO输入状态。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `DI` | `int` | 数字输入状态，1-高，0-低。 |

- **代码示例**

**输入**

获取所有IO输入状态。

```json
{"command":"get_IO_input"}
```

**输出**

```json
{
    "command":"get_IO_input",
    "DI": [
,
,
        1
    ]
}
```

### 查询所有IO输出状态get\_IO\_output

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_IO_output` | `string` | 获取所有IO输出状态。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `DO` | `int` | 数字输出状态，1-高，0-低。 |

- **代码示例**

**输入** 获取所有IO输出。

```json
{"command":"get_IO_output"}
```

**输出**

```json
{
    "command":"get_IO_output",
    "DO": [
,
,
,
        1
    ]
}
```

### 设置电源输出set\_voltage

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_voltage` | `string` | 设置电源输出。 |
| `voltage_type` | `int` | 电源输出类型，0：0V，2：12V，3：24V。 |
| `start_enable` | `bool` | `true` 代表开机启动时即输出此配置电压， `false` 代表取消开机启动即配置电压。 |

- **代码示例**

**输入**

设置电源输出。

```json
{"command":"set_voltage","voltage_type":2,"start_enable":true}
```

**输出**

配置成功:

```json
{
    "command": "set_voltage",
    "state": true
}
```

配置失败:

```json
{
    "command": "set_voltage",
    "state": false
}
```

### 查询电源输出get\_voltage

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_voltage` | `string` | 获取电源输出。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `voltage_type` | `int` | 电源输出类型，0：0V，2：12V，3：24V。 |

- **代码示例**

**输入** 获取控制器电源输出类型。

```json
{"command":"get_voltage"}
```

**输出**

```json
{
    "command": "voltage_state",
    "voltage_type": 2
}
```

## 末端工具IO

机械臂末端工具端具有IO端口，数量和分类如下所示：

| 类型 | 说明 |
| --- | --- |
| 电源输出 | 1路，可配置为0V/12V/24V。 |
| 数字IO | 2路，输入输出可配置。 |
| 通讯接口 | 1路，可配置为RS485。 |

### 设置工具端数字IO输出状态set\_tool\_DO\_state

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_tool_DO_state` | `string` | 设置数字IO输出。 |
| `IO_Num` | `int` | IO端口号，范围：1~2。 |
| `state` | `int` | IO状态，1-输出高，0-输出低。 |

- **代码示例**

**输入** 设置工具端数字IO输出。

```json
{"command":"set_tool_DO_state","IO_Num":1,"state":1}
```

**输出** 配置成功：

```json
{
    "command": "set_tool_DO_state",
    "set_state": true
}
```

配置失败：

```json
{
    "command": "set_tool_DO_state",
    "set_state": false
}
```

### 设置工具端数字IO模式set\_tool\_IO\_mode

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_tool_IO_mode` | `string` | 设置数字IO模式。 |
| `IO_Num` | `int` | IO端口号，范围：1~2。 |
| `state` | `int` | IO状态，0-输入状态，1-输出状态。 |

- **代码示例**

**输入** 设置数字IO模式

```json
{"command":"set_tool_IO_mode","IO_Num":1,"state":0}
```

**输出** 配置成功：

```json
{
    "command": "set_tool_IO_mode",
    "set_state": true
}
```

配置失败：

```json
{
    "command": "set_tool_IO_mode",
    "set_state": false
}
```

### 查询工具端数字IO状态get\_tool\_IO\_state

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_tool_IO_state` | `string` | 获取数字IO状态。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `IO_Mode` | `int` | 0-输入模式，1-输出模式。 |
| `IO_State` | `int` | IO状态，1-输出高，0-输出低。 |

- **代码示例**

**输入** 获取数字IO状态。

```json
{"command":"get_tool_IO_state"}
```

**输出**

```json
{
    "command":"get_tool_IO_state",
    "IO_Mode": [
,
        1
    ],
    "IO_State": [
,
        1
    ]
}
```

### 设置工具端电源输出set\_tool\_voltage

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `set_tool_voltage` | `string` | 设置电源输出。 |
| `voltage_type` | `int` | 电源输出类型，0：0V，2：12V，3：24V。 |

- **代码示例**

**输入** 设置电源输出

```json
{"command":"set_tool_voltage","voltage_type":2}
```

**输出** 配置成功

```json
{
    "command": "set_tool_voltage",
    "state": true
}
```

配置失败

```json
{
    "command": "set_tool_voltage",
    "state": false
}
```

### 查询工具端电源输出get\_tool\_voltage

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_tool_voltage` | `string` | 获取电源输出。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_tool_voltage` | `int` | 电源输出类型，0：0V，2：12V，3：24V。 |

- **代码示例**

**输入** 获取电源输出类型

```json
{"command":"get_tool_voltage"}
```

**输出**

```json
{
    "command":"get_tool_voltage",
    "voltage_type": 2
}
```