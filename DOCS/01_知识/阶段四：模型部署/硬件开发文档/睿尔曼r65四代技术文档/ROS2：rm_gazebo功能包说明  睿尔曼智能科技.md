---
title: "ROS2：rm_gazebo功能包说明 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/ros2/gazebo/"
author:
published: 2026-04-22
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## rm\_gazebo功能包说明

rm\_gazebo的主要作用是帮助我们实现机械臂Moveit2规划的仿真功能，我们将在Gazebo的仿真环境中搭建一个虚拟机械臂，然后通过Moveit2控制Gazebo中的虚拟机械臂。  
这里将从以下两个方面整体介绍该功能包：

- 1.功能包使用：了解该功能包的使用。
- 2.功能包架构说明：熟悉功能包中的文件构成及作用。

代码链接： [https://github.com/RealManRobot/ros2\_rm\_robot/tree/humble/rm\_gazebo](https://github.com/RealManRobot/ros2_rm_robot/tree/humble/rm_gazebo)

## 1\. 控制仿真机械臂

### 1.1 启动Gazebo虚拟空间和虚拟机械臂

在完成环境安装和功能包安装后，我们可以进行rm\_gazebo功能包的运行。  
使用如下指令启动Gazebo虚拟空间和虚拟机械臂。

- 启动标准版本机械臂的命令为：
	```
	ros2 launch rm_gazebo gazebo_<arm_type>_demo.launch.py
	```
- 启动六维力版本机械臂的命令为(eco63、gen72、gen72\_II不可用)：
	```
	ros2 launch rm_gazebo gazebo_<arm_type>_6f_demo.launch.py
	```
- 启动一体化六维力版本机械臂的命令为(gen72、gen72\_II不可用)：
	```
	ros2 launch rm_gazebo gazebo_<arm_type>_6fb_demo.launch.py
	```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72、gen72\_II。

例如65标准版机械臂的启动命令如下：

```
ros2 launch rm_gazebo gazebo_65_demo.launch.py
```

运行成功后将弹出如下界面。 ![image](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/ros2/gazebo/rm_gazebo1.png)

### 1.2 启动moveit2控制仿真机械臂

之后我们使用如下指令启动moveit2控制gazebo中的仿真机械臂。

- 启动标准版本机械臂的命令为：
	```
	ros2 launch rm_<arm_type>_config gazebo_moveit_demo.launch.py
	```
- 启动六维力版本机械臂的命令为(eco63、gen72、gen72\_II不可用)：
	```
	ros2 launch rm_<arm_type>_config gazebo_moveit_demo_6f.launch.py
	```
- 启动一体化六维力版本机械臂的命令为(gen72、gen72\_II不可用)：
	```
	ros2 launch rm_<arm_type>_config gazebo_moveit_demo_6fb.launch.py
	```

在实际使用时需要将以上的<arm\_type>更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72、gen72\_II。

例如65标准版机械臂的启动命令如下：

```
ros2 launch rm_65_config gazebo_moveit_demo.launch.py
```

弹出rviz2的控制界面后就可以进行moveit2和gazebo的仿真控制了。

## 2\. rm\_gazebo功能包架构文件总览

```
├── CMakeLists.txt                              #编译规则文件
├── config
│   ├── gazebo_63_6fb_description.urdf.xacro    #RML63一体化六维力gazebo模型描述文件
│   ├── gazebo_65_6fb_description.urdf.xacro    #RM65一体化六维力gazebo模型描述文件
│   ├── gazebo_75_6fb_description.urdf.xacro    #RM75一体化六维力gazebo模型描述文件
│   ├── gazebo_eco63_6fb_description.urdf.xacro #ECO63一体化六维力gazebo模型描述文件
│   ├── gazebo_eco65_6fb_description.urdf.xacro #ECO65一体化六维力gazebo模型描述文件
│   ├── gazebo_63_description.urdf.xacro        #RML63gazebo模型描述文件
│   ├── gazebo_65_description.urdf.xacro        #RM65gazebo模型描述文件
│   ├── gazebo_75_description.urdf.xacro        #RM75gazebo模型描述文件
│   ├── gazebo_eco65_description.urdf.xacro     #ECO65gazebo模型描述文件
│   ├── gazebo_eco63_description.urdf.xacro     #ECO63gazebo模型描述文件
│   ├── gazebo_gen72_description.urdf.xacro     #GEN72gazebo模型描述文件
│   └── gazebo_gen72_II_description.urdf.xacro  #GEN72_IIgazebo模型描述文件
├── doc
│   ├── rm_gazebo1.png
│   └── rm_gazebo2.png
├── include
│   └── rm_gazebo
├── launch
│   ├── gazebo_63_6fb_demo.launch.py       #RML63一体化六维力gazebo启动文件
│   ├── gazebo_63_6f_demo.launch.py        #RML63六维力gazebo启动文件
│   ├── gazebo_63_demo.launch.py           #RML63gazebo启动文件
│   ├── gazebo_65_6fb_demo.launch.py       #RM65一体化六维力gazebo启动文件
│   ├── gazebo_65_6f_demo.launch.py        #RM65六维力gazebo启动文件
│   ├── gazebo_65_demo.launch.py           #RM65gazebo启动文件
│   ├── gazebo_75_6fb_demo.launch.py       #RM75一体化六维力gazebo启动文件
│   ├── gazebo_75_6f_demo.launch.py        #RM75六维力gazebo启动文件
│   ├── gazebo_75_demo.launch.py           #RM75gazebo启动文件
│   ├── gazebo_eco63_6fb_demo.launch.py    #ECO63一体化六维力gazebo启动文件
│   ├── gazebo_eco63_demo.launch.py        #ECO63gazebo启动文件
│   ├── gazebo_eco65_6fb_demo.launch.py    #ECO65一体化六维力gazebo启动文件
│   ├── gazebo_eco65_6f_demo.launch.py     #ECO65六维力gazebo启动文件
│   ├── gazebo_eco65_demo.launch.py        #ECO65gazebo启动文件
│   ├── gazebo_gen72_demo.launch.py        #GEN72gazebo启动文件
│   └── gazebo_gen72_II_demo.launch.py     #GEN72_IIgazebo启动文件
├── package.xml
├── README_CN.md
└── README.md
```
