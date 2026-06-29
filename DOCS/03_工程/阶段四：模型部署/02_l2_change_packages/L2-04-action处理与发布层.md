# L2-04 · action 处理与发布层（输出侧）

> [!info] 归属
> - 对应分层：**Service + Runtime + UI**（相邻三层，输出链路紧密耦合）。
> - 上游：[[00_L2改造工作包总览]]、依赖 [[L2-01-Types层重构]]（action 结构）。
> - 下游：通过 `/pi05/policy_action`（UI 对外接口）连接 L2-05（硬件栈）。
> - 关联 Delta：D12（发布出口）、D13（safety 切分）、D17（可观测性）、D18（runtime mode）。

## 一句话定位

把模型输出的 action，经 policy-action 层安全检查后，发布成单路 `/pi05/policy_action`（16D Float32MultiArray）。隐藏「模型输出 → policy_action 发布」的逻辑，含 mode/gate 控制。

## 对应分层

- **Service 层**：`safety_guard.filter_action`（policy-action 通用检查）。
- **Runtime 层**：`deploy_node._control_tick` 的调度部分（调 control_loop.tick + 决定发不发）。
- **UI 层**：`deploy_node._create_publishers` + `_control_tick` 的发布部分 + `_publish_metrics`。

三层是输出链路的紧密耦合（safety 结果直接决定发不发），拆开反而增加协调成本。Service→Runtime→UI 单向依赖成立。合并。

## 涉及的现有代码

| 文件 | 部分 | AS-IS 现状 |
|---|---|---|
| `deploy/runtime/safety_guard.py` | 全文（L1-99） | 关节 delta 限幅（`max_joint_delta_rad`）、`hand_min/max`、`_build_joint_limits`、`_clamp_delta` |
| `deploy/ros_nodes/pi05_vla_deploy_node.py` | `_create_publishers`（L145-152）、`_control_tick`（L196-211）、`_publish_metrics`（L213-218）、`_joint_msg`（L242-248） | 4 路 publisher（JointState×2 + Float64×2）；`_control_tick` 发四路；`_joint_msg` 辅助 |
| `deploy/runtime/control_loop.py` | `tick()` 返回 `ControlCommand(action=BimanualAction)` | 调 safety_guard；依赖 action_dim + BimanualAction 结构 |

## 已有能力盘点

**保留的能力**：
- `SafetyGuard.filter_action` 的「shape 检查 + NaN/Inf 检查」前置逻辑——保留。
- `ControlLoop.tick` 的调度逻辑（预取/chunk消费/blend/fallback）——**完全不动**（L2-03 已声明，这里同样不动）。
- `_control_tick` 的「command is None 不发」+「mode 判断发不发」框架——保留，改发布内容。
- `_publish_metrics` 的 metrics/status 发布——保留，改字段。
- mode 三档（dry/shadow/safe）的 `publishes_command_topics` 属性——保留（Q4）。

**必须保留的原始行为**：
- safety 检查的「失败即拒绝 + 返回 SafetyResult(accepted=False)」语义。
- mode 三档对发布的控制（dry-run 不发 / shadow+safe 发 policy_action）。
- ControlLoop 的 fallback policy（safe_stop/hold_last_action/continue_old_chunk）。

## 真实改造边界

### 改 `safety_guard.py`（Service 层）

1. 删除关节 delta 限幅（`_clamp_delta`/`_delta_anchor`/`max_joint_delta_rad` 逻辑）——下移到 bridge。
2. 删除 `hand_min/hand_max` clip 和 `_build_joint_limits`——下移到 bridge。
3. 保留并强化 policy-action 通用检查：
   - action shape = 16D（用 Types 层 `ACTION_DIM`）
   - 全部 finite（NaN/Inf）
   - **新增 quaternion 归一化校验**（pose 段 [0:7] 和 [8:15] 的 quaternion 模长≈1）
   - **新增 TCP 单步位移限幅**（`max_tcp_delta_m`，相对上一帧或 observation 的 TCP）
   - **新增 gripper_width 值域** `[0,1]`
4. `filter_action` 返回的 `SafetyResult.action` 用新 `BimanualAction`（TCP+width）。

### 改 `deploy_node` 发布侧（Runtime + UI 层）

1. `_create_publishers`：删除 `left_arm_pub`/`right_arm_pub`/`left_hand_pub`/`right_hand_pub`；新增 `policy_action_pub`（Float32MultiArray，topic = `/pi05/policy_action`）。保留 status_pub/metrics_pub。
2. `_control_tick`：
   - command is None → 不发（保留）
   - mode dry-run → 日志打印 action（保留框架，改打印内容为 16D）
   - mode shadow/safe → 发 `policy_action_pub`（Float32MultiArray，16D，用 `BimanualAction.as_vector()`）
3. 删除 `_joint_msg` 辅助函数。
4. `_publish_metrics`：metrics 字段补充（observation_ready/policy_ready/最近 policy_action 发布时间）；status 文本改 mode + 新字段。

### mode/gate 逻辑（Q4 三档）

- mode=dry-run：不发 policy_action（`publishes_command_topics=False`）。
- mode=shadow-run：发 policy_action，但 **bridge 的 gate 关闭**（bridge 在 L2-05，本 L2 只负责发 policy_action）。
- mode=safe-run：发 policy_action，bridge gate 开（由 L2-05 的 bridge 实现）。

> [!note] 本 L2 只到「发 policy_action」
> policy_action 发出去后，是否到达硬件、bridge gate 开不开，属于 L2-05。本 L2 的边界是 `/pi05/policy_action` 这个 UI 接口。

## adapter 优先策略

safety_guard **直接修改**（关节检查逻辑整体替换为 TCP 检查）。但保留 `filter_action` 的**接口签名**（input: action + observation + previous_action → output: SafetyResult），让 ControlLoop 不用改。

发布侧**直接修改**（publisher 整体替换）。

## 真机风险

**中**。safety_guard 的 TCP 检查如果阈值设错，可能导致 action 被误拒或放过。dry-run + shadow-run 验证后才进 safe-run。

## 验收路径

1. **单测 safety_guard**：构造 16D action（含 NaN / 非归一化 quaternion / 越界 width），断言被拒绝；构造合法 action 断言通过。
2. **dry-run**：mode=dry-run，看日志打印的 16D action 是否正确。
3. **shadow-run**：mode=shadow-run，看 `/pi05/policy_action` 发布的 Float32MultiArray 是否 16D、段序正确；bridge（L2-05）此时不接，但 topic 有输出。
4. **mode 切换测试**：dry→shadow→safe 的 publishes_command_topics 属性正确。

## 回滚方式

git 回退 safety_guard + deploy_node + 切回旧 config/bundle。

## 可拆分的 L3 草案

| L3 | 目标 | 改的文件 |
|---|---|---|
| L3-04a | 改 `safety_guard`：删关节检查，加 TCP/width/quaternion 归一化检查 | safety_guard.py |
| L3-04b | 改 `deploy_node` 发布侧：删四路 publisher，加 policy_action_pub；改 `_control_tick` 发 16D | pi05_vla_deploy_node.py（发布部分） |
| L3-04c | 改 `_publish_metrics`：补充新字段 | pi05_vla_deploy_node.py（metrics 部分） |
| L3-04d | 单测 + dry-run + shadow-run 验证 | tests/ + dry-run |

> [!note] 与 L2-03 的协调
> L2-03 改 deploy_node 订阅侧，L2-04 改 deploy_node 发布侧。同一文件两半。建议：要么同一 Agent 顺序完成（先 L2-03 再 L2-04），要么明确约定改动行范围避免冲突。两者都依赖 L2-01 的 Types，彼此通过 control_loop/safety_guard 解耦。
