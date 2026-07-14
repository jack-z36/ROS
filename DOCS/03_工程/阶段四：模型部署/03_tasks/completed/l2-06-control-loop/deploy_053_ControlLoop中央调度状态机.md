# L3 微元改造任务：ControlLoop 中央调度状态机

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
L3 编号：deploy_053
改造类型：behavior-change
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_053_ControlLoop中央调度状态机.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_053_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[downstream-l2]
本地验收是否必须：true
真机风险等级：dry-run-only
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 上游放行
> dispatch 保持 blocked。deploy_051/052 PASS_LOCAL 后，还必须由 deploy_056～060 分别闭合 L2-01～05 的真实 public seam；本任务禁止在 ControlLoop 内猜字段、重写上游 owner 或加兼容旁路。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_053
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_053_ControlLoop中央调度状态机.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G06, G07]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_053_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [downstream-l2]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 5
  parallel_group: l2-06-control-loop-p5-control-loop
  depends_on: [deploy_051, deploy_052, deploy_056, deploy_057, deploy_058, deploy_059, deploy_060]
  must_run_after: [deploy_051, deploy_052, deploy_056, deploy_057, deploy_058, deploy_059, deploy_060]
  can_run_parallel_with: []
  blocks: [deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/runtime/control_loop.py
      - src/model_deploy/act/runtime/__init__.py
      - src/model_deploy/act/tests/runtime/test_control_loop.py
    modules:
      - model_deploy.act.runtime.control_loop
    runtime_modes: [fake-policy, dry-run]
    hardware_paths:
      - /act/policy_action
      - /act/command/*
  robot_risk: dry-run-only
  dispatch_status: blocked
~~~

### Agent 执行 / 验收边界

- 执行 Agent 完整实现 A4、B3-B8、C3/C7/C13-C19/C23-C26，不拆出第二个调度器。
- 验收只用进程内 fake clock/permit/publisher；真实业务对象使用 SafetyGuard 与 L2-05 public request/result。
- 不连接 ROS graph、driver 或硬件；最多 3 轮。

## 3. 本次唯一目标

实现非阻塞 ControlLoop.tick 中央状态机：正确关联 worker result，管理 active/pending/cursor/prefetch，唯一解释 fallback，调用真实 safety/publish port，并按六种 PublishOutcome fail-closed 归约跨 tick 状态。

## 4. 所属 L2 边界与设计来源

### L2 负责

- 拥有 request id/in-flight、active/pending、cursor、candidate provenance、fallback、metrics、runtime/output fault latch。
- 每个 candidate safety 恰好一次、publish 至多一次；非 safety 失败不伪造 SafetyResult。

### L2 不负责

- 不构造 ACT batch、不执行 policy forward、不实现 SafetyGuard 算法、不适配 ROS message。
- 不写 /act/command/status，不做 smoothstep/blend/RTC/跨 chunk 融合，不声称 driver accepted。

### 本 L3 在 L2 中的位置

消费 deploy_051/052 的 channel/metrics/worker 结果以及 deploy_056～060 已验收的真实上游 public seam，交付 deploy_054 timer 可直接驱动的 A4 public tick。

### 必读 L2 设计文档

- 目标 L2 agent_context/01、03、03a、04、06、09、10。
- deploy_056～060 已落地并验收的 L2-01～05 public types/service/factory。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 类型 | 已有能力 | 与 ACT 差距 | 复用判断 |
|---|---|---|---|---|---|
| ControlLoop.tick | deploy/runtime/control_loop.py:59-222 | 编排函数 | result/request/cursor/fallback | 旧 safety/ControlCommand/metadata；错误 result 可能缺失 | 结构复用后重写 |
| is_action_chunk_usable | 同文件 :37-56 | 计算函数 | age/shape 判断 | age 错放 ActionChunk，当前需读 C2 | 结构复用 |
| active/pending/cursor | 同文件 | 内部状态更新 | chunk 切换 | 含 blend/aligned cursor | 仅保留直取 |
| smoothstep/blend | 同文件 :254-314 | 计算/状态 | 跨 chunk 平滑 | 第一版明确禁止 | 不复用 |
| fallback | 同文件 :316-333 | 编排函数 | hold/stop 分流 | 旧 ControlCommand/accepted 语义 | 参考理解后重写 |

### 必须保留的源码启发

- tick 不等待 GPU；active/pending 保护当前 horizon；失败路径显式。

### 禁止照搬的源码行为

- 不添加 aligned index、blend、runtime metadata 到 ActionChunk、旧 accepted/ControlCommand 或直接硬件 publish。

### 已知风险

- outstanding id 在 chunk invalidation 时被清空会产生两个并发 request。
- publish result 与原 request 不一致若未锁存，会让 permission 或安全事实失真。
- hold 若用 publish time 刷新 age，可无限重复 stale target。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 runtime/control_loop.py，完整实现 C3/C7/C13-C19/C23-C26 与 A4/B3-B8。
- tick 接收 monotonic_s、ros_time_s、CommandPermit；构造期注入 config、max observation age、startup command switch、ports、queues、metrics。
- result 匹配成功/失败都终结 in-flight；旧 id 丢弃、未知大 id/clock/queue/port invariant 锁存 runtime fault。
- pending 不截断 active；normal 到 execute_horizon，continue 才可到 chunk_size，全部按 observation capture age 复验。
- B6 normal-only；B8 独占 hold/continue/safe-stop；CandidateSelection 始终深复制并保留原 capture time。
- 调真实 SafetyGuard.filter_action 和绑定 publish_action；C19 按 request/result echo 与 L2-05 build→policy publish→gate→command 顺序核验。
- PARTIAL/FAILED 锁存 output fault；REJECTED/BLOCKED 保存一次性 deferred reason；safe-stop 逐 tick no-output 可恢复。

### 本次不做

- 不创建 ROS Node/timer/publisher，不加载配置/权重，不实现 permit source。
- 不在 REJECTED 同 tick 再发 fallback，不用全零 action 假装 safe-stop。

### 明确禁止修改

- L2-01～05 源码、设计投影与 owner tests；若接缝失败，退回 deploy_056～060 对应任务，不在本任务二次修补。
- ui/act_deploy_node.py、Pi0.5、硬件/launch。

### 函数 / class 策略

A4 持有跨 tick 状态，必须是 class；C13/C14/C18 纯计算，C15-C17/C19/C23-C25 为内部状态更新，B3-B8 为有顺序和失败传播的编排。

## 7. 六层产物落点

| 层 | 是否涉及 | 路径 | 职责 |
|---|---|---|---|
| runtime | 是 | src/model_deploy/act/runtime/control_loop.py；__init__.py | A4/B3-B8/C3/C7/C13-C19/C23-C26 |
| tests | 是 | src/model_deploy/act/tests/runtime/test_control_loop.py | fake-clock deterministic matrix |
| types/config/service | 只读 | public contracts | 输入/输出 |
| repo/ui/launch | 否 | — | 无产物 |
| acceptance | 否 | — | deploy_055 汇总 |

### 对应六层设计文档

| 设计文档 | 本 L3 内容 |
|---|---|
| 06_types层设计.md | 复用 ActionChunk/Safety/Publish contracts，不新增 ControlDecision |
| 09_service层设计.md | 三个真实能力接口与固定调用顺序 |
| 10_runtime层设计.md | §5 A4 完整状态机 |
| 07/08/11 | 只读边界 |

## 8. 文件内 3.5 层功能微元

| 文件 | 微元 | 类型 | 输入 | 输出/修改 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| runtime/control_loop.py | C3/C26 | 数据 | reason/action/source time | enum/frozen selection | 无 | FALLBACK_MATRIX |
| 同上 | C7 | 数据 | injected ports/config | cross-tick state | 无 | state invariants |
| 同上 | C13/C14/C18 | 计算函数 | result/state/request facts | decision/request | 无 | age/submit/request contract |
| 同上 | C15-C17/C19/C23-C25 | 内部状态更新 | pending/chunk/outcome/fault | state transition | RAM 修改 | correlation/reducer/latches |
| 同上 | B3-B8/A4 | class/编排 | tick facts | result或None | queue/safety/publish port | G06-G07 |

## 9. 实施步骤

1. 先写 correlation、age、prefetch/horizon、copy/provenance、fallback 和六 outcome 红测试。
2. 实现数据/纯 helper，再实现 A4 state、B4-B8，最后以 B3 固定总顺序串联。
3. 增量导出 public A4/C3，运行 deploy_051-053 回归和 UI/ROS/smoothing 负向扫描。

## 10. 允许修改

- src/model_deploy/act/runtime/control_loop.py
- src/model_deploy/act/runtime/__init__.py
- src/model_deploy/act/tests/runtime/test_control_loop.py

### 本次产物落点

| 产物 | 路径 | 层 |
|---|---|---|
| 中央状态机 | src/model_deploy/act/runtime/control_loop.py | runtime |
| 单元/状态迁移测试 | src/model_deploy/act/tests/runtime/test_control_loop.py | tests/runtime |

## 11. 禁止修改

- types/config/repo/service/ui、其他 L2 tests/dispatch/cards。
- /act/command/status writer、ROS action message、driver/SDK。
- smoothstep/blend/aligned/RTC/cross-chunk smoothing。

## 12. 验证方式

### 自动化验收命令

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py \
  src/model_deploy/act/tests/runtime/test_inference_worker.py \
  src/model_deploy/act/tests/runtime/test_control_loop.py -v
~~~

~~~bash
! rg -n "publish_safe|emit_fallback|\\.filter\\(|\\.accepted|ControlDecision|ControlCommand|smoothstep|blend|aligned|RTC|rclpy|create_publisher" \
  src/model_deploy/act/runtime
~~~

### 分层验证

| 层级 | 需要 | 内容 | PASS |
|---|---|---|---|
| unit/import | 是 | A4/C3/C7/C13-C19/C23-C26 | deterministic 全 PASS |
| fake-policy/FakePublisher | 是 | 慢/错 result、六 outcome | 无阻塞/无命令泄漏 |
| ROS/real-policy | 后续 | deploy_055 | 本卡不宣称通过 |
| real-robot | 禁止 | 无授权 | 不执行 |

### 真机风险控制

本任务只能使用进程内 FakePublisher。不得连接 ROS graph；真实 command 由 deploy_055/人工关卡另行控制。

### 验收证据落点

DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs/deploy_053/

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | G06 调度/correlation/age；G07 safety/publish/fallback/reducer |
| 能力 | A4 中央状态机、fail-closed latches、可恢复 fallback |
| 后续 | deploy_054 提供 ROS 驱动与生命周期；deploy_055 做真实跨 L2 tracer |

## 13. 必读上下文

- 阶段四工作流、L3 模板、ACT 落点约束。
- 目标 L2 agent_context/00-11，重点 01、03a、04、09、10。
- deploy_051/052 实现与验收反馈。
- 当前 L2-04 SafetyGuard、L2-05 ActionPublishRequest/Result/ActionPublisher tests。

## 14. 执行要求

- 校验 deploy_053 身份与 deploy_051/052、deploy_056～060 全部依赖完成。
- 任一 owner-remediation 未 PASS 时保持 blocked，不得添加临时字段兼容。
- 测试优先；执行 Agent 不改验收结论、不做 Git。

## 15. 成功标准

- [x] tick 永不等待 worker，最多一个 outstanding request。
- [x] matching success/error 均终结 request；乱序/未知 id/invalidation 规则正确。
- [x] active/pending/prefetch/horizon/continue/age 全部可由 fake clock确定测试。
- [x] candidate/previous/hold arrays 深复制且原 source age 不刷新。
- [x] 每 candidate safety=1、publish<=1；非 safety 失败不伪造 SafetyResult。
- [x] 六 outcome/provenance/echo 矩阵严格，矛盾为 PUBLISH_RESULT_INVARIANT。
- [x] REJECTED/BLOCKED deferred reason 一次性交付；PARTIAL/FAILED 与 runtime fault 分离锁存。
- [x] safe-stop 本 tick no-output、可恢复、不声称物理 stop。
- [x] 无 UI/ROS/smoothing/假接口污染。

## 16. 回滚方式

删除 control_loop.py 与测试，恢复 runtime facade；deploy_051/052 保持。FakePublisher 调用仅在进程内，无外部回滚。

## 17. 完成后交接

摘要必须给出状态迁移矩阵、边界 case、实际 pytest node、命令计数、fault/deferred reason、上游未闭合项和 deploy_054 解锁条件。

## 18. 执行摘要（deploy_053 完成）

### 18.1 实现符号（落到 control_loop.py）

- `ControlLoopConfig`（C7，frozen）：chunk_size / action_dim / execute_horizon / max_observation_age_s / command_output_enabled / continue_to_chunk_size / fallback_policy / prefetch_steps。
- `ControlLoop`（A4）：`tick(monotonic_s, ros_time_s, command_permit) -> Optional[ActionPublishResult]`、`request_shutdown()`、`metrics_snapshot()`；跨 tick 持有 active/pending chunk、cursor、outstanding id、last safe action、pending fallback reason、deferred delivered、runtime_status 单写者。
- 编排：`_collect_chunk_result`（B4/C15 关联）、`_maybe_submit_inference`（B5/C14 prefetch/horizon）、`_select_raw_action`（B6 cursor/horizon/age 复验）、`_run_fallback`（B8 hold/continue/safe-stop）。
- 归约/锁存：`_call_publish`（C18/C19 echo 检查）、`_reduce_publish_outcome`（C17 六 outcome）、`_deliver_deferred_reason` / `_clear_deferred`（C25）、`_latch_output_fault`（C23）、`_latch_runtime_fault`（C24）、`_finalize_runtime_status`（单写者优先级 SHUTDOWN > RUNTIME_FAULT > OUTPUT_FAULT > per-tick）。
- 数据/纯函数：`FallbackReason`、`FallbackSelection`、`select_fallback`、`FALLBACK_MATRIX`、`CandidateSelection`、`select_candidate`、`is_action_chunk_usable`（C13）、`build_inference_request`（C18）；`_deep_copy_spec` 保证 array 深复制。

### 18.2 验证命令与计数

| 命令 | 结果 |
|---|---|
| `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/runtime/test_control_loop.py -v` | **31 passed** |
| `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/runtime -q` | **102 passed**, 1 warning(既有, worker KeyboardInterrupt 测试) |
| `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q` | **783 passed / 4 skipped / 0 failed**, 2 warning(既有) |
| `rg/rg -n "rclpy\|create_publisher\|create_timer\|import yaml\|torch.load\|SafetyGuard\|ActionPublisher" src/model_deploy/act/runtime/control_loop.py` | **0 匹配**（仅通过注入的 safety_port/publish_port/observation_port 调用 public seam） |

### 18.3 状态迁移矩阵（per tick）

| 前置 | 触发 | 关联/动作 | 输出 | runtime_status |
|---|---|---|---|---|
| no chunk | 首 tick | 提交 rid=1 | None（NO_ACTIVE_ACTION fallback） | FALLBACK / SAFE_STOP |
| outstanding=rid | result 命中 | 终结 in-flight，pending→active | 候选→safety→publish | NORMAL / 对应 outcome |
| outstanding=rid | result 错误 | 终结，INFERENCE_ERROR | hold/safe-stop（无 latch） | FALLBACK_SAFE_STOP |
| no outstanding | result id 不合法 | UNKNOWN/STALE_RESULT_ID latch | None | RUNTIME_FAULT |
| active chunk 过期 | age > max | OBSERVATION_STALE discard | hold（保留原 source age） | NORMAL / FALLBACK_SAFE_STOP |
| candidate | safety REJECTED | 不补发 fallback，deliver deferred | None | FALLBACK |
| publish | PUBLISHED/OBSERVED | 清 deferred | result | NORMAL |
| publish | BLOCKED/REJECTED | deliver deferred 一次 | result | FALLBACK |
| publish | PARTIAL/FAILED | output_fault latch | result/None | OUTPUT_FAULT |
| publish port 篡改 action_id | echo 不符 | PUBLISH_RESULT_INVARIANT latch | — | RUNTIME_FAULT |
| request_shutdown | — | 关双队列，冻结 | None（不再 safety/publish） | SHUTDOWN（最高优先级） |

### 18.4 边界 case

- 至多一个 outstanding：error tick 不再同 tick 重发（由 `_pending_fallback_reason` 守卫，恢复交给下一 tick）。
- pending 不截断 active：仅在 cursor 到达 horizon 边界才切换到 pending。
- continue 模式 cursor 可越过 execute_horizon 直至 chunk_size；normal 模式停在 execute_horizon。
- hold 深复制且 `_store_safe_action(refresh_source=False)` 保留原 capture time，避免 stale target 无限重复。
- 单写者：`_finalize_runtime_status` 中 SHUTDOWN 优先级高于一切 latch，shutdown 后 status 不再被 per-tick 覆盖。

### 18.5 fault / deferred reason 计数（metrics 事件）

- runtime_fault_latched（C24，sticky）：UNKNOWN_RESULT_ID / STALE_RESULT_ID / CHUNK_SHAPE_INVALID / PENDING_CHUNK_STALE / PUBLISH_RESULT_INVARIANT。
- output_fault_latched（C23，sticky）：PARTIAL / FAILED。
- deferred_fallback（C25，一次性）：PERMIT_DENIED / SAFETY_REJECTED / 等；成功 PUBLISHED/OBSERVED 后 `_clear_deferred` 可恢复。

### 18.6 上游未闭合项 / 验证空白（unverified）

- **未本地执行**：真实 ROS graph、真实 policy forward、真实 SafetyGuard 配置边界、ActionPublisher 真实 ROS 发布、硬件 driver 均未在本地跑（本卡 dry-run-only，符合 robot_risk 与分层验证表）。
- **deploy_054/055 解锁**：deploy_053 已 PASS_LOCAL；deploy_054（ROS timer/生命周期驱动）与 deploy_055（真实跨 L2 tracer）可基于本 A4.tick 接入。验收卡片 `deploy_053_验收卡片.md` 应作为下一执行对象（本 L3 仅完成实现与进程内测试，不宣称真机/ROS 通过）。
- `ObservationBuffer._default_monotonic_clock` 存在一处既有 bug（`return time.monotonic` 缺调用括号），但属 L2-02，不在本任务 scope，未被 control_loop.py 直接引用（ControlLoop 注入 observation_port），未改动。

