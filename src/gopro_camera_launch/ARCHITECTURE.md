# gopro_camera_launch 架构文档

## 概述

轻量级 ROS 2 launch 包，专注于 GoPro HDMI 相机的图像采集。录制、位姿桥接和 TF 发布功能已在重构中移除，交由独立包处理。

## 数据流

```
GoPro Camera (HDMI Output)
    → 视频采集卡 (USB/HDMI)
    → Linux V4L2 设备 (/dev/video4)
    → v4l2_camera_node (ROS 2)
    → /<namespace>/image_raw (sensor_msgs/Image, RGB8, 640x480, 30fps)
    → /<namespace>/camera_info (sensor_msgs/CameraInfo)
```

## 目录结构

```
gopro_camera_launch/
├── launch/
│   └── gopro_pose_record.launch.py   # 唯一 launch 文件，启动 v4l2_camera 节点
├── config/
│   └── gopro_camera.yaml             # V4L2 相机参数配置
├── gopro_camera_launch/
│   └── __init__.py                   # 包标记文件（无自定义节点）
├── resource/
│   └── gopro_camera_launch           # ament 包索引标记
├── package.xml                       # ROS 2 包清单
├── setup.py                          # Python 安装配置
└── setup.cfg                         # 安装目录配置
```

## 核心组件

### 1. Launch 文件 (`launch/gopro_pose_record.launch.py`)

启动单个 `v4l2_camera` 节点：

- **节点名**: `gopro_camera`
- **可执行文件**: `v4l2_camera_node`（来自 `v4l2_camera` 包）
- **启动前动作**: 先执行 `v4l2-ctl --set-parm <frame_rate>`，再启动相机节点，用于明确设置采集卡 V4L2 帧率。

**Launch 参数**:
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `video_device` | `/dev/video4` | V4L2 设备路径 |
| `frame_rate` | `30` | 通过 `v4l2-ctl --set-parm` 设置的目标采集帧率 |
| `publish_camera_info` | `true` | 是否发布相机标定信息 |
| `camera_namespace` | `gopro` | 节点命名空间 |
| `node_name` | `gopro_camera` | 节点名称 |
| `camera_name` | `gopro` | 相机名称 |
| `frame_id` | `camera_optical_frame` | TF 帧标识 |
| `image_raw_topic` | `image_raw` | 图像话题名 |
| `camera_info_topic` | `camera_info` | 相机信息话题名 |

**节点参数**:
| 参数 | 值 | 说明 |
|------|----|------|
| `camera_name` | `gopro` | 相机名称 |
| `frame_id` | `camera_optical_frame` | TF 帧标识 |
| `use_v4l2_buffer_timestamps` | `true` | 使用硬件时间戳 |
| `image_size` | `[640, 480]` | 分辨率 |
| `time_per_frame` | `[1, 30]` | 保留配置项；当前实机以 launch 前置 `v4l2-ctl --set-parm` 为准 |
| `pixel_format` | `YUYV` | 视频格式 |
| `output_encoding` | `rgb8` | ROS 图像编码 |

**话题重映射**:
- `image_raw` → `<image_raw_topic>`
- `camera_info` → `<camera_info_topic>`

### 2. 配置文件 (`config/gopro_camera.yaml`)

V4L2 相机完整参数配置，launch 文件通过 `FindPackageShare` 定位并加载。

### 3. 自动化脚本 (`start_capture_demo.sh`)

| 命令 | 功能 |
|------|------|
| `build` | colcon 构建包 |
| `run` | 启动相机节点 |
| `verify` | 打印验证命令 |
| `help` | 显示帮助 |

环境变量 `VIDEO_DEVICE` 可覆盖默认设备路径。

## 发布话题

| 话题 | 类型 | 频率 | 说明 |
|------|------|------|------|
| `/<namespace>/image_raw` | `sensor_msgs/msg/Image` | 30 Hz | RGB8 图像，640x480 |
| `/<namespace>/camera_info` | `sensor_msgs/CameraInfo` | 30 Hz | 相机标定信息 |

## 依赖

| 依赖 | 用途 |
|------|------|
| `v4l2_camera` | V4L2 相机驱动节点（核心依赖） |
| `v4l-utils` / `v4l2-ctl` | 启动前设置采集卡帧率和诊断 V4L2 设备 |
| `launch` / `launch_ros` | ROS 2 launch 系统 |
| `sensor_msgs` | 传感器消息定义 |

## 构建与运行

```bash
# 构建
colcon build --packages-select gopro_camera_launch
source install/setup.bash

# 运行（默认设备）
ros2 launch gopro_camera_launch gopro_pose_record.launch.py

# 运行（指定设备）
ros2 launch gopro_camera_launch gopro_pose_record.launch.py video_device:=/dev/video2

# 验证
ros2 topic hz /gopro/image_raw
ros2 topic echo /gopro/camera_info --once
```

## 已移除的功能

以下组件在重构中被移除，应由独立包处理：
- `image_topic_relay.py` — 内部话题中转节点（因帧率瓶颈于 2026-04-28 移除，v4l2_camera_node 现直接发布到公开命名空间）
- `external_pose_bridge.py` — 外部位姿桥接节点
- `image_activity_monitor.py` — 图像活动监控
- `sync_monitor.py` — 多传感器同步
- 静态 TF 发布器
- MCAP/rosbag 录制
- `/camera/pose`、`/sensor_time_reference`、`/tf`、`/tf_static` 话题

## 关键设计决策

- **单一职责**: 仅处理 GoPro 图像采集
- **硬件时间戳**: 优先使用 V4L2 buffer 时间戳保证精度
- **模块化**: 录制/位姿/TF 功能解耦到独立包
- **命名约定**: 话题命名空间 `/gopro/`，frame_id 为 `camera_optical_frame`
- **多实例隔离**: 当总 launch 同时 include 两个 GoPro 实例时，每个 include 必须使用独立 scoped launch 上下文；本 launch 内部用 `OpaqueFunction` 立即解析参数，避免 `OnProcessExit` 延迟启动相机节点时发生 right/left 参数串扰。
