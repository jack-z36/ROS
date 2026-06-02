# Scene1Config

## 定义

`Scene1Config` 是场景一清洗所需配置的总契约，覆盖 batch 输入输出、gripper 标定、work frames、pose stream 和标定状态。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[cleaned MCAP 契约稳定]]。

## 现实语义

它对应现有 `config/data_clean/*.yaml` 和 `src/data_clean/repo/config/mcap_process_config.py` 中的配置对象。正式主链路使用独立 `camera_from_tcp`、[[WorkFrameInBaseConfig]] 与 `pose_streams.output_arm_base_tcp_pose`。

## 字段或取值

| 配置块 | 字段 | 现实含义 |
|---|---|---|
| `batch` | `input_dir` | raw MCAP 输入目录，默认应迁移到 `asset/阶段二：数据清洗/dev/mcap_raw` |
| `batch` | `output_dir` | cleaned MCAP 输出目录，默认应迁移到 `asset/阶段二：数据清洗/dev/mcap_cleaned` |
| `batch` | `file_glob`、`workers`、`overwrite`、`fail_fast` | 批处理匹配、并行和失败策略 |
| `gripper_streams` | `image_topic`、`output_topic`、`marker_*`、`gripper_max` | 图像输入、夹爪输出和 [[GripperCalibrationConfig]] 字段 |
| `camera_from_tcp` | `left` / `right` | TCP frame 在对应 camera frame 下的固定平移，人工配置字段为 `translation_mm`；旋转固定为零 |
| `work_frames` | `left` / `right` | 每个 hand 的 [[WorkFrameInBaseConfig]]，人工配置使用 `position_mm` 与 `rotation_euler_rad` |
| `pose_streams.output_arm_base_tcp_pose` | topic string | 左右 arm-base TCP pose 输出 topic |
| ~~`frame_alignment`~~（已废弃） | ~~`common_anchor`~~ | ~~旧 common frame 配置，保留读取兼容~~ |
| ~~`frame_alignment.pose_streams`~~（已废弃） | ~~`input_topic`、`output_camera_pose_common`、`output_tcp_pose_common`~~ | ~~旧 pose 流配置，保留读取兼容~~ |
| ~~`frame_alignment.extrinsics`~~（已废弃） | ~~`common_from_*_start`、`camera_from_*_tcp`~~ | ~~旧外参配置，保留读取兼容~~ |
| `calibration` | `gripper`、`frame_alignment`（已废弃） | 左右夹爪和位姿转换配置状态 |

## 有效性规则

- `gripper_streams[].output_msg_type` 必须是 `std_msgs/msg/Float32`。
- `marker_max` 必须大于 `marker_min`，`gripper_max` 必须大于 0。
- 人工配置平移单位固定为 `mm`；加载后必须换算为 Runtime `m`。
- `camera_from_tcp` 旋转固定为零，不提供人工配置字段。
- `work_frames` 中每个 hand 的 `base_frame_id` 必须与 hand 匹配。
- 正式生产配置必须提供 `/left_arm_base_tcp_pose` 与 `/right_arm_base_tcp_pose`。
- 旧 `frame_alignment` 块保留读取兼容，新配置不应写入。
- 配置加载失败必须阻塞清洗，不允许进入 YOLO 式 topic 探测。

## 上游来源

- 场景一配置模板。
- 浏览器标定向导生成的 [[GripperCalibrationConfig]]。
- 位姿转换配置生成模块生成的 [[WorkFrameInBaseConfig]]（旧链路由 [[FrameAlignmentConfig]] 生成，已废弃）。

## 下游消费者

- 场景一 MCAP 清洗、夹爪宽度提取、arm-base 位姿转换、基础校验。
- Runtime 配置预检查和配置快照。
- [[Scene1CleanReport]]。

## 不负责

- 不负责场景二滤波、IK、MuJoCo 或时间对齐配置。
- 不负责定义 canonical dataset schema。

## 相关链接

- [[CleanedMcap]]
- [[GripperCalibrationConfig]]
- [[WorkFrameInBaseConfig]]
- [[ArmBaseTcpPose]]
- [[GripperWidthSample]]
- [[Scene1CleanReport]]
