# dual_fisheye_camera

双鱼眼相机 ROS 2 节点包。通过 V4L2 持续将左右鱼眼相机的实时图像发布为 ACT 可订阅的 ROS 图像流，
并周期发布相机硬件健康状态。

## 一句话功能

通过 V4L2 持续将左右鱼眼相机的实时图像发布为 ACT 可订阅的 ROS 图像流。

## 发布 / 订阅

| 方向 | topic | msg | 说明 |
|---|---|---|---|
| 发布 | `/image/left_fisheye` | `sensor_msgs/msg/Image` | 左鱼眼图像，`encoding=rgb8` |
| 发布 | `/image/right_fisheye` | `sensor_msgs/msg/Image` | 右鱼眼图像，`encoding=rgb8` |
| 发布 | `/hardware/camera/health` | `act_interfaces/msg/HardwareHealth` | 相机健康状态（见下「Health 字段映射」） |
| 订阅 | 无 | — | 不订阅任何 ACT topic，不依赖外部触发 |

> topic 名均为 launch 参数，可在命令行覆盖（如切换到契约名 `/pi05/observation/image/left_gripper_fisheye`）。

## 落点说明

本包位于 `src/model_deploy/dual_fisheye_camera/`，符合强制落点约束（双鱼眼相机节点包）。
图像采集**复用**系统安装的 `v4l2_camera` 包的 `v4l2_camera_node`（不重写相机驱动，
遵循 `fisheye_camera_node 契约.md`）；本包自有的 `camera_health_node` 仅订阅两侧 image、
发布 health。包间只通过 ROS topic 通信，不跨包 import 其他硬件节点实现。

## 包结构

```
dual_fisheye_camera/
├── package.xml                          # ament_python
├── setup.py / setup.cfg
├── resource/dual_fisheye_camera         # ament 索引标记
├── dual_fisheye_camera/
│   ├── __init__.py
│   └── camera_health_node.py            # 订阅两侧 image，发布 HardwareHealth
├── config/dual_fisheye_camera.yaml      # 默认参数（对齐阶段一）
├── launch/dual_fisheye_camera.launch.py # 2x v4l2_camera_node + health 节点
└── README.md
```

## 依赖

- ROS 2 Jazzy（`/opt/ros/jazzy`）
- 系统包：`ros-jazzy-v4l2-camera`、`v4l-utils`（提供 `v4l2_camera_node` 与 `v4l2-ctl`）
- 本仓库包：`act_interfaces`（提供 `HardwareHealth.msg`，属独立 PR `act-hardware-interfaces`）

> **依赖顺序**：ROS 接口（act_interfaces）→ 相机（本包）。本包 `package.xml` 已声明
> `exec_depend act_interfaces`。本地构建前请确保 `act_interfaces` 已在同 workspace 的
> `src/` 下并 `colcon build` 完成。

## 构建

```bash
# 在 workspace 根（含 src/ 的目录）
cd <workspace>
colcon build --packages-select act_interfaces        # 先建接口
colcon build --packages-select dual_fisheye_camera   # 再建本包
source install/setup.bash
```

## 运行

```bash
# 用包内默认 config（设备路径需按真机核对）
ros2 launch dual_fisheye_camera dual_fisheye_camera.launch.py

# 通过命令行覆盖左右设备路径与帧率（生产推荐）
ros2 launch dual_fisheye_camera dual_fisheye_camera.launch.py \
  left_video_device:=/dev/v4l/by-path/<left-by-path> \
  right_video_device:=/dev/v4l/by-path/<right-by-path> \
  frame_rate:=30
```

## 验证

```bash
# 1. topic 存在 + 类型正确
ros2 topic list
ros2 topic info /image/left_fisheye          # 期望 sensor_msgs/msg/Image
ros2 topic info /hardware/camera/health      # 期望 act_interfaces/msg/HardwareHealth

# 2. 编码正确（encoding=rgb8, step=width*3）
ros2 topic echo --once /image/left_fisheye --field encoding
ros2 topic echo --once /image/left_fisheye --field step

# 3. 帧率稳定（接近配置帧率）
ros2 topic hz /image/left_fisheye

# 4. 左右不混淆：遮挡左相机，变化只出现在 /image/left_fisheye；
#    同时 /hardware/camera/health 的 left_connected 应变 false，right_connected 仍 true
ros2 topic echo /hardware/camera/health

# 5. launch 日志确认实际启动的是 v4l2_camera_node（而非重写的采集节点）
```

## Health 字段映射（相机场景）

`act_interfaces/HardwareHealth` 原为 RM65 双臂设计；相机场景下字段语义借用如下：

| 字段 | 相机场景填充 |
|---|---|
| `header.stamp` | health 发布时刻 |
| `left/right_connected` | 该侧在 `frame_timeout_sec`（默认 1.0s）内是否收到过帧 |
| `left/right_estop_active` | 固定 `false`（相机无急停概念） |
| `left/right_sdk_code` | 固定 `0`（相机无 SDK 返回码） |
| `left/right_controller_err` | 固定 `0`（相机无控制器错误码） |
| `left/right_reason` | `""` 正常 / `NO_FRAME_YET` 启动后未收到帧 / `STREAM_TIMEOUT` 断流 |

> 后续如需更贴切的相机语义（如帧间隔、解码错误计数），建议另立 Contract Delta，
> 在 `act_interfaces` 新增 `CameraHealth.msg`，而非继续借用 `HardwareHealth`。

## 关键约束（实现遵守情况）

- **设备路径**：默认值与 README 均使用 `/dev/v4l/by-path/...`；禁止生产配置使用裸 `/dev/videoX`。
- **输出编码**：固定 `rgb8`（对齐 Pi05 观测输入）。
- **时间戳**：`use_v4l2_buffer_timestamps=true`，优先 V4L2 buffer timestamp。
- **QoS**：`use_sensor_data_qos=true`（BEST_EFFORT）；health 节点订阅侧用 sensor_data 匹配发布方。
- **单路断流不影响另一路**：health 节点对左右独立计时；v4l2_camera_node 各自独立实例。
- **不重写驱动**：图像采集完全复用 `v4l2_camera_node`。

## 未验证项（无真机环境时）

- [ ] 真机左右鱼眼相机的实际 `/dev/v4l/by-path/...` 路径（需在部署机上 `ls /dev/v4l/by-path/` 核对）
- [ ] 工业鱼眼相机实际支持的像素格式（YUYV / MJPG）与分辨率——默认按阶段一 640×480 @30Hz YUYV
- [ ] 30Hz 下 `ros2 topic hz` 的实际稳定性
- [ ] 遮挡左右相机时 health 字段的真实翻转行为
- [ ] USB 拔插后的重连行为（依赖 `v4l2_camera_node` 自身语义）

## 真机风险 / 急停准备

- 相机节点本身**不发送任何硬件控制指令**，风险面仅在图像采集。
- 若相机异常导致下游 policy 异常，应由上游 `manual_safety_controller`（待建）的 CommandPermit fail-closed 机制兜底，
  本包不承担急停职责。
- 部署前务必用 `v4l2-ctl -d <by-path> --all` 确认设备支持设定的像素格式与帧率，避免 open 失败反复重试。
