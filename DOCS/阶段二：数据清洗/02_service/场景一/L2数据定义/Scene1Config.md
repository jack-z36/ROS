# Scene1Config

## 定义

`Scene1Config` 是场景一清洗所需配置的总契约，覆盖 batch 输入输出、gripper 标定、frame alignment、pose stream 和标定状态。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[cleaned MCAP 契约稳定]]。

## 现实语义

它对应现有 `config/data_clean/*.yaml` 和 `src/data_clean/config/mcap_process_config.py` 中的配置对象。后续 L3 需要把旧 `pose_streams + transform_file + start_from_common` 逐步迁移到 [[FrameAlignmentConfig]]。

## 字段或取值

| 配置块 | 字段 | 现实含义 |
|---|---|---|
| `batch` | `input_dir` | raw MCAP 输入目录，默认应迁移到 `asset/阶段二：数据清洗/dev/mcap_raw` |
| `batch` | `output_dir` | cleaned MCAP 输出目录，默认应迁移到 `asset/阶段二：数据清洗/dev/mcap_cleaned` |
| `batch` | `file_glob`、`workers`、`overwrite`、`fail_fast` | 批处理匹配、并行和失败策略 |
| `gripper_streams` | `image_topic`、`output_topic`、`marker_*`、`gripper_max` | 图像输入、夹爪输出和 [[GripperCalibrationConfig]] 字段 |
| `frame_alignment` | `common_anchor` | 默认 `left`，表示 `common_frame = left_umi_start_frame` |
| `frame_alignment.pose_streams` | `input_topic`、`output_camera_pose_common`、`output_tcp_pose_common` | raw pose 输入和 common pose 输出 topic |
| `frame_alignment.extrinsics` | `common_from_*_start`、`camera_from_*_tcp` | start frame 到 common frame、camera 到 TCP 的外参 |
| `calibration` | `gripper`、`frame_alignment` | 左右夹爪和位姿转换配置状态 |

## 有效性规则

- `gripper_streams[].output_msg_type` 必须是 `std_msgs/msg/Float32`。
- `marker_max` 必须大于 `marker_min`，`gripper_max` 必须大于 0。
- `common_anchor` 必须是 `left` 或 `right`。
- `camera_from_tcp` 命名和矩阵方向必须与 [[CameraFromTcpExtrinsic]] 一致。
- 配置加载失败必须阻塞清洗，不允许进入 YOLO 式 topic 探测。

## 上游来源

- 场景一配置模板。
- 浏览器标定向导生成的 [[GripperCalibrationConfig]]。
- 位姿转换配置生成模块生成的 [[FrameAlignmentConfig]]。

## 下游消费者

- 场景一 MCAP 清洗、夹爪宽度提取、common frame 位姿转换、基础校验。
- Runtime 配置预检查和配置快照。
- [[Scene1CleanReport]]。

## 不负责

- 不负责场景二滤波、IK、MuJoCo 或时间对齐配置。
- 不负责定义 canonical dataset schema。

## 相关链接

- [[CleanedMcap]]
- [[GripperCalibrationConfig]]
- [[FrameAlignmentConfig]]
- [[CommonFrameCameraPose]]
- [[CommonFrameTcpPose]]
- [[GripperWidthSample]]
- [[Scene1CleanReport]]
