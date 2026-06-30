# CleanedMcap

## 定义

`CleanedMcap` 是场景一从 raw MCAP 生成的 cleaned MCAP 数据产物，保留原始多模态 topic，并补齐夹爪宽度和 arm-base TCP pose。旧 `tcp_common` / `camera_common` 字段保留为历史兼容。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[cleaned MCAP 契约稳定]]。

## 现实语义

它是场景二可靠性验证的直接输入。它仍是 MCAP topic 世界，不是 episode/step/observation/action 世界。

## 字段或取值

| 内容 | 契约 |
|---|---|---|
| 文件位置 | `asset/阶段二：数据清洗/dev/mcap_cleaned/*.mcap` |
| 原始 topic | 默认保留 raw MCAP 中的原始 topic 和消息顺序 |
| raw pose topic | `/baton_mini_left/fast_odom`、`/baton_mini_right/fast_odom` 必须可追溯保留 |
| arm-base TCP pose（主位姿） | `arm_base_tcp_pose`，frame_id = `<hand>_arm_base_link`，由 [[ArmBaseTcpPose]] 定义 |
| `arm_base_tcp_pose` 子字段 | `hand`（`left`/`right`）、`frame_id`（`left_arm_base`/`right_arm_base`）、`position_m`、`orientation` |
| ~~common camera pose~~（已弃用） | ~~[[CommonFrameCameraPose]]~~，保留读取兼容，不推荐消费方依赖 |
| ~~common TCP pose~~（已弃用） | ~~[[CommonFrameTcpPose]]~~，保留读取兼容，不推荐消费方依赖 |
| 左右 gripper topic | `/gopro_left/gripper_width`、`/gopro_right/gripper_width` |
| gripper payload 语义 | 每帧图像对应一个归一化 [[GripperWidthSample]] |
| 配置来源 | [[Scene1Config]] |
| 报告来源 | [[Scene1CleanReport]] 契约，第一轮可由终端摘要或 RAW_JSON 承载 |

## 有效性规则

- raw MCAP 不得被原地覆盖。
- raw pose 必须保留或在报告中有可追溯来源，不能只留下转换后 pose。
- arm-base TCP pose 消息数量必须与输入 pose topic 数量一致。
- gripper topic 消息数量必须等于对应 image topic 图像帧数。
- gripper 输出 topic 不得与输入 MCAP 已有 topic 冲突。
- `tcp_common` / `camera_common` 字段标记为已弃用，保留读取兼容，但不推荐新消费方依赖。

## 上游来源

- 阶段一 Octopus 录制的 raw MCAP。
- 浏览器 GoPro 标定生成的 [[GripperCalibrationConfig]]。
- 位姿配置生成模块生成的 [[WorkFrameInBaseConfig]]（旧链路由 [[FrameAlignmentConfig]] 生成，已废弃）。
- 场景一 MCAP 清洗能力。

## 下游消费者

- 场景二位姿滤波器、触觉滤波器、异常值检测器、数据补全器。
- 后续场景三、场景四间接依赖其基础语义。
- Runtime 单场景运行和全流程运行。

## 不负责

- 不负责滤波、异常修复、IK、MuJoCo 仿真或时间对齐。
- 不负责 episode、step、action、mask 或 canonical dataset 语义。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| `arm_base_tcp_pose` 的最终 MCAP topic 名称 | 由 L3 改造任务在代码中落定并同步场景二 |
| 是否必须写独立 JSON clean report | 本轮只定义 [[Scene1CleanReport]] 契约 |

## 相关链接

- [[Scene1Config]]
- [[ArmBaseTcpPose]]
- [[TcpInCamera]]
- [[WorkFrameInBaseConfig]]
- [[GripperWidthSample]]
- [[Scene1CleanReport]]
