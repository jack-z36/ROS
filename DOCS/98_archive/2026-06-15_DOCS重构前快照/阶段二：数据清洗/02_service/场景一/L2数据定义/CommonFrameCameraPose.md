> ⚠️ **Deprecated since 2026-06 debug-common-frames L3 001**。当前主链路不再输出 common-frame 相机 pose；保留为历史字段，不推荐消费方依赖。替代品：见 [[arm-base 位姿转换]]。

# CommonFrameCameraPose

## 定义

`CommonFrameCameraPose` 是左右 Baton Mini 相机在 common frame 下的位姿表达（已废弃，保留历史兼容）。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[arm-base 位姿转换]]。

## 现实语义

它由 raw MCAP 中 Baton Mini start frame 下的相机 pose 经过 [[FrameAlignmentConfig]] 转换得到。首版默认：

```text
common_frame = left_umi_start_frame
```

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `x`、`y`、`z` | float | common frame 下相机位置 |
| `qx`、`qy`、`qz`、`qw` | float | common frame 下相机姿态四元数，顺序为 xyzw |
| `source_topic` | string | 原 pose topic，例如 `/baton_mini_left/fast_odom` |
| `output_topic` | string | 配置中的 camera common pose 输出 topic |
| `common_anchor` | string | `left` 或 `right` |
| `extrinsic_source` | string | `common_from_left_start` 或 `common_from_right_start` |

## 有效性规则

- 四元数必须是单位四元数或在配置加载时归一化。
- 消息数量必须与输入 pose topic 数量一致。
- raw pose 必须保留或可追溯，场景二不得把 raw pose 和 common pose 混作同一语义。
- 当 `common_anchor: left` 时，左侧静止在底座内的 camera pose 应接近单位位姿；右侧静止在底座内的 camera pose 应接近 `common_from_right_start`。

## 上游来源

- raw MCAP pose topic。
- [[FrameAlignmentConfig]] 中 `pose_streams` 和 `extrinsics`。
- 位姿转换配置生成流程。

## 下游消费者

- [[CommonFrameTcpPose]]
- 场景二位姿滤波器、异常值检测器。
- 场景四 action 构建的上游位姿语义。

## 不负责

- 不负责判断 pose 是否物理可靠、是否可执行或是否需要滤波。
- 不负责替代 raw pose 的追溯用途。

## 相关链接

- [[CleanedMcap]]
- [[Scene1Config]]
- [[FrameAlignmentConfig]]
- [[CommonFrameTcpPose]]
