---
title: "ROS2：rm_driver功能包说明 | 睿尔曼智能科技"
source: "https://develop.realman-robotics.com/robot4th/ros2/driver/"
author:
published: 2026-04-22
created: 2026-05-09
description: "睿尔曼智能科技有限公司-在线文档V1.6.18"
tags:
  - "clippings"
---
## rm\_driver功能包说明

rm\_driver功能包在机械臂ROS2功能包中是十分重要的，该功能包实现了通过ROS与机械臂进行通信控制机械臂的功能，在下文中将通过以下几个方面详细介绍该功能包。  
这里将从以下三个方面整体介绍该功能包：

- 1.功能包使用：了解该功能包的使用。
- 2.功能包架构说明：熟悉功能包中的文件构成及作用。
- 3.功能包话题说明：熟悉功能包相关的话题，方便开发和使用。

代码链接： [https://github.com/RealManRobot/ros2\_rm\_robot/tree/humble/rm\_driver](https://github.com/RealManRobot/ros2_rm_robot/tree/humble/rm_driver)

## 1\. rm\_driver功能包使用

### 1.1 功能包基础使用

通过以下命令直接启动节点，控制机械臂：

说明

当前的控制基于我们没有改变过机械臂的IP即当前机械臂的IP仍为192.168.1.18。

```
ros2 launch rm_driver rm_<arm_type>_driver.launch.py
```

在实际使用时需要将以上的 `<arm_type>` 更换为实际的机械臂型号，可选择的机械臂型号有65、63、eco65、eco63、75、gen72。  
底层驱动启动成功后，将显示以下画面: ![image](https://develop.realman-robotics.com/realman/docs/attachments/multimedia/zh/robot4th/ros2/driver/rm_driver1.png)

### 1.2 功能包进阶使用

当我们的机械臂IP被改变后我们的启动指令就失效了，再直接使用如上指令就无法成功连接到机械臂了，我们可以通过修改如下配置文件，重新建立连接。  
该配置文件位于我们的rm\_driver功能包下的config文件夹下。  
  
其配置文件内容如下：

```
rm_driver:   
  ros__parameters:  
    #robot param  
    arm_ip: "192.168.1.18"        #设置TCP连接时的IP  
    tcp_port: 8080                #设置TCP连接时的端口  
    
    arm_type: "RM_65"             #机械臂型号设置    
    arm_dof: 6                    #机械臂自由度设置  

    udp_ip: "192.168.1.10"        #设置udp主动上报IP  
    udp_cycle: 5                  #udp主动上报周期，需要是5的倍数  
    udp_port: 8089                #设置udp主动上报端口  
    udp_force_coordinate: 0       #设置系统受力时六维力的基准坐标，0为传感器坐标系 1为当前工作坐标系 2为当前工具坐标系
    udp_hand: false               #设置灵巧手udp主动上报使能
    udp_plus_base: false          #设置末端设备基础信息udp主动上报使能
    udp_plus_state: false         #设置末端设备实时信息udp主动上报使能

    trajectory_mode: 0            #设置高跟随模式下，支持多种模式，0-完全透传模式、1-曲线拟合模式、2-滤波模式
    radio: 0                      #设置曲线拟合模式下平滑系数（范围0-100）或者滤波模式下的滤波参数（范围0-1000），数值越大表示平滑效果越好
    arm_joints: ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
```

其中主要有以下几个参数。

- arm\_ip：改参数代表机械臂当前的IP
- tcp\_port：设置TCP连接时的端口。
- arm\_type：该参数代表机械臂当前的型号，可以选择的参数有RM\_65（65系列）、RM\_eco65（ECO65系列）、RM\_eco63（ECO63系列）、RML\_63（63系列）、RM\_75（75系列）、GEN\_72（GEN72系列）。
- arm\_dof: 机械臂自由度设置。6为6自由度，7为7自由度。
- udp\_ip: 设置udp主动上报目标IP。
- udp\_cycle：udp主动上报周期，需要是5的倍数。
- udp\_port：设置udp主动上报端口。
- udp\_force\_coordinate：设置系统受力时六维力的基准坐标，0为传感器坐标系（原始数据） 1为当前工作坐标系 2为当前工具坐标系。
- trajectory\_mode：设置高跟随模式下，支持多种模式，0-完全透传模式、1-曲线拟合模式、2-滤波模式。
- radio：设置曲线拟合模式下平滑系数（范围0-100）或者滤波模式下的滤波参数（范围0-1000），数值越大表示平滑效果越好。
- 在实际使用时，我们选择对应的launch文件启动时会自动选择正确的型号，若有特殊要求可在此处进行相应的参数修改，修改之后需要在工作空间目录下进行重新编译，之后修改的配置才会生效。
- 在工作空间目录运行colcon build指令。
```
colcon build
```
- 编译成功后可按如上指令进行功能包启动。

## 2\. rm\_driver功能包架构文件总览

```
├── CMakeLists.txt                 #编译规则文件
├── config                         #配置文件夹
│   ├── rm_63_config.yaml          #63配置文件
│   ├── rm_65_config.yaml          #65配置文件
│   ├── rm_75_config.yaml          #75配置文件
│   ├── rm_eco65_config.yaml       #eco65配置文件
│   ├── rm_eco63_config.yaml       #eco63配置文件
│   └── rm_gen72_config.yaml       #gen72配置文件
├── doc
│   ├── RealMan Robotic Arm rm_driver Topic Detailed Description (ROS2).md
│   ├── rm_driver1.png
│   ├── rm_driver2.png
│   ├── rm_driver3.png
│   ├── rm_driver4.png
│   └── 睿尔曼机械臂ROS2rm_driver话题详细说明.md
├── include                        #依赖头文件文件夹
│   └── rm_driver
│       ├── cJSON.h                #API头文件
│       ├── constant_define.h      #API头文件
│       ├── rman_int.h             #API头文件
│       ├── rm_base_global.h       #API头文件
│       ├── rm_base.h              #API头文件
│       ├── rm_define.h            #API头文件
│       ├── rm_driver.h            #rm_driver.cpp头文件
│       ├── rm_praser_data.h       #API头文件
│       ├── rm_queue.h             #API头文件
│       ├── rm_service_global.h    #API头文件
│       ├── rm_service.h           #API头文件
│       └── robot_define.h         #API头文件
├── launch
│   ├── rm_63_driver.launch.py     #63启动文件
│   ├── rm_65_driver.launch.py     #65启动文件
│   ├── rm_75_driver.launch.py     #75启动文件
│   ├── rm_eco65_driver.launch.py  #eco65启动文件
│   ├── rm_eco63_driver.launch.py  #eco63启动文件
│   └── rm_gen72_driver.launch.py  #gen72启动文件
├── lib
│   ├── libRM_Service.so -> libRM_Service.so.1.0.0        #API库文件
│   ├── libRM_Service.so.1 -> libRM_Service.so.1.0.0      #API库文件
│   ├── libRM_Service.so.1.0 -> libRM_Service.so.1.0.0    #API库文件
│   ├── libRM_Service.so.1.0.0                            #API库文件
│   ├── linux_arm_service_release_v4.3.7.t7.tar.bz2       #API库文件
│   └── linux_x86_service_release_v4.3.7.t7.tar.bz2       #API库文件
├── package.xml                                           #依赖声明文件
├── README_CN.md
├── README.md
└── src
    └── rm_driver.cpp                                     #驱动代码源文件
```

## 3\. rm\_driver话题说明

rm\_driver的话题较多，基于机械臂API实现机械臂本体的功能。 运行功能包后可以通过如下指令了解其话题信息:

```
ros2 topic list
```

话题如下：

```
/joint_states
/parameter_events
/rm_driver/change_work_frame_cmd
/rm_driver/change_work_frame_result
/rm_driver/clear_force_data_cmd
/rm_driver/clear_force_data_result
/rm_driver/force_position_move_cmd
/rm_driver/force_position_move_joint_cmd
/rm_driver/force_position_move_pose_cmd
/rm_driver/get_all_tool_frame_cmd
/rm_driver/get_all_tool_frame_result
/rm_driver/get_all_work_frame_cmd
/rm_driver/get_all_work_frame_result
/rm_driver/get_curr_workFrame_cmd
/rm_driver/get_curr_workFrame_result
/rm_driver/get_current_arm_original_state_result
/rm_driver/get_current_arm_state_cmd
/rm_driver/get_current_arm_state_result
/rm_driver/get_current_tool_frame_cmd
/rm_driver/get_current_tool_frame_result
/rm_driver/get_force_data_cmd
/rm_driver/get_force_data_result
/rm_driver/get_lift_state_cmd
/rm_driver/get_lift_state_result
/rm_driver/get_realtime_push_cmd
/rm_driver/get_realtime_push_result
/rm_driver/get_rm_plus_mode_cmd
/rm_driver/get_rm_plus_mode_result
/rm_driver/get_rm_plus_touch_cmd
/rm_driver/get_rm_plus_touch_result
/rm_driver/get_tool_force_data_result
/rm_driver/get_work_force_data_result
/rm_driver/get_zero_force_data_result
/rm_driver/move_stop_cmd
/rm_driver/move_stop_result
/rm_driver/movec_cmd
/rm_driver/movec_result
/rm_driver/movej_canfd_cmd
/rm_driver/movej_canfd_custom_cmd
/rm_driver/movej_cmd
/rm_driver/movej_p_cmd
/rm_driver/movej_p_result
/rm_driver/movej_result
/rm_driver/movel_cmd
/rm_driver/movel_result
/rm_driver/movep_canfd_cmd
/rm_driver/movep_canfd_custom_cmd
/rm_driver/set_force_postion_cmd
/rm_driver/set_force_postion_result
/rm_driver/set_gripper_pick_cmd
/rm_driver/set_gripper_pick_on_cmd
/rm_driver/set_gripper_pick_on_result
/rm_driver/set_gripper_pick_result
/rm_driver/set_gripper_position_cmd
/rm_driver/set_gripper_position_result
/rm_driver/set_hand_angle_cmd
/rm_driver/set_hand_angle_result
/rm_driver/set_hand_follow_angle_cmd
/rm_driver/set_hand_follow_angle_result
/rm_driver/set_hand_follow_pos_cmd
/rm_driver/set_hand_follow_pos_result
/rm_driver/set_hand_force_cmd
/rm_driver/set_hand_force_result
/rm_driver/set_hand_posture_cmd
/rm_driver/set_hand_posture_result
/rm_driver/set_hand_seq_cmd
/rm_driver/set_hand_seq_result
/rm_driver/set_hand_speed_cmd
/rm_driver/set_hand_speed_result
/rm_driver/set_joint_err_clear_cmd
/rm_driver/set_joint_err_clear_result
/rm_driver/set_joint_teach_cmd
/rm_driver/set_joint_teach_result
/rm_driver/set_lift_height_cmd
/rm_driver/set_lift_height_result
/rm_driver/set_lift_speed_cmd
/rm_driver/set_lift_speed_result
/rm_driver/set_ort_teach_cmd
/rm_driver/set_ort_teach_result
/rm_driver/set_pos_teach_cmd
/rm_driver/set_pos_teach_result
/rm_driver/set_realtime_push_cmd
/rm_driver/set_realtime_push_result
/rm_driver/set_rm_plus_mode_cmd
/rm_driver/set_rm_plus_mode_result
/rm_driver/set_rm_plus_touch_cmd
/rm_driver/set_rm_plus_touch_result
/rm_driver/set_stop_teach_cmd
/rm_driver/set_stop_teach_result
/rm_driver/set_tool_voltage_cmd
/rm_driver/set_tool_voltage_result
/rm_driver/start_force_position_move_cmd
/rm_driver/start_force_position_move_result
/rm_driver/stop_force_position_move_cmd
/rm_driver/stop_force_position_move_result
/rm_driver/stop_force_postion_cmd
/rm_driver/stop_force_postion_result
/rm_driver/udp_arm_coordinate
/rm_driver/udp_arm_current_status
/rm_driver/udp_arm_position
/rm_driver/udp_hand_status
/rm_driver/udp_joint_current
/rm_driver/udp_joint_en_flag
/rm_driver/udp_joint_error_code
/rm_driver/udp_joint_pose_euler
/rm_driver/udp_joint_speed
/rm_driver/udp_joint_temperature
/rm_driver/udp_joint_voltage
/rm_driver/udp_one_force
/rm_driver/udp_one_zero_force
/rm_driver/udp_rm_err
/rm_driver/udp_rm_plus_base
/rm_driver/udp_rm_plus_state
/rm_driver/udp_six_force
/rm_driver/udp_six_zero_force
/rosout
```
