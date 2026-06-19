---
title: "ROS2：快速开始 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/ros2/getStarted/"
author:
published: 2026-01-23
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## 快速开始

机械臂的ROS2支持是基于 `ros2_rm_robot` 功能包，以下为使用环境：

- 当前支持的机械臂有RM65系列、RM75系列、ECO63系列、ECO65系列和RML63系列，详细可参考网址 [RealMan robots](https://www.realman-robotics.cn/) 。
- ROS2最新版本为1.5.0，与机械臂控制器版本配套关系，请参考 [版本变更说明](https://develop.realman-robotics.com/robot4th/releaseNotes/releaseNotesfour/#42281) 。
- ROS2支持humble为Ubuntu版本是22.04。
- ROS2支持foxy为Ubuntu版本是20.04。

humble功能包下载地址： [humble](https://github.com/RealManRobot/ros2_rm_robot/releases/tag/humble1.5.0) 。 foxy功能包下载地址： [foxy](https://github.com/RealManRobot/ros2_rm_robot/releases/tag/foxy1.5.0) 。

## 1\. 搭建环境

### 1.1 安装ROS2

我们提供了ROS2的安装脚本ros2\_install.sh，该脚本位于rm\_install功能包中的scripts文件夹下，在实际使用时我们需要移动到该路径执行如下指令。

```
cd ~/ros2_rm_robot/rm_install/scripts/
sudo bash ros2_install.sh
```

如果不想使用脚本安装也可以参考网址 [ROS2\_INSTALL](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) 。

### 1.2 安装Moveit2

我们提供了Moveit2的安装脚本moveit2\_install.sh，该脚本位于rm\_install功能包中的scripts文件夹下，在实际使用时我们需要移动到该路径执行如下指令。

```
cd ~/ros2_rm_robot/rm_install/scripts/
sudo bash moveit2_install.sh
```

如果不想使用脚本安装也可以参考网址 [Moveit2\_INSTALL](https://moveit.ros.org/install-moveit2/binary/) 进行安装。

### 1.3 配置功能包环境

该脚本位于rm\_driver功能包中的lib文件夹下，在实际使用时我们需要移动到该路径执行如下指令。

```
cd ~/ros2_rm_robot/rm_driver/lib/
sudo bash lib_install.sh
```

### 1.4 编译

以上执行成功后，可以执行如下指令进行功能包编译，首先需要构建工作空间，并将功能包文件导入工作空间下的src文件夹下，之后使用colcon build指令进行编译。

```
mkdir -p ~/ros2_ws/src
cp -r ros2_rm_robot ~/ros2_ws/src
cd ~/ros2_ws
colcon build --packages-select rm_ros_interfaces
source ./install/setup.bash
colcon build
```

编译完成后即可进行功能包的运行操作。

## 2\. 功能运行

### 2.1 功能包简介

1. 安装与环境配置(rm\_install： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_install) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_install))
	该功能包为机械臂使用辅助功能包，主要作用为介绍功能包使用环境安装与搭建方式，功能包的依赖库安装和功能包编译方法。
2. 硬件驱动(rm\_driver： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_driver) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_driver))
	该功能包为机械臂的ROS2底层驱动功能包，其作用为订阅和发布机械臂底层相关话题信息。
3. 启动(rm\_bringup： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_bringup) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_bringup))
	该功能包为机械臂的节点启动功能包，其作用为快速启动多节点复合的机械臂功能。
4. 模型描述(rm\_description： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_description) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_description))
	该功能包为机械臂模型描述功能包，其作用为提供机械臂模型文件和模型加载节点，并为其他功能包提供机械臂关节间的坐标变换关系。
5. ROS消息接口(rm\_ros\_interfaces： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_ros_interfaces) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_ros_interfaces))
	该功能包为机械臂的消息文件功能包，其作用为提供机械臂适配ROS2的所有控制消息和状态消息。
6. Moveit2配置(rm\_moveit2\_config： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_moveit2_config) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_moveit2_config))
	该功能包为机械臂的moveit2适配功能包，其作用为适配和实现各系列机械臂的moveit2规划控制功能，主要包括虚拟机械臂控制和真实机械臂控制两部分控制功能。
7. Moveit2与硬件驱动通信连接(rm\_config： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_control) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_control))
	该功能包为底层驱动功能包（rm\_driver）和moveit2功能包（rm\_moveit2\_config）之间的通信连接功能包，主要功能为将moveit2的规划点进行细分然后通过透传的形式传递给底层驱动功能包控制机械臂运动。
8. Gazebo仿真机械臂控制(rm\_gazebo： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_gazebo) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_gazebo))
	该功能包为gazebo仿真机械臂功能包，主要功能为在gazebo仿真环境中显示机械臂模型，可通过moveit2对仿真的机械臂进行规划控制。
9. 使用案例(rm\_examples： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_example) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_example))
	该功能包为机械臂的一些使用案例，主要功能为实现机械臂的一些基本的控制功能和运动功能的使用案例。
10. 技术文档(rm\_docs： [humble](https://github.com/RealManRobot/ros2_rm_robot/tree/humble1.5.0/rm_doc) 、 [foxy](https://github.com/RealManRobot/ros2_rm_robot/tree/foxy1.5.0/rm_doc))
	该功能包为介绍文档的功能包，其主要包括为对整体的功能包内容和使用方式进行总体介绍的文档和对每个功能包中的内容和使用方式进行详细介绍的文档。

以上为当前的十个功能包，每个功能包都有其独特的作用，详情请参考rm\_doc功能包下的doc文件夹中的文档进行详细了解。

### 2.2 运行虚拟机械臂

使用如下指令可以启动gazebo显示仿真机械臂，并同时启动moveit2进行仿真机械臂的规划操控。

```
source ~/ros2_ws/install/setup.bash
ros2 launch rm_gazebo gazebo_<arm_type>_demo.launch.py
ros2 launch rm_<arm_type>_config gazebo_moveit_demo.launch.py
```

<arm\_type>需要使用65、75、eco65、eco63、63、gen72、gen72\_II 字符进行代替，如使用RM65机械臂时，命令如下。

```
ros2 launch rm_gazebo gazebo_65_demo.launch.py
ros2 launch rm_65_config gazebo_moveit_demo.launch.py
```

启动成功后即可使用moveit2进行虚拟机械臂的控制。

### 2.3 控制真实机械臂

使用如下指令可以启动机械臂硬件驱动，并同时启动moveit2进行机械臂的规划操控。

```
source ~/ros2_ws/install/setup.bash
ros2 launch rm_bringup rm_<arm_type>_gazebo.launch.py
```

<arm\_type>需要使用65、75、eco65、eco63、63、gen72、gen72\_II 字符进行代替，如使用RM65机械臂时，命令如下。

```
ros2 launch rm_bringup rm_65_bringup.launch.py
```

启动成功后即可使用moveit2进行真实机械臂的控制。

## 3\. 安全提示

在使用机械臂时，为保证使用者安全，请参考如下操作规范。

- 每次使用前检查机械臂的安装情况，包括固定螺丝是否松动，机械臂是否存在震动、晃动的情况。
- 机械臂在运行过程中，人不可处于机械臂落下或工作范围内，也不可将其他物体放到机械臂动作的安全范围内。
- 在不使用机械臂时，应将机械臂置于安全位置，防止震动时机械臂跌落而损坏或砸伤其他物体。
- 在不使用机械臂时应及时断开机械臂电源。