# L3 微元改造任务：InferenceWorker 串行异步执行

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：l2-06-control-loop ControlLoop 中央运行调度闭环
L3 编号：deploy_052
改造类型：source-adaptation
当前任务文件路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_052_InferenceWorker串行异步执行.md
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_052_验收卡片.md
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
真机风险等级：none
L2 分支：feat/model_deploy/l2-06-control-loop
集成分支：model_deploy

> [!warning] 上游放行
> dispatch 保持 blocked，直到 P0-01～P0-10 owner/路径已闭合并且 deploy_051 达到 PASS_LOCAL。本任务只调用 L2-03 的同步 public port，不修改 L2-03。

## 2. 调度元数据

~~~yaml
dispatch:
  task_id: deploy_052
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_052_InferenceWorker串行异步执行.md
  group: l2-06-control-loop
  branch: feat/model_deploy/l2-06-control-loop
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop
  acceptance_scenarios: [G05]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_052_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs
  wave: 2
  parallel_group: l2-06-control-loop-p2
  depends_on: [deploy_051]
  must_run_after: [deploy_051]
  can_run_parallel_with: []
  blocks: [deploy_053, deploy_054, deploy_055]
  conflict_scope:
    files:
      - src/model_deploy/act/runtime/inference_worker.py
      - src/model_deploy/act/runtime/__init__.py
      - src/model_deploy/act/tests/runtime/test_inference_worker.py
    modules:
      - model_deploy.act.runtime.inference_worker
    runtime_modes: [fake-policy]
    hardware_paths: []
  robot_risk: none
  dispatch_status: blocked
~~~

### Agent 执行 / 验收边界

- 执行 Agent 实现 A3、B1-B2、C22；不得实现 tick、fallback、safety 或 publish。
- 验收 Agent 使用可阻塞/抛错的 fake inference port，另用真实 ActInferenceService 的同步签名做 import/contract 检查。
- 最多 3 轮执行-验收迭代。

## 3. 本次唯一目标

实现一个 daemon、单线程、stop-aware 的 InferenceWorker：阻塞消费最新 request，串行调用 L2-03 同步服务，并为成功或普通异常都生成 terminal InferenceResult。

## 4. 所属 L2 边界与设计来源

### L2 负责

- 把可能阻塞的 policy inference 隔离到一个后台线程。
- 维护 start-to-start 限频、stop/close/join 合同和 worker fatal metrics。

### L2 不负责

- 不在 worker 中决定 request 时机、active/pending/cursor、fallback、safety、permit 或 publish。
- 不把 thread/queue/error recovery 放回 L2-03。

### 本 L3 在 L2 中的位置

消费 deploy_051 的 A1/A2/C1/C2，向 deploy_053 提供不会阻塞 timer 的唯一推理执行轴。

### 必读 L2 设计文档

- 目标 L2 agent_context/01、02、03、03a、04、09_service层设计.md、10_runtime层设计.md。
- L1 边界/协作与 ACT 代码树约束。

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 类型 | 已有能力 | 与 ACT 差距 | 复用判断 |
|---|---|---|---|---|---|
| InferenceWorker.run | deploy/runtime/inference_worker.py:15-91 | 编排函数 | 后台取 request、限频、调 policy | policy 异常只记 metrics、不产 terminal result；stop/close 边界不完整 | 结构复用 |
| _run_request | 同文件 | 编排函数 | 单次 forward | 旧 ActionChunk 携带 runtime metadata | 结构复用后重写 |

### 必须保留的源码启发

- timer/worker 解耦和单一 policy 最大并发为 1。

### 禁止照搬的源码行为

- 不吞异常后让 in-flight 永久悬挂；不向 ActionChunk 写 request/time/error。

### 已知风险

- 限频使用 wall clock 或 busy sleep 会破坏 fake-clock Gate 和 shutdown 有界性。
- stop 与 put result 的竞态若处理错误，可能在 shutdown 后写入 closed queue。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 runtime/inference_worker.py 实现 A3、B1、B2、C22。
- 构造固定 daemon=True；注入 service、双 queue、metrics、inference_hz 与 monotonic callable。
- 普通 Exception 转为 C2 error；KeyboardInterrupt/SystemExit 不吞。
- 检查 start/complete clock finite、非负、非倒退；异常 queue/drop 写稳定 fatal reason。
- 增量更新 runtime facade并补 thread/stop/error/serial unit tests。

### 本次不做

- 不创建 request、不清 ControlLoop in-flight、不直接发布 metrics 或 command。
- 不强杀正在执行的 policy；shutdown late result 仅丢弃。

### 明确禁止修改

- L2-03 service 实现及 L2-01～05 源码。
- ControlLoop/UI/ROS/硬件路径。

### 函数 / class 策略

A3 需要 thread/event/period/lifecycle state，必须是 class；B1/B2 为编排 method，C22 只幂等更新 stop event。

## 7. 六层产物落点

| 层 | 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| runtime | 是 | src/model_deploy/act/runtime/inference_worker.py；__init__.py | A3/B1-B2/C22 |
| tests | 是 | src/model_deploy/act/tests/runtime/test_inference_worker.py | serial/error/stop/clock |
| types/config/repo/service/ui/launch | 否 | — | 只读 public contracts |
| acceptance | 否 | — | deploy_055 汇总 |

### 对应六层设计文档

| 设计文档 | 本 L3 内容 |
|---|---|
| 09_service层设计.md | 精确调用 ActInferenceService.predict_action_chunk |
| 10_runtime层设计.md | §4 A3/B1/B2/C22 |
| 06/07/08/11 | 只读边界，不新增产物 |

## 8. 文件内 3.5 层功能微元

| 文件 | 微元 | 类型 | 输入 | 输出 | 副作用 | 验收 |
|---|---|---|---|---|---|---|
| runtime/inference_worker.py | A3 state | 数据/class | service、queue、clock、hz | worker object | thread state | WORKER_SERIAL_POLICY |
| 同上 | B1 run | 编排函数 | request queue/stop | 连续 result | 阻塞 wait、queue write | WORKER_TICK_NONBLOCKING、WORKER_SHUTDOWN |
| 同上 | B2 execute | 编排函数 | C1 | C2 success/error | 同步 policy call | WORKER_ERROR_RECOVERY |
| 同上 | C22 stop | 内部状态更新 | — | stop event set | waiter 可退出 | idempotent stop |

## 9. 实施步骤

1. 先写慢 policy、并发探针、异常一次后成功、clock invalid、stop-before/after-policy、closed result queue 测试。
2. 实现 A3/B1/B2/C22，复用 deploy_051 public channel/metrics。
3. 更新 facade，运行 worker 与 deploy_051 回归测试和 runtime→ui 反向依赖扫描。

## 10. 允许修改

- src/model_deploy/act/runtime/inference_worker.py
- src/model_deploy/act/runtime/__init__.py
- src/model_deploy/act/tests/runtime/test_inference_worker.py

### 本次产物落点

| 产物 | 路径 | 层 |
|---|---|---|
| worker | src/model_deploy/act/runtime/inference_worker.py | runtime |
| unit tests | src/model_deploy/act/tests/runtime/test_inference_worker.py | tests/runtime |

## 11. 禁止修改

- src/model_deploy/act/service/act_inference.py 及其 batch/postprocess。
- runtime/control_loop.py、ui/act_deploy_node.py。
- config/repo/policy loader、ROS graph、硬件。

## 12. 验证方式

### 自动化验收命令

~~~bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py \
  src/model_deploy/act/tests/runtime/test_inference_worker.py -v
~~~

~~~bash
! rg -n "SafetyGuard|ActionPublisher|create_timer|create_publisher|rclpy|yaml|torch\\.load" \
  src/model_deploy/act/runtime/inference_worker.py
~~~

### 分层验证

| 层级 | 需要 | 验证内容 | PASS |
|---|---|---|---|
| unit/import | 是 | serial/error/clock/stop/late-result | 全 PASS，无 live thread |
| fake-policy | 是 | 可阻塞和异常 port | terminal C2 且 worker 继续 |
| ROS/real-policy/robot | 否 | 后续 Gate | 不适用 |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/logs/deploy_052/

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | G05：WORKER_TICK_NONBLOCKING、WORKER_SERIAL_POLICY、WORKER_ERROR_RECOVERY、WORKER_SHUTDOWN |
| 能力 | 后台单线程推理轴与 terminal result 合同 |
| 后续 | deploy_053 负责 correlation/cursor/fallback/publish |

## 13. 必读上下文

- 阶段四工作流、L3 模板、ACT 落点约束。
- 目标 L2 agent_context/00-11，重点 03a、04、09、10。
- deploy_051 任务、实现与验收反馈。
- Pi0.5 inference_worker.py 只读参考；当前 ActInferenceService public method。

## 14. 执行要求

- 核对任务身份 deploy_052，depends_on deploy_051 已完成。
- dispatch 解锁前不得执行；不得把上游 P0 修复混入本 commit。
- 测试优先，不运行 Git 操作。

## 15. 成功标准

- [x] 同一 service 最大并发 forward 数始终为 1。
- [x] 普通异常形成 C2 error，不杀 worker，后续 request 可成功。
- [x] start-to-start 限频和 clock invalid 规则可由 fake clock 确定验证。
- [x] stop-aware 双检查、closed queue 和 late result 行为符合设计。
- [x] C22 幂等；正常 shutdown 无 live thread。
- [x] worker 不拥有 cursor/safety/fallback/publish/UI 逻辑。
- [x] 已登记实际命令、结果与未验证项。

## 16. 回滚方式

删除 inference_worker.py 与其测试，恢复 runtime/__init__.py；deploy_051 channel/metrics 保持不变。

## 17. 完成后交接

摘要需给出最大并发证据、异常恢复、时钟/限频、stop/join、late-result 和边界扫描；说明 deploy_053 尚依赖的上游 public contract。

## 18. 执行摘要（deploy_052）

### 18.1 实现的 public 符号

- `model_deploy.act.runtime.inference_worker.InferenceWorker`（A3 / B1 / B2 / C22）
  - 继承 `threading.Thread`，构造固定 `daemon=True`。
  - 构造签名：`InferenceWorker(*, service, request_queue, result_queue, metrics, inference_hz, clock)`。
  - 公共方法：`start()` / `run()` / `stop()`（幂等 `_stop_event.set()`）/ `join()` / `is_alive()`（均沿用 `threading.Thread` 标准合同）。
  - 内部方法：`_execute_request`（B2）、`_publish_result`、`_read_clock`、`_rate_limit_remaining`、`_fatal`。
- `model_deploy.act.runtime.__init__` 增量导出 `InferenceWorker`，未删除/遮蔽已有 `InferenceRequest / InferenceResult / LatestQueue / RuntimeMetrics / RuntimeMetricsSnapshot` 导出。

### 18.2 测试结果

- 验证命令（L3 指定）：
  `PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/runtime/test_inference_channel.py src/model_deploy/act/tests/runtime/test_runtime_metrics.py src/model_deploy/act/tests/runtime/test_inference_worker.py -v`
- 结果：**57 passed**（deploy_051 的 40 个用例全绿 + deploy_052 新增 17 个用例全绿）。
- 全 runtime 目录回归：`src/model_deploy/act/tests/runtime/ -q` → **71 passed**（含其它已有 runtime 用例）。
- 结论：**PASS_LOCAL**。

### 18.3 最大并发证据（WORKER_SERIAL_POLICY）

- `TestHappyPathAndConcurrency::test_max_concurrency_is_one`：使用 `SerialProbeService`（`predict_action_chunk` 内带锁+计数器），单 worker 串喂 7 个 request 并即时消费结果，断言 `service._max_in_flight == 1` 且 `call_count == 7`。
- 单 daemon 线程天然保证同一 service 的 forward 调用串行；并发探针确认运行期无任何重叠调用。

### 18.4 异常恢复证据（WORKER_ERROR_RECOVERY）

- `test_exception_becomes_terminal_error_and_worker_continues`：service 第一次抛 `ValueError`、之后成功；worker 产出 error C2（`error_type="ValueError"`、截断 message），`inference_error_count==1`，worker 仍 alive，继续处理第二个 request 产出 success C2（`inference_success_count==1`）。
- `test_keyboard_interrupt_not_swallowed`：`KeyboardInterrupt` 不被吞，线程以未捕获异常退出（`worker_fatal_reason` 为 None）。
- 普通 `Exception` 经 `InferenceResult.error` 转成稳定 class name + bounded message（≤512），不写 exception/traceback/ROS 对象。

### 18.5 时钟 / 限频（WORKER_TICK_NONBLOCKING + clock invalid）

- 限频为 start-to-start：`remaining = max(0, _last_inference_start_s + period - now)`，首 request 立即执行（`_last_inference_start_s is None` → 0）。
- `_rate_limit_remaining` 由 fake clock 确定性单测覆盖：`test_first_request_immediate`、`test_respects_period`、`test_rate_limit_does_not_cause_errors`。
- 实际 wait 用 `_stop_event.wait(remaining)`（可中断、无 wall-clock sleep、无忙轮询）。
- clock invalid 规则：所有 worker 时钟读经 `_read_clock` 校验 finite / 非负 / 非递减；非法读记录稳定 `worker_fatal_reason="CLOCK_INVALID"` 并退出。
  - `test_non_finite_clock_is_fatal`（nan）→ CLOCK_INVALID。
  - `test_backwards_clock_is_fatal`（completed 回退到 5.0 < 10.0）→ CLOCK_INVALID。

### 18.6 stop / join

- `test_stop_before_policy_idle_worker_never_calls_policy`：idle 时 `stop()` + `request_queue.close()` 唤醒阻塞的 `take_latest`，service 调用 0 次。
- `test_stop_after_policy_discards_result_and_exits`：policy 运行期间 `stop()`，完成后丢弃结果并退出（published 为空，`worker_fatal_reason` 为 None）。
- `test_idempotent_stop`：`stop()` 连续两次无副作用，事件置位，worker 干净退出。
- `test_no_live_thread_after_clean_shutdown`：处理完 3 个 request 后 `stop()` + `close()` + `join(timeout)`，断言 `not is_alive()`。

### 18.7 late-result / closed queue 行为

- `test_late_result_after_shutdown_is_discarded`：policy 运行期间 `result_queue.close()` + `stop()`，结果 put 抛 `RuntimeError("queue is closed")` 被捕获、丢弃，worker 优雅退出（不抛/不挂）。
- `test_unexpected_closed_result_queue_is_queue_invariant`：仅 `result_queue.close()`（未 stop），记录 `result_queue_drop_count>=1` 与稳定 `worker_fatal_reason="QUEUE_INVARIANT"` 并退出（不抛/不挂）。
- `_publish_result` 在 fatal 分支返回 `True`，驱动 `run` 终止循环，避免 shutdown 后写 closed queue 或无限阻塞在 `take_latest`。

### 18.8 边界扫描结果

- forbidden-pattern grep 对 `src/model_deploy/act/runtime/inference_worker.py` 扫描 `SafetyGuard|ActionPublisher|create_timer|create_publisher|rclpy|torch.load|import yaml`：**无匹配**。
- 未引入对 `act_inference.py` / `control_loop.py` / `ui/act_deploy_node.py` / config / repo / policy loader / ROS graph / hardware 的修改。
- 只用 deploy_051 的 public API：`InferenceRequest`、`InferenceResult`、`LatestQueue`、`RuntimeMetrics`；只调用 L2-03 `ActInferenceService.predict_action_chunk` 这一个 public method。

### 18.9 未验证项

- 真实 `ActInferenceService`（torch policy 加载 + 真实 `prepare_observation_batch` / `postprocess_action_chunk`）下的端到端推理：本 L3 仅用 fake inference port，遵循 `fake-policy` 验收模式；真实 policy 与 ROS/robot 行为属于后续 Gate，本环境不适用。
- 多 worker 共享同一 service 的全局最大并发：本实现保证单 worker 串行；若未来由 ControlLoop 启动多个 worker 共享 service，需由上游保证 service 自身线程安全或在 worker 外加序列化（非本 L3 范围）。
- `RUNTIME_PREFETCH_SWITCH` / `WORKER_RESULT_CORRELATION` 等涉及 cursor/active-pending 的场景由 deploy_053 实现并验收。

### 18.10 deploy_053 依赖的上游 public contract

deploy_053 将消费本 L3 提供的下列稳定 public 合同（不得修改）：

- `InferenceWorker`（已导出）：`start()` / `stop()`（幂等）/ `join()` / `is_alive()`，以及构造注入的 `service / request_queue / result_queue / metrics / inference_hz / clock`。
- deploy_051 的 `InferenceRequest`（C1，含 `request_id / observation / submitted_at_s / trigger_cursor`）与 `InferenceResult`（C2，success/error XOR、`worker_fatal_reason` 经 `RuntimeMetrics.snapshot().worker_fatal_reason` 暴露，稳定值为 `"CLOCK_INVALID"` / `"QUEUE_INVARIANT"`）。
- `LatestQueue`（A1）的 `put_latest` / `take_latest` / `close` 与 capacity=1 语义。
- `RuntimeMetrics`（A2）事件名：`inference_success` / `inference_error` / `latency` / `result_queue_drop` / `worker_fatal_reason`。
- L2-03 的 `ActInferenceService.predict_action_chunk(observation: ObservationSnapshot) -> ActionChunk` 同步签名（deploy_053 不修改 L2-03）。

