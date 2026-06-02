# WorkFrameInBaseConfig

## 定义

`WorkFrameInBaseConfig` 是用户定义的 work frame 在对应机械臂基坐标系下的配置，是 `Algo.rm_algo_workframe2base` 的第二个输入。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[arm-base 位姿转换]]。

## 现实语义

Work frame 是用户在机械臂工作空间中定义的一个参考坐标系。`WorkFrameInBaseConfig` 描述该 work frame 的原点和姿态在对应机械臂基坐标系（`left_arm_base` 或 `right_arm_base`）下的表达。

```text
work_matrix = rm_algo_pos2matrix(work_frame_euler_pose)
// work_matrix 表示 base → work 的映射
// p_work = work_matrix · p_base
```

配置来源于 `McapProcessConfig.work_frames` 块。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|------|------|----------|
| `hand` | string | `left` 或 `right` |
| `base_frame_id` | string | `left_arm_base` 或 `right_arm_base` |
| `position_mm` | dict | Work frame 原点在基坐标系下的位置，`{x, y, z}`，人工配置单位 mm |
| `rotation_euler_rad` | dict | Work frame 姿态欧拉角，`{rx, ry, rz}`，单位 rad |
| `work_frame_id` | string | 用户指定的 work frame 名称，默认 `"work"` |
| `source` | string | 来源：`user_input`、`calibration_file`、`external_config` |

## 有效性规则

- `hand` 必须与 `base_frame_id` 匹配：`left` → `left_arm_base`，`right` → `right_arm_base`。
- Parser 加载后将 `position_mm / 1000` 换算为 Runtime `position_m`。
- `rotation_euler_rad` 直接传给 RealMan SDK，不再绕行 quaternion 转换。
- 左右手必须分别配置各自的 work frame。

## 上游来源

- 用户配置（`McapProcessConfig.work_frames`）。
- 标定或外参测量。

## 下游消费者

- [[arm-base 位姿转换]] 模块的 `compute_arm_base_tcp_pose`。
- [[ArmBaseTcpPose]] 的输入来源。

## 相关链接

- [[ArmBaseTcpPose]]
- [[TcpInCamera]]
- [[arm-base 位姿转换]]
- [[HandType]]
- [[FrameIdType]]
