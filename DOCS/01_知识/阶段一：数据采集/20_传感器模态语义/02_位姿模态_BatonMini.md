# 位姿模态（Baton Mini 双目 VIO 相机）

本页定义阶段一位姿模态的硬件接入、通信协议、topic 契约和使用约束。Baton Mini 提供 IMU、里程计和双目图像，是 Octopus 位姿面板的数据来源。

## 定位

本页回答：Baton Mini 是怎么接入 ROS 的？它发什么 topic、什么格式、什么频率？

本页不涉及 Octopus 如何显示位姿（见 `30_Octopus运转逻辑/02_显示链路.md`），也不涉及录制链路对 fast_odom 的 60Hz 节流（见 `10_数据流与产物/02_raw_MCAP产物语义.md`）。

## 硬件接入

```text
Baton Mini 双目 VIO 相机 (固定 IP 192.168.1.10)
  → 以太网/TCP
  → baton_mini 节点 (baton_mini_sdk_demo)
  → /baton_mini_{left,right}/{imu,odometry,fast_odom,image_left,image_right}
```

Baton Mini 是网络相机，本机通过 `local_ip`（默认 192.168.1.18）与之通信。设备控制命令走 HTTP API，数据流走 TCP。

## TCP 端口与数据流

| 数据 | TCP 端口 | 包大小 | 频率 | 发布的 ROS 消息类型 |
|---|---|---|---|---|
| IMU | 9996 | 54 字节 | 200Hz | `sensor_msgs/msg/Imu` |
| 快速里程计 (fast_odom) | 9994 | 65 字节 | 200Hz | `nav_msgs/msg/Odometry` |
| 左目图像 | 9997 | 4字节长度头+图像 | 帧率 | `sensor_msgs/msg/Image` |
| 右目图像 | 9998 | 4字节长度头+图像 | 帧率 | `sensor_msgs/msg/Image` |
| 算法里程计 (VIO) | SDK 内部 | — | 算法帧率 | `nav_msgs/msg/Odometry` |

## topic 契约

左右两台 Baton Mini 通过 namespace 区分：

| topic | 消息类型 | 说明 |
|---|---|---|
| `/baton_mini_left/fast_odom` | `nav_msgs/msg/Odometry` | 左位姿（Octopus 默认录制） |
| `/baton_mini_right/fast_odom` | `nav_msgs/msg/Odometry` | 右位姿（Octopus 默认录制） |
| `/baton_mini_{left,right}/imu` | `sensor_msgs/msg/Imu` | IMU（可选录制） |
| `/baton_mini_{left,right}/odometry` | `nav_msgs/msg/Odometry` | VIO 算法位姿（可选录制） |
| `/baton_mini_{left,right}/image_{left,right}` | `sensor_msgs/msg/Image` | 双目图像 640×480 mono8（可选录制） |

注意 topic 命名中的 `left/right` 有两层含义：外层 `baton_mini_{left,right}` 是左右两台设备，内层 `image_{left,right}` 是单台设备的双目左右摄像头。

## 通信协议

所有 TCP 数据包使用自定义二进制协议：

- 帧头：`0x66 0x10`
- 帧尾：`0x55 0x99`
- 校验和验证
- IMU 包：3 轴加速度 + 3 轴角速度 + 关键帧标志
- 里程计包：位姿 + 速度 + 时间戳

## 时间戳来源

- **图像**：时间戳由 IMU 关键帧同步（固件内部完成），非 ROS 时钟。
- **IMU / odom**：由 SDK 内部时钟打，TCP 包携带。

详见 `10_数据流与产物/03_时间戳与时钟模型.md`。

## 使用约束

- **固件版本**：设备固件版本必须 > 2025-03-17，否则协议不兼容。
- **200Hz fast_odom**：在高振动场景下不建议使用，可能输出不稳定位姿。
- **录制节流**：Octopus 录制链路对 fast_odom 按 60Hz 节流，raw MCAP 中实际约 60Hz 而非 200Hz。
- **启动交互**：节点启动后进入键盘交互模式，按键 0-5 控制算法/数据流开关（详见 `batonmini运行指南.md`）。

## 坐标系

- `nav_msgs/Odometry` 含 `child_frame_id`，表示位姿参考坐标系。
- 具体 frame_id 命名规则见 `40_身份与稳定性/02_topic命名与frame_id.md`。

## 详细内容

- SDK demo 源码：`src/data_collection/baton_mini_sdk_demo/`
- 架构说明：`src/data_collection/baton_mini_sdk_demo/baton_mini_architecture.md`
- 运行指南：`src/data_collection/baton_mini_sdk_demo/batonmini运行指南.md`
- launch 入口（ROS2）：`src/data_collection/baton_mini_sdk_demo/launch/baton_mini.launch.py`
