# Scene1CleanReport

## 定义

`Scene1CleanReport` 是场景一清洗结果的机器可读报告契约，用于解释一个 raw MCAP 如何生成对应的 [[CleanedMcap]]。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[cleaned MCAP 契约稳定]]、[[基础校验与输出契约检查]]。

## 现实语义

它让人工、Runtime 和场景二能追溯输入文件、输出文件、topic 变化、位姿转换、夹爪提取统计、配置来源和失败原因。第一轮先定义契约，不要求现有代码立即写出独立 JSON 文件。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_file` | string | raw MCAP 路径 |
| `output_file` | string | [[CleanedMcap]] 路径 |
| `status` | enum string | `success` / `failed` / `skipped` |
| `config_path` | string | 使用的 [[Scene1Config]] 文件路径 |
| `input_topic_count` | integer | 输入 MCAP topic 数 |
| `output_topic_count` | integer | 输出 MCAP topic 数 |
| `pose_topics` | list | raw pose、camera common pose、TCP common pose 的消息数量和 payload 语义 |
| `gripper_topics` | list | 每个 gripper topic 的图像帧数、输出数、缺失帧和插值帧 |
| `raw_pose_retention` | string | raw pose 保留或备份策略 |
| `common_anchor` | string | [[FrameAlignmentConfig]] 使用的 common anchor |
| `tcp_extrinsic_source` | string | [[TcpFromCameraExtrinsic]] 来源 |
| `failure_reason` | string/null | 失败或跳过原因 |

## 有效性规则

- `status=success` 时，`output_file` 必须存在且满足 [[CleanedMcap]] 契约。
- `status=failed` 时，必须有 `failure_reason`。
- `pose_topics` 必须说明 raw pose 是否保留、[[CommonFrameCameraPose]] 和 [[CommonFrameTcpPose]] 的输出数量。
- 如果 TCP 外参是单位占位，必须记录 `tcp_extrinsic_source: identity_placeholder`。
- `gripper_topics` 的输出数量必须能追溯到 [[GripperWidthSample]]。
- 报告中的路径应使用仓库相对路径或运行端可解释路径，不写开发者本机绝对路径进任务文档。

## 上游来源

- 场景一基础校验与输出契约检查。
- 当前 `FileProcessingReport`、`PoseTopicStats`、`GripperTopicStats` 的代码行为。

## 下游消费者

- 场景二上游接口检查。
- Runtime 结构化日志、manifest 和错误摘要。
- 人工复查和 Win 端阶段汇总。

## 不负责

- 不负责记录滤波、IK、仿真、时间对齐或 canonical dataset 检查结果。
- 不负责替代 Runtime 的 `run_log.json` 或后续 `processing_manifest.json`。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 报告文件最终路径 | 待 Runtime/run 目录接入时确定 |
| 是否每个 cleaned MCAP 旁边生成独立报告 | 本轮不锁死，只要求契约能承载 |

## 相关链接

- [[CleanedMcap]]
- [[Scene1Config]]
- [[CommonFrameCameraPose]]
- [[CommonFrameTcpPose]]
- [[FrameAlignmentConfig]]
- [[GripperWidthSample]]
