# 图像模态（GoPro / v4l2 相机链路）

本页定义阶段一图像模态的采集链路、topic 契约和关键配置。图像是 Octopus 显示链路和 raw MCAP 录制链路共同消费的核心模态。

## 定位

本页回答：图像数据是怎么进 ROS 的？发布的 topic 叫什么、是什么格式？

本页不涉及相机硬件身份的稳定映射策略（见 `40_身份与稳定性/01_硬件身份策略.md`），也不涉及 Octopus 如何渲染图像（见 `30_Octopus运转逻辑/02_显示链路.md`）。

## 采集链路

```text
相机本体(GoPro 或其它)
  → USB 采集卡
  → /dev/videoX (v4l2 设备)
  → v4l2_camera_node (gopro_camera_launch 启动)
  → /gopro_{left,right}/image_raw  (sensor_msgs/Image)
  → /gopro_{left,right}/camera_info (sensor_msgs/CameraInfo)
```

关键点：相机本体在阶段一被视为可替换的"黑盒"。无论物理相机是 GoPro 还是其它型号，只要通过 USB 采集卡接入 v4l2，就沿用这条链路和这套 topic 命名。

## topic 契约

| topic | 消息类型 | namespace | 说明 |
|---|---|---|---|
| `/gopro_left/image_raw` | `sensor_msgs/msg/Image` | `gopro_left` | 左相机图像 |
| `/gopro_right/image_raw` | `sensor_msgs/msg/Image` | `gopro_right` | 右相机图像 |
| `/gopro_left/camera_info` | `sensor_msgs/msg/CameraInfo` | `gopro_left` | 左相机标定信息 |
| `/gopro_right/camera_info` | `sensor_msgs/msg/CameraInfo` | `gopro_right` | 右相机标定信息 |

左右相机是**两个独立的 `v4l2_camera_node` 实例**，通过 `namespace` 区分，发布到各自的 topic 空间下。

## 关键配置（v4l2 参数）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `video_device` | `/dev/v4l/by-path/...` | 设备路径，用 by-path 稳定路径而非 `/dev/video4` |
| `pixel_format` | `YUYV` | v4l2 采集像素格式（v2 起**可参数化**） |
| `output_encoding` | `rgb8` | ROS Image 输出编码（v2 起**可参数化**） |
| `frame_rate` | `30` | 目标帧率 |
| `use_v4l2_buffer_timestamps` | `true` | 用 v4l2 硬件缓冲区时间戳，非 ROS 时钟 |
| `use_sensor_data_qos` | `true` | QoS 用 BEST_EFFORT（sensor_data profile） |
| `frame_id` | `gopro_{left,right}_optical_frame` | 相机光学坐标系 |

v4l2_camera 包未暴露 `publish_rate` 参数，且 `time_per_frame` 单独设置不生效。因此 `gopro_pose_record.launch.py` 在启动节点**之前**会先执行 `v4l2-ctl --set-parm <frame_rate>` 来设置帧率。

## 时间戳来源

图像消息的 `header.stamp` 来自 v4l2 硬件缓冲区时间戳（`use_v4l2_buffer_timestamps: true`），**不是 ROS 时钟**。详见 `10_数据流与产物/03_时间戳与时钟模型.md`。

## topic 名锁定约定

相机本体可替换，但 **topic 名锁定为 `/gopro_*/image_raw` 不变**。这是阶段一的明确设计决策：

- 更换物理相机（GoPro → 工业相机或其它）不需要改 topic 名。
- 下游（Octopus 显示、raw MCAP 录制、阶段二清洗）对 `/gopro_*/image_raw` 的依赖保持稳定，无需同步改名。
- 相机改动只需调整 `video_device`、`pixel_format`、`output_encoding` 等接入参数。

## 详细内容

- 启动包源码：`src/data_collection/gopro_camera_launch/`
- launch 入口：`src/data_collection/gopro_camera_launch/launch/gopro_pose_record.launch.py`
- 默认配置：`src/data_collection/gopro_camera_launch/config/gopro_camera.yaml`
- 生产配置：`config/all_sensor_nodes.yaml`（`gopro.left/right` 节）
- 硬件身份：`40_身份与稳定性/01_硬件身份策略.md`
