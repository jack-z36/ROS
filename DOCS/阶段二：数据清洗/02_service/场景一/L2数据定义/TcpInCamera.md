# TcpInCamera

## 定义

`TcpInCamera` 是 arm-base 转换前的 TCP in camera 中间位姿，描述夹爪 TCP 在 Baton Mini 相机坐标系下的位置和姿态。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[arm-base 位姿转换]]。

## 现实语义

它由 `compute_tcp_in_camera` 将 Baton Mini 每帧动态 camera pose 与固定外参 [[CameraFromTcpExtrinsic]] 组合得到。TCP 动态位姿作为 `rm_algo_workframe2base` 的 `pose_in_work` 输入，其中 camera 所在工作坐标系充当 work frame 角色。

```text
T_tcp_in_camera = extrinsic translation + rotation（固定值，不依赖相机运动）
```

注意：`compute_tcp_in_camera` 接受 camera pose 参数但结果不依赖它，因为 TCP in camera 仅由固定外参决定。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|------|------|----------|
| `hand` | string | `left` 或 `right`，对应 [[HandType]] |
| `frame_id` | string | `<hand>_camera_optical_frame` |
| `position_m` | dict | TCP 位置，`{x, y, z}`，单位 m |
| `orientation` | dict | TCP 姿态四元数，`{x, y, z, w}`，顺序 xyzw |

## 坐标轴约定

- 与 Baton Mini camera optical frame 约定一致。
- 位置单位：m。
- 姿态单位：弧度。

## 有效性规则

- Baton Mini raw pose 的位置单位固定为 `m`，不得忽略每帧动态位姿。
- 相机到 TCP 外参仅提供固定平移，旋转固定为零。
- `frame_id` 格式为 `<hand>_camera_optical_frame`。
- 左右手必须使用各自的外参。

## 上游来源

- raw camera pose（来自 Baton Mini odometry）。
- [[CameraFromTcpExtrinsic]]，固定外参。

## 下游消费者

- [[arm-base 位姿转换]] 模块的 `compute_arm_base_tcp_pose`。
- [[ArmBaseTcpPose]] 的输入来源。

## 相关链接

- [[CameraFromTcpExtrinsic]]
- [[ArmBaseTcpPose]]
- [[arm-base 位姿转换]]
- [[HandType]]
