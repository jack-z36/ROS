# 核心 topic 清单

本页是阶段一所有核心 topic 的路由总表，标注每个 topic 的发布者、消费者、消息类型、频率和 QoS。

## 定位

本页是"谁发布谁订阅"的速查表。它解决一个常见困惑：Octopus 的**显示订阅**和**录制订阅**是两套独立的订阅，topic 在两者中的角色不同。

## 核心 topic 路由表

以下是 Octopus 默认关心的 8 个核心 topic（2 图像 + 2 位姿 + 4 触觉）：

| topic | 消息类型 | 发布者 | 显示订阅 | 录制订阅 | 频率 | QoS |
|---|---|---|---|---|---|---|
| `/gopro_left/image_raw` | `sensor_msgs/msg/Image` | `gopro_left_camera` (v4l2) | 固定订阅 | 默认勾选 | 30Hz | BEST_EFFORT |
| `/gopro_right/image_raw` | `sensor_msgs/msg/Image` | `gopro_right_camera` (v4l2) | 固定订阅 | 默认勾选 | 30Hz | BEST_EFFORT |
| `/baton_mini_left/fast_odom` | `nav_msgs/msg/Odometry` | `baton_mini` (左) | 固定订阅 | 默认勾选（60Hz节流） | 200Hz原始/60Hz录制 | reliable |
| `/baton_mini_right/fast_odom` | `nav_msgs/msg/Odometry` | `baton_mini` (右) | 固定订阅 | 默认勾选（60Hz节流） | 200Hz原始/60Hz录制 | reliable |
| `/pressure/left_hand/gripper_1` | `PressureFrame` | `pressure_driver_node` | 固定订阅 | 默认勾选 | 100Hz | reliable |
| `/pressure/left_hand/gripper_2` | `PressureFrame` | `pressure_driver_node` | 固定订阅 | 默认勾选 | 100Hz | reliable |
| `/pressure/right_hand/gripper_1` | `PressureFrame` | `pressure_driver_node` | 固定订阅 | 默认勾选 | 100Hz | reliable |
| `/pressure/right_hand/gripper_2` | `PressureFrame` | `pressure_driver_node` | 固定订阅 | 默认勾选 | 100Hz | reliable |

## 显示订阅 vs 录制订阅

Octopus 内部有**两个独立的 ROS 节点**，各自维护一套订阅：

| | 显示链路（`octopus` 节点） | 录制链路（`recorder` 节点） |
|---|---|---|
| 订阅方式 | **固定订阅** 8 个 topic（硬编码在 `subscribeTopics()`） | **勾选订阅**（用户在 Operation 面板勾选） |
| 订阅时机 | `MainWindow` 构造时立即建立 | 点击 Start 时才建立 |
| 用途 | 驱动 Qt 面板实时显示 | 写入 raw MCAP |
| QoS | typed subscription | generic subscription（收 SerializedMessage） |
| 节点关系 | 独立 executor + 独立线程 | 独立 executor + 独立线程 |

关键推论：**显示面板能看到数据，不代表 recorder 节点已经订阅了该 topic。** 录制必须在 Operation 面板勾选并点击 Start。

详见 `30_Octopus运转逻辑/01_双链路架构总览.md`。

## 非核心 topic（可选录制）

以下 topic 不在 Octopus 的默认 8 个录制列表内，但可在 Operation 面板手动勾选录制：

| topic | 消息类型 | 发布者 | 说明 |
|---|---|---|---|
| `/baton_mini_{left,right}/imu` | `sensor_msgs/msg/Imu` | `baton_mini` | IMU 200Hz |
| `/baton_mini_{left,right}/odometry` | `nav_msgs/msg/Odometry` | `baton_mini` | VIO 算法位姿 |
| `/baton_mini_{left,right}/image_left` | `sensor_msgs/msg/Image` | `baton_mini` | 双目左目 640×480 mono8 |
| `/baton_mini_{left,right}/image_right` | `sensor_msgs/msg/Image` | `baton_mini` | 双目右目 640×480 mono8 |
| `/gopro_{left,right}/camera_info` | `sensor_msgs/msg/CameraInfo` | `gopro_*_camera` | 相机标定信息 |

注意：录制链路只录制 Start 时刻 ROS graph 中**已存在**的 topic；不存在的勾选项会被静默跳过。详见 `30_Octopus运转逻辑/03_录制链路.md`。

## 各模态详情

- 图像模态：`01_图像模态_GoPro.md`
- 位姿模态：`02_位姿模态_BatonMini.md`
- 触觉模态：`03_触觉模态_HWK.md`

## 详细内容

- 显示链路固定订阅源码：`src/data_collection/VTLA_octopus-master/octopus/src/mainwindow.cpp`（`subscribeTopics()`）
- 默认录制 topic 源码：`src/data_collection/VTLA_octopus-master/octopus/src/utils/config.cpp`
- 录制订阅逻辑：`src/data_collection/VTLA_octopus-master/octopus/src/mcap-recorder.cpp`
