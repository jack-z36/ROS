---
name: baton_mini 架构说明

description: Baton Mini 双目相机 ROS SDK Demo 包的完整架构、接口、通信协议和使用方法

type: reference

originSessionId: 93e31d10-2492-4e58-b781-08963f9a7141
---
# baton_mini 架构说明

## 包位置

`src/baton_mini_sdk_demo/`，构建输出在 `build/baton_mini/`。

## 概述

Baton Mini 双目相机的 SDK Demo，提供视觉惯性里程计（VIO）功能。支持 ROS1（Noetic）/ ROS2（Humble）双版本自动切换构建。

## 目录结构

```

src/baton_mini_sdk_demo/

├── CMakeLists.txt                 # 通过 ROS_VERSION 环境变量自动选择 ROS1/ROS2 构建

├── package.xml                    # ament_cmake/catkin 双格式

├── ros_build.sh                   # ROS 构建脚本

├── build_non_ros.sh               # 非 ROS 独立构建

├── README_EN.md / readme.md       # 英文/中文文档

├── include/

│   ├── baton_mini.h               # pose_t / speed_t / odom_t 数据结构

│   ├── baton_cmd.h                # API 端点、枚举（system_status, image_get, recv_switch）、标定参数结构

│   ├── baton_ros.h                # 旧版 ROS 接口（已废弃）

│   ├── io/ros_interface.h         # ROS1/ROS2 统一抽象层（ROS_IO 类）

│   └── nlohmann/json.hpp          # JSON 库

├── src/

│   ├── baton_mini.cpp             # 主入口：SDK 初始化、登录、回调注册、命令线程

│   ├── baton_cmd.cpp              # 设备控制命令（算法开关、IMU/图像/里程计开关、IP/网络配置、版本查询）

│   ├── io/ros_interface.cpp       # ROS_IO 实现：Publisher 创建、消息发布、参数读取

│   └── sdk/

│       ├── vio_sdk.cpp/h          # VIO SDK 主接口

│       ├── vio_msg.cpp/h          # VIO 消息处理

│       ├── imu_tcp.hpp            # IMU TCP 接收（端口 9996，54 字节包，200Hz）

│       ├── image_tcp.hpp          # 图像 TCP 接收（端口 9997 左目 / 9998 右目，640x480 mono8）

│       ├── odom_tcp.hpp           # 快速里程计 TCP 接收（端口 9994，65 字节包，200Hz）

│       ├── CommonSocket.cpp/h     # Socket 通信

│       ├── CHttpRequest.cpp/h     # HTTP 请求

│       ├── cJSON.cpp/h            # JSON 解析

│       ├── Base64.cpp/h           # Base64 编解码

│       └── syslib.cpp/h           # 系统工具

└── launch/

    ├── baton_mini.launch          # ROS1 launch

    └── baton_mini.launch.py       # ROS2 launch

```

## 架构分层

```

┌─────────────────────────────────────────────┐

│  baton_mini.cpp（主程序）                     │

│  初始化 SDK → 登录设备 → 启动算法/数据流       │

│  注册回调 → 启动命令交互线程                   │

├──────────────────┬──────────────────────────┤

│  baton_cmd.cpp   │  io/ros_interface.cpp     │

│  设备控制命令     │  ROS 消息发布              │

│  （HTTP API）    │  （ROS1/ROS2 统一封装）     │

├──────────────────┴──────────────────────────┤

│  SDK 层 (src/sdk/)                           │

│  vio_sdk → TCP 接收线程（IMU/图像/里程计）     │

│  回调函数将数据传递到上层                      │

├─────────────────────────────────────────────┤

│  硬件设备（Baton Mini 相机）                   │

│  IP: 192.168.1.10，TCP 端口 9994/9996/9997/9998 │

└─────────────────────────────────────────────┘

```

## 数据流

1.**IMU**: 设备 → TCP:9996 → imu_tcp.hpp → 回调 → ros_interface 发布 sensor_msgs/Imu

2.**快速里程计**: 设备 → TCP:9994 → odom_tcp.hpp → 回调 → ros_interface 发布 nav_msgs/Odometry

3.**算法里程计**: SDK 内部 VIO 算法 → 回调 → ros_interface 发布 nav_msgs/Odometry

4.**双目图像**: 设备 → TCP:9997/9998 → image_tcp.hpp → 回调 → ros_interface 发布 sensor_msgs/Image（与 IMU 关键帧时间戳同步）

## 通信协议

所有 TCP 数据包使用自定义二进制协议：

- 帧头: `0x66 0x10`
- 帧尾: `0x55 0x99`
- 校验和验证
- IMU 包: 54 字节（3 轴加速度 + 3 轴角速度 + 关键帧标志）
- 里程计包: 65 字节（位姿 + 速度 + 时间戳）
- 图像包: 4 字节长度头 + 图像数据

## ROS2 接口详情

### 节点名

`baton_mini`

### 参数

| 参数 | 默认值 | 说明 |

|------|--------|------|

| server_ip | 192.168.1.10 | 设备 IP |

| local_ip | 192.168.1.18 | 本机 IP（launch 文件默认值，代码中为 192.168.1.16） |

| imu_topic | /baton_mini/imu | IMU 话题 |

| odom_topic | /baton_mini/odometry | 里程计话题 |

| fast_odom_topic | /baton_mini/fast_odometry | 快速里程计话题 |

| image_left_topic | /baton_mini/image_left | 左目图像话题 |

| image_right_topic | /baton_mini/image_right | 右目图像话题 |

### 发布话题

| 话题 | 消息类型 | 频率 | 说明 |

|------|----------|------|------|

| /baton_mini/imu | sensor_msgs/Imu | 200Hz | IMU 数据 |

| /baton_mini/odometry | nav_msgs/Odometry | 算法帧率 | VIO 算法位姿输出 |

| /baton_mini/fast_odometry | nav_msgs/Odometry | 200Hz | 高频快速里程计 |

| /baton_mini/image_left | sensor_msgs/Image | 帧率 | 640x480 mono8 |

| /baton_mini/image_right | sensor_msgs/Image | 帧率 | 640x480 mono8 |

### 交互命令

启动后自动开启算法 + IMU + 快速里程计，进入键盘交互模式：

| 按键 | 功能 |

|------|------|

| 0 | 退出并注销 |

| 1 | 启动/停止 stereo3 算法 |

| 2 | 重启算法 |

| 3 | 开关 IMU 接收 |

| 4 | 开启双目图像接收 |

| 5 | 开关快速里程计接收 |

## 构建与运行

```bash

# 构建

cd. && colconbuild--packages-selectbaton_mini

sourceinstall/setup.bash


# 运行（ROS2）

ros2launchbaton_minibaton_mini.launch.pyserver_ip:=<设备IP>local_ip:=<本机IP>


# 运行（ROS1）

roslaunchbaton_minibaton_mini.launchserver_ip:=<设备IP>local_ip:=<本机IP>

```

## 约束与注意事项

- 设备固件版本需 > 2025-03-17
- 200Hz 快速里程计在高振动场景下不建议使用
- 图像时间戳通过 IMU 关键帧同步
- CMakeLists.txt 通过 `ROS_VERSION` 环境变量自动检测 ROS1/ROS2
- 设备控制命令通过 HTTP API 发送（非 ROS 服务）
