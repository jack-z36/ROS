---
title: "ROS2调用API接口功能包说明V1.0.0 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/ros2/ros2Description/"
author:
published: 2026-03-30
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## ROS2调用API接口功能包说明V1.0.0

为了方便用户通过ROS2控制机械臂，睿尔曼提供了基于API的ROS2功能包，有关机械臂的控制细节想要了解的话也可以参考API的相关文档和说明，在实际使用机械臂时，用户可通过以太网口与机械臂建立通信，并控制机械臂。

## 报错说明

### 控制器错误类型

| 序号 | 错误代码(16进制) | 错误内容 |
| --- | --- | --- |
| 1 | 0x0000 | 系统正常 |
| 2 | 0x1001 | 关节通信异常 |
| 3 | 0x1002 | 目标角度超过限位 |
| 4 | 0x1003 | 该处不可达，为奇异点 |
| 5 | 0x1004 | 实时内核通信错误 |
| 6 | 0x1005 | 关节通信总线错误 |
| 7 | 0x1006 | 规划层内核错误 |
| 8 | 0x1007 | 关节超速 |
| 9 | 0x1008 | 末端接口板无法连接 |
| 10 | 0x1009 | 超速度限制 |
| 11 | 0x100A | 超加速度限制 |
| 12 | 0x100B | 关节抱闸未打开 |
| 13 | 0x100C | 拖动示教时超速 |
| 14 | 0x100D | 机械臂发生碰撞 |
| 15 | 0x100E | 无该工作坐标系 |
| 16 | 0x100F | 无该工具坐标系 |
| 17 | 0x1010 | 关节发生掉使能错误 |

### 关节错误类型

| 序号 | 错误代码(16进制) | 错误内容 |
| --- | --- | --- |
| 1 | 0x0000 | 关节正常 |
| 2 | 0x0001 | FOC错误 |
| 3 | 0x0002 | 过压 |
| 4 | 0x0004 | 欠压 |
| 5 | 0x0008 | 过温 |
| 6 | 0x0010 | 启动失败 |
| 7 | 0x0020 | 编码器错误 |
| 8 | 0x0040 | 过流 |
| 9 | 0x0080 | 软件错误 |
| 10 | 0x0100 | 温度传感器错误 |
| 11 | 0x0200 | 位置超限错误 |
| 12 | 0x0400 | 关节ID非法 |
| 13 | 0x0800 | 位置跟踪错误 |
| 14 | 0x1000 | 电流检测错误 |
| 15 | 0x2000 | 抱闸打开失败 |
| 16 | 0x4000 | 位置指令阶跃警告 |
| 17 | 0x8000 | 多圈关节丢圈数 |
| 18 | 0xF000 | 通信丢帧 |

### API错误类型

| 参数 | 类型 | 说明 | 处理建议 |
| --- | --- | --- | --- |
| 0 | `int` | 成功。 | \- |
| 1 | `int` | 控制器返回false，传递参数错误或机械臂状态发生错误。 | \- **校验JSON指令** ：   ①启用API的DEBUG日志，捕获原始JSON数据。   ②检查JSON语法：确保括号、引号、逗号等格式正确（可借助JSON校验工具）。   ③对照API文档，验证参数名称、数据类型及取值范围是否符合规范。   ④修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。   \- **检查机械臂状态** ：   ①查看机械臂控制器或日志中的实时报错信息（如硬件故障、超限等），根据提示复位、校准或排查硬件问题。   ②修正问题后重新发送指令，检查控制器返回的状态码及业务数据是否正常。 |
| \-1 | `int` | 数据发送失败，通信过程中出现问题。 | **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |
| \-2 | `int` | 数据接收失败，通信过程中出现问题或者控制器超时没有返回。 | \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。   \- **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。   \- **调用ModbusTCP接口** ：仅在读写控制器ModbusTCP设备时适用，创建机械臂控制句柄后，必须调用 `rm_set_modbustcp_mode()` 接口，否则无法接收到返回值。 |
| \-3 | `int` | 返回值解析失败，接收到的数据格式不正确或不完整。 | **校验版本兼容性** ：   ①核对控制器固件版本是否支持当前API功能，具体版本配套关系请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/) 。   ②若版本过低需升级控制器或使用适配的API版本。 |
| \-4 | `int` | 当前到位设备校验失败，即当前到位设备不为关节/升降机构/夹爪/灵巧手。 | \- **检测多设备并发控制** ：检查是否有其他设备给机械臂发送运动指令：包括机械臂、夹爪、灵巧手、升降机的运动；   \- **实时监听指令事件** ：注册回调函数 `rm_get_arm_event_call_back` ：   ①捕获设备到位事件（如运动完成、超时等）；   ②通过回调参数 device 判断触发事件的具体设备类型。 |
| \-5 | `int` | 单线程阻塞模式超时未接收到返回，请确保超时时间设置合理。 | \- **检查超时时长设置** ：单线程阻塞模式下，支持配置等待设备运动完成的超时时间，务必确保设置超时时间大于设备运动时间；   \- **检查网络连通性** ：   使用ping/telnet等工具检测与控制器的通信链路是否正常。 |

## ROS功能包机械臂相关指令使用说明

该部分介绍如何来通过ROS话题查询和控制机械臂。

### 关节配置

#### 清除关节错误代码Jointerrclear.msg

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_num` | `uint8` | 对应关节序号，从基座到机械臂手爪端，六自由度序号依次为1～6，七自由度序号依次为1～7。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_joint_err_clear_cmd rm_ros_interfaces/msg/Jointerrclear "joint_num: 1"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_joint_err_clear_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。 |

### 版本查询

#### 查询关节软件版本

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带空消息类型，无具体参数。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_joint_software_version_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_joint_software_version_result
```

**参数说明：** `Jointversion.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_version` | `string[7]` | 获取到的各关节软件版本号数组，需转换为十六进制（例如：54536 转换为十六进制为 D508，对应版本号为 Vd5.0.8（三代控制器））。 |
| `state` | `bool` | 获取状态，true：获取成功，false：获取失败。 |

#### 查询末端接口板软件版本号

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带空消息类型，无具体参数。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_tool_software_version_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_tool_software_version_result
```

**参数说明：** `Toolsoftwareversionv4.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `tool_version` | `string` | 末端接口板软件版本号（End interface board software version number）。 |
| `state` | `bool` | 查询状态，true：获取成功，false：获取失败。 |

### 工作坐标系设置

#### 切换当前工作坐标系

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `String` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/change_work_frame_cmd std_msgs/msg/String "data: 'Base'"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/change_work_frame_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。 |

### 坐标系查询

#### 查询当前工具坐标系

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_current_tool_frame_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：** 当前工具坐标系名称。

```json
ros2 topic echo /rm_driver/get_current_tool_frame_result
```

#### 查询所有工具坐标系名称

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/get_all_tool_frame_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：** 当前工具坐标系所有名称。

```json
ros2 topic echo /rm_driver/get_all_tool_frame_result
```

#### 查询当前工作坐标系

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_curr_workFrame_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_curr_workFrame_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。 |

#### 查询所有工作坐标系

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_all_work_frame_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：** 所有工作坐标系名称。

```json
ros2 topic echo /rm_driver/get_all_work_frame_result
```

### 机械臂状态查询

#### 获取机械臂当前状态-返回各关节角度和欧拉角

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_current_arm_state_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：** 当前机械臂关节状态(角度)+位姿信息(欧拉角)+报错信息。

```json
ros2 topic echo /rm_driver/get_current_arm_original_state_result
```

#### 获取机械臂当前状态-返回各关节弧度和四元数

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_current_arm_state_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：** 当前机械臂关节状态(弧度)+位姿信息(四元数)+报错信息。

```json
ros2 topic echo /rm_driver/get_current_arm_state_result
```

### 机械臂运动规划

#### 关节空间运动MoveJ.msg

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint` | `float32[6]` | 关节角度，单位：弧度。 |
| `speed` | `uint8` | 速度百分比例系数，0~100。 |
| `trajectory_connect` | `uint8` | 可选参数，代表是否和下一条运动一起规划，   0代表立即规划，   1代表和下一条轨迹一起规划，当为1时，轨迹不会立即执行。 |
| `block` | `bool` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |
| `dof` | `uint8` | 机械臂自由度。 |

**使用命令示例：** 六自由度：

```json
ros2 topic pub --once /rm_driver/movej_cmd rm_ros_interfaces/msg/Movej "joint: [0, 0, 0, 0, 0, 0] speed: 20 block: true trajectory_connect: 0 dof: 6"
```

七自由度：

```json
ros2 topic pub --once /rm_driver/movej_cmd rm_ros_interfaces/msg/Movej "joint: [0, 0, 0, 0, 0, 0, 0] speed: 20 block: true trajectory_connect: 0 dof: 7"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/movej_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 笛卡尔空间直线运动Movel.msg

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `geometry_msgs/Pose` | `float` | 机械臂位姿，x、y、z坐标(float类型，单位：m)+四元数。 |
| `speed` | `uint8` | 速度百分比例系数，0~100。 |
| `trajectory_connect` | `uint8` | 可选参数，代表是否和下一条运动一起规划，   0代表立即规划，   1代表和下一条轨迹一起规划，当为1时，轨迹不会立即执行。 |
| `block` | `bool` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |

**使用命令示例：** 先使用MoveJ\_P：

```json
ros2 topic pub --once /rm_driver/movej_p_cmd rm_ros_interfaces/msg/Movejp "pose:position: x: -0.317239 y: 0.120903 z: 0.255765 orientation: x: -0.983404 y: -0.178432 z: 0.032271 w: 0.006129 speed:20 trajectory_connect: 0 block: true"
```

后使用MoveL：

```json
ros2 topic pub --once /rm_driver/movel_cmd rm_ros_interfaces/msg/Movel "pose: position: x: -0.317239 y: 0.120903 z: 0.295765 orientation: x: -0.983404 y: -0.178432 z: 0.032271 w: 0.006129 speed: 20 trajectory_connect: 0 block: true"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/movel_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 笛卡尔空间直线偏移运动

**参数说明：** `Moveloffset.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `geometry_msgs/Pose` | `float` | 位置姿态偏移，位置单位：米，姿态单位：弧度。 |
| `speed` | `int32` | 速度百分比系数，1~100。 |
| `r` | `int32` | 交融半径百分比系数，0~100。 |
| `trajectory_connect` | `bool` | 轨迹连接标志，0-立即规划并执行轨迹，不与后续轨迹连接；1-将当前轨迹与下一条轨迹一起规划，但不立即执行（阻塞模式下，即使发送成功也会立即返回）。 |
| `frame_type` | `bool` | 参考坐标系类型，0-工作坐标，1-工具坐标。 |
| `block` | `bool` | 阻塞设置。多线程模式下，0-非阻塞模式（发送指令后立即返回），1-阻塞模式（等待机械臂到达目标位置或规划失败后才返回）；单线程模式下，0-非阻塞模式（发送指令后立即返回），其他值-阻塞模式并设置超时时间（根据运动时间设置，单位为秒）。 |

**使用命令示例：**

先使用MoveJP：

```json
ros2 topic pub --once /rm_driver/movej_p_cmd rm_ros_interfaces/msg/Movejp "{
  pose: {
    position: {
      x: -0.317239,
      y: 0.120903,
      z: 0.255765
    },
    orientation: {
      x: -0.983404,
      y: -0.178432,
      z: 0.032271,
      w: 0.006129
    }
  },
  speed: 20,
  trajectory_connect: 0,
  block: true
}"
```

后使用MoveL\_offset：

```json
ros2 topic pub --once /rm_driver/movel_offset_cmd rm_ros_interfaces/msg/Moveloffset "{
  pose: {
    position: {
      x: -0.317239,
      y: 0.120903,
      z: 0.295765
    },
    orientation: {
      x: -0.983404,
      y: -0.178432,
      z: 0.032271,
      w: 0.006129
    }
  },
  speed: 20,
  r: 0,
  trajectory_connect: false,
  frame_type: false,
  block: false
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/movel_offset_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：运动成功；false：运动失败。driver终端返回错误码。 |

#### 笛卡尔空间圆弧运动Movec.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `pose_mid` | `geometry_msgs/Pose` | 机械臂中间位姿，x、y、z坐标(float类型，单位：m)+四元数。 |
| `pose_end` | `geometry_msgs/Pose` | 终点位姿，x、y、z坐标(float类型，单位：m)+四元数。 |
| `speed` | `uint8` | 速度百分比例系数，0~100。 |
| `trajectory_connect` | `uint8` | 可选参数，代表是否和下一条运动一起规划，   0代表立即规划，   1代表和下一条轨迹一起规划，当为1时，轨迹不会立即执行。 |
| `block` | `bool` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |
| `loop` | `uint16` | 旋转圈数。 |

**使用命令示例：** 先使用MoveJ\_P：

```json
ros2 topic pub --once /rm_driver/movej_p_cmd rm_ros_interfaces/msg/Movejp "pose: position: x: 0.274946 y: -0.058786 z: 0.299028 orientation: x: 0.7071 y: -0.7071 z: 0.0 w: 0.0 speed: 0 trajectory_connect: 0 block: true"
```

使用movec到达指定位置：

```json
ros2 topic pub --once /rm_driver/movec_cmd rm_ros_interfaces/msg/Movec "pose_mid: position: x: 0.324946 y: -0.008786 z: 0.299028 orientation: x: 0.7071 y: -0.7071 z: 0.0 w: 0.0 pose_end: position: x: 0.274946 y: 0.041214 z: 0.299028 orientation: x: 0.7071 y: -0.7071 z: 0.0 w: 0.0 speed: 20 trajectory_connect: 0 block: false loop: 0
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/movec_result
```

#### 关节角度CANFD透传Jointpos.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint` | `float32[6]` | 关节角度，单位：弧度。 |
| `follow` | `bool` | 跟随状态，true高跟随，false低跟随，不设置默认高跟随。 |
| `expand` | `float32` | 拓展关节，单位：弧度。 |
| `dof` | `uint8` | 机械臂自由度。 |

**使用命令示例：** 透传需要连续发送多个连续的点实现，单纯靠以下命令并不能实现功能，当前moveit2控制使用了角度透传的控制方式。

```json
ros2 topic pub /rm_driver/movej_canfd_cmd rm_ros_interfaces/msg/Jointpos "joint: [0, 0, 0, 0, 0, 0] follow: false expand: 0.0 dof: 6"
```

**返回命令示例：** 成功：无返回值；失败返回：driver终端返回错误码。

#### 自定义高跟随模式关节角度CANFD透传

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint` | `float32[6]` | 关节角度，单位：弧度。 |
| `follow` | `bool` | 跟随状态，true高跟随，false低跟随，不设置默认高跟随。 |
| `expand` | `float32` | 拓展关节，单位：弧度。 |
| `trajectory_mode` | `uint8` | 高跟随模式下，支持多种模式，0-完全透传模式、1-曲线拟合模式、2-滤波模式。 |
| `radio` | `uint8` | 设置曲线拟合模式下平滑系数（范围0-100）或者滤波模式下的滤波参数（范围0-1000），数值越大表示平滑效果越好。 |
| `dof` | `uint8` | 机械臂自由度。 |

**使用命令示例：** 透传需要连续发送多个连续的点实现，单纯靠以下命令并不能实现功能，当前moveit2控制使用了角度透传的控制方式。

```json
ros2 topic pub /rm_driver/movej_canfd_custom_cmd rm_ros_interfaces/msg/Jointposcustom "joint: [0, 0, 0, 0, 0, 0] follow: false expand: 0.0 trajectory_mode: 0 radio: 0 dof: 6"
```

**返回命令示例：** 成功：无返回值；失败返回：driver终端返回错误码。

#### 位姿CANFD透传Jointpos.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `pose` | `geometry_msgs/Pose` | 透传位姿，x、y、z坐标(float类型，单位：m)+四元数。 |
| `follow` | `bool` | 跟随状态，true高跟随，false低跟随，不设置默认高跟随。 |

**使用命令示例：** 需要是大量(10个以上)位置连续的点，单纯靠以下命令并不能实现功能，以2ms以上的周期持续发布。

```json
ros2 topic pub /rm_driver/movep_canfd_cmd rm_ros_interfaces/msg/Cartepos "pose: position: x: 0.0 y: 0.0 z: 0.0 orientation: x: 0.0 y: 0.0 z: 0.0 w: 1.0 follow: false"
```

**返回命令示例：** 成功：无返回值；失败返回：driver终端返回错误码。

#### 自定义高跟随模式位姿CANFD透传

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `pose` | `geometry_msgs/Pose` | 透传位姿，x、y、z坐标(float类型，单位：m)+四元数。 |
| `follow` | `bool` | 跟随状态，true高跟随，false低跟随，不设置默认高跟随。 |
| `trajectory_mode` | `uint8` | 高跟随模式下，支持多种模式，0-完全透传模式、1-曲线拟合模式、2-滤波模式。 |
| `radio` | `uint8` | 设置曲线拟合模式下平滑系数（范围0-100）或者滤波模式下的滤波参数（范围0-1000），数值越大表示平滑效果越好。 |

**使用命令示例：** 需要是大量(10个以上)位置连续的点，单纯靠以下命令并不能实现功能，以2ms以上的周期持续发布。

```json
ros2 topic pub /rm_driver/movep_canfd_custom_cmd rm_ros_interfaces/msg/Carteposcustom "pose: position: x: 0.0 y: 0.0 z: 0.0 orientation: x: 0.0 y: 0.0 z: 0.0 w: 1.0 follow: false trajectory_mode: 0 radio: 0"
```

**返回命令示例：** 成功：无返回值；失败返回：driver终端返回错误码。

#### 关节空间规划到目标位姿Movejp.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `pose` | `geometry_msgs/Pose` | 目标位姿，x、y、z坐标(float类型，单位：m)+四元数。 |
| `speed` | `uint8` | 速度百分比例系数，0~100。 |
| `block` | `bool` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/movej_p_cmd rm_ros_interfaces/msg/Movejp "pose: position: x: -0.317239 y: 0.120903 z: 0.255765 orientation: x: -0.983404 y: -0.178432 z: 0.032271 w: 0.006129 speed: 20 block: true"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/movej_p_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 轨迹急停std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/move_stop_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/move_stop_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 紧急停止

**参数说明：** `Stop.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `stop` | `bool` | 急停状态设置，true：急停，false：恢复。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/emergency_stop_cmd rm_ros_interfaces/Stop "state: true"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/emergency_stop_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

### 示教指令

#### 关节示教

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `num` | `uint8` | 示教关节的序号，1~7。 |
| `direction` | `uint8` | 示教方向，0-负方向，1-正方向。 |
| `speed` | `uint8` | 速度百分比例系数，0~100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_joint_teach_cmd rm_ros_interfaces/msg/Jointteach "num: 1 direction: 0 speed: 10"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_joint_teach_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 位置示教

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `type` | `uint8` | 坐标轴，0-X轴方向、1-Y轴方向、2-Z轴方向。 |
| `direction` | `uint8` | 示教方向，0-负方向，1-正方向。 |
| `speed` | `uint8` | 速度百分比例系数，0~100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_pos_teach_cmd rm_ros_interfaces/msg/Posteach "type: 2 direction: 0 speed: 10"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_pos_teach_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 姿态示教

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `type` | `uint8` | 旋转所绕坐标轴，0-RX轴方向、1-RY轴方向、2-RZ轴方向。 |
| `direction` | `uint8` | 示教方向，0-负方向，1-正方向。 |
| `speed` | `uint8` | 速度百分比例系数，0~100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_ort_teach_cmd rm_ros_interfaces/msg/Ortteach "type: 2 direction: 0 speed: 10"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_ort_teach_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 示教停止

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_stop_teach_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_stop_teach_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

### 轨迹列表

#### 查询轨迹列表

**参数说明：** `Gettrajectorylist.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int32` | 页码。 |
| `page_size` | `int32` | 每页大小。 |
| `vague_search` | `string` | 模糊搜索关键词。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_trajectory_file_list_cmd rm_ros_interfaces/msg/Gettrajectorylist "{
  page_num: 1,
  page_size: 10,
  vague_search: 's'
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_trajectory_file_list_result
```

**参数说明：** `Trajectorylist.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int32` | 页码。 |
| `page_size` | `int32` | 每页大小。 |
| `total_size` | `int32` | 列表长度。 |
| `vague_search` | `string` | 模糊搜索关键词。 |
| `tra_list` | `Trajectoryinfo[]` | 返回符合的轨迹列表。 |
| `state` | `bool` | 查询状态，成功返回 true，失败返回 false。 |

#### 开始运行指定轨迹

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `String` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_run_trajectory_cmd std_msgs/msg/String "data: 'sss'"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_run_trajectory_result
```

#### 删除指定文件

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `String` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/delete_trajectory_file_cmd std_msgs/msg/String "data: 'sss'"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/delete_trajectory_file_result
```

#### 保存轨迹文件

**参数说明：**

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `String` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/save_trajectory_file_cmd std_msgs/msg/String "data: 'test'"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/save_trajectory_file_result
```

#### 查询流程图编程状态

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `String` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_flowchart_program_run_state_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_flowchart_program_run_state_result
```

**参数说明：** `Flowchartrunstate.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `run_state` | `int` | 运行状态，0 - 未开始，1 - 运行中，2 - 暂停中。 |
| `id` | `int` | 当前使能的文件 ID。 |
| `name[32]` | `char` | 当前使能的文件名称（32 字符长度）。 |
| `plan_speed` | `int` | 当前使能的文件全局规划速度比例，1-100。 |
| `step_mode` | `int` | 单步模式，0 - 空，1 - 正常，2 - 单步。 |
| `modal_id[50]` | `char` | 运行到的流程图块的 ID（50 字符长度）。 |
| `state` | `bool` | 运行状态标识，正常运行返回 true，未正常运行返回 false。 |

### Modbus模式查询与配置

#### 设置控制器通讯端口RS485模式

**参数说明：** `RS485params.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int32` | 通讯模式，0-RS485串行通讯，1-modbus-RTU主站模式，2-modbus-RTU从站模式。 |
| `baudrate` | `int32` | 波特率，当前支持9600、19200、38400、57600、115200、230400、460800。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_controller_rs485_mode_cmd rm_ros_interfaces/msg/RS485params "{
  mode: 0,
  baudrate: 115200
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_controller_rs485_mode_result
```

#### 查询控制器RS485模式

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_controller_rs485_mode_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_controller_rs485_mode_result
```

**参数说明：** `RS485params.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int32` | 通讯模式，0 - 默认 RS485 串行通讯，1-modbus-RTU 主站模式，2-modbus-RTU 从站模式。 |
| `baudrate` | `int32` | 波特率（当前支持 9600、19200、38400、57600、115200、230400、460800）。 |
| `state` | `bool` | 查询状态，true - 查询成功，false - 查询失败。 |

#### 设置工具端RS485模式

**参数说明：** `RS485params.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int32` | 工具端RS485模式，0-设置为RTU主站，1-灵巧手模式，2-夹爪模式。 |
| `baudrate` | `int32` | 波特率，当前支持9600、115200、460800。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_tool_rs485_mode_cmd rm_ros_interfaces/msg/RS485params "{
  mode: 0,
  baudrate: 115200
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_tool_rs485_mode_result
```

#### 查询工具端RS485模式

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_tool_rs485_mode_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_tool_rs485_mode_result
```

**参数说明：** `RS485params.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | `int32` | 工具端 RS485 模式，0 - 设置为 RTU 主站，1 - 灵巧手模式，2 - 夹爪模式。 |
| `baudrate` | `int32` | 波特率（当前支持 9600、19200、38400、57600、115200、230400、460800）。 |
| `state` | `bool` | 查询状态，true：查询成功，false：查询失败。 |

#### 新增ModbusTCP主站

**参数说明：** `Modbustcpmasterinfo.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `master_name` | `string` | Modbus主站名称。 |
| `ip` | `string` | TCP主站IP地址。 |
| `port` | `int32` | TCP主站端口号。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/add_modbus_tcp_master_cmd rm_ros_interfaces/msg/Modbustcpmasterinfo "{
  master_name: '1',
  ip: '127.0.0.1',
  port: 502
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/add_modbus_tcp_master_result
```

#### 更新ModbusTCP主站

**参数说明：** `Modbustcpmasterupdata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `master_name` | `string` | Modbus原本的主站名称。 |
| `new_master_name` | `string` | Modbus新的主站名称。 |
| `ip` | `string` | TCP主站IP地址。 |
| `port` | `int32` | TCP主站端口号。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/update_modbus_tcp_master_cmd rm_ros_interfaces/msg/Modbustcpmasterupdata "{
  master_name: '1',
  new_master_name: '125',
  ip: '127.0.0.1',
  port: 502
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/update_modbus_tcp_master_result
```

#### 删除ModbusTCP主站

**参数说明：** `Mastername.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `master_name` | `string` | Modbus主站名称（通过Mastername.msg消息传递）。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/delete_modbus_tcp_master_cmd rm_ros_interfaces/msg/Mastername "
master_name: '321'
"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/delete_modbus_tcp_master_result
```

#### 查询指定Modbus主站

**参数说明：** `Mastername.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `master_name` | `string` | Modbus主站名称。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_modbus_tcp_master_cmd rm_ros_interfaces/msg/Mastername "master_name: '321'"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_modbus_tcp_master_result
```

**参数说明：** `Modbustcpmasterinfo.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `master_name` | `string` | Modbus 主站名称，最大长度 15 个字符，不超过 15 个字符。 |
| `ip` | `string` | TCP 主站 IP 地址。 |
| `port` | `int32` | TCP 主站端口号。 |
| `state` | `bool` | 查询状态信息，true：查询成功， false：查询失败。失败时 driver 终端返回错误码。 |

#### 查询Modbus主站列表

**参数说明：** `Getmodbustcpmasterlist.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `int32` | 页码。 |
| `page_size` | `int32` | 每页大小。 |
| `vague_search` | `string` | 模糊搜索关键词，若输入为空则返回所有主站列表。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_modbus_tcp_master_list_cmd rm_ros_interfaces/msg/Getmodbustcpmasterlist "{
  page_num: 1,
  page_size: 10,
  vague_search: '1'
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_modbus_tcp_master_list_result
```

**参数说明：** `Modbustcpmasterlist.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `page_num` | `uint8` | 页码。 |
| `page_size` | `uint8` | 每页大小。 |
| `total_size` | `uint8` | 列表长度。 |
| `vague_search` | `string` | 模糊搜索关键词。 |
| `master_list` | `Modbustcpmasterinfo[]` | 返回符合条件的 TCP 主站列表。 |
| `state` | `bool` | 查询状态，true：查询成功，false：查询失败。失败时 driver 终端返回错误码。 |

#### ModbusRTU协议读线圈

**参数说明：** `Modbusrtureadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `device` | `int32` | 外设设备地址。 |
| `type` | `int32` | 主机类型，0-控制器端Modbus主机；1-工具端Modbus主机。 |
| `num` | `int32` | 要读的数据的数量，数据长度不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_rtu_coils_cmd rm_ros_interfaces/msg/Modbusrtureadparams "{
  address: 0,
  device: 1,
  type: 0,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_rtu_coils_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true:读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

#### ModbusRTU协议写线圈

**参数说明：** `Modbusrtuwriteparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `device` | `int32` | 外设设备地址。 |
| `type` | `int32` | 主机类型，0-控制器端modbus主机；1-工具端modbus主机。 |
| `num` | `int32` | 要写的数据的数量，最大不超过100。 |
| `data` | `int32[]` | 要写的数据，数据长度与num对应。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/write_modbus_rtu_coils_cmd rm_ros_interfaces/msg/Modbusrtuwriteparams "{
  address: 0,
  device: 1,
  type: 0,
  num: 2,
  data: [1, 1]
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/write_modbus_rtu_coils_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：写入成功；false：写入失败。driver 终端返回错误码。 |

#### ModbusRTU协议读离散量输入

**参数说明：** `Modbusrtureadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `device` | `int32` | 外设设备地址。 |
| `type` | `int32` | 主机类型，0-控制器端modbus主机；1-工具端modbus主机。 |
| `num` | `int32` | 要读的数据的数量，数据长度不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_rtu_input_status_cmd rm_ros_interfaces/msg/Modbusrtureadparams "{
  address: 0,
  device: 0,
  type: 0,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_rtu_input_status_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true：读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

#### ModbusRTU协议读保持寄存器

**参数说明：** `Modbusrtureadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `device` | `int32` | 外设设备地址。 |
| `type` | `int32` | 主机类型，0-控制器端Modbus主机；1-工具端Modbus主机。 |
| `num` | `int32` | 要读的数据的数量，数据长度不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_rtu_holding_registers_cmd rm_ros_interfaces/msg/Modbusrtureadparams "{
  address: 0,
  device: 0,
  type: 0,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_rtu_holding_registers_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true：读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

#### ModbusRTU协议写保持寄存器

**参数说明：** `Modbusrtuwriteparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `device` | `int32` | 外设设备地址。 |
| `type` | `int32` | 主机类型，0-控制器端Modbus主机；1-工具端Modbus主机。 |
| `num` | `int32` | 要写的数据的数量，最大不超过100。 |
| `data` | `int32[]` | 要写的数据，数据长度与num对应。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/write_modbus_rtu_registers_cmd rm_ros_interfaces/msg/Modbusrtuwriteparams "{
  address: 0,
  device: 0,
  type: 0,
  num: 2,
  data: [1, 1]
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/write_modbus_rtu_registers_result
```

#### ModbusRTU协议读输入寄存器

**参数说明：** `Modbusrtureadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `device` | `int32` | 外设设备地址。 |
| `type` | `int32` | 主机类型，0-控制器端modbus主机；1-工具端modbus主机。 |
| `num` | `int32` | 要读的数据的数量，数据长度不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_rtu_input_registers_cmd rm_ros_interfaces/msg/Modbusrtureadparams "{
  address: 0,
  device: 0,
  type: 0,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_rtu_input_registers_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true：读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

#### ModbusTCP协议读线圈

**参数说明：** `Modbustcpreadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `master_name` | `string` | Modbus 主站名称，最大长度15个字符。 |
| `ip` | `string` | 主机连接的 IP 地址。 |
| `port` | `int32` | 主机连接的端口号。 |
| `num` | `int32` | 读取数据数量，最大不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_tcp_coils_cmd rm_ros_interfaces/msg/Modbustcpreadparams "{
  address: 0,
  master_name: '3',
  ip: '127.0.0.6',
  port: 502,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_tcp_coils_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true:读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

#### ModbusTCP协议写线圈

**参数说明：** `Modbustcpwriteparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `master_name` | `string` | Modbus 主站名称，最大长度15个字符。 |
| `ip` | `string` | 主机连接的 IP 地址。 |
| `port` | `int32` | 主机连接的端口号。 |
| `num` | `int32` | 写入数据数量，最大不超过100。 |
| `data` | `int32[]` | 写入的数据，数据长度与num对应。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/write_modbus_tcp_coils_cmd rm_ros_interfaces/msg/Modbustcpwriteparams "{
  address: 0,
  master_name: '3',
  ip: '127.0.0.6',
  port: 502,
  num: 2,
  data: [1, 1]
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/write_modbus_tcp_coils_result
```

#### ModbusTCP协议读离散量输入

**参数说明：** `Modbustcpreadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `master_name` | `string` | Modbus 主站名称，最大长度15个字符。 |
| `ip` | `string` | 主机连接的 IP 地址。 |
| `port` | `int32` | 主机连接的端口号。 |
| `num` | `int32` | 读取数据数量，最大不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_tcp_input_status_cmd rm_ros_interfaces/msg/Modbustcpreadparams "{
  address: 0,
  master_name: '3',
  ip: '127.0.0.6',
  port: 502,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_tcp_input_status_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true：读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

#### ModbusTCP协议读保持寄存器

**参数说明：** `Modbustcpreadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `master_name` | `string` | Modbus 主站名称，最大长度15个字符。 |
| `ip` | `string` | 主机连接的 IP 地址。 |
| `port` | `int32` | 主机连接的端口号。 |
| `num` | `int32` | 读取数据数量，最大不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_tcp_holding_registers_cmd rm_ros_interfaces/msg/Modbustcpreadparams "{
  address: 0,
  master_name: '3',
  ip: '127.0.0.6',
  port: 502,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_tcp_holding_registers_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true：读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

#### ModbusTCP协议写保持寄存器

**参数说明：** `Modbustcpwriteparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `master_name` | `string` | Modbus 主站名称，最大长度15个字符。 |
| `ip` | `string` | 主机连接的 IP 地址。 |
| `port` | `int32` | 主机连接的端口号。 |
| `num` | `int32` | 写入数据数量，最大不超过100。 |
| `data` | `int32[]` | 写入的数据，数据长度与num对应。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/write_modbus_tcp_registers_cmd rm_ros_interfaces/msg/Modbustcpwriteparams "{
  address: 0,
  master_name: '3',
  ip: '127.0.0.6',
  port: 502,
  num: 2,
  data: [1, 1]
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/write_modbus_tcp_registers_result
```

#### ModbusTCP协议读输入寄存器

**参数说明：** `Modbustcpreadparams.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `address` | `int32` | 数据起始地址。 |
| `master_name` | `string` | Modbus 主站名称，最大长度15个字符。 |
| `ip` | `string` | 主机连接的 IP 地址。 |
| `port` | `int32` | 主机连接的端口号。 |
| `num` | `int32` | 读取数据数量，最大不超过100。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/read_modbus_tcp_input_registers_cmd rm_ros_interfaces/msg/Modbustcpreadparams "{
  address: 0,
  master_name: '3',
  ip: '127.0.0.6',
  port: 502,
  num: 1
}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/read_modbus_tcp_input_registers_result
```

**参数说明：** `Modbusreaddata.msg`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `read_data` | `int32[]` | 读取到的 modbus 数据。 |
| `state` | `bool` | 反馈查询状态信息，true：读取成功，false：读取失败。失败时 driver 终端返回错误码。 |

### 末端工具IO配置

#### 设置工具端电源输出std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `data` | `uint16` | 电源输出类型，0：0V，2：12V，3：24V。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_tool_voltage_cmd std_msgs/msg/UInt16 "data: 0"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_tool_voltage_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

### 末端手爪控制

睿尔曼机械臂末端支持各种常见夹爪，系统配置了因时的EG2-4C2手爪，为了便于用户操作手爪，机械臂控制器对用户适配了手爪的ROS控制。

#### 设置夹爪力控夹取Gripperpick.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `speed` | `uint16` | 1～1000，代表手爪开合速度，无量纲。 |
| `force` | `uint16` | 1～1000，代表手爪夹持力，最大1.5kg。 |
| `block` | `uint16` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |
| `timeout` | `uint16` | 阻塞模式下超时时间设置，单位：秒。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_gripper_pick_cmd rm_ros_interfaces/msg/Gripperpick "speed: 200 force: 200 block: true timeout: 10"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_gripper_pick_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 设置夹爪持续力控夹取Gripperpick.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `speed` | `uint16` | 1～1000，代表手爪开合速度，无量纲。 |
| `force` | `uint16` | 1～1000，代表手爪夹持力，最大1.5kg。 |
| `block` | `bool` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |
| `timeout` | `uint16` | 阻塞模式下超时时间设置，单位：秒。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_gripper_pick_on_cmd rm_ros_interfaces/msg/Gripperpick "speed: 200 force: 200 block: true timeout: 10"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_gripper_pick_on_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 夹爪到达指定位置Gripperset.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `position` | `uint16` | 手爪目标位置，范围：1～1000，代表手爪开口度：0～70mm。 |
| `block` | `bool` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |
| `timeout` | `uint16` | 阻塞模式下超时时间设置，单位：秒。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_gripper_position_cmd rm_ros_interfaces/msg/Gripperset "position: 500 block: true timeout: 10"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_gripper_position_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

### 拖动示教及轨迹复现

#### 设置力位混合控制Setforceposition.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `sensor` | `uint8` | 0-一维力；1-六维力。 |
| `mode` | `uint8` | 0-基坐标系力控；1-工具坐标系力控。 |
| `direction` | `uint8` | 力控方向；0-沿X轴；1-沿Y轴；2-沿Z轴；3-沿RX姿态方向；4-沿RY姿态方向；5-沿RZ姿态方向。 |
| `n` | `int16` | 力的大小，单位N，精确到0.1N。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_force_postion_cmd rm_ros_interfaces/msg/Setforceposition "sensor: 1 mode: 0 direction: 2 n: 3"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_force_postion_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 结束力位混合控制std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/stop_force_postion_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/clear_force_data_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

### 末端六维力传感器的使用

睿尔曼RM-65F机械臂末端配备集成式六维力传感器，无需外部走线，用户可直接通过ROS话题对六维力进行操作。

#### 查询六维力数据

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub rm_driver/get_force_data_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

成功返回对应坐标系六维力数据。

- 原始数据：
	```json
	ros2 topic echo /rm_driver/get_force_data_result
	```
- 系统受力数据：
	```json
	ros2 topic echo /rm_driver/get_zero_force_data_result
	```
- 工作坐标系受力数据：
	```json
	ros2 topic echo /rm_driver/get_work_force_data_result
	```
- 工具坐标系受力数据：
	```json
	ros2 topic echo /rm_driver/get_tool_force_data_result
	```

#### 清空六维力数据std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/clear_force_data_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/clear_force_data_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

### 末端五指灵巧手控制

睿尔曼RM-65机械臂末端配备了五指灵巧手，可通过ROS对灵巧手进行设置。

#### 设置灵巧手角度跟随

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `hand_angle` | `int16[6]` | 手指角度数组，范围（根据实际设备属性，以下为因时参考）：0~1000。另外，-1 代表该自由度不执行任何操作，保持当前状态。 |
| `block` | `bool` | 是否为阻塞模式，true:阻塞，false:非阻塞。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_hand_follow_angle_cmd rm_ros_interfaces/msg/Handangle "hand_angle: - 0 - 0 - 0 - 0 - 0 - 0 block: true"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_hand_follow_angle_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 设置灵巧手姿态跟随

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `hand_angle` | `int16[6]` | 手指姿态数组，范围（根据实际设备属性，以下为因时参考）：0~1000。另外，-1 代表该自由度不执行任何操作，保持当前状态。 |
| `block` | `bool` | 是否为阻塞模式，true:阻塞，false:非阻塞。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_hand_follow_pos_cmd rm_ros_interfaces/msg/Handangle "hand_angle: - 0 - 0 - 0 - 0 - 0 - 0 block: true"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_hand_follow_pos_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

### 升降机构

睿尔曼机械臂控制器可集成自主研发升降机构，本接口可以用于升降机构的控制。

#### 升降机构速度开环控制Liftspeed.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `speed` | `int16` | 速度百分比，-100~100：   1\. speed<0：升降机构向下运动；   2\. speed>0：升降机构向上运动；   3\. speed=0：升降机构停止运动。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_lift_speed_cmd rm_ros_interfaces/msg/Liftspeed "speed: 100"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_lift_speed_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 升降机构位置闭环控制Liftheight.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `height` | `int16` | 目标高度，单位 mm，范围：0-2600。 |
| `speed` | `int16` | 速度百分比，1-100。 |
| `block` | `bool` | 是否为阻塞模式，true：阻塞，false：非阻塞。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_lift_height_cmd rm_ros_interfaces/msg/Liftheight "height: 0 speed: 10 block: true"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_lift_height_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 获取升降机构状态Liftstate.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `height` | `int16` | 目标高度，单位 mm。 |
| `current` | `int16` | 当前电流。 |
| `err_flag` | `uint16` | 驱动错误代码。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/get_lift_state_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：** 成功返回：升降机构当前状态；失败返回：driver终端返回错误码.

```json
ros2 topic echo /rm_driver/get_lift_state_result
```

### 末端生态协议

末端生态协议支持下的末端设备基础信息与实时信息的读取。

#### 设置末端生态协议模式

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `data` | `int32` | 0-禁用协议；   9600-开启协议（波特率9600）；   115200-开启协议（波特率115200）；   256000-开启协议（波特率256000）；   460800-开启协议（波特率460800）。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_rm_plus_mode_cmd std_msgs/msg/Int32 "data: 0"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_rm_plus_mode_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 查询末端生态协议模式

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/get_rm_plus_mode_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_rm_plus_mode_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `int32` | 0-禁用协议；   9600-开启协议（波特率9600）；   115200-开启协议（波特率115200）；   256000-开启协议（波特率256000）；   460800-开启协议（波特率460800）。 |

#### 设置触觉传感器模式

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `data` | `int32` | 0-关闭触觉传感器；   1-打开触觉传感器（返回处理后数据）；   2-打开触觉传感器（返回原始数据）。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/set_rm_plus_touch_cmd std_msgs::msg::Int32 "data: 0"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_rm_plus_touch_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 获取触觉传感器模式

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/get_rm_plus_touch_cmd std_msgs::msg::Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_rm_plus_touch_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `int32` | 0-关闭触觉传感器；   1-打开触觉传感器（返回处理后数据）；   2-打开触觉传感器（返回原始数据）。 |

### 透传力位混合控制补偿

针对睿尔曼六维力版本的机械臂，用户除了可直接使用示教器调用底层的力位混合控制模块外，还可以将自定义的轨迹以周期性透传的形式结合底层的力位混合控制算法进行补偿。 在进行力的操作之前，如果未进行力数据标定，可使用清空六维力数据接口对零位进行标定。

#### 开启透传力位混合控制补偿模式std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | 开启透传力位混合控制补偿模式。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/start_force_position_move_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/start_force_position_move_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 关闭透传力位混合控制补偿模式std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | 关闭透传力位混合控制补偿模式。 |

**使用命令示例：**

```json
ros2 topic pub /rm_driver/stop_force_position_move_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/stop_force_position_move_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 透传力位混合补偿-关节Forcepositionmovejoint.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint` | `float32[6]` | 目标关节弧度。 |
| `sensor` | `uint8` | 所使用传感器类型，0-一维力，1-六维力。 |
| `mode` | `uint8` | 模式，0-沿基坐标系，1-沿工具端坐标系。 |
| `dir` | `int16` | 力控方向，0~5分别代表X/Y/Z/Rx/Ry/Rz，其中一维力类型时默认方向为Z方向。 |
| `force` | `float32` | 力的大小 单位N。 |
| `follow` | `bool` | 是否高跟随，true：高跟随，false：低跟随。 |
| `dof` | `uint8` | 机械臂自由度。 |

**使用命令示例：** 需要是大量(10个以上)位置连续的点，以2ms以上的周期持续发布。

```json
ros2 topic pub /rm_driver/force_position_move_joint_cmd rm_ros_interfaces/msg/Forcepositionmovejoint "joint: [0, 0, 0, 0, 0, 0] sensor: 0 mode: 0 dir: 0 force: 0.0 follow: false dof: 6"
```

**返回命令示例：** 成功无返回；失败返回：false，driver终端返回错误码。

#### 透传力位混合补偿-位姿Forcepositionmovepose.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `pose` | `float` | 目标位姿，x、y、z坐标(单位：m)+四元数。 |
| `sensor` | `uint8` | 所使用传感器类型，0-一维力，1-六维力。 |
| `mode` | `uint8` | 模式，0-沿基坐标系，1-沿工具端坐标系。 |
| `dir` | `int16` | 力控方向，0~5分别代表X/Y/Z/Rx/Ry/Rz，其中一维力类型时默认方向为Z方向。 |
| `force` | `float32` | 力的大小 单位N。 |
| `follow` | `bool` | 是否高跟随，true：高跟随，false：低跟随。 |

**使用命令示例：** 需要是大量(10个以上)位置连续 的点，以2ms以上的周期持续发布。

```json
ros2 topic pub /rm_driver/force_position_move_pose_cmd rm_ros_interfaces/msg/Forcepositionmovepose "pose: position: x: 0.0 y: 0.0 z: 0.0 orientation: x: 0.0 y: 0.0 z: 0.0 w: 1.0 sensor: 0 mode: 0 dir: 0 force: 0 follow: false"
```

**返回命令示例：** 成功无返回；失败返回：false，driver终端返回错误码。

### 机械臂状态主动上报

#### 设置UDP机械臂状态主动上报配置Setrealtimepush.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `cycle` | `uint16` | 设置广播周期，单位为5ms(默认1即1\*5=5ms，200Hz)。 |
| `port` | `uint16` | 设置广播的端口号(默认8089)。 |
| `force_coordinate` | `uint16` | 设置系统外受力数据的坐标系(仅带有力传感器的机械臂支持)。 |
| `ip` | `string` | 设置自定义的上报目标IP 地址(默认192.168.1.10)。 |
| `hand_enable` | `bool` | 设置是否使能灵巧手状态上报，true使能，false不使能。 |
| `aloha_state_enable` | `bool` | 设置是否使能aloha主臂状态上报，true使能，false不使能。 |
| `arm_current_status_enable` | `bool` | 设置是否使能机械臂状态上报，true使能，false不使能。 |
| `expand_state_enable` | `bool` | 是否使能扩展关节相关数据上报，true使能，false不使能。 |
| `joint_speed_enable` | `bool` | 设置是否使能关节速度上报，true使能，false不使能。 |
| `lift_state_enable` | `bool` | 设置是否使能升降关节数据上报，true使能，false不使能。 |
| `plus_base_enable` | `bool` | 末端设备基础信息上报，true使能，false不使能。 |
| `plus_state_enable` | `bool` | 末端设备实时信息上报，true使能，false不使能。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/set_realtime_push_cmd rm_ros_interfaces/msg/Setrealtimepush "cycle: 1 port: 8089 force_coordinate: 0 ip: '192.168.1.10' hand_enable: false aloha_state_enable: false arm_current_status_enable: false expand_state_enable: false joint_speed_enable: false lift_state_enable: false plus_base_enable: false plus_state_enable: false"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/set_realtime_push_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `bool` | true：设置成功；false：设置失败。driver终端返回错误码。 |

#### 查询UDP机械臂状态主动上报配置Getrealtimepush.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `std_msgs` | `Empty` | ROS自带msg。 |

**使用命令示例：**

```json
ros2 topic pub --once /rm_driver/get_realtime_push_cmd std_msgs/msg/Empty "{}"
```

**返回命令示例：**

```json
ros2 topic echo /rm_driver/get_realtime_push_result
```

**参数说明：**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `cycle` | `uint16` | 设置广播周期，单位为5ms(默认1即1\*5=5ms，200Hz)。 |
| `port` | `uint16` | 设置广播的端口号(默认8089)。 |
| `force_coordinate` | `uint16` | 设置系统外受力数据的坐标系(仅带有力传感器的机械臂支持)。 |
| `ip` | `string` | 设置自定义的上报目标IP 地址(默认192.168.1.10)。 |
| `hand_enable` | `bool` | 设置是否使能灵巧手状态上报，true使能，false不使能。 |
| `aloha_state_enable` | `bool` | 设置是否使能aloha主臂状态上报，true使能，false不使能。 |
| `arm_current_status_enable` | `bool` | 设置是否使能机械臂状态上报，true使能，false不使能。 |
| `expand_state_enable` | `bool` | 是否使能扩展关节相关数据上报，true使能，false不使能。 |
| `joint_speed_enable` | `bool` | 设置是否使能关节速度上报，true使能，false不使能。 |
| `lift_state_enable` | `bool` | 设置是否使能升降关节数据上报，true使能，false不使能。 |
| `plus_base_enable` | `bool` | 末端设备基础信息上报，true使能，false不使能。 |
| `plus_state_enable` | `bool` | 末端设备实时信息上报，true使能，false不使能。 |

#### UDP机械臂状态主动上报

##### 六维力Sixforce.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `force_fx` | `float32` | 沿x轴方向受力大小。 |
| `force_fy` | `float32` | 沿y轴方向受力大小。 |
| `force_fz` | `float32` | 沿z轴方向受力大小。 |
| `force_mx` | `float32` | 沿x轴方向转动受力大小。 |
| `force_my` | `float32` | 沿y轴方向转动受力大小。 |
| `force_mz` | `float32` | 沿y轴方向转动受力大小。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_six_force
```

##### 一维力Oneforce.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `force_fx` | `float32` | 沿x轴方向受力大小。 |
| `force_fy` | `float32` | 沿y轴方向受力大小。 |
| `force_fz` | `float32` | 沿z轴方向受力大小。(仅该数值有效) |
| `force_mx` | `float32` | 沿x轴方向转动受力大小。 |
| `force_my` | `float32` | 沿y轴方向转动受力大小。 |
| `force_mz` | `float32` | 沿y轴方向转动受力大小。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_one_force
```

##### 机械臂错误std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `data` | `uint16` | 机械臂报错信息。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_arm_err
```

##### 系统错误std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `data` | `uint16` | 系统报错信息。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_sys_err
```

##### 关节错误Jointerrorcode.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_error` | `uint16` | 每个关节报错信息。 |
| `dof` | `uint8` | 机械臂自由度信息。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_joint_error_code
```

##### 机械臂弧度数据sensor\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `sec` | `int32` | 时间信息，秒。 |
| `nanosec` | `uint32` | 时间信息，纳秒。 |
| `frame_id` | `string` | 坐标系名称。 |
| `name` | `string` | 关节名称。 |
| `position` | `float64` | 关节弧度信息。 |
| `elocity` | `float64` | 关节速度信息。 |
| `effort` | `float64` | 关节受力信息。 |

**使用命令示例：**

```json
ros2 topic echo /joint_states
```

##### 位姿信息geometry\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `Point position` | `float64` | 机械臂当前坐标信息：x，y，z。 |
| `Quaternion orientation` | `float64` | 机械臂当前姿态信息：x，y，z，w。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_arm_position
```

##### 六维力传感器外受力数据Sixforce.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `force_fx` | `float32` | 当前传感器沿x轴方向受外力大小。 |
| `force_fy` | `float32` | 当前传感器沿y轴方向受外力大小。 |
| `force_fz` | `float32` | 当前传感器沿z轴方向受外力大小。 |
| `force_mx` | `float32` | 当前传感器沿x轴方向转动受外力大小。 |
| `force_my` | `float32` | 当前传感器沿y轴方向转动受外力大小。 |
| `force_mz` | `float32` | 当前传感器沿z轴方向转动受外力大小。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_six_zero_force
```

##### 一维力传感器系统外受力数据Oneforce.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `force_fx` | `float32` | 当前传感器沿x轴方向受外力大小。 |
| `force_fy` | `float32` | 当前传感器沿y轴方向受外力大小。 |
| `force_fz` | `float32` | 当前传感器沿z轴方向受外力大小。（仅该数据有效） |
| `force_mx` | `float32` | 当前传感器沿x轴方向转动受外力大小。 |
| `force_my` | `float32` | 当前传感器沿y轴方向转动受外力大小。 |
| `force_mz` | `float32` | 当前传感器沿z轴方向转动受外力大小。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_one_zero_force
```

##### 系统外受力数据参考坐标系std\_msgs

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `data` | `uint16` | 系统外受力数据的坐标系，0 为传感器坐标系 1 为当前工作坐标系 2 为当前工具坐标系。该数据会影响一维力和六维力传感器系统外受力数据的参考坐标系。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_arm_coordinate
```

##### 灵巧手力当前状态Handstatus.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `hand_angle` | `uint16[6]` | 手指角度数组，范围：0~2000。 |
| `hand_pos` | `uint16[6]` | 手指位置数组，范围：0~1000。 |
| `hand_state` | `uint16[6]` | 手指状态，0正在松开，1正在抓取，2位置到位停止，3力到位停止，5电流保护停止，6电缸堵转停止，7电缸故障停止。 |
| `hand_force` | `uint16[6]` | 灵巧手自由度电流，单位mN。 |
| `hand_err` | `uint16[6]` | 灵巧手系统错误，1表示有错误，0表示无错误。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_hand_status
```

##### 机械臂当前状态Armcurrentstatus.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `arm_current_status` | `uint16` | 机械臂状态：   0 - RM\_IDLE\_E // 使能但空闲状态   1 - RM\_MOVE\_L\_E // move L运动中状态   2 - RM\_MOVE\_J\_E // move J运动中状态   3 - RM\_MOVE\_C\_E // move C运动中状态   4 - RM\_MOVE\_S\_E // move S运动中状态   5 - RM\_MOVE\_THROUGH\_JOINT\_E // 角度透传状态   6 - RM\_MOVE\_THROUGH\_POSE\_E // 位姿透传状态   7 - RM\_MOVE\_THROUGH\_FORCE\_POSE\_E // 力控透传状态   8 - RM\_MOVE\_THROUGH\_CURRENT\_E // 电流环透传状态   9 - RM\_STOP\_E // 急停状态   10 - RM\_SLOW\_STOP\_E // 缓停状态   11 - RM\_PAUSE\_E // 暂停状态   12 - RM\_CURRENT\_DRAG\_E // 电流环拖动状态   13 - RM\_SENSOR\_DRAG\_E // 六维力拖动状态   14 - RM\_TECH\_DEMONSTRATION\_E // 示教状态 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_arm_current_status
```

##### 当前关节电流Jointcurrent.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_current` | `float32` | 当前关节电流，精度 0.001mA。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_joint_current
```

##### 当前关节使能状态Jointenflag.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_en_flag` | `bool` | 当前关节使能状态，1为上使能，0为掉使能。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_joint_en_flag
```

##### 机械臂欧拉角位姿Jointposeeuler.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `euler` | `float32[3]` | 当前路点姿态欧拉角，精度 0.001rad。 |
| `position` | `float32[3]` | 当前路点位置，精度 0.000001M。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_joint_pose_euler
```

##### 当前关节速度Jointspeed.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_speed` | `float32` | 当前关节速度，精度0.02RPM。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_joint_speed
```

##### 当前关节温度Jointtemperature.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_temperature` | `float32` | 当前关节温度，精度 0.001℃。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_joint_temperature
```

##### 当前关节电压Jointvoltage.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `joint_voltage` | `float32` | 当前关节电压，精度 0.001V。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_joint_voltage
```

##### 查询末端生态基础信息Rmplusbase.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `manu` | `string` | 设备厂家。 |
| `type` | `int8` | 设备类型 1：两指夹爪 2：五指灵巧手 3：三指夹爪。 |
| `hv` | `string` | 硬件版本。 |
| `sv` | `string` | 软件版本。 |
| `bv` | `string` | boot版本。 |
| `id` | `int32` | 设备ID。 |
| `dof` | `int8` | 自由度。 |
| `check` | `int8` | 自检开关。 |
| `bee` | `int8` | 蜂鸣器开关。 |
| `force` | `bool` | 力控支持。 |
| `touch` | `bool` | 触觉支持。 |
| `touch_num` | `int8` | 触觉个数。 |
| `touch_sw` | `int8` | 触觉开关。 |
| `hand` | `int8` | 手方向，1：左手，2： 右手。 |
| `pos_up` | `int32[12]` | 位置上限,单位：无量纲。 |
| `pos_low` | `int32[12]` | 位置下限,单位：无量纲。 |
| `angle_up` | `int32[12]` | 角度上限,单位：0.01度。 |
| `angle_low` | `int32[12]` | 角度下限,单位：0.01度。 |
| `speed_up` | `int32[12]` | 速度上限,单位：无量纲。 |
| `speed_low` | `int32[12]` | 速度下限,单位：无量纲。 |
| `force_up` | `int32[12]` | 力上限,单位：0.001N。 |
| `force_low` | `int32[12]` | 力下限,单位：0.001N。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_rm_plus_base
```

##### 查询末端生态实时状态Rmplusstate.msg

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `sys_state` | `int32` | 系统状态。 |
| `dof_state` | `int32[12]` | 各自由度当前状态。 |
| `dof_err` | `int32[12]` | 各自由度错误信息。 |
| `pos` | `int32[12]` | 各自由度当前位置。 |
| `speed` | `int32[12]` | 各自由度当前速度。 |
| `angle` | `int32[12]` | 各自由度当前角度。 |
| `current` | `int32[12]` | 各自由度当前电流。 |
| `normal_force` | `int32[18]` | 自由度触觉三维力的法向力。 |
| `tangential_force` | `int32[18]` | 自由度触觉三维力的切向力。 |
| `tangential_force_dir` | `int32[18]` | 自由度触觉三维力的切向力方向。 |
| `tsa` | `int32[12]` | 自由度触觉自接近。 |
| `tma` | `int32[12]` | 自由度触觉互接近。 |
| `touch_data` | `int32[18]` | 触觉传感器原始数据。 |
| `force` | `int32[12]` | 自由度力矩。 |

**使用命令示例：**

```json
ros2 topic echo /rm_driver/udp_rm_plus_state
```