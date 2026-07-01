---
title: "ROS2：rm_bringup功能包 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/ros2/bringup/"
author:
published: 2026-04-22
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## rm\_bringup功能包

rm\_bringup功能包为实现多个launch文件同时运行所设计的功能包，使用该功能包可用一条命令实现多个节点结合的复杂功能的启动。  
这里将从以下三个方面整体介绍该功能包：

- 1.功能包使用：了解该功能包的使用。
- 2.功能包架构说明：熟悉功能包中的文件构成及作用。
- 3.功能包话题说明：熟悉功能包相关的话题，方便开发和使用。

代码链接： [https://github.com/RealManRobot/ros2\_rm\_robot/tree/humble/rm\_bringup](https://github.com/RealManRobot/ros2_rm_robot/tree/humble/rm_bringup)

## 1\. rm\_bringup功能包使用

### 1.1 moveit2控制真实机械臂

首先配置好环境完成连接后我们可以通过以下命令直接启动节点，运行rm\_bringup功能包中的launch.py文件。

- 启动标准版本机械臂的命令为：
	```
	ros2 launch rm_bringup rm_<arm_type>_bringup.launch.py
	```
- 启动六维力版本机械臂的命令为(eco63、gen72、gen72\_II不可用)：
	```
	ros2 launch rm_bringup rm_<arm_type>_6f_bringup.launch.py
	```
- 启动一体化六维力版本机械臂的命令为(gen72、gen72\_II不可用)：
	```
	ros2 launch rm_bringup rm_<arm_type>_6fb_bringup.launch.py
	```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72、gen72\_II。

例如65标准版机械臂的启动命令如下：

```
ros2 launch rm_bringup rm_65_bringup.launch.py
```

节点启动成功后，将弹出以下画面。 ![image](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/ros2/bringup/rm_bringup1.png)  
实际该launch文件启动的为moveit2控制真实机械臂的功能下面就可以使用控制球规划控制机械臂运动，详细可查看 [rm\_moveit2\_config详解](https://develop.realman-robotics.com/robot4th/ros2/moveit2Config/) 相关内容。

### 1.2 控制gazebo仿真机械臂

我们可以通过以下命令运行rm\_bringup功能包中的launch.py文件，直接启动其中的gzaebo仿真节点。

- 启动标准版本机械臂的命令为：
	```
	ros2 launch rm_bringup rm_<arm_type>_gazebo.launch.py
	```
- 启动六维力版本机械臂的命令为(eco63、gen72、gen72\_II不可用)：
	```
	ros2 launch rm_bringup rm_<arm_type>_6f_gazebo.launch.py
	```
- 启动一体化六维力版本机械臂的命令为(gen72、gen72\_II不可用)：
	```
	ros2 launch rm_bringup rm_<arm_type>_6fb_gazebo.launch.py
	```

在实际使用时需要将以上的<arm\_type>更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72、gen72\_II。

例如65标准版机械臂的启动命令如下：

```
ros2 launch rm_bringup rm_65_gazebo.launch.py
```

节点启动成功后，将弹出以下画面。  
之后我们使用如下指令启动moveit2控制gazebo中的仿真机械臂。

## 2\. rm\_bringup功能包架构文件总览

当前rm\_bringup功能包的文件构成如下。

```
├── CMakeLists.txt                      #编译规则文件
├── doc                                 #辅助文档、图片存放文件夹
│   ├── rm_bringup1.png                 #图片1
│   ├── rm_bringup2.png                 #图片2
│   └── rm_bringup3.png                 #图片3
├── launch                              #启动文件
│   ├── rm_63_6f_bringup.launch.py      #63臂六维力moveit2启动文件
│   ├── rm_63_6fb_bringup.launch.py     #63臂一体化六维力moveit2启动文件
│   ├── rm_63_bringup.launch.py         #63臂moveit2启动文件
│   ├── rm_65_6f_bringup.launch.py      #65臂六维力moveit2启动文件
│   ├── rm_65_6fb_bringup.launch.py     #65臂一体化六维力moveit2启动文件
│   ├── rm_65_bringup.launch.py         #65臂moveit2启动文件
│   ├── rm_75_6f_bringup.launch.py      #75臂六维力moveit2启动文件
│   ├── rm_75_6fb_bringup.launch.py     #75臂一体化六维力moveit2启动文件
│   ├── rm_75_bringup.launch.py         #75臂moveit2启动文件

│   ├── rm_eco63_6fb_bringup.launch.py  #eco63臂一体化六维力moveit2启动文件
│   ├── rm_eco63_bringup.launch.py      #eco63臂moveit2启动文件
│   ├── rm_eco65_6f_bringup.launch.py   #eco65臂六维力moveit2启动文件
│   ├── rm_eco65_6fb_bringup.launch.py  #eco65臂一体化六维力moveit2启动文件
│   ├── rm_eco65_bringup.launch.py      #eco65臂moveit2启动文件
│   ├── rm_gen72_bringup.launch.py      #gen72臂moveit2启动文件
│   ├── rm_gen72_gazebo.launch.py       #gen72臂gazebo启动文件
│   ├── rm_gen72_II_bringup.launch.py   #gen72_II臂moveit2启动文件
│   └── rm_gen72_II_gazebo.launch.py    #gen72_II臂gazebo启动文件
├── package.xml                         #依赖说明文件
├── README_CN.md                        #中文说明文档
└── README.md                           #英文说明文档
```

## 3\. rm\_bringup话题说明

该功能包当前并没有本身的话题，主要为调用其他功能包的话题实现。
