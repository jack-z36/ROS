# CleanedMcap

## 定义

`CleanedMcap` 是场景一从 raw MCAP 生成的 cleaned MCAP 数据产物，保留原始多模态 topic，并补齐夹爪宽度、common frame camera pose 和 common frame TCP pose。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[cleaned MCAP 契约稳定]]。

## 现实语义

它是场景二可靠性验证的直接输入。它仍是 MCAP topic 世界，不是 episode/step/observation/action 世界。

## 字段或取值

| 内容 | 契约 |
|---|---|
| 文件位置 | `asset/阶段二：数据清洗/dev/mcap_cleaned/*.mcap` |
| 原始 topic | 默认保留 raw MCAP 中的原始 topic 和消息顺序 |
| raw pose topic | `/baton_mini_left/fast_odom`、`/baton_mini_right/fast_odom` 必须可追溯保留 |
| camera common pose | [[CommonFrameCameraPose]]，由 [[FrameAlignmentConfig]] 转换得到 |
| TCP common pose | [[CommonFrameTcpPose]]，由 camera common pose 叠加 [[CameraFromTcpExtrinsic]] 得到 |
| 左右 gripper topic | `/gopro_left/gripper_width`、`/gopro_right/gripper_width` |
| gripper payload 语义 | 每帧图像对应一个归一化 [[GripperWidthSample]] |
| 配置来源 | [[Scene1Config]] |
| 报告来源 | [[Scene1CleanReport]] 契约，第一轮可由终端摘要或 RAW_JSON 承载 |

## 有效性规则

- raw MCAP 不得被原地覆盖。
- raw pose 必须保留或在报告中有可追溯来源，不能只留下转换后 pose。
- camera common pose 和 TCP common pose 消息数量必须与输入 pose topic 数量一致。
- gripper topic 消息数量必须等于对应 image topic 图像帧数。
- gripper 输出 topic 不得与输入 MCAP 已有 topic 冲突。
- 如果首版为了兼容旧消费者仍复用 `/fast_odom` 写转换后 payload，必须同步新增 raw 备份 topic 或报告字段，且 L3 需要显式说明迁移策略。

## 上游来源

- 阶段一 Octopus 录制的 raw MCAP。
- 浏览器 GoPro 标定生成的 [[GripperCalibrationConfig]]。
- 位姿配置生成模块生成的 [[FrameAlignmentConfig]]。
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
| common pose 和 TCP pose 的最终 MCAP topic 名是否直接采用配置推荐名 | 由 L3 改造任务在代码中落定并同步场景二 |
| 是否必须写独立 JSON clean report | 本轮只定义 [[Scene1CleanReport]] 契约 |

## 相关链接

- [[Scene1Config]]
- [[CommonFrameCameraPose]]
- [[CommonFrameTcpPose]]
- [[GripperWidthSample]]
- [[Scene1CleanReport]]
