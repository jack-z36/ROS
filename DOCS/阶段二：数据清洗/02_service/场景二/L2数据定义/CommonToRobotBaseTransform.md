# CommonToRobotBaseTransform

> ⚠️ **Deprecated since 2026-06 debug-common-frames L3 001**。当前主链路不再使用此转换；替代品：见 [[arm-base 位姿转换]] + [[WorkFrameInArmBasePose]]（由 `Algo.rm_algo_workframe2base` 完成）。

## 定义

`CommonToRobotBaseTransform` 是场景二第 6 功能模块使用的固定外参，用于把场景一 common frame 下的 TCP 位姿转换到左右 RM65 机械臂 base 坐标系。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[IK 求解与 MCAP_B 生成器]]。

## 现实语义

它描述 `T_robot_base_common`，也就是 common frame 原点和姿态在某一侧 RM65 机械臂 base frame 下的固定变换。第 6 模块按以下规则使用它：

```text
T_robot_base_tcp(t) = T_robot_base_common * T_common_tcp(t)
```

左右臂必须分别配置，不允许用一个含义不明的共享外参覆盖双臂。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `left_robot_base_from_common.translation_m` | float[3] | common frame 原点在左臂 base 下的位置，单位 m |
| `left_robot_base_from_common.rotation_quat_xyzw` | float[4] | common frame 在左臂 base 下的姿态，四元数 xyzw |
| `right_robot_base_from_common.translation_m` | float[3] | common frame 原点在右臂 base 下的位置，单位 m |
| `right_robot_base_from_common.rotation_quat_xyzw` | float[4] | common frame 在右臂 base 下的姿态，四元数 xyzw |
| `source` | string | CAD、测量、标定、手工录入或调试占位来源 |

## 有效性规则

- 字段方向固定为 `robot_base_from_common`，不得写成方向含混的 `common_to_base`。
- translation 单位固定为 m，不允许混入 mm。
- 四元数顺序固定为 xyzw，必须为单位四元数。
- 左右臂配置必须同时存在；缺任一侧时第 6 模块 strict 失败。
- 若外参来源为调试占位，必须进入 [[IkSolveSummary]] 和运行日志，不能静默当作真实标定。

## 上游来源

- 场景一 [[FrameAlignmentConfig]] 定义的 common frame 语义。
- 机械臂安装测量、CAD、标定或人工配置。

## 下游消费者

- [[RobotBaseTcpPose]]
- IK 求解与 MCAP_B 生成器。

## 不负责

- 不负责生成或标定 common 到 base 外参。
- 不负责 IK、多解选择、关节限制或 MuJoCo 仿真。

## 相关链接

- [[CommonFrameTcpPose]]
- [[RobotBaseTcpPose]]
- [[Rm65IkConfig]]

