# GripperWidthSample

## 定义

`GripperWidthSample` 是场景一从 GoPro 图像中估计出的单帧夹爪宽度样本。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[夹爪宽度提取]]。

## 现实语义

它对应 cleaned MCAP 中 `/gopro_left/gripper_width` 或 `/gopro_right/gripper_width` 的 `std_msgs/msg/Float32` payload。当前实现写入归一化值，真实物理宽度由 [[Scene1Config]] 中 `gripper_max` 追溯。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `value` | float | 归一化夹爪宽度，范围 `[0, 1]` |
| `log_time` | integer | 与来源图像消息相同的 MCAP log time |
| `publish_time` | integer | 与来源图像消息相同的 publish time |
| `source_image_topic` | string | 来源图像 topic |
| `output_topic` | string | 输出夹爪宽度 topic |
| `source_method` | enum string | `direct_marker` / `single_marker_estimate` / `interpolated` |

## 有效性规则

- 每个 image frame 必须对应一个 gripper width message。
- `value` 必须在 `[0, 1]` 范围内。
- 完全检测不到有效 marker 时，本 gripper stream 必须失败，不能静默写入默认值。
- 插值帧数必须能进入 [[Scene1CleanReport]]。

## 上游来源

- raw MCAP 中的 GoPro image topic。
- [[Scene1Config]] 中的 ArUco 字典、marker id、像素范围和 `gripper_max`。

## 下游消费者

- 场景二异常值检测器和数据补全器。
- 场景四 observation/action/mask 构建。
- [[Scene1CleanReport]]。

## 不负责

- 不负责判断夹爪宽度是否物理可靠或机器人可执行。
- 不负责把归一化值直接解释为米制单位；物理含义必须结合配置。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 是否在 MCAP 中保留 source_method | v1 只写 Float32，source_method 先进入报告契约 |
| 是否输出物理宽度而不是归一化值 | 当前按现有实现固定为归一化 `[0, 1]` |

## 相关链接

- [[CleanedMcap]]
- [[Scene1Config]]
- [[Scene1CleanReport]]
