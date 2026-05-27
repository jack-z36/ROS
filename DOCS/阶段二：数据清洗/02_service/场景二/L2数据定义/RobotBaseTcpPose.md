# RobotBaseTcpPose

## 定义

`RobotBaseTcpPose` 是左右 RM65 机械臂 base 坐标系下的 TCP 目标位姿，是睿尔曼 SDK IK 的直接输入。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[IK 求解与 MCAP_B 生成器]]。

## 现实语义

它由 [[McapA]] 中的 [[CommonFrameTcpPose]] 通过 [[CommonToRobotBaseTransform]] 转换得到，保持来源样本的时间戳、排序和样本引用不变。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `arm_side` | enum `left` / `right` | 目标属于左臂还是右臂 |
| `source_topic` | string | MCAP_A 中的 common-frame TCP pose topic |
| `timestamp_ns` | int | 来源 pose 时间戳 |
| `message_index` | int | 来源 topic 内样本序号 |
| `x` / `y` / `z` | float | RM65 base frame 下 TCP 位置，单位 m |
| `qx` / `qy` / `qz` / `qw` | float | RM65 base frame 下 TCP 姿态四元数，xyzw |
| `transform_ref` | [[CommonToRobotBaseTransform]] | 本样本使用的外参引用 |

## 有效性规则

- 位置单位固定为 m。
- 四元数必须可归一化为单位四元数。
- 输出样本数必须与对应输入 TCP pose 样本数一致。
- `left` 和 `right` 不能混用外参。
- 不允许直接把 common frame pose 当作 robot base pose。

## 上游来源

- [[McapA]]
- [[CommonFrameTcpPose]]
- [[CommonToRobotBaseTransform]]

## 下游消费者

- [[Rm65IkSampleResult]]
- [[IkSolveSummary]]

## 不负责

- 不保存关节角。
- 不表达 IK 是否成功。
- 不表达关节限制、速度、加速度或仿真结果。

## 相关链接

- [[CommonToRobotBaseTransform]]
- [[Rm65IkConfig]]

