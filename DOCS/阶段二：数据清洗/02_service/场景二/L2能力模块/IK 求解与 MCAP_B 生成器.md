# L2 能力模块说明：IK 求解与 MCAP_B 生成器

## 1. 能力名称

```text
IK 求解与 MCAP_B 生成器
```

## 2. 所属位置

阶段：阶段二：数据清洗
L1：service_s2
场景：场景二：硬件数据可靠性验证
模块类别：数据计算类 / 数据读写类
来源功能模块清单：`DOCS/阶段二：数据清洗/02_service/场景二/功能模块清单.md`

## 3. 一句话目标

```text
从 [[McapA|MCAP_A]] 读取左右 common-frame TCP pose，转换到左右 RM65 base 坐标系后调用睿尔曼 SDK 做 IK，并写出诊断用 [[McapB|MCAP_B]] 与 [[IkSolveSummary]]。
```

## 4. 能力角色

本能力是场景二机器人执行可行性诊断链路的第一步，位于 [[MCAP_A生成器]] 之后、关节限制检查器和 MuJoCo 仿真验证器之前。它不修改 [[McapA|MCAP_A]]，只生成派生诊断产物 [[McapB|MCAP_B]] 和 [[IkSolveSummary]]。

已按 `grill-me` 约束完成意图澄清：首版使用睿尔曼 RM65 四代 6DOF Python SDK `Algo`，左右双臂分别求解；`common_frame -> robot_base` 转换并入本模块但必须单独描述、单独测试；失败帧不伪造关节角；SDK 本地部署与 IK 自检必须写入 L3。

## 5. 上游关系

- 直接上游是 [[MCAP_A生成器]]。
- 来源主数据是 [[McapA|MCAP_A]]。
- TCP pose 语义来自场景一 [[CommonFrameTcpPose]]。
- `common_frame -> robot_base` 外参由 [[CommonToRobotBaseTransform]] 表达。
- RM65 SDK、初始关节角和 IK 策略由 [[Rm65IkConfig]] 表达。
- 本模块的 common-frame 变换逻辑必须参考场景一 [[common frame 位姿转换]]，并优先复用或抽取 `src/data_clean/service/tcp_transform.py` 的 pose 矩阵转换能力。

## 6. 下游关系

- 关节限制检查器读取 [[McapB|MCAP_B]] 和 [[IkSolveSummary]] 检查 IK 失败、关节角、速度、加速度和 workspace。
- MuJoCo 仿真验证器读取 [[McapB|MCAP_B]] 做仿真验证。
- Parquet 标注与验证报告生成器读取 [[IkSolveSummary]] 生成 IK 失败标注。
- 开发者入口 `scene2_ik_mcap_b_writer` 展示坐标转换、IK 求解、MCAP_B 写出和 sidecar 统计。

## 7. 上游接口对齐检查

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
|---|---|---|---|---|
| MCAP_A 生成器 | [[McapA]]、[[McapAWriteSummary]] | 读取左右 TCP / common-frame pose，追溯输入 MCAP_A | 已对齐 | 复用，不修改 MCAP_A |
| 场景一 common frame 位姿转换 | [[CommonFrameTcpPose]]、[[FrameAlignmentConfig]] | 复用 common frame 语义、m 单位、xyzw 四元数、样本数不变原则 | 已对齐 | 复用文档语义，抽取通用 transform helper |
| 场景一 pose transform 代码 | `src/data_clean/service/tcp_transform.py` | 复用或抽取 pose->matrix / matrix->pose / transform compose | 部分对齐 | 新增通用 helper 时不得破坏场景一行为 |
| 睿尔曼 SDK | 官方 `RealManRobot/RM_API2`、Python `Algo` | 调用 RM65 离线 IK | 缺本地环境定义 | 先拆 SDK 环境自检 L3 |
| RM65 本体参数 | 官方 RM65 系列参数及 D-H 模型 | 固化 6DOF、关节限位和默认配置 | 已对齐 | 复用官方文档 |

## 8. 职责边界

本能力负责：

1. 将 [[McapA|MCAP_A]] 中左右 [[CommonFrameTcpPose]] 转换为 [[RobotBaseTcpPose]]。
2. 调用睿尔曼 RM65 SDK，对左右 [[RobotBaseTcpPose]] 逐样本求解 IK。
3. 按上一成功解连续策略生成 [[Rm65IkSampleResult]]。
4. 将成功 IK 结果写出为 [[McapB|MCAP_B]] 中左右 `sensor_msgs/msg/JointState` topic。
5. 写出覆盖所有输入 pose 的 [[IkSolveSummary]]。
6. 提供可由无上下文 Agent 执行的 SDK 本地部署与 IK 自检任务。

本能力不负责：

1. 不重新做异常检测、补全或滤波。
2. 不修改 [[McapA|MCAP_A]]。
3. 不在 IK 失败帧写 NaN 或复制上一关节角。
4. 不执行关节速度、加速度、workspace 综合检查。
5. 不执行 MuJoCo 仿真。
6. 不决定 mask、episode 丢弃或 canonical dataset 结构。

## 9. 官方参考与 SDK 本地部署

后续 L3 必须列入以下官方来源：

- [RealManRobot/RM_API2](https://github.com/RealManRobot/RM_API2)
- [RMDemo_AlgoInterface](https://develop.realman-robotics.com/en/robot/demo/python/algoInterface/)
- [Algorithm Interface Configuration algo](https://develop.realman-robotics.com/en/robot4th/apipython/classes/algo/)
- [rm_inverse_kinematics_params_t](https://develop.realman-robotics.com/en/robot4th/apipython/struct/inverseKinematicsParams/)
- [Developer Center](https://realman-robotics.com/en/main/developer-center.html)

SDK 环境 L3 必须写清自动化步骤：

```bash
git clone https://github.com/RealManRobot/RM_API2.git vendor/RealManRobot/RM_API2
cd vendor/RealManRobot/RM_API2/Demo/RMDemo_Python/RMDemo_AlgoInterface
python3 -m pip install -r requirements.txt
python3 ./src/main.py
```

如果官方仓库路径变化，执行端必须先在 `vendor/RealManRobot/RM_API2` 内搜索 `RMDemo_AlgoInterface`，不得硬编码路径失败后停止。

SDK 自检必须验证：

1. `from Robotic_Arm.rm_robot_interface import *` 可导入。
2. 可初始化 `Algo(rm_robot_arm_model_e.RM_MODEL_RM_65_E, rm_force_type_e.RM_MODEL_RM_B_E)`。
3. 可调用 `rm_algo_inverse_kinematics`。
4. 使用官方 Demo 的 RM65 示例 pose 能返回成功或稳定失败码。
5. 失败时明确区分 SDK 未安装、Python 版本不足、依赖缺失、动态库加载失败、API 变更和 IK 返回失败。

## 10. 子功能拆解

| 子功能 | 输入 | 输出 | 独立验收 |
|---|---|---|---|
| common_frame -> robot_base | [[McapA]]、[[CommonToRobotBaseTransform]] | [[RobotBaseTcpPose]] | 单位外参、平移、旋转、左右隔离、非法外参 strict 失败 |
| IK 求解生成关节角 | [[RobotBaseTcpPose]]、[[Rm65IkConfig]]、SDK `Algo` | [[Rm65IkSampleResult]] | mock SDK、真实 SDK smoke、seed 连续策略、状态码映射 |
| 生成 MCAP_B | [[Rm65IkSampleResult]]、写出配置 | [[McapB]]、[[IkSolveSummary]] | 成功帧写出、失败帧跳过、sidecar 覆盖 left/right 全样本 |

## 11. 计算职责

| 计算项 | 输入 | 输出 | 影响下游 |
|---|---|---|---|
| common 到 base 转换 | [[CommonFrameTcpPose]]、[[CommonToRobotBaseTransform]] | [[RobotBaseTcpPose]] | IK 输入坐标系正确 |
| SDK 环境自检 | 官方 SDK、Python 环境 | SDK 可用性结果 | 阻止无 SDK 时进入业务实现 |
| IK seed 管理 | [[Rm65IkConfig]]、上一成功解 | 每帧 `q_in` | 保持关节轨迹连续 |
| IK 状态映射 | SDK 返回码、异常 | [[Rm65IkSampleResult]] | 下游能区分失败原因 |
| 失败区间聚合 | 逐样本失败记录 | [[IkSolveSummary]].`failure_intervals` | Parquet 标注和关节检查消费 |

## 12. 计算规则

| 规则 | 触发条件 | 计算 / 判断方式 | 结果表达 |
|---|---|---|---|
| 坐标转换 | 每个 TCP pose | `T_robot_base_tcp(t) = T_robot_base_common * T_common_tcp(t)` | [[RobotBaseTcpPose]] |
| 外参缺失 | 左右任一侧缺外参 | strict 失败 | `missing_common_to_robot_base_transform` |
| 第一帧 seed | 每侧第一条 pose | 使用配置 `initial_joint_deg.<side>` | [[Rm65IkSampleResult]].`seed_joint_deg` |
| 后续 seed | 上一帧 IK 成功 | 使用上一成功 `joint_deg` | `seed_policy=previous_success` |
| 失败帧 seed | 当前帧 IK 失败 | 不推进 seed | 失败记录 |
| SDK 状态 | SDK 返回非 0 或抛异常 | 映射为稳定 failure reason | [[Rm65IkSampleResult]] |
| 写出过滤 | 生成 MCAP_B | 只写 `status=success` 样本 | [[McapB]] |

## 13. 输出结果结构

| 字段 | 类型 | 含义 | 有效性要求 | 下游使用方式 |
|---|---|---|---|---|
| `robot_base_pose_sequences` | list[[RobotBaseTcpPose]] | 左右 base-frame TCP pose | 样本数与输入 TCP pose 一致 | IK 输入 |
| `ik_sample_records` | list[[Rm65IkSampleResult]] | 逐样本 IK 结果 | 覆盖所有输入 pose | sidecar 和标注 |
| `output_mcap_b` | [[McapB]] | 成功解 JointState MCAP | 失败帧不写 | 关节检查和仿真 |
| `ik_solve_summary` | [[IkSolveSummary]] | 运行摘要和失败区间 | 覆盖所有输入 pose | 报告和开发者入口 |

## 14. 读写职责

| 动作 | 读取来源 | 写入目标 | 格式 | 下游消费者 |
|---|---|---|---|---|
| 读取 MCAP_A | [[McapA]] | 内存中的 TCP pose 序列 | MCAP | common->base 转换 |
| 读取配置 | [[CommonToRobotBaseTransform]]、[[Rm65IkConfig]] | 内存配置对象 | YAML / JSON | IK 求解 |
| 写出 MCAP_B | [[Rm65IkSampleResult]] 成功样本 | [[McapB]] | MCAP | 关节检查、MuJoCo |
| 写出摘要 | 全部逐样本结果和写出统计 | [[IkSolveSummary]] | JSON | 报告生成器、开发者入口 |

## 15. 路径与命名规则

| 文件 / 目录 | 路径来源 | 命名规则 | 是否允许覆盖 | 创建时机 |
|---|---|---|---|---|
| SDK 仓库 | L3 环境任务 | `vendor/RealManRobot/RM_API2` | 已存在时复用并校验 | SDK 自检前 |
| MCAP_B 默认目录 | 写出配置 | `asset/阶段二：数据清洗/dev/mcap_validated/` | 默认不覆盖 | IK 完成后 |
| MCAP_B 文件 | MCAP_A stem | `<stem>_mcap_b.mcap` | 默认不覆盖 | 写出前 |
| IK 摘要 | MCAP_B 同级或 run artifacts | `ik_solve_summary.json` | 同一 run 可覆盖临时产物 | 完成或失败 |
| 开发者调试产物 | 独立 run 输出目录 | `artifacts/ik_mcap_b/` | 只影响本次 run | 功能检验时 |

## 16. 文件格式与内容契约

| 文件 | 格式 | 必填内容 | 可选内容 | 校验方式 |
|---|---|---|---|---|
| [[McapB]] | MCAP | 左右 `sensor_msgs/msg/JointState` 成功样本 | 关节名配置 | topic / type / timestamp contract test |
| [[IkSolveSummary]] | JSON | 输入、输出、配置引用、sample records、failure intervals、status | SDK 版本、耗时 | JSON schema / dataclass 序列化测试 |
| 运行日志 | JSON / text | 输入、配置、步骤、错误、输出位置 | SDK 自检详情 | 开发者入口 smoke |

## 17. 覆盖策略与幂等性

- 重复运行时如何处理：默认检查目标 MCAP_B 是否存在；存在且未显式覆盖时失败。
- 是否允许覆盖已有文件：生产默认不允许；开发者 run 内临时产物允许覆盖本次半成品。
- 如何避免污染旧 run：开发者功能检验必须写入独立 run 目录。
- 临时文件或半成品如何处理：MCAP_B 写出应先写临时文件，成功后原子改名；失败时删除或在摘要中标记。

## 18. 失败处理

| 失败情况 | 判断方式 | 处理策略 | 错误信息要求 | 是否写入报告 |
|---|---|---|---|---|
| SDK 不可导入 | import 失败 | SDK 自检失败，不进入 IK | `realman_sdk_import_failed` | 是 |
| SDK API 变更 | 找不到 `Algo` 或 IK 函数 | 自检失败 | `realman_sdk_api_missing` | 是 |
| common->base 外参缺失 | 配置缺字段 | strict 失败，不写 MCAP_B | `missing_common_to_robot_base_transform` | 是 |
| pose 四元数非法 | 输入校验失败 | 当前样本 `invalid_input` | `invalid_pose_quaternion` | 是 |
| IK 无解 | SDK 返回失败码 | 当前样本失败，不写 JointState | `ik_failed` | 是 |
| 输出目标已存在 | 路径存在且未允许覆盖 | 失败，不覆盖 | `output_exists` | 是 |

## 19. 可验证样例

| 样例 | 输入特征 | 预期输出 | 验证方式 |
|---|---|---|---|
| SDK smoke | 官方 Demo RM65 示例 pose | SDK 可导入且 IK 返回成功或稳定失败码 | L3 环境自检 |
| 单位外参 | common pose + identity 外参 | base pose 等于 common pose | 转换单测 |
| 左右双臂 | 左右 pose 和不同外参 | left/right 独立 base pose 和 IK 记录 | 双臂单测 |
| IK 失败 | mock SDK 返回失败 | 不写 JointState，sidecar 记录失败 | IK 单测 |
| 成功写出 | 合成成功 IK 结果 | MCAP_B 有左右 JointState | MCAP 写出测试 |

## 20. 整体完成标准

- [ ] [[CommonToRobotBaseTransform]]、[[RobotBaseTcpPose]]、[[Rm65IkConfig]]、[[Rm65IkSampleResult]]、[[McapB]] 和 [[IkSolveSummary]] 已形成原子数据定义。
- [ ] 本能力明确拆为 3 个子功能，且每个子功能可独立测试。
- [ ] SDK 本地部署与 IK 自检步骤能让无上下文 Agent 自动执行。
- [ ] common->base 转换对齐场景一 common frame 位姿转换语义，并复用或抽取现有 transform helper。
- [ ] 失败帧不写伪造关节角，所有输入 pose 都进入 [[IkSolveSummary]]。
- [ ] 开发者入口能通过场景二功能检验项查看 MCAP_B、IK 摘要和运行日志。

## 21. 开发者验收入口设计

| 项目 | 设计 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二：硬件数据可靠性验证 |
| 对应功能检验项 | `scene2_ik_mcap_b_writer` / 检查 IK 求解与 MCAP_B 生成 |
| 是否影响场景完整 smoke test | 是 |
| 小样本输入要求 | MCAP_A 小样本、common->base 外参、RM65 IK 配置、SDK 自检通过记录 |
| 调试输出目录要求 | 独立 run 目录，不写正式生产输出 |
| 测试产物 | `artifacts/ik_mcap_b/<stem>_mcap_b.mcap`、`artifacts/ik_solve_summary.json`、SDK 自检日志、运行日志 |
| 运行日志最低字段 | 输入 MCAP_A、外参配置、IK 配置、SDK 来源、转换统计、IK 成功/失败统计、输出位置、错误信息 |
| 临时覆盖配置 | 允许临时覆盖外参、初始关节角、输出目录和覆盖策略；覆盖只对本次运行生效 |
| 保存覆盖到配置文件 | 默认不保存；仅开发者明确选择时允许 |
| 人工最终验收方式 | 用户运行 `./start_data_clean.sh --dev` 后选择场景二和 `scene2_ik_mcap_b_writer`，检查 SDK 自检、MCAP_B JointState、IK sidecar 和运行日志 |

## 22. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 自动化验收方式 | 开发者入口验收关联 |
|---|---|---|---|---|---|---|---|
| service_s2_021 | 建立睿尔曼 SDK 本地部署与 IK 自检 | 数据读写类 | 官方 SDK 仓库、官方 Demo 文档 | SDK 拉取脚本或说明、自检测试 | `vendor/RealManRobot/`、`src/data_clean/tests/`、必要环境说明 | `python3` SDK import / IK smoke | 间接覆盖 `scene2_ik_mcap_b_writer` |
| service_s2_022 | 定义 IK 与 MCAP_B 数据契约 | 数据定义类 | 本 L2、场景二数据定义 | 代码类型 / schema、原子文档同步 | `src/data_clean/schemas/`、`src/data_clean/tests/`、场景二 L2 数据定义 | `python3` 导入与序列化测试 | 间接覆盖 `scene2_ik_mcap_b_writer` |
| service_s2_023 | 实现 common frame 到 robot base 坐标转换 | 数据计算类 | [[McapA]]、[[CommonToRobotBaseTransform]]、现有 transform helper | [[RobotBaseTcpPose]] | `src/data_clean/service/`、`src/data_clean/tests/` | `python3` 坐标转换单测 | `scene2_ik_mcap_b_writer` |
| service_s2_024 | 实现 RM65 SDK IK 求解适配器 | 数据计算类 | [[RobotBaseTcpPose]]、[[Rm65IkConfig]]、SDK `Algo` | [[Rm65IkSampleResult]] | `src/data_clean/service/`、`src/data_clean/tests/` | `python3` mock SDK / SDK smoke 测试 | `scene2_ik_mcap_b_writer` |
| service_s2_025 | 写出 MCAP_B 并接入开发者功能检验项 | 数据读写类 / 流程编排类 | [[Rm65IkSampleResult]]、[[McapB]]、[[IkSolveSummary]] | MCAP_B、sidecar、运行日志、开发者入口 | `src/data_clean/repo/`、`src/data_clean/runtime/`、`src/data_clean/ui/`、`start_data_clean.sh`、`src/data_clean/tests/` | `python3` MCAP_B contract / CLI smoke | `scene2_ik_mcap_b_writer` |

## 23. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
|---|---|---|---|
| 左右 common->base 外参的真实数值 | 直接决定 IK 物理正确性 | L2 固化配置契约；缺失时 strict 失败 | 用户 / 标定流程 |
| RM65 force type 是否固定标准版 | 影响 SDK `Algo` 初始化 | 默认 `RM_MODEL_RM_B_E`，允许配置覆盖 | 用户确认硬件版本 |
| MCAP_B JointState 关节名最终命名 | 影响下游关节检查和 MuJoCo 映射 | 首版用稳定 `joint1` 到 `joint6`，保留配置槽位 | 关节检查 / MuJoCo L2 |
| SDK 是否需要纳入 requirements | 影响 CI 和离线执行 | 首版 L3 使用 vendor 官方仓库和自检；后续再决定依赖固化 | Ubuntu 执行结果 |

## 24. 给 L3 任务生成的约束

1. 每个 L3 只能解决一个核心目标。
2. 第 6 模块必须拆为 SDK 自检、数据契约、common->base、IK 求解、MCAP_B 写出/入口接入等小任务。
3. common->base L3 必须先读取场景一 `common frame 位姿转换.md` 和 `src/data_clean/service/tcp_transform.py`。
4. common->base L3 必须复用或抽取通用 pose transform helper，不得复制一套方向不明的四元数代码。
5. IK L3 必须使用睿尔曼 SDK `Algo`，不得改为自研 MDH IK。
6. IK 失败帧不得写 NaN 或复制上一帧关节角。
7. MCAP_B L3 必须写 [[IkSolveSummary]]，且 sidecar 覆盖所有输入 pose。
8. 每个子功能必须有独立测试，不能只用最终集成 smoke 证明。
9. 每个 Service 场景 L3 必须写明它对应或影响 `./start_data_clean.sh --dev` 下的场景二功能检验项或场景完整 smoke test。
10. L3 自动化验收只证明局部实现正确；场景最终验收必须由用户本人运行 `./start_data_clean.sh --dev` 后确认。

