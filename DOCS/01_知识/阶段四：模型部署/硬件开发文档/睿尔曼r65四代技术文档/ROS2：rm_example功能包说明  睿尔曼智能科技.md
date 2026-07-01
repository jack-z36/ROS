---
title: "ROS2：rm_example功能包说明 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/ros2/example/"
author:
published: 2026-04-22
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## rm\_example功能包说明

rm\_example功能包为实现了一些基本的机械臂功能，通过该功能包我们可以实现机械臂的的控制功能，如机械臂关节运动、机械臂笛卡尔空间运动、机械臂样条曲线轨迹运动等。  
这里将从以下三个方面整体介绍该功能包：

- 1.功能包使用：了解该功能包的使用。
- 2.功能包架构说明：熟悉功能包中的文件构成及作用。
- 3.功能包话题说明：熟悉功能包相关的话题，方便开发和使用。

代码链接： [https://github.com/RealManRobot/ros2\_rm\_robot/tree/humble/rm\_example](https://github.com/RealManRobot/ros2_rm_robot/tree/humble/rm_example)

## 1\. rm\_example功能包使用

### 1.1 更换工作坐标系

首先需要运行机械臂的底层驱动节点rm\_driver。

```
ros2 launch rm_driver rm_<arm_type>_driver.launch.py
```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72。  
例如65机械臂的启动命令：

```
ros2 launch rm_driver rm_65_driver.launch.py
```

节点启动成功后，需要执行如下指令运行我们更换工作坐标系的节点。

```
ros2 run rm_example rm_change_work_frame
```

弹出以下指令代表更换成功： 首先订阅当前的工作坐标系话题，可以在终端中输入如下指令进行验证：

```
ros2 topic echo /rm_driver/get_curr_workFrame_result
```

之后发布当前坐标系的请求。

```
ros2 topic pub --once /rm_driver/get_curr_workFrame_cmd std_msgs/msg/Empty "{}"
```

可以看到终端中弹出如下界面。 ![image](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/ros2/example/rm_example1.png)

### 1.2 得到当前的机械臂状态信息

首先需要运行机械臂的底层驱动节点rm\_driver。

```
ros2 launch rm_driver rm_<arm_type>_driver.launch.py
```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72。  
例如65机械臂的启动命令：

```
ros2 launch rm_driver rm_65_driver.launch.py
```

节点启动成功后，需要执行如下指令运行获得机械臂当前状态的节点。

```
ros2 run rm_example rm_get_state
```

弹出以下指令代表更换成功。 界面中现实的为机械臂当前的角度信息，以及机械臂当前的末端坐标位置和欧拉角姿态信息。

### 1.3 机械臂MoveJ运动

通过如下指令可以控制机械臂进行MoveJ关节运动。 首先需要运行机械臂的底层驱动节点rm\_driver。

```
ros2 launch rm_driver rm_<arm_type>_driver.launch.py
```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72。  
例如65机械臂的启动命令：

```
ros2 launch rm_driver rm_65_driver.launch.py
```

节点启动成功后，需要执行如下指令控制机械臂进行运动。

```
ros2 launch rm_example rm_<dof>_movej.launch.py
```

命令中的dof代表机械当前的自由度信息，可以选的参数有6dof和7dof。  
例如启动7轴的机械臂时需要使用如下指令。

```
ros2 launch rm_example rm_7dof_movej.launch.py
```

运行成功后，机械臂的关节将发生转动，且界面将显示如下信息。

### 1.4 机械臂MoveJ\_P运动

通过如下指令可以控制机械臂进行MoveJ\_P关节运动。  
首先需要运行机械臂的底层驱动节点rm\_driver。

```
ros2 launch rm_driver rm_<arm_type>_driver.launch.py
```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72。  
例如65机械臂的启动命令：

```
ros2 launch rm_driver rm_65_driver.launch.py
```

节点启动成功后，需要执行如下指令控制机械臂进行运动。

```
ros2 run rm_example movejp_demo
```

注意

若机械臂型号为GEN72则使用如下指令。

```
ros2 run rm_example movejp_gen72_demo
```

执行成功后界面将出现如下提示，并且机械臂运动到指定位姿。

### 1.5 机械臂MoveL运动

通过如下指令可以控制机械臂进行MoveL关节运动。 首先需要运行机械臂的底层驱动节点rm\_driver。

```
ros2 launch rm_driver rm_<arm_type>_driver.launch.py
```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72。  
例如65机械臂的启动命令：

```
ros2 launch rm_driver rm_65_driver.launch.py
```

节点启动成功后，需要执行如下指令控制机械臂进行运动。

```
ros2 run rm_example movel_demo
```

注意

若机械臂型号为GEN72则使用如下指令。

```
ros2 run rm_example movel_gen72_demo
```

执行成功后界面将出现如下提示，并且机械臂将进行两次运动，首先通过MoveJP运动到指定位姿，之后通过MoveL进行关节运动。

## 2\. rm\_example功能包架构文件总览

当前rm\_example功能包的文件构成如下。

```
├── CMakeLists.txt                             #编译规则文件
├── doc
│   ├── rm_example10.png
│   ├── rm_example11.png
│   ├── rm_example1.png
│   ├── rm_example2.png
│   ├── rm_example3.png
│   ├── rm_example4.png
│   ├── rm_example5.png
│   ├── rm_example6.png
│   ├── rm_example7.png
│   ├── rm_example8.png
│   └── rm_example9.png
├── launch
│   ├── rm_6dof_movej.launch.py                 #6自由度MoveJ运动启动文件
│   └── rm_7dof_movej.launch.py                 #7自由度MoveJ运动启动文件
├── package.xml
└── src
    ├── api_ChangeWorkFrame_demo.cpp        #更换工作坐标系源文件
    ├── api_Get_Arm_State_demo.cpp          #获得机械臂状态源文件
    ├── api_MoveJ_demo.cpp                  #MoveJ运动源文件
    ├── api_MoveJP_demo.cpp                 #MoveJP运动源文件
    ├── api_MoveJP_Gen72_demo.cpp           #适用于Gen72的MoveJP运动源文件
    └── api_MoveL_demo.cpp                  #MoveL运动源文件
    └── api_MoveL_Gen72_demo.cpp            #适用于Gen72的MoveL运动源文件
```

## 3\. rm\_example话题说明

### 3.1 rm\_change\_work\_frame话题说明

以下为该节点的数据通信图： 可以看到/changeframe节点和/rm\_driver之间的主要通信话题为/rm\_driver/change\_work\_frame\_result和/rm\_driver/change\_work\_frame\_cmd。/rm\_driver/change\_work\_frame\_cmd为切换请求和切换目标坐标的发布，/rm\_driver/change\_work\_frame\_result为切换结果。

### 3.2 rm\_get\_state话题说明

以下为该节点的数据通信图： 可以看到/get\_state节点和/rm\_driver之间的主要通信话题为/rm\_driver/get\_current\_arm\_state\_cmd和/rm\_driver/get\_current\_arm\_original\_state\_result。/rm\_driver/get\_current\_arm\_state\_cmd为获取机械臂当前状态请求，/rm\_driver/get\_current\_arm\_original\_state\_result为切换结果。

### 3.3 movej\_demo话题说明

以下为该节点的数据通信图： 可以看到/Movej\_demo节点和/rm\_driver之间的主要通信话题为/rm\_driver/movej\_cmd和/rm\_driver/movej\_result。/rm\_driver/movej\_cmd为控制机械臂运动的请求，将发布需要运动到的各关节的弧度信息，/rm\_driver/ movej\_result为运动结果。

### 3.4 movejp\_demo话题说明

以下为该节点的数据通信图： 可以看到/Movejp\_demo\_node节点和/rm\_driver之间的主要通信话题为/rm\_driver/movej\_p\_cmd和/rm\_driver/movej\_p\_result。/rm\_driver/movej\_p\_cmd为控制机械臂运动规划的请求，将发布需要运动到的目标点的坐标，/rm\_driver/ movej\_p\_result为运动结果。

### 3.5 movel\_demo话题说明

以下为该节点的数据通信图： 可以看到/Movel\_demo\_node节点和/rm\_driver之间的主要通信话题为/rm\_driver/movej\_p\_cmd和/rm\_driver/movej\_p\_result还有/rm\_driver/movel\_cmd和/rm\_driver/movel\_result。/rm\_driver/movej\_p\_cmd为控制机械臂运动规划的请求，将发布机械臂首先需要运动到的目标点的坐标， /rm\_driver/ movej\_p\_result为运动结果，到达第一个点位后我们通过直线运动到达第二个点位，就可以通过/rm\_driver/movel\_cmd发布第二个点位的位姿，/rm\_driver/movel\_result话题代表运动的结果。
