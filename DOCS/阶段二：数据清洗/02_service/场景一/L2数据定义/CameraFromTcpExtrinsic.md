> ⚠️ **Intermediate use only** — 当前仅作为 TCP in camera 推导的中间量，不直接暴露给下游。消费方应直接使用 [[TcpInCamera]] 或 [[ArmBaseTcpPose]]。

# CameraFromTcpExtrinsic

## 定义

`CameraFromTcpExtrinsic` 是 TCP 坐标系在 Baton Mini 相机坐标系下的固定外参，用于 `compute_tcp_in_camera` 推导 TCP in camera 中间位姿。

## 命名约束

配置字段统一使用：

```text
camera_from_left_tcp
camera_from_right_tcp
```

矩阵语义统一为：

```text
T_camera_tcp
```

也就是：

```text
T_common_tcp(t) = T_common_camera(t) * T_camera_tcp
```

不得再使用方向含混的 `tcp_from_camera` 字段名。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `translation_mm` | float[3] | TCP 原点在 camera frame 下的位置，人工配置单位 mm |
| `source` | string | CAD、测量、标定或默认占位 |

## 有效性规则

- 相机到 TCP 的旋转固定为零，不允许在普通生产配置中覆盖。
- Parser 加载后将 `translation_mm / 1000` 换算为 Runtime `translation_m`。
- 左右 TCP 外参必须分别配置。
- 若首版没有真实 TCP 外参，可用单位变换占位，但必须在报告中标记 `tcp_extrinsic_source: identity_placeholder`。

## 下游消费者

- [[CommonFrameTcpPose]]
- 场景二 IK 求解器。

## 相关链接

- [[FrameAlignmentConfig]]
- [[CommonFrameCameraPose]]
