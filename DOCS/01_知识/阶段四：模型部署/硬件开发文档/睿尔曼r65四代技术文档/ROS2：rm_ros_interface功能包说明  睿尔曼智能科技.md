---
title: "ROS2：rm_ros_interface功能包说明 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/ros2/rosInterfaces/"
author:
published: 2025-09-18
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## rm\_ros\_interface功能包说明

rm\_ros\_interface功能包的主要作用为RM机械臂在ROS2的框架下运行提供必要的消息文件，没有可执行的使用命令。  
这里将从以下三个方面整体介绍该功能包：

- 1.功能包使用：了解该功能包的使用。
- 2.功能包架构说明：熟悉功能包中的文件构成及作用。
- 3.功能包话题说明：熟悉功能包相关的话题，方便开发和使用。

代码链接： [https://github.com/RealManRobot/ros2\_rm\_robot/tree/humble/rm\_ros\_interfaces](https://github.com/RealManRobot/ros2_rm_robot/tree/humble/rm_ros_interfaces)

## rm\_ros\_interface功能包架构文件总览

```
当前rm_ros_interface功能包的文件构成如下。
├── CMakeLists.txt                                    #编译规则文件
├── msg
│   ├── Armcurrentstatus.msg
│   ├── Armoriginalstate.msg
│   ├── Armsoftversion.msg
│   ├── Armsoftversionv3.msg
│   ├── Armsoftversionv4.msg
│   ├── Armstate.msg
│   ├── Carteposcustom.msg
│   ├── Cartepos.msg
│   ├── Flowchartrunstate.msg
│   ├── Forcepositionmovejoint.msg
│   ├── Forcepositionmovepose.msg
│   ├── Force_Position_State.msg
│   ├── Getallframe.msg
│   ├── GetArmState_Command.msg
│   ├── Getmodbustcpmasterlist.msg
│   ├── Gettrajectorylist.msg
│   ├── Gripperpick.msg
│   ├── Gripperset.msg
│   ├── Handangle.msg
│   ├── Handforce.msg
│   ├── Handposture.msg
│   ├── Handseq.msg
│   ├── Handspeed.msg
│   ├── Handstatus.msg
│   ├── Jointcurrent.msg
│   ├── Jointenflag.msg
│   ├── Jointerrclear.msg
│   ├── Jointerrorcode.msg
│   ├── Jointposcustom.msg
│   ├── Jointposeeuler.msg
│   ├── Jointpos.msg
│   ├── Jointspeed.msg
│   ├── Jointteach.msg
│   ├── Jointtemperature.msg
│   ├── Jointversion.msg
│   ├── Jointvoltage.msg
│   ├── Liftheight.msg
│   ├── Liftspeed.msg
│   ├── Liftstate.msg
│   ├── Mastername.msg
│   ├── Modbusreaddata.msg
│   ├── Modbusrtureadparams.msg
│   ├── Modbusrtuwriteparams.msg
│   ├── Modbustcpmasterinfo.msg
│   ├── Modbustcpmasterlist.msg
│   ├── Modbustcpmasterupdata.msg
│   ├── Modbustcpreadparams.msg
│   ├── Modbustcpwriteparams.msg
│   ├── Movec.msg
│   ├── Movej.msg
│   ├── Movejp.msg
│   ├── Movel.msg
│   ├── Moveloffset.msg
│   ├── Ortteach.msg
│   ├── Posteach.msg
│   ├── Programrunstate.msg
│   ├── Rmerr.msg
│   ├── Rmplusbase.msg
│   ├── Rmplusstate.msg
│   ├── Rmversion.msg
│   ├── RobotInfo.msg
│   ├── RS485params.msg
│   ├── Sendproject.msg
│   ├── Setforceposition.msg
│   ├── Setrealtimepush.msg
│   ├── Sixforce.msg
│   ├── Softwarebuildinfo.msg
│   ├── Stop.msg
│   ├── Toolsoftwareversionv4.msg
│   ├── Trajectoryinfo.msg
│   └── Trajectorylist.msg
├── package.xml
├── README_CN.md
└── README.md
```

## rm\_ros\_interface消息说明

### 关节错误代码Jointerrorcode.msg

```
uint16[] joint_error  
uint8 dof
```

**msg成员：**

- `joint_error` ：每个关节报错信息。
- `dof` ：机械臂自由度信息。

### 清除关节错误代码Jointerrclear.msg

```
uint8 joint_num
```

**msg成员：**

- `joint_num` ：对应关节序号，从基座到机械臂夹爪端，序号依次为1-6或1-7。

### 所有坐标系名称Getallframe.msg

```
string[10] frame_name
```

**msg成员：**

- `frame_name` ：返回的工作坐标系的名称数组。

### 关节运动Movej.msg

```
float32[] joint  
uint8 speed  
bool block  
uint8 trajectory_connect  
uint8 dof
```

**msg成员：**

- `joint` ：关节角度，float类型，单位：弧度。
- `speed` ：速度百分比例系数，0-100。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。
- `trajectory_connect` ：0 代表立即规划，1 代表和下一条轨迹一起规划，当为 1 时，轨迹不会立即执行。
- `dof` ：机械臂自由度信息。

### 直线运动Movel.msg

```
geometry_msgs/Pose pose  
uint8 speed  
uint8 trajectory_connect  
bool block
```

**msg成员：**

- `pose` ：机械臂位姿，geometry\_msgs/Pose类型，x、y、z坐标（float类型，单位：m）+四元数（float类型）。
- `speed` ：速度百分比例系数，0-100。
- `trajectory_connect` ：0 代表立即规划，1 代表和下一条轨迹一起规划，当为 1 时，轨迹不会立即执行
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。

### 圆弧运动Movec.msg

```
geometry_msgs/Pose pose_mid  
geometry_msgs/Pose pose_end  
uint8 speed  
uint8 trajectory_connect  
bool block  
uint8 loop
```

**msg成员：**

- `pose_mid` ：中间位姿，geometry\_msgs/Pose类型，x、y、z坐标（float类型，单位：m）+四元数。
- `pose_end` ：目标位姿，geometry\_msgs/Pose类型，x、y、z坐标（float类型，单位：m）+四元数。
- `speed` ：速度百分比例系数，0-100。
- `trajectory_connect` ：0 代表立即规划，1 代表和下一条轨迹一起规划，当为 1 时，轨迹不会立即执行
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。
- `loop` ：循环次数。

### 关节空间规划到目标位姿Movejp.msg

```
geometry_msgs/Pose pose  
uint8 speed  
uint8 trajectory_connect
bool block
```

**msg成员：**

- `pose` ：目标位姿，geometry\_msgs/Pose类型，x、y、z坐标（float类型，单位：m）+四元数。
- `speed` ：速度百分比例系数，0-100。
- `trajectory_connect` ：0 代表立即规划，1 代表和下一条轨迹一起规划，当为 1 时，轨迹不会立即执行
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。

### 关节示教Jointteach.msg

```
uint8 num
uint8 direction
uint8 speed
```

**msg成员：**

- `num` ：示教关节的序号，1~7。
- `direction` ：示教方向，0-负方向，1-正方向。
- `speed` ：速度比例1~100，即规划速度和加速度占关节最大线转速和加速度的百分比。

### 位置示教Posteach.msg

```
uint8 type
uint8 direction
uint8 speed
```

**msg成员：**

- `type` ：坐标轴，0：X轴方向，1：Y轴方向，2：Z轴方向。
- `direction` ：示教方向，0-负方向，1-正方向。
- `speed` ：速度比例1~100，即规划速度和加速度占关节最大线转速和加速度的百分比。

### 姿态示教Ortteach.msg

```
uint8 type
uint8 direction
uint8 speed
```

**msg成员：**

- `type` ：旋转所绕坐标轴，0：RX轴方向，1：RY轴方向，2：RZ轴方向。
- `direction` ：示教方向，0-负方向，1-正方向。
- `speed` ：速度比例1~100，即规划速度和加速度占关节最大线转速和加速度的百分比。

### 角度透传Jointpos.msg

```
float32[] joint  
bool follow  
float32 expand  
uint8 dof
```

**msg成员：**

- `joint` ：关节角度，float类型，单位：弧度。
- `follow` ：跟随状态，bool类型，true高跟随，false低跟随，不设置默认高跟随。
- `expand` ：拓展关节，float类型，单位：弧度。
- `dof` ：机械臂自由度信息。

### 位姿透传Cartepos.msg

```
geometry_msgs/Pose pose  
bool follow
```

**msg成员：**

- `pose` ：机械臂位姿，geometry\_msgs/Pose类型，x、y、z坐标（float类型，单位：m）+四元数。
- `follow` ：跟随状态，bool类型，true高跟随，false低跟随，不设置默认高跟随。

### 机械臂当前状态-角度和欧拉角Armoriginalstate.msg

```
float32[] joint  
float32[6] pose  
uint16 arm_err  
uint16 sys_err  
uint8 dof
```

**msg成员：**

- `joint` ：关节角度，float类型，单位：度。
- `pose` ：机械臂当前位姿，float类型，x、y、z坐标，单位：m，x、y、z欧拉角，单位：度。
- `arm_err` ：机械臂运行错误代码，unsigned int类型。
- `sys_err` ：系统错误代码，unsigned int类型。
- `dof` ：机械臂自由度信息。

### 机械臂当前状态-弧度和四元数Armstate.msg

```
float32[] joint  
geometry_msgs/Pose pose  
uint16 arm_err  
uint16 sys_err  
uint8 dof
```

**msg成员：**

- `joint` ：关节角度，float类型，单位：弧度。
- `pose` ：机械臂当前位姿，float类型，x、y、z坐标，单位：m，x、y、z、w四元数。
- `arm_err` ：机械臂运行错误代码，unsigned int类型。
- `sys_err` ：系统错误代码，unsigned int类型。
- `dof` ：机械臂自由度信息。

### 夹爪力控夹取Gripperpick.msg

```
uint16 speed  
uint16 force  
bool block
uint16 timeout
```

**msg成员：**

- `speed` ：夹爪力控夹取速度，unsigned int类型，范围：1-1000。
- `force` ：夹爪夹取力矩阈值，unsigned int类型，范围 ：50-1000。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。
- `timeout` ：设置返回超时时间，阻塞模式生效（以秒为单位）。

### 夹爪力控夹取-持续力控夹取Gripperpick.msg

```
uint16 speed  
uint16 force  
bool block
uint16 timeout
```

**msg成员：**

- `speed` ：夹爪力控夹取速度，unsigned int类型，范围：1-1000。
- `force` ：夹爪夹取力矩阈值，unsigned int类型，范围 ：50-1000。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。
- `timeout` ：设置返回超时时间，阻塞模式生效（以秒为单位）。

### 夹爪到达指定位置Gripperset.msg

```
uint16 position  
bool block
uint16 timeout
```

**msg成员：**

- `position` ：夹爪目标位置，unsigned int类型，范围：1-1000,代表夹爪开口度：0-70mm。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。
- `timeout` ：设置返回超时时间，阻塞模式生效（以秒为单位）。

### 力位混合控制Setforceposition.msg

```
uint8 sensor  
uint8 mode  
uint8 direction  
int16 n
```

**msg成员：**

- `sensor` ：传感器；0-一维力；1-六维力。
- `mode` ：Mode：0-工作坐标系力控； 1-工具坐标系力控。
- `Direction` ：力控方向；0-沿X 轴；1-沿Y 轴；2-沿 Z 轴；3-沿RX 姿态方向；4-沿 RY 姿态方向；5-沿 RZ 姿态方向。
- `n` ：力的大小，单位 N。

### 六维力数据Sixforce.msg

```
float32 force_fx  
float32 force_fy  
float32 force_fz  
float32 force_mx  
float32 force_my  
float32 force_mz
```

**msg成员：**

- `force_fx` ：沿x轴方向受力大小。
- `force_fy` ：沿y轴方向受力大小。
- `force_fz` ：沿z轴方向受力大小。
- `force_mx` ：沿x轴方向转动受力大小。
- `force_my` ：沿y轴方向转动受力大小。
- `force_mz` ：沿z轴方向转动受力大小。

### 设置灵巧手手势Handposture.msg

```
uint16 posture_num  
bool block
uint16 timeout
```

**msg成员：**

- `posture_num` ：预先保存在灵巧手内的手势序号，范围：1-40。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。
- `timeout` ：阻塞模式下超时时间设置，单位：秒。

### 设置灵巧手动作序列Handseq.msg

```
uint16 seq_num  
bool block
uint16 timeout
```

**msg成员：**

- `seq_num` ：预先保存在灵巧手内的序列序号，范围：1-40。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。
- `timeout` ：阻塞模式下超时时间设置，单位：秒。

### 设置灵巧手各自由度角度Handangle.msg

```
int16[6] hand_angle   
bool block
```

**msg成员：**

- `hand_angle` ：手指角度数组，范围：0-1000。另外，-1 代表该自由度不执行任何操作，保持当前状态。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。

### 设置灵巧手速度Handspeed.msg

```
uint16 hand_speed
```

**msg成员：**

- `hand_speed` ：手指速度，范围：1-1000。

### 设置灵巧手力阈值Handforce.msg

```
uint16 hand_force
```

**msg成员：**

- `hand_force` ：手指力，范围：1-1000。

### 透传力位混合补偿-角度Forcepositionmovejoint.msg

```
float32[] joint  
uint8 sensor  
uint8 mode  
int16 dir  
float32 force  
bool follow  
uint8 dof
```

**msg成员：**

- `joint` ：角度力位混合透传，单位：弧度。
- `sensor` ：所使用传感器类型，0-一维力，1-六维力。
- `mode` ：模式，0-沿工作坐标系，1-沿工具端坐标系。
- `dir` ：力控方向，0-5 分别代表 X/Y/Z/Rx/Ry/Rz，其中一维力类型时默认方向为Z 方向。
- `force` ：力的大小，精度 0.1N 或者 0.1Nm。
- `follow` ：跟随状态，bool类型，true高跟随，false低跟随，不设置默认高跟随。
- `dof` ：机械臂自由度信息。

### 透传力位混合补偿-位姿Forcepositionmovejoint.msg

```
geometry_msgs/Pose pose  
uint8 sensor  
uint8 mode  
int16 dir  
float32 force  
bool follow
```

**msg成员：**

- `pose` ：机械臂位姿信息，x、y、z位置信息+四元数姿态信息。
- `sensor` ：所使用传感器类型，0-一维力，1-六维力。
- `mode` ：模式，0-沿工作坐标系，1-沿工具端坐标系。
- `dir` ：力控方向，0-5 分别代表 X/Y/Z/Rx/Ry/Rz，其中一维力类型时默认方向为Z 方向。
- `force` ：力的大小，精度 0.1N 或者 0.1Nm。
- `follow` ：跟随状态，bool类型，true高跟随，false低跟随，不设置默认高跟随。

### 速度开环控制-升降机构Liftspeed.msg

```
int16 speed  
bool block
```

**msg成员：**

- `speed` ：速度百分比，-100-100。Speed<0：升降机构向下运动；Speed>0：升降机构向上运动；Speed=0：升降机构停止运动。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。

### 位置闭环控制-升降机构Liftheight.msg

```
uint16 height  
uint16 speed  
bool block
```

**msg成员：**

- `height` ：目标高度，单位 mm。
- `speed` ：速度百分比，1-100。
- `block` ：是否为阻塞模式，bool类型，true：阻塞，false：非阻塞。

### 获取升降机构状态-升降机构Liftstate.msg

```
int16 height   
int16 current  
uint16 err_flag
```

**msg成员：**

- `height` ：当前升降机构高度，单位：mm，精度：1mm。
- `current` ：当前升降机构电流，精度 0.001mA。
- `err_flag` ：升降驱动错误代码，错误代码类型参考关节错误代码。

### 查询或设置UDP机械臂状态主动上报配置Setrealtimepush.msg

```
uint16 cycle  
uint16 port  
uint16 force_coordinate  
string ip
bool aloha_state_enable
bool arm_current_status_enable
bool expand_state_enable
bool hand_enable
bool joint_speed_enable
bool lift_state_enable
bool plus_base_enable
bool plus_state_enable
```

**msg成员：**

- `cycle` ：设置广播周期，为5ms的倍数。
- `port` ：设置广播的端口号。
- `force_coordinate` ：系统外受力数据的坐标系，0 为传感器坐标系 1 为当前工作坐标系 2 为当前工具坐标系。
- `ip` ：自定义的上报目标IP 地址。
- `aloha_state_enable` ：aloha状态信息主动上报使能。
- `arm_current_status_enable` ：机械臂当前状态主动上报使能。
- `expand_state_enable` ：拓展关节主动上报使能。
- `hand_enable` ：灵巧手数据主动上报使能。
- `joint_speed_enable` ：关节速度主动上报使能。
- `lift_state_enable` ：升降机主动上报使能。
- `plus_base_enable` ：末端设备基础信息主动上报使能。
- `plus_state_enable` ：末端设备实时信息主动上报使能。

### UDP机械臂状态上报Armcurrentstatus.msg

```
uint16 arm_current_status
```

**msg成员：**

- `arm_current_status` ：机械臂状态，定义如下：
	```bash
	0 - RM_IDLE_E             // 使能但空闲状态
	1 - RM_MOVE_L_E           // move L运动中状态
	2 - RM_MOVE_J_E           // move J运动中状态
	3 - RM_MOVE_C_E           // move C运动中状态
	4 - RM_MOVE_S_E           // move S运动中状态
	5 - RM_MOVE_THROUGH_JOINT_E // 角度透传状态
	6 - RM_MOVE_THROUGH_POSE_E  // 位姿透传状态
	7 - RM_MOVE_THROUGH_FORCE_POSE_E // 力控透传状态
	8 - RM_MOVE_THROUGH_CURRENT_E // 电流环透传状态
	9 - RM_STOP_E             // 急停状态
	10 - RM_SLOW_STOP_E        // 缓停状态
	11 - RM_PAUSE_E            // 暂停状态
	12 - RM_CURRENT_DRAG_E     // 电流环拖动状态
	13 - RM_SENSOR_DRAG_E      // 六维力拖动状态
	14 - RM_TECH_DEMONSTRATION_E // 示教状态
	```

### UDP关节电流上报Jointcurrent.msg

```
float32[] joint_current
```

**msg成员：**

- `joint_current` ：当前关节电流，精度 0.001mA。

### UDP关节使能状态上报Jointenflag.msg

```
bool[] joint_en_flag
```

**msg成员：**

- `joint_en_flag` ：当前关节使能状态 ，1 为上使能，0 为掉使能。

### UDP机械臂欧拉角位姿上报Jointposeeuler.msg

```
float32[3] euler
float32[3] position
```

**msg成员：**

- `euler` ：当前路点姿态欧拉角，精度 0.001rad。
- `position` ：当前路点位置，精度 0.000001M。

### UDP关节速度上报Jointspeed.msg

```
float32[] joint_speed
```

**msg成员：**

- `joint_speed` ：当前关节速度，精度0.02RPM。

### UDP关节温度上报Jointtemperature.msg

```
float32[] joint_temperature
```

**msg成员：**

- `joint_temperature` ：当前关节温度，精度 0.001℃。

### UDP关节电压上报Jointvoltage.msg

```
float32[] joint_voltage
```

**msg成员：**

- `joint_voltage` ：当前关节电压，精度 0.001V。

### UDP错误上报Rmerr.msg

```
uint8 err_len
int32[] err
```

**msg成员：**

- `err_len` ：当前报错数量，uint8。
- `err` ：当前报错代码，int32。

### 末端设备基础信息Rmplusbase.msg

```
string manu
int8 type
string hv
string sv
string bv
int32 id
int8 dof
int8 check
int8 bee
bool force
bool touch
int8 touch_num
int8 touch_sw
int8 hand
int32[12] pos_up
int32[12] pos_low
int32[12] angle_up
int32[12] angle_low
int32[12] speed_up
int32[12] speed_low
int32[12] force_up
int32[12] force_low
```

**msg成员：**

- `manu` ：设备厂家。
- `type` ：设备类型 1：两指夹爪 2：五指灵巧手 3：三指夹爪。
- `hv` ：硬件版本。
- `sv` ：软件版本。
- `bv` ：boot版本。
- `id` ：设备ID。
- `dof` ：自由度。
- `check` ：自检开关。
- `bee` ：蜂鸣器开关。
- `force` ：力控支持。
- `touch` ：触觉支持。
- `touch_num` ：触觉个数。
- `touch_sw` ：触觉开关。
- `hand` ：手方向 1 ：左手 2： 右手。
- `pos_up` ：位置上限,单位：无量纲。
- `pos_low` ：位置下限,单位：无量纲。
- `angle_up` ：角度上限,单位：0.01度。
- `angle_low` ：角度下限,单位：0.01度。
- `speed_up` ：速度上限,单位：无量纲。
- `speed_low` ：速度下限,单位：无量纲。
- `force_up` ：力上限,单位：0.001N。
- `force_low` ：力下限,单位：0.001N。

### 末端设备基础信息Rmplusstate.msg

```
int32 sys_state
int32[12] dof_state
int32[12] dof_err
int32[12] pos
int32[12] speed
int32[12] angle
int32[12] current
int32[18] normal_force
int32[18] tangential_force
int32[18] tangential_force_dir
uint32[12] tsa
uint32[12] tma
int32[18] touch_data
int32[12] force
```

**msg成员：**

- `sys_state` ：系统状态。
- `dof_state` ：各自由度当前状态。
- `dof_err` ：各自由度错误信息。
- `pos` ：各自由度当前位置。
- `speed` ：各自由度当前速度。
- `angle` ：各自由度当前角度。
- `current` ：各自由度当前电流。
- `normal_force` ：自由度触觉三维力的法向力。
- `tangential_force` ：自由度触觉三维力的切向力。
- `tangential_force_dir` ：自由度触觉三维力的切向力方向。
- `tsa` ：自由度触觉自接近。
- `tma` ：自由度触觉互接近。
- `touch_data` ：触觉传感器原始数据。
- `force` ：自由度力矩。

### 自定义高跟随模式角度透传Jointposcustom.msg

```
float32[] joint  
bool follow  
float32 expand  
uint8 dof
uint8 trajectory_mode
uint8 radio
```

**msg成员：**

- `joint` ：关节角度，float类型，单位：弧度。
- `follow` ：跟随状态，bool类型，true高跟随，false低跟随，不设置默认高跟随。
- `expand` ：拓展关节，float类型，单位：弧度。
- `dof` ：机械臂自由度信息。
- `trajectory_mode` ：设置高跟随模式下，支持多种模式，0-完全透传模式、1-曲线拟合模式、2-滤波模式。
- `radio` ：设置曲线拟合模式下平滑系数（范围0-100）或者滤波模式下的滤波参数（范围0-1000），数值越大表示平滑效果越好。

### 自定义高跟随模式位姿透传Carteposcustom.msg

```
geometry_msgs/Pose pose  
bool follow
uint8 trajectory_mode
uint8 radio
```

**msg成员：**

- `pose` ：机械臂位姿，geometry\_msgs/Pose类型，x、y、z坐标（float类型，单位：m）+四元数。
- `follow` ：跟随状态，bool类型，true高跟随，false低跟随，不设置默认高跟随。
- `trajectory_mode` ：设置高跟随模式下，支持多种模式，0-完全透传模式、1-曲线拟合模式、2-滤波模式。
- `radio` ：设置曲线拟合模式下平滑系数（范围0-100）或者滤波模式下的滤波参数（范围0-1000），数值越大表示平滑效果越好。

主要为套用API实现的一些机械臂本体的功能，其详细介绍和使用在此不详细展开，可以通过 [RM-机械臂ROS2话题详细说明](https://develop.realman-robotics.com/robot4th/ros2/ros2Description/) 进行查看。