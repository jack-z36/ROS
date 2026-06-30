# Data Collection — 环境依赖

## 运行环境

**不使用 conda 环境**。本项目依赖 ROS2 系统包 + 系统 Python。

### 系统依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| ROS2 Jazzy | `/opt/ros/jazzy/setup.bash` | 系统 apt |
| python3-serial | HWK 压力传感器驱动 | `sudo apt install python3-serial` |
| python3-yaml | 配置文件解析 | `sudo apt install python3-yaml` |
| v4l2-camera | GoPro ROS2 节点依赖 | `sudo apt install ros-jazzy-v4l2-camera` |
| v4l-utils | 视频设备工具 | `sudo apt install v4l-utils` |
| Qt 6.11.0 | Octopus 录制 GUI | `~/Qt/6.11.0/gcc_64` |

### 构建方式

从工作空间根目录执行：

```bash
source /opt/ros/jazzy/setup.bash
colcon build
```

### 包列表

| 包名 | 路径 | 说明 |
|------|------|------|
| baton_mini_sdk_demo | baton_mini_sdk_demo/ | Baton Mini 双目 VIO 相机 (C++) |
| gopro_camera_launch | gopro_camera_launch/ | GoPro HDMI 相机 ROS2 启动 |
| hwk_pressure_driver | hwk_pressure_driver/ | HWK 灵巧手压力传感器驱动 |
| hwk_pressure_interfaces | hwk_pressure_interfaces/ | 压力传感器消息定义 |
| VTLA_octopus-master | VTLA_octopus-master/ | Octopus 多模态数据录制器 (C++/Qt) |

### 启动入口

```bash
./start_all_sensor.sh          # 启动所有传感器
./start_octopus.sh             # 启动 Octopus 录制 GUI
./start_gopro_only.sh           # 仅启动 GoPro
```
