# ACT Contract Delta：AS-IS → ACT TO-BE 契约变更集

> [!info] 产物归属
> - 类型：Contract Delta（阶段四开发工作流 · 阶段三产物）。
> - 目标路径：`DOCS/03_工程/阶段四：模型部署/01_contracts/ACT Contract Delta.md`。
> - 上游契约：[[AS-IS Contract]]（现有 Pi0.5 代码现状）、[[ACT部署契约]]（ACT TO-BE）。
> - 并存说明：本文件与 [[Contract Delta]]（Pi0.5 版）并存。Pi0.5 版作为历史契约保留。
> - 本次只做规划与文档产出，不创建代码、不创建 L2 / L3 任务文件。

> [!warning] 真机风险声明
> 本 Delta 集新建了完整 ACT 部署链路。凡标记 `真机风险=高` 的 Delta，在进入 real-robot 前，必须先通过 dry-run + shadow-run 验证链路打通；凡涉及硬件发送的改造，必须保留可切回旧 launch 的回滚路径。

## 0. 如何阅读本文档

- §1 是 Delta 总表索引。
- §2 按变更对象分组展开每条 Delta 的完整字段。
- §3 是跨阶段依赖与尚未确认问题。

## 1. Delta 总表索引

本 Delta 集描述的是「从零新建 ACT 部署链路」。AS-IS 是现有 Pi0.5 代码（26D state / 14D action / 关节空间），ACT TO-BE 是新建独立 ACT 代码树（16D state / 16D action / TCP 空间）。

| 编号 | 变更对象 | 一句话差异 | 变更类型 | 是否兼容 | 真机风险 |
|---|---|---|---|---|---|
| A1 | Code Tree | 新建 `src/model_deploy/act/` 独立代码树，Pi0.5 代码原地保留 | 新增 | 兼容（不动 Pi0.5） | 低 |
| A2 | Types · state | 新建 ACT state_codec：16D，段序分组排列（左TCP+右TCP+左夹爪+右夹爪），不含触觉，边界校验 quaternion 模长 | 新增 | 独立 | 低 |
| A3 | Types · action | 新建 ACT action_codec + action_spec：16D，段序交替排列（左TCP+左夹爪+右TCP+右夹爪），绝对 TCP 目标 | 新增 | 独立 | 低 |
| A4 | Config | 新建 ACT config schema：`/act/*` topic、维度 16/16、bundle 路径、safety 配置、fps=15 | 新增 | 独立 | 低 |
| A5 | Repo+Service · bundle 加载 | 新建 ACT policy_loader：加载 ACT checkpoint，校验 manifest/normalizers/config，不做接口抽象 | 新增 | 独立 | 低 |
| A6 | Repo+Service · observation 装配 | 新建 observation_collector：16D snapshot 装配，`_build_batch` 构造 ACT 输入 | 新增 | 独立 | 低 |
| A7 | Service+Runtime+UI · 推理发布 | 新建 ActVlaDeployNode + control_loop + inference_worker + safety_guard + `/act/policy_action` 发布 | 新增 | 独立 | 中 |
| A8 | Safety · policy-action 层 | ACT safety_guard 只做 policy-action 通用检查（shape/NaN/Inf/quaternion/单步变化），硬件检查下移 bridge | 新增 | 独立 | 中 |
| A9 | Runtime Mode | dry-run / shadow-run / safe-run 三档，gate 由 command_bridge 控制 | 新增 | 独立 | 中 |
| A10 | Observability | `/act/status` + `/act/metrics` + `/act/command/status` | 新增 | 独立 | 低 |
| A11 | 独立子系统 · 硬件栈 | 新建 command_bridge_sender_node + rm65_driver_node + elephant_gripper_node + 新 launch，只依赖 `/act/policy_action` 16D 契约 | 新增 | 独立 | **高** |
| A12 | Failure Semantics | 硬件发送失败集中到 `/act/command/status`，不伪装成功 | 新增 | 独立 | 高 |

> [!note] 聚类观察
> 12 条 Delta 围绕**两个核心设计决策**聚集：
> 1. **ACT 推理链路新建**（A2~A10）：从零搭建 ACT 的 Types → Config → Repo → Service → Runtime → UI。
> 2. **硬件执行栈新建**（A11~A12）：policy_action → RM65/夹爪的指令边界与安全门。
> 这两个聚类通过 `/act/policy_action` 16D topic 解耦，分别对应 L2-01~04（推理链路）和 L2-05（硬件栈）。

## 2. Delta 分组详情

### 2.1 代码树（Code Tree）

#### A1 · 新建 ACT 独立代码树

| 字段 | 内容 |
|---|---|
| 变更对象 | Code Tree |
| AS-IS 契约 | 仅有 `src/model_deploy/pi05/`（Pi0.5 实现，26D state / 14D action）。无 ACT 部署代码。 |
| TO-BE 契约 | 新建 `src/model_deploy/act/` 独立代码树，与 `pi05/` 对称分层（common/deploy/tests）。Pi0.5 代码原地保留不动，不抽象 PolicyBackend 接口。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/`（全新目录）。不修改 `pi05/` 任何文件。 |
| 是否兼容 | 兼容（Pi0.5 代码零改动） |
| 实现方式 | 按 L2 分层逐步落地：L2-01 建 common/data，L2-02 建 common/config，L2-03 建 deploy 输入侧，L2-04 建 deploy 输出侧，L2-05 建硬件栈节点。 |
| 验收方式 | 目录结构存在；import 成功；Pi0.5 代码不受影响（pi05 测试仍通过）。 |
| 回滚方式 | 删除 `src/model_deploy/act/` 目录。 |

> [!note] 为什么不抽象 PolicyBackend 接口
> 依据《Agent编程执行原则》「简单优先 / 不为单次使用抽象新框架 / 不提前做未来扩展」：第一版只部署 ACT，Pi0.5 后端无验收场景，提前抽象接口违反此原则。将来需要 Pi0.5 与 ACT 切换时再重构。

### 2.2 Types 层（A2 / A3）

#### A2 · ACT state_codec（16D，分组段序，不含触觉）

| 字段 | 内容 |
|---|---|
| 变更对象 | Types · state |
| AS-IS 契约 | 无 ACT state codec。Pi0.5 的 state_codec 是 26D 关节语义（`left_arm_q` / `right_arm_q` / `left_hand_q` / EE pos+rpy）。 |
| TO-BE 契约 | 新建 ACT state_codec：16D = `left_tcp_pose[7] + right_tcp_pose[7] + left_gripper_width[1] + right_gripper_width[1]`，**分组段序**。pose 用 quaternion xyzw 归一化（模长≈1）；position 单位 m；夹爪 width[0,1]。不含触觉。与阶段二数据清洗 observation.state（去掉触觉段后）同构。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/common/data/state_codec.py`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | dataclass `ActBimanualState` + `encode_state()` + 边界校验（shape=16、dtype=float32、quaternion 模长≈1、width∈[0,1]）。对照《架构边界与机械约束原则》第三节：shape 在边界校验，下游不靠猜测。 |
| 验收方式 | 纯单测：构造合法/非法 state，断言编码结果维度段序、非法输入报错。 |
| 回滚方式 | 删除文件。 |

#### A3 · ACT action_codec + action_spec（16D，交替段序，绝对 TCP 目标）

| 字段 | 内容 |
|---|---|
| 变更对象 | Types · action |
| AS-IS 契约 | 无 ACT action codec。Pi0.5 的 action_spec 是 14D 关节空间。 |
| TO-BE 契约 | 新建 ACT action_codec + action_spec：16D = `left_tcp[7] + left_gripper_width[1] + right_tcp[7] + right_gripper_width[1]`，**交替段序**。绝对 TCP 目标（`action_t = target at step t+1`）。语义依据：阶段二 `数据清洗交付说明.md` action 段。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/common/data/action_codec.py`、`action_spec.py`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | 常量 `ACTION_DIM=16` + `split_bimanual_action()`（按交替段序拆解）+ 边界校验。 |
| 验收方式 | 纯单测：编码/解码 round-trip；段序拆解正确。 |
| 回滚方式 | 删除文件。 |

### 2.3 Config 层（A4）

#### A4 · ACT config schema

| 字段 | 内容 |
|---|---|
| 变更对象 | Config |
| AS-IS 契约 | 无 ACT config。Pi0.5 config schema 是 26D/14D 关节语义 + realsense/inspire topic。 |
| TO-BE 契约 | 新建 ACT config schema：observation topic（`/act/observation/*`）、维度 state=16/action=16、bundle 路径、`policy_type=act`、safety 配置（TCP 步长/quaternion delta/width 值域）、fps=15、cameras。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/common/config/schema.py`、`src/model_deploy/act/deploy/config/schema.py`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | frozen dataclass + `__post_init__` 校验（参考 Pi0.5 schema 结构，改维度和 topic）。 |
| 验收方式 | 单测：合法 config 加载成功；非法 config（维度错/topic 错）报错。 |
| 回滚方式 | 删除文件。 |

### 2.4 Repo + Service 层（A5 / A6）

#### A5 · ACT policy_loader（bundle 加载，不抽象接口）

| 字段 | 内容 |
|---|---|
| 变更对象 | Repo + Service · bundle 加载 |
| AS-IS 契约 | 无 ACT bundle 加载。Pi0.5 的 policy_loader 加载 base + LoRA adapter。 |
| TO-BE 契约 | 新建 ACT policy_loader：加载 ACT checkpoint（完整 policy 权重），校验 manifest（policy_type=act/state_dim=16/action_dim=16）、normalizers（mean/std 长度 16）、experiment_config（重建 ACTConfig）。**不做接口抽象**（不定义 PolicyBackend ABC），直接实现 `load_act_policy()` → `ActPolicyRuntime`。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/deploy/src/act/deploy/models/policy_loader.py`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | 显式接入 bundle（对照《架构边界与机械约束原则》第五节横切能力显式接入）；加载失败抛结构化错误，不静默。 |
| 验收方式 | dry-run：加载合法 ACT bundle 成功，离线推理输出 [n_action_steps, 16]。 |
| 回滚方式 | 删除文件。 |

#### A6 · observation_collector + batch adapter（16D 装配）

| 字段 | 内容 |
|---|---|
| 变更对象 | Repo + Service · observation 装配 |
| AS-IS 契约 | 无 ACT observation 装配。Pi0.5 的 collector 装配 26D 关节 state。 |
| TO-BE 契约 | 新建 observation_collector：订阅 `/act/observation/*`，装配 16D state（分组段序）+ 双目图像 snapshot；`_build_batch()` 是唯一的 `snapshot → ACT processor input` 映射位置。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/deploy/src/act/deploy/runtime/observation_collector.py`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | snapshot 完整性门控（必需字段齐全且未过期）；state 编码集中在 codec 边界，不散落 ROS 回调。 |
| 验收方式 | dry-run：缺 TCP pose 不生成 snapshot；snapshot 的 state 维度=16。 |
| 回滚方式 | 删除文件。 |

### 2.5 Service + Runtime + UI 层（A7 / A8 / A9 / A10）

#### A7 · ActVlaDeployNode + 推理发布链路

| 字段 | 内容 |
|---|---|
| 变更对象 | Service + Runtime + UI |
| AS-IS 契约 | 无 ACT 推理节点。Pi0.5 的 `Pi05VlaDeployNode` 是 Pi0.5 推理 + 四路 command 发布。 |
| TO-BE 契约 | 新建 `ActVlaDeployNode`：observation 汇聚 → ActPolicyRuntime 推理 → control_loop 按 control_hz 消费 chunk → 发布单路 `/act/policy_action`（16D）。复用 Pi0.5 的并发调度模型（SharedBuffer / InferenceWorker / ControlLoop），只替换模型加载和 batch 构造。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/deploy/src/act/deploy/ros_nodes/act_vla_deploy_node.py`、`runtime/control_loop.py`、`runtime/inference_worker.py`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | 参考 Pi0.5 的节点结构（对照 `pi05_old/` AS-IS），新建 ACT 版；inference_hz/control_hz/chunk_size 等调度参数走 config。 |
| 验收方式 | dry-run：节点启动不报错；shadow-run：`/act/policy_action` 16D 发布。 |
| 回滚方式 | 节点不启动。 |

#### A8 · safety_guard（policy-action 层检查）

| 字段 | 内容 |
|---|---|
| 变更对象 | Safety · policy-action 层 |
| AS-IS 契约 | 无 ACT safety。Pi0.5 的 SafetyGuard 做关节空间检查。 |
| TO-BE 契约 | 新建 ACT safety_guard：只做 policy-action 通用检查——action shape=16、NaN/Inf、quaternion 模长≈1、单步 TCP 位移/姿态变化约束、gripper_width∈[0,1]。硬件检查（workspace/IK/gripper 限幅/急停）下移到 command_bridge。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/deploy/src/act/deploy/runtime/safety_guard.py`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | 参数化检查项；TCP 步长检查替代关节 delta 检查。 |
| 验收方式 | dry-run：构造 NaN/越界 action，safety_guard 拒绝并记录 rejected reason。 |
| 回滚方式 | 删除文件。 |

#### A9 · Runtime Mode（三档）

| 字段 | 内容 |
|---|---|
| 变更对象 | Runtime Mode |
| AS-IS 契约 | Pi0.5 mode 依赖 mux 旁路/放行。 |
| TO-BE 契约 | dry-run / shadow-run / safe-run 三档。dry-run：不发 policy_action；shadow-run：发 policy_action + bridge gate 关；safe-run：发 + gate 开。gate 由 command_bridge 的 enable/急停/deadman 控制，mode 解耦。 |
| 变更类型 | 新增 |
| 影响范围 | `ActVlaDeployNode` 发布逻辑、`command_bridge_sender_node` gate。 |
| 是否兼容 | 独立 |
| 实现方式 | mode∈{shadow,safe} 时发 policy_action；bridge gate 按 mode + 物理开关与运算。 |
| 验收方式 | dry-run 无 policy_action；shadow-run 有 policy_action 但 `/act/command/status.sent_to_driver=false`；safe-run 机械臂动且急停可切断。 |
| 回滚方式 | 节点不启动。 |

#### A10 · Observability（status / metrics / command_status）

| 字段 | 内容 |
|---|---|
| 变更对象 | Observability |
| AS-IS 契约 | Pi0.5 的 `/pi05_vla/{status,metrics}`。 |
| TO-BE 契约 | `/act/status`（mode/observation_ready/policy_ready/last_error）+ `/act/metrics`（inference/latency/chunk/safety/published 计数 + observation 诊断）+ `/act/command/status`（bridge 发送结果）。 |
| 变更类型 | 新增 |
| 影响范围 | `ActVlaDeployNode` publisher、`command_bridge_sender_node`。 |
| 是否兼容 | 独立 |
| 实现方式 | topic 名走 config；JSON payload。 |
| 验收方式 | dry-run：`/act/metrics` 含新字段；`/act/command/status` 在 bridge 发送后更新。 |
| 回滚方式 | topic 名切回旧值。 |

### 2.6 硬件执行栈（A11 / A12）

#### A11 · command_bridge_sender_node + 硬件驱动 + launch

| 字段 | 内容 |
|---|---|
| 变更对象 | 独立子系统 · 硬件栈 |
| AS-IS 契约 | 无 ACT 硬件栈。Pi0.5 下游是 bridge+mux+picotele。 |
| TO-BE 契约 | 新建 `command_bridge_sender_node`（订阅 `/act/policy_action`，解析 16D，安全检查，发布 `/act/command/*`）+ `rm65_driver_node`（PoseStamped TCP 目标，movep_canfd）+ `elephant_gripper_node`（width→angle 映射）+ 新 launch。**只依赖 `/act/policy_action` 16D 契约**，与 ACT 推理链路解耦。 |
| 变更类型 | 新增 |
| 影响范围 | `src/model_deploy/act/deploy/src/act/deploy/ros_nodes/command_bridge_sender_node.py`、`rm65_driver_node.py`、`elephant_gripper_node.py`、`src/model_deploy/act/deploy/launch/`（新文件）。 |
| 是否兼容 | 独立 |
| 实现方式 | bridge 不读 ActVlaDeployNode 内部状态；发送前检查序列见 [[ACT部署契约]]（16D/finite/quaternion/workspace/IK预检/gripper限幅/急停gate）。硬件约定（TCP pose 来源、width↔angle 映射）复用 Pi0.5 契约设计。 |
| 验收方式 | shadow-run：16D→PoseStamped+Float64 转换正确，安全检查失败不发送；real-robot smoke test：保守动作阶梯（保持位姿→1cm位移→急停→gripper半开）。 |
| 回滚方式 | 节点不启动。 |

#### A12 · 硬件发送失败语义

| 字段 | 内容 |
|---|---|
| 变更对象 | Failure Semantics |
| AS-IS 契约 | Pi0.5 硬件层失败不回传。 |
| TO-BE 契约 | bridge 记录 action_id/safety_ok/sent_to_driver/failure_reason；SDK 错误透传到 `/act/command/status`，不伪装成功。 |
| 变更类型 | 新增 |
| 影响范围 | `command_bridge_sender_node`、`/act/command/status`。 |
| 是否兼容 | 独立 |
| 实现方式 | action_id 单调计数；每次发送写 status。 |
| 验收方式 | shadow-run：构造 IK 失败/越界场景，`failure_reason` 正确记录且不发硬件。 |
| 回滚方式 | bridge 不启动则无该 status。 |

## 3. 跨阶段依赖与尚未确认问题

### Q1 · ACT bundle 何时就绪

**状态**：待训练侧（阶段三）交付 ACT checkpoint。

依赖关系：
- A5/A6（bundle 加载 + observation 装配）依赖 ACT bundle 就绪才能运行验证。
- bundle 未就绪前，deploy 侧代码可以写，但只能人工 review，无法运行验证。
- 联调期必须严格按 dry-run → shadow-run → safe-run 阶梯，不能跳步。

### Q2 · ACT 训练是否使用 temporal ensemble

**状态**：待训练侧确认。

`temporal_ensemble_coeff` 影响 `n_action_steps`（启用时必须为 1，每步推理）。若训练侧启用，deploy 侧 control_loop 的 chunk 消费逻辑需对应调整。`experiment_config.yaml` 必须显式声明该值。

### Q3 · 触觉升级路径（第一版不含，后续 32D）

**状态**：已确认分两版（与 Pi0.5 契约 Q6 一致）。

- **第一版**：state=16D，不含触觉，不订阅 `/act/observation/tactile/*`。
- **后续版本**：state=32D，追加 16D 触觉段（4 片 × 4D），重新训练 32D bundle。
- **代码要求**：第一版 state codec 可记录升级路径，但**不提前预留触觉段逻辑**（依据《Agent编程执行原则》「不提前做未来扩展」）。升级时作为独立 L2 处理。

### Q4 · width→angle 映射系数标定

**状态**：待硬件标定。

理论上 `angle = width*100`，但闭合点/全开点的真实寄存器值需用大象夹爪实测标定。标定前不接真机。复用 Pi0.5 契约的 width↔angle 约定（见 [[TO-BE Contract]]）。
