---
title: "JSON协议：末端工具指令集（选配） | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/json/endTool/"
author:
published: 2026-04-22
created: 2026-05-08
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 末端工具指令集（选配）

## 五指灵巧手

睿尔曼机械臂末端配置因时的五指灵巧手，可通过协议对灵巧手进行设置。

### 灵巧手角度跟随控制hand\_follow\_angle

设置灵巧手跟随角度，灵巧手：6个主动自由度，自由度1（大拇指弯曲）、自由度2（食指）、自由度3（中指）、自由度4（无名指）、自由度5（小指）、自由度6（大拇指旋转），最高50Hz的控制频率。

注意

如果要使用此功能，需要联系技术支持发送定制的灵巧手固件升级包（傲意或者因时）。

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `hand_follow_angle` | `string` | 设置手指角度。 |

- **因时各自由度的角度定义和运动范围说明如下。**

| 角度 | 图例说明 | 范围 |
| --- | --- | --- |
| 小拇指   无名指   中指   食指 | ![image6](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/json/endTool/image6.png) | 19°~176.7° |
| 大拇指弯曲角度 | ![image7](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/json/endTool/image7.png) | \-130~53.6° |
| 大拇旋转曲角度 | ![image8](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/json/endTool/image8.png) | 90°~165° |

- **傲意各自由度的角度定义和运动范围说明如下。**

| 角度 | 图例说明 | 范围 |
| --- | --- | --- |
| 食指   中指   无名指   小拇指 | ![image9](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/json/endTool/image9.png) | 100.22°~178.37°   97.81° ~ 176.06°   101.38°~176.54°   98.84°~174.86° |
| 大拇指弯曲角度 | ![image10](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/json/endTool/image10.png) | 2.26° ~ 36.76° |
| 大拇旋转曲角度 | ![image11](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/json/endTool/image11.png) | 0° ~ 90° |

- **代码示例**

**输入**

说明：设置灵巧手各手指动作，hand\_angle表示手指角度数组，按照灵巧手厂商定义的角度做控制，例如：

1. 傲意的角度范围为-32768到+32767。
2. 因时的角度范围为0到+1000；

灵巧手角度的定义（int16）：

1. 傲意：第一指关节1的角度\*100。
2. 因时：0-1000，通过联系技术支持得到驱动器行程与角度关系表。
```json
{"command":"hand_follow_angle","hand_angle":[100,100,200,300,400,500]}
```

**输出**

设置成功

```json
{
    "command": "hand_follow_angle",
    "set_state": true
}
```

设置失败

```json
{
    "command": "hand_follow_angle",
    "set_state": false
}
```

### 灵巧手位置跟随控制hand\_follow\_pos

设置灵巧手跟随角度，灵巧手：6个主动自由度，自由度1（大拇指弯曲）、自由度2（食指）、自由度3（中指）、自由度4（无名指）、自由度5（小指）、自由度6（大拇指旋转），最高50Hz的控制频率。

注意

如果要使用此功能，需要联系技术支持发送定制的灵巧手固件升级包（傲意或者因时）。

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `hand_follow_pos` | `string` | 设置手指角度。 |

- **代码示例**

**输入**

说明：设置灵巧手各手指动作，hand\_pos表示手指位置数组，按照灵巧手厂商定义的角度做控制，例如：

1. 因时的位置范围为0-2000；
2. 傲意的位置范围为0-65535。
```json
{"command":"hand_follow_pos","hand_pos":[100,100,200,300,400,500]}
```

**输出**

设置成功

```json
{
    "command": "hand_follow_pos",
    "set_state": true
}
```

设置失败

```json
{
    "command": "hand_follow_pos",
    "set_state": false
}
```

## 末端动作列表

睿尔曼机械臂末端动作列表相关功能，支持对末端动作进行全面管理与控制。

### 查询动作列表get\_tool\_action\_list

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_tool_action_list` | `string` | 查询动作列表。 |
| `page_num` | `int` | 页码（全部查询时不传此参数）。 |
| `page_size` | `int` | 每页大小（全部查询时不传此参数）。 |
| `vague_search` | `string` | 模糊搜索 （传递此参数可进行模糊查询）。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `get_tool_action_list` | `string` | 查询动作列表。 |
| `total_size` | `int` | 动作总数。 |
| `list` | `object` | 动作详细信息。 |

- **代码示例**

**输入**

```json
{"command":"get_tool_action_list"}
```

**输出**

```json
{
    "action_list": [
    {
      "hand_pos": [0, 0, 0, 0, 0, 0],
      "name": "睿尔曼"
    },
    {
      "hand_pos": [0, 0, 0, 0, 0, 0],
      "name": "111111111111111"
    },
    {
      "hand_pos": [0, 0, 0, 0, 0, 0],
      "name": "QN-触觉"
    },
    {
      "hand_pos": [14, 19, 18, 9, 6, 4],
      "name": "QN-夹爪闭合"
    },
    {
      "hand_pos": [14, 19, 18, 9, 6, 4],
      "name": "QN-夹爪闭合-1-1-1-1"
    },
    {
      "hand_pos": [14, 19, 18, 9, 6, 4],
      "name": "强脑-目标位置"
    },
    {
      "hand_pos": [12],
      "name": "张开-1-1-1-1"
    },
    {
      "hand_pos": [12000],
      "name": "夹爪闭合-1-1-1-1"
    },
    {
      "hand_pos": [12],
      "name": "张开-1-1-1"
    },
    {
      "hand_pos": [12000],
      "name": "夹爪闭合-1-1-1"
    },
    {
      "hand_pos": [12],
      "name": "张开-1-1"
    },
    {
      "hand_pos": [12000],
      "name": "夹爪闭合-1-1"
    },
    {
      "hand_pos": [12],
      "name": "张开-1"
    },
    {
      "hand_pos": [12000],
      "name": "夹爪闭合-1"
    },
    {
      "hand_pos": [12000],
      "name": "夹爪闭合"
    },
    {
      "hand_pos": [12],
      "name": "张开"
    }
  ],
  "command": "get_tool_action_list",
  "total_size": 16
}
```

### 运行指定末端动作run\_tool\_action

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `run_tool_action` | `string` | 开始运行编号轨迹。 |
| `name` | `string` | 运行指定name的动作，存在该动作即可运行。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `run_state` | `bool` | `true`:开始运行。 `false` 运行失败。 |
| `run_tool_action` | `string` | 轨迹文件运行到位。 |

- **代码示例**

**输入**

开始运行动作“123”。

```json
{
    "command": "run_tool_action",
    "name": "123"
}
```

**输出**

开始运行成功。

```json
{
    "command": "run_tool_action",
    "run_state": true
}
```

开始运行失败。

```json
{
    "command": "run_tool_action",
    "run_state": false
}
```

末端动作结束后，返回运行结束命令。

```json
{
    "state": "current_trajectory_state",
    "trajectory_state": true,
    "device": 5,
    "trajectory_connect": 0
}
```

### 删除指定末端动作delete\_tool\_action

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `delete_tool_action` | `string` | 删除指定名称的动作。 |
| `name` | `string` | 删除的动作名称。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `delete_state` | `bool` | `true`:成功。 `false` 失败。 |

- **代码示例**

**输入**

删除轨迹2。

```json
{
    "command": "delete_tool_action",
    "name": "pick"
}
```

**输出**

删除成功。

```json
{
    "command": "delete_tool_action",
    "delete_state": true
}
```

删除失败。

```json
{
    "command": "delete_tool_action",
    "delete_state": false
}
```

### 保存动作save\_tool\_action

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `save_tool_action` | `string` | 保存动作。 |
| `name` | `string` | 保存的动作名称。 |
| `hand_pos` | `array` | 位置。 |
| `hand_angle` | `array` | 角度。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `save_state` | `bool` | `true`:成功。 `false` 失败。 |

- **代码示例**

**输入**

```json
{
    "command": "save_tool_action",
    "name": "pick",
    "hand_pos": [0, 0, 0, 0, 0, 0]
}

{
    "command": "save_tool_action",
    "name": "pick",
    "hand_angle": [0, 0, 0, 0, 0, 0]
}
```

**输出**

保存成功。

```json
{
    "command": "save_tool_action",
    "save_state": true
}
```

保存失败。

```json
{
    "command": "save_tool_action",
    "save_state": false
}
```

### 更新动作update\_tool\_action

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `update_tool_action` | `string` | 更新动作。 |
| `name` | `string` | 要更新的动作名称。 |
| `new_name` | `string` | 新动作名称。 |
| `hand_pos` | `array` | 位置。 |
| `hand_angle` | `array` | 角度。 |

- **输出参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `update_state` | `bool` | `true`:成功。 `false` 失败。 |

- **代码示例**

**输入**

```json
{
    "command": "update_tool_action",
    "name": "pick",
    "new_name": "1",
    "hand_pos": [0, 0, 0, 0, 0, 0]
}

{
    "command": "update_tool_action",
    "name": "pick",
    "name": "1",
    "hand_angle": [0, 0, 0, 0, 0, 0]
}
```

**输出**

更新成功。

```json
{
    "command": "update_tool_action",
    "update_state": true,
}
```

更新失败。

```json
{
    "command": "update_tool_action",
    "update_state": false,
}
```

### 轨迹结束返回标志current\_trajectory\_state

轨迹为当前轨迹。

- **输入参数**

| 功能描述 | 类型 | 说明 |
| --- | --- | --- |
| `current_trajectory_state` | `string` | 当前轨迹结束返回标志。 |
| `device` | `int` | 0: 关节、1: 夹爪、2: 灵巧手、3: 升降机构、4: 扩展关节、5: 末端工具动作、其他: 保留。 |

- **代码示例**

实现：当前轨迹到达目标。

```json
{
    "state": "current_trajectory_state",
    "trajectory_state": true,
    "device": 0
}
```
