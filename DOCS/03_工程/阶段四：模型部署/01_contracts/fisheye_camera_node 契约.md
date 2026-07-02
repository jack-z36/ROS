# fisheye_camera_node 契约

关联总契约：[[TO-BE Contract#传感器数据发送节点|传感器数据发送节点]]

## 节点定位

`fisheye_camera_node` 是相机观测发送节点，只负责从左 / 右夹爪工业鱼眼相机读取视频流，并发布给 `Pi05VlaDeployNode`。

它不做模型推理、不拼接左右图像、不发送任何硬件控制指令。

实现优先级：**优先直接复用阶段一数据采集模块的 `gopro_camera_launch` + `v4l2_camera_node` 链路**。这里的 `fisheye_camera_node` 是阶段四契约名，不要求重新写一个相机驱动节点；如果工业鱼眼相机能通过 V4L2 接入，则应通过配置 / launch include / topic remap 复用现有实现。

参考：

- [[01-doing/ROS/DOCS/01_知识/阶段一：数据采集/20_传感器模态语义/01_图像模态_GoPro.md]]
- [[01-doing/ROS/DOCS/01_知识/阶段一：数据采集/40_身份与稳定性/01_硬件身份策略.md]]
- `src/data_collection/gopro_camera_launch/`
- `src/data_collection/gopro_camera_launch/launch/gopro_pose_record.launch.py`
- `config/all_sensor_nodes.yaml`

## 上下游接口

| 方向 | topic | ROS msg | 现实语义 |
|---|---|---|---|
| 订阅 | 无 | 无 | 相机节点不依赖其他 ROS topic 触发。 |
| 发布 | `/pi05/observation/image/left_gripper_fisheye` | `sensor_msgs/msg/Image` | 左夹爪末端鱼眼相机采集到的当前画面。 |
| 发布 | `/pi05/observation/image/right_gripper_fisheye` | `sensor_msgs/msg/Image` | 右夹爪末端鱼眼相机采集到的当前画面。 |

## 输入读取契约

| 字段 | 契约 |
|---|---|
| 首选实现 | 复用 `gopro_camera_launch` 启动两个 `v4l2_camera_node` 实例。 |
| 读取接口 | V4L2。只有当工业鱼眼相机无法通过 V4L2 稳定接入时，才新增厂商 SDK adapter。 |
| 相机数量 | 2 路：`left_gripper_fisheye`、`right_gripper_fisheye`。 |
| 设备映射 | 沿用阶段一身份策略，优先使用 `/dev/v4l/by-path/...` 或 `/dev/v4l/by-id/...` 稳定路径；禁止依赖 `/dev/video4` 这类裸枚举号。 |
| 生产配置来源 | 优先复用 `config/all_sensor_nodes.yaml` 中 `gopro.left/right` 的结构，并将 `namespace`、`frame_id`、`video_device`、`frame_rate` 映射到阶段四相机。 |
| 默认采集像素格式 | 与阶段一 `gopro_camera.yaml` 对齐，默认 `pixel_format = YUYV`。如相机 / 采集卡只稳定支持 `MJPG`，可配置为 `MJPG`，但必须显式记录。 |
| ROS 输出编码 | 固定 `output_encoding = rgb8`。 |
| 分辨率与帧率 | 由配置指定；阶段一默认 `640x480 @ 30Hz`。如果阶段四模型训练使用其他分辨率，必须以模型训练分辨率为准。 |
| 帧率设置 | 沿用阶段一做法：启动 `v4l2_camera_node` 前先执行 `v4l2-ctl --set-parm <frame_rate>`。 |
| QoS | 沿用阶段一 `use_sensor_data_qos = true`，即 sensor_data QoS / BEST_EFFORT。 |
| 时间戳来源 | 沿用阶段一 `use_v4l2_buffer_timestamps = true`，优先使用 V4L2 buffer timestamp，而不是节点收到图像时的 ROS clock。 |

## 阶段一复用方式

| 复用项 | 阶段一实现 | 阶段四要求 |
|---|---|---|
| 相机驱动 | `v4l2_camera_node` | 直接复用，不重新实现采集循环。 |
| launch 包 | `gopro_camera_launch` | include 两次，分别对应左 / 右夹爪鱼眼相机。 |
| 配置结构 | `config/all_sensor_nodes.yaml` 的 `gopro.left/right` | 可沿用字段，但语义从 `gopro_left/right` 改成 `left/right_gripper_fisheye`。 |
| 稳定设备路径 | `/dev/v4l/by-path/...` | 必须使用稳定路径或序列号路径。 |
| 输出编码 | `rgb8` | 保持一致，直接供 `Pi05VlaDeployNode` 消费。 |
| 图像 topic | 阶段一为 `/gopro_left/image_raw`、`/gopro_right/image_raw` | 阶段四 remap 到 `/pi05/observation/image/left_gripper_fisheye`、`/pi05/observation/image/right_gripper_fisheye`。 |

推荐实现形态：

```text
deploy_camera_launch
  include gopro_pose_record.launch.py
    video_device := <left by-path>
    camera_namespace := pi05_camera_left
    node_name := left_gripper_fisheye_camera
    camera_name := left_gripper_fisheye
    frame_id := left_gripper_fisheye
    image_raw_topic := /pi05/observation/image/left_gripper_fisheye
    publish_camera_info := false

  include gopro_pose_record.launch.py
    video_device := <right by-path>
    camera_namespace := pi05_camera_right
    node_name := right_gripper_fisheye_camera
    camera_name := right_gripper_fisheye
    frame_id := right_gripper_fisheye
    image_raw_topic := /pi05/observation/image/right_gripper_fisheye
    publish_camera_info := false
```

如果 `gopro_pose_record.launch.py` 的参数不足以满足工业鱼眼相机，只允许在 `gopro_camera_launch` 上做小改造，例如暴露 `pixel_format`、`output_encoding`、`image_size`。不应另起一套重复的相机采集代码。


## 发布 msg 契约

| 字段 | 值 |
|---|---|
| `msg.header.stamp` | 图像采集时间。复用阶段一链路时优先来自 V4L2 buffer timestamp。 |
| `msg.header.frame_id` | 左相机为 `left_gripper_fisheye`；右相机为 `right_gripper_fisheye`。 |
| `msg.height` / `msg.width` | 解码后的图像高宽。 |
| `msg.encoding` | 固定为 `rgb8`。 |
| `msg.is_bigendian` | `0`。 |
| `msg.step` | `width * 3`。 |
| `msg.data` | `uint8` RGB 连续内存，通道顺序为 `R, G, B`。 |

## 与 Pi05VlaDeployNode 对齐

| Pi05 需求 | 本节点保证 |
|---|---|
| `Pi05VlaDeployNode` 需要左右夹爪鱼眼图像作为 policy observation。 | 固定发布左右两个独立 topic。 |
| `Pi05VlaDeployNode` 按 `sensor_msgs/msg/Image` 解码图像。 | 不发布裸字节流，不发布压缩包，不发布拼接图。 |
| policy 输入需要稳定时间语义。 | 每帧使用 V4L2 buffer timestamp 或明确的采集时刻写入 `header.stamp`；断流时不重复发布旧帧。 |
| Pi05 不关心阶段一历史 topic 名。 | 通过 launch remap 直接输出 `/pi05/observation/image/*`，避免额外 relay。 |

## 异常处理契约

| 场景 | 处理方式 |
|---|---|
| 相机打开失败 | 沿用 `v4l2_camera_node` 的失败语义；deploy launch 应明确日志打印失败设备。 |
| 单路相机断流 | 该路停止发布旧帧，按配置间隔重连；另一侧相机不受影响。 |
| 解码失败 | 丢弃当前帧，不发布半解析图像。 |
| 实际编码与配置不一致 | 日志报错；若能正确解码则继续运行，否则拒绝发布。 |
| 时间戳倒退 | 丢弃异常帧并记录诊断。 |

## 配置参数

| 参数 | 类型 | 含义 |
|---|---|---|
| `left_video_device` | string | 左夹爪鱼眼相机 V4L2 稳定路径，优先 `/dev/v4l/by-path/...`。 |
| `right_video_device` | string | 右夹爪鱼眼相机 V4L2 稳定路径，优先 `/dev/v4l/by-path/...`。 |
| `left_frame_id` | string | 默认 `left_gripper_fisheye`。 |
| `right_frame_id` | string | 默认 `right_gripper_fisheye`。 |
| `image_size` | int[2] | 期望图像宽高；默认沿用阶段一 `[640, 480]`，但应与训练数据一致。 |
| `frame_rate` | int | 期望采集帧率；默认沿用阶段一 `30`。 |
| `pixel_format` | string | 默认沿用阶段一 `YUYV`；可按硬件实测改为 `MJPG`。 |
| `output_encoding` | string | 固定 `rgb8`。 |
| `use_v4l2_buffer_timestamps` | bool | 固定 `true`，除非硬件不支持且有明确降级记录。 |
| `use_sensor_data_qos` | bool | 固定 `true`。 |

## 验收方式

| 检查项      | 命令 / 标准                                                                                    |
| -------- | ------------------------------------------------------------------------------------------ |
| topic 存在 | `ros2 topic list` 能看到左右两个 image topic。                                                     |
| msg 类型   | `ros2 topic info /pi05/observation/image/left_gripper_fisheye` 显示 `sensor_msgs/msg/Image`。 |
| 编码正确     | `ros2 topic echo --once ...` 中 `encoding` 为 `rgb8`。                                        |
| 帧率稳定     | `ros2 topic hz ...` 接近配置帧率。                                                                |
| 左右不混淆    | 遮挡左 / 右相机时，变化只出现在对应 topic。                                                                 |
| 复用确认 | launch 日志中能看到实际启动的是 `v4l2_camera_node`，而不是新写的重复采集节点。 |
| 设备路径稳定 | 配置中使用 `/dev/v4l/by-path/...` 或 `/dev/v4l/by-id/...`，不使用裸 `/dev/videoX` 作为生产配置。 |
