> ⚠️ **Deprecated since 2026-06 debug-common-frames L3 001**。当前主链路不再输出 common-frame TCP pose；保留为历史字段，不推荐消费方依赖。替代品：见 [[ArmBaseTcpPose]]。

# CommonFrameTcpPose

## 定义

`CommonFrameTcpPose` 是左右夹爪 TCP 在 common frame 下的位姿表达（已废弃，保留历史兼容）。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[arm-base 位姿转换]]。

## 现实语义

它由 [[CommonFrameCameraPose]] 叠加 [[CameraFromTcpExtrinsic]] 得到：

```text
T_common_tcp(t) = T_common_camera(t) * T_camera_tcp
```

默认 common frame 是 `left_umi_start_frame`。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `x`、`y`、`z` | float | common frame 下 TCP 位置 |
| `qx`、`qy`、`qz`、`qw` | float | common frame 下 TCP 姿态四元数，xyzw |
| `source_camera_pose` | string | 来源 camera common pose topic 或字段 |
| `tcp_extrinsic_source` | string | TCP 外参来源 |

## 有效性规则

- 消息数量必须与对应输入 pose topic 数量一致。
- 位置单位固定为 m。
- 若 TCP 外参为单位占位，必须进入 [[Scene1CleanReport]] 或 RAW_JSON 摘要。

## 下游消费者

- 场景二位姿滤波器、异常值检测器。
- IK 求解器和后续 action 构建。

## 相关链接

- [[CommonFrameCameraPose]]
- [[FrameAlignmentConfig]]
