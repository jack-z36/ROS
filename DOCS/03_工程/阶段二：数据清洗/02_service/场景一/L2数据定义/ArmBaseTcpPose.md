# ArmBaseTcpPose

## 定义

`ArmBaseTcpPose` 是左右夹爪 TCP 在对应机械臂基坐标系下的位姿表达，是场景二位姿滤波、异常检测和后续 IK 的优先输入。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[arm-base 位姿转换]]。

## 现实语义

它由 [[TcpInCamera]] 经 `Algo.rm_algo_workframe2base` 转换得到。每个 hand 对应独立的机械臂基坐标系：

- `left` → `left_arm_base`（RM65 左臂 base link）
- `right` → `right_arm_base`（RM65 右臂 base link）

```text
T_arm_base_tcp = rm_algo_workframe2base(work_matrix, tcp_in_camera_pose)
```

## 字段或取值

| 字段 | 类型 | 现实含义 |
|------|------|----------|
| `hand` | string | `left` 或 `right`，对应 [[HandType]] |
| `frame_id` | string | `left_arm_base` 或 `right_arm_base`，对应 [[FrameIdType]] |
| `position_m` | dict | TCP 位置，`{x, y, z}`，单位 m |
| `orientation` | dict | TCP 姿态四元数，`{x, y, z, w}`，顺序 xyzw，无量纲 |
| `official_api` | string | `"Algo.rm_algo_workframe2base"` |

可选追溯字段：

| 字段 | 类型 | 现实含义 |
|------|------|----------|
| `source_camera_pose_ref` | string/null | 来源 camera pose 标识 |
| `source_tcp_in_camera_ref` | string/null | 来源 TCP in camera 标识 |
| `source_work_frame_in_base_ref` | string/null | 来源 work frame 配置标识 |
| `timestamp_ns` | int/null | 采样时间戳（纳秒） |

## 坐标轴约定

- X 轴：机械臂基座前方
- Y 轴：机械臂基座左方（右手系）
- Z 轴：机械臂基座上方
- 单位：位置为 `m`；姿态输出为 ROS quaternion `xyzw`，无量纲。
- 左右 arm-base 分属不同物理坐标系，不可直接相加、叠加或解释成一个统一世界坐标。

## 有效性规则

- `hand` 必须与 `frame_id` 匹配：`left` → `left_arm_base`，`right` → `right_arm_base`。
- 位置单位固定为 m。
- 四元数必须是单位四元数或在输出前归一化。
- 消息数量必须与输入 pose topic 数量一致。

## 上游来源

- [[TcpInCamera]]，由 `compute_tcp_in_camera` 产出。
- [[WorkFrameInBaseConfig]]，由场景一配置的 `work_frames` 块提供。

## 下游消费者

- 场景二位姿滤波器、异常值检测器。
- IK 求解器和后续 action 构建。
- LeRobot v3 数据导出的 TCP pose 输入。

## 相关链接

- [[HandType]]
- [[FrameIdType]]
- [[TcpInCamera]]
- [[WorkFrameInBaseConfig]]
- [[arm-base 位姿转换]]
- [[CleanedMcap]]
