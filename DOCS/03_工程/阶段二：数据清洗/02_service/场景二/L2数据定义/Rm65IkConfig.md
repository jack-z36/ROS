# Rm65IkConfig

## 定义

`Rm65IkConfig` 是场景二第 6 功能模块调用睿尔曼 RM65 四代 6DOF Python SDK `Algo` 所需的配置契约。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[IK 求解与 MCAP_B 生成器]]。

## 现实语义

它回答“用哪个睿尔曼 SDK、哪个机械臂型号、左右臂初始关节角是什么、关节限位如何设置、IK 连续性策略是什么”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `sdk_source` | enum string | `official_github` / `installed_package` |
| `official_repo` | string | `https://github.com/RealManRobot/RM_API2.git` |
| `arm_model` | string | 固定优先 `RM_MODEL_RM_65_E` |
| `force_type` | string | 标准版优先 `RM_MODEL_RM_B_E`，按硬件配置可覆盖 |
| `initial_joint_deg.left` | float[6] | 左臂第一帧 IK seed，单位 deg |
| `initial_joint_deg.right` | float[6] | 右臂第一帧 IK seed，单位 deg |
| `joint_min_deg` | float[6] | RM65 关节最小限位，单位 deg |
| `joint_max_deg` | float[6] | RM65 关节最大限位，单位 deg |
| `seed_policy` | enum string | 固定首版 `previous_success` |
| `pose_flag` | int | SDK IK 输入姿态形式，首版使用 `0` 表示四元数 |
| `solution_mode` | enum string | 首版使用单步 IK，后续可扩展全解选择 |
| `sdk_setup_ref` | string | SDK 环境自检记录或版本引用 |

## 有效性规则

- 左右初始关节角必须各 6 个，单位为 deg。
- 首版 `seed_policy=previous_success`：第一帧用配置 seed，后续用上一成功解；失败帧不推进 seed。
- 默认 RM65 关节范围来自官方文档：J1 ±178、J2 ±130、J3 ±135、J4 ±178、J5 ±128、J6 ±360。
- SDK 不可导入、API 缺失或动态库加载失败时，本模块不得降级为自研 IK。

## 上游来源

- 睿尔曼官方 SDK 和技术文档。
- 本项目配置文件或开发者临时覆盖。

## 下游消费者

- [[Rm65IkSampleResult]]
- [[IkSolveSummary]]
- 关节限制检查器。

## 不负责

- 不保存 MCAP_B 文件路径。
- 不定义 MuJoCo 模型。
- 不决定训练 mask。

## 相关链接

- [[CommonToRobotBaseTransform]]
- [[RobotBaseTcpPose]]
- [[Rm65IkSampleResult]]

