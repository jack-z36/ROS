# L2-04 ACT action 处理与发布

> [!info] 归属
> - 对应分层：Service + Runtime + UI（输出侧，依赖 L2-01 Types）
> - 关联 ACT Delta：A7（推理发布链路）、A8（safety_guard）、A9（mode）、A10（observability）
> - 关联契约：[[ACT部署契约]]

## 一句话定位

隐藏「ACT 模型输出 → `/act/policy_action` 发布」的逻辑：safety_guard 做 policy-action 层检查，ActVlaDeployNode 装配推理调度并发布单路 16D policy_action。

## 本次唯一目标

- 新建 `src/model_deploy/act/service/safety_guard.py`：policy-action 层检查（shape/NaN/Inf/quaternion/单步变化/width 值域）。
- 新建 `src/model_deploy/act/runtime/control_loop.py`、`inference_worker.py`、`shared_buffer.py`：**直接复用**同事调度骨架。
- 新建 `src/model_deploy/act/ui/ros_nodes/act_vla_deploy_node.py`：ActVlaDeployNode（observation 汇聚 + 异步推理 + chunk 消费 + policy_action 发布）。
- mode/gate 逻辑：dry-run/shadow-run/safe-run 三档。
- metrics/status 发布。

## 同事源码复用边界

| ACT 目标 | 同事源文件 | 方式 | 复用要点 |
|---|---|---|---|
| `act/runtime/shared_buffer.py` | `pi05_old/.../deploy/src/pi05/deploy/runtime/shared_buffer.py` (242行) | **直接复用** | 零改动。纯数据结构+线程同步：`ObservationSnapshot`/`ActionChunk`/`InferenceRequest`/`LatestQueue[T]`/`RuntimeMetrics`/`SharedBuffer`。无模型 import（仅 TYPE_CHECKING 下 import torch）。只改包名 `pi05.`→`act.` |
| `act/runtime/control_loop.py` | `pi05_old/.../deploy/src/pi05/deploy/runtime/control_loop.py` (348行) | **直接复用** | 几乎零改动。核心调度逻辑（chunk 消费/预取/smoothstep blend/fallback/aligned_index 时间对齐）全部保留。通过抽象接口交互（`BimanualAction`/`SafetyGuard`/`SharedBuffer`），不碰模型。仅 import 路径改 `pi05.`→`act.` |
| `act/runtime/inference_worker.py` | `pi05_old/.../deploy/src/pi05/deploy/runtime/inference_worker.py` (91行) | **直接复用** | 零改动。后台线程消费 request → 调 `policy_runtime.predict_action_chunk(obs)` → 推回 chunk。与模型唯一耦合点是这一个方法调用，L2-03 的 `ActPolicyRuntime` 保持签名即可。线程名 `pi05_inference_worker`→`act_inference_worker` |
| `act/service/safety_guard.py` | `pi05_old/.../deploy/src/pi05/deploy/runtime/safety_guard.py` (98行) | **结构复用** | 保留 `SafetyGuard`/`SafetyResult`/`filter_action()` 框架 + NaN/Inf 检查。改检查项：`max_joint_delta_rad`→`max_tcp_step_m`；新增 `max_quat_delta` quaternion 检查；hand 范围 `hand_min/hand_max`→`gripper_width∈[0,1]` |
| `act/ui/ros_nodes/act_vla_deploy_node.py` | `pi05_old/.../deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py` (274行) | **结构复用** | 保留节点装配骨架：`MultiThreadedExecutor`(4线程) + timer 驱动 `_control_tick` + collector/buffer/control_loop/inference_worker 装配顺序。改：订阅列表（3 相机+本体感知 → 双目+TCP+gripper）；publisher（四路 command → 单路 `/act/policy_action`）；import `policy_loader`→`act.repo.policy_loader`；类名 `Pi05VlaDeployNode`→`ActVlaDeployNode` |

> [!success] 本 L2 是复用收益最大的工作包
> runtime 层三个文件（shared_buffer 242行 + control_loop 348行 + inference_worker 91行 = **681 行**）几乎原样搬运，这是同事已验证的并发调度模型（producer-consumer + latest-only 队列 + chunk 预取 + smoothstep blend）。**不重写这些**，只改包名和 import。

## 明确不做

- 不直接发送 RM65 / 夹爪硬件命令（由 L2-05 command_bridge 负责）。
- 不做硬件层安全检查（workspace/IK/gripper 限幅/急停，下移到 bridge）。
- 不修改 Pi0.5 节点。

## safety_guard 检查项（policy-action 层）

| 检查 | 失败行为 |
|---|---|
| action shape == 16 | 拒绝，记录 rejected reason |
| 全部 finite（无 NaN/Inf） | 拒绝 |
| quaternion 模长 ≈ 1（[3:7] 和 [11:15]） | 拒绝（或按配置归一化） |
| 单步 TCP 位移 ≤ max_tcp_step_m | 拒绝 |
| 单步 quaternion delta ≤ max_quat_delta | 拒绝 |
| gripper_width ∈ [0,1] | clip 或拒绝（按配置） |

## ActVlaDeployNode 运行逻辑

参考 Pi0.5 的并发调度模型（`pi05_old/` AS-IS），新建 ACT 版：
- ROS 回调解码 observation topic → ObservationCollector（L2-03）。
- SharedBuffer：latest-only 缓冲。
- ControlLoop：按 control_hz 消费 action chunk，预取推理请求。
- InferenceWorker：后台线程，调 ActPolicyRuntime（L2-03）。
- 发布 `/act/policy_action`（16D Float32MultiArray）+ `/act/status` + `/act/metrics`。

mode 语义：
- dry-run：不发 policy_action（只打印日志）。
- shadow-run：发 policy_action，bridge gate 关（机械臂不动）。
- safe-run：发 policy_action，bridge gate 开（机械臂动）。

## 依赖

- L2-01：action_codec/safety 相关常量。
- L2-03：observation_collector、policy_loader（ActPolicyRuntime）。
- L2-02：config（topic、mode、safety 阈值）。

## L3 草案

| L3 | 目标 | 验收模式 |
|---|---|---|
| deploy_013 | 从同事 shared_buffer + control_loop + inference_worker **直接复用**到 `act/runtime/`（改包名 import） | direct-local 单测（import 成功 + 基础单测） |
| deploy_014 | 从同事 safety_guard 结构复用：建 `act/service/safety_guard.py`，改检查项 TCP/quaternion/width | direct-local 单测 |
| deploy_015 | 从同事 deploy_node 结构复用：建 `act/ui/ros_nodes/act_vla_deploy_node.py`，改订阅/publisher | downstream-l2（shadow-run） |
| deploy_016 | mode/gate 三档 + metrics/status + shadow-run 全链路验证 | direct-local（shadow-run） |

## 真机风险

中。不直接驱动硬件，但 policy_action 发布质量直接影响下游 bridge。shadow-run 验证必须先于 safe-run。

## 回滚方式

删除 act_vla_deploy_node.py / safety_guard.py / control_loop.py / inference_worker.py。节点不启动即回滚。

## L2 Gate（AI 侧自动化）

- required L3：deploy_013 ~ deploy_016。
- 运行命令：`pytest src/model_deploy/act/tests/deploy/ -v`；shadow-run 启动节点。
- 通过现象：safety_guard 拒绝非法 action；shadow-run 下 `/act/policy_action` 16D 发布；`/act/metrics` 含 inference/latency/rejected 计数。

## 人类验收标准

验收性质为「机械」（shadow-run）：

| 验收项 | 运行命令 | 通过现象 |
|---|---|---|
| 1 | `pytest src/model_deploy/act/tests/deploy/test_safety_guard.py -v` | 构造 NaN/模长≠1/width=2 的 action，全部被拒绝，rejected_reason 记录正确 |
| 2 | shadow-run 启动节点（mode=shadow-run），`ros2 topic echo /act/policy_action` | 有 16D 输出，段序交替（左tcp7+左width1+右tcp7+右width1） |
| 3 | `ros2 topic echo /act/metrics` | JSON 含 inference_count、latency_ms、rejected_action_count |
| 4 | `ros2 topic echo /act/command/status`（若 L2-05 bridge 已启动） | shadow-run 显示 sent_to_driver=false |

用户签字位置：`05_acceptance/l2-04-publish/验收结果.md` 末尾「人类验收」段。
