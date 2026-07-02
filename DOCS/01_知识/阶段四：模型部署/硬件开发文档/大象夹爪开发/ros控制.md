---
title: "ros控制"
source: "https://docs.elephantrobotics.com/docs/myGripper-F100-cn/6-SDKDevelopment/6.3.html"
author:
published:
created: 2026-06-08
description:
tags:
  - "clippings"
---
## ros 控制

**USB-485模块接线** ：

连接夹爪端的 24V，GND, 485\_A(T/R+,485+), 485\_B(T/R-,485-)共 4 根线，电源为24V直流稳压电源，将模块的 USB 插口插入到电脑的 USB 接口

![](https://docs.elephantrobotics.com/docs/myGripper-F100-cn/img/new485c.jpg)

485A 接入 485 转 USB 模块 A+;  
485B 接入 485 转 USB 模块 B-;  
24V 接入 24V 直流稳压电源正极;  
GND 接入 24V 直流稳压电源负极

**使用环境**

Linux Ubuntu20.04 ROS Noetic，具体环境搭建内容请查看 [ROS环境搭建](https://docs.elephantrobotics.com/docs/mycobot_320_m5_cn/11-ApplicationBaseROS/11.1-ROS1/11.1.1-320M5/11.1.1.1-%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA.html)

**pro\_gripper\_ros 包安装**

`pro_gripper_ros` 是 ElephantRobotics 推出的，适配旗下myGripper F100 力控夹爪的 ROS 包。

项目地址： [http://github.com/elephantrobotics/pro\_gripper\_ros](http://github.com/elephantrobotics/pro_gripper_ros)

**注意：** 在安装包之前，请保证拥有 ROS 工作空间，默认的 ROS 工作空间是 catkin\_ws。

```bash
cd ~/catkin_ws/src  # 进入工作区的src文件夹中
# 克隆github上的代码
git clone https://github.com/elephantrobotics/pro_gripper_ros.git
cd ..       # 返回工作区
catkin_make # 构建工作区中的代码
cd ..
source devel/setup.bash # 添加环境变量
```

**案例使用**

<video controls="" width="100%"><source src="https://docs.elephantrobotics.com/docs/myGripper-F100-cn/img/f100_gripper_ros.mp4"></video>

打开终端命令行运行：

```bash
roslaunch pro_gripper_f100 force_gripper_slider.launch
```

打开 rviz 和一个滑块组件，您将看到如下界面：

![gripper_ros_img](https://docs.elephantrobotics.com/docs/myGripper-F100-cn/img/gripper_f100_ros.png)

然后你就可以在 rviz 中 控制模型，通过拖动滑块使其打开或关闭。如果想让真实的夹爪随着模型打开或关闭，则需要打开另一个终端命令行并运行：

```bash
# 确保在运行之前授予串行端口权限, 默认串口为/dev/ttyACM0，波特率为115200, 可根据实际串口修改
rosrun pro_gripper_f100 force_gripper_slider.py _port:=/dev/ttyACM0 _baud:=115200
```