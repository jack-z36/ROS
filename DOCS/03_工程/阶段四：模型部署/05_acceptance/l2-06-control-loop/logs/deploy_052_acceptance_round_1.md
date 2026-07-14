# 验收反馈：deploy_052 InferenceWorker 串行异步执行 — Round 1

- 验收模式：`direct-local`
- 验收 Agent：只读子 Agent（acceptance sub-agent）
- 结论：**PASS_LOCAL**

## 0. 结论行

**PASS_LOCAL**

## 1. 任务身份与前置核对

- 卡片：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-06-control-loop/deploy_052_验收卡片.md`（已读）
- L3 任务：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_052_InferenceWorker串行异步执行.md`（已读，§18 执行摘要存在，§15 七个成功标准全部 `[x]`）
- 前置：deploy_051 已 PASS_LOCAL（公共 API `InferenceRequest/InferenceResult/LatestQueue/RuntimeMetrics` 作为被消费依赖，worker 仅 import 公共符号）
- 验收轮次：1 / 上限 3

## 2. 必跑命令与输出

### 2.1 三文件 pytest（verbose）

```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py \
  src/model_deploy/act/tests/runtime/test_inference_worker.py -v
```

结果（节选 / 末尾汇总）：

```
... (57 个用例逐一 PASSED，含 deploy_051 的 40 个 + deploy_052 新增 17 个) ...
=============================== warnings summary ===============================
src/model_deploy/act/tests/runtime/test_inference_worker.py::TestErrorRecovery::test_keyboard_interrupt_not_swallowed
  /usr/lib/python3/dist-packages/_pytest/threadexception.py:73: PytestUnhandledThreadExceptionWarning: Exception in thread act_inference_worker
  ...
  raise KeyboardInterrupt()
  KeyboardInterrupt
======================== 57 passed, 1 warning in 1.30s =========================
```

- **57 passed**。
- **1 warning**，来源唯一：`TestErrorRecovery::test_keyboard_interrupt_not_swallowed`。该用例**故意**验证 worker 不吞 `KeyboardInterrupt`——线程以未捕获异常退出（符合 L3 规范"不吞 KeyboardInterrupt/SystemExit"）。

### 2.2 禁止模式扫描

```
grep -rn "SafetyGuard|ActionPublisher|create_timer|create_publisher|rclpy|torch.load|import yaml" \
  src/model_deploy/act/runtime/inference_worker.py
```

结果：**无任何匹配**（grep 退出码 1）。

### 2.3 全 runtime 回归

```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/runtime/ -q
```

结果：

```
71 passed, 1 warning in 1.30s
```

- 唯一 warning 同上，仍仅来自 `test_keyboard_interrupt_not_swallowed`。

## 3. 关键观察：KeyboardInterrupt warning 是否构成线程泄漏 / FAIL_LOCAL

任务要求重点排查该 `PytestUnhandledThreadExceptionWarning` 是否代表真实线程泄漏或异常杀 worker 后状态异常。

### 3.1 核查 (a)：warning 仅来自"期望线程在 KeyboardInterrupt 下死亡"的故意测试

确认：warning traceback 完整指向
`run` (inference_worker.py:148) → `_execute_request` (inference_worker.py:177) → `service.predict_action_chunk`（测试桩 `test_inference_worker.py:276` 抛 `KeyboardInterrupt`）。
即该异常由测试桩主动抛出，worker 在 `_execute_request` 的 `except (KeyboardInterrupt, SystemExit): raise` 分支**按规范重新抛出**，线程从而退出。非实现缺陷。

### 3.2 核查 (b)：测试后无残留 live 线程

- 测试本身断言 `assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)` 且 `metrics.snapshot().worker_fatal_reason is None` —— 均已 PASSED，证明线程已死亡且 worker 未将该中断记录为 fatal。
- 额外独立复核（临时脚本置于 `/tmp`，未触碰仓库任何文件）：
  - 复现 KI 场景 → `is_alive after death+join: False`
  - `threading.enumerate()` 中名为 `act_inference_worker` 的 live 线程：`[]`（空）
  - `worker_fatal_reason: None`
  - 断言"无残留 live 线程、干净 shutdown"通过。

**结论**：该 warning 仅为规范的"不吞 BaseException"行为产生的良性告警，**不是线程泄漏，也不是把 worker 留在坏状态**；不构成 FAIL_LOCAL。

## 4. 变更范围核对（card §3 无越界修改）

| 文件 | 状态 | 是否 deploy_052 范围 |
|---|---|---|
| src/model_deploy/act/runtime/inference_worker.py | 新增 | ✅ 允许 |
| src/model_deploy/act/runtime/__init__.py | 已跟踪，修改 +28（仅增量导出 `InferenceWorker`，保留全部既有导出） | ✅ 允许 |
| src/model_deploy/act/tests/runtime/test_inference_worker.py | 新增 | ✅ 允许 |
| inference_channel.py / runtime_metrics.py / test_inference_channel.py / test_runtime_metrics.py | 未跟踪（deploy_051 产物，被消费依赖，PASS_LOCAL） | ➖ 非 deploy_052 修改 |
| service/act_inference.py、runtime/control_loop.py、ui/act_deploy_node.py、config/repo/policy loader/ROS graph/硬件 | 未被修改 | ✅ 未越界 |

- `__init__.py` 仅新增 `InferenceWorker` 导出，未删除/遮蔽 `InferenceRequest/InferenceResult/LatestQueue/RuntimeMetrics/RuntimeMetricsSnapshot`。
- worker 仅调用 L2-03 单一 public 方法 `ActInferenceService.predict_action_chunk`，且仅 import deploy_051 公共符号。

## 5. 清单结果（card §3 PASS_LOCAL）

- [x] **policy 最大并发始终为 1；慢 policy 不要求 timer 等待。**
      `test_max_concurrency_is_one` 用 `SerialProbeService`（锁+计数器），单 worker 串喂 7 请求，断言 `_max_in_flight == 1` 且 `call_count == 7`；限频 wait 用 `_stop_event.wait(remaining)`（非 timer、非 wall-clock sleep、非忙轮询）。
- [x] **普通异常形成 terminal error result，worker 存活并可处理下一请求。**
      `test_exception_becomes_terminal_error_and_worker_continues`：首次 `ValueError` → error C2（`error_type="ValueError"`、`inference_error_count==1`），`is_alive()` 仍为 True，第二次请求成功（`inference_success_count==1`）。
- [x] **start-to-start 限频、clock nonfinite/negative/regression 由 fake clock 确定验证。**
      `test_first_request_immediate` / `test_respects_period` / `test_rate_limit_does_not_cause_errors` 用 `ScriptedClock`/`IncrementClock` 确定性覆盖；`_read_clock` 校验 finite/非负/非递减：`test_non_finite_clock_is_fatal`(nan→`CLOCK_INVALID`)、`test_backwards_clock_is_fatal`(completed 5.0<10.0→`CLOCK_INVALID`)。
- [x] **stop-before/while/after policy、closed result queue 和 late result 均有界收敛。**
      `test_stop_before_policy_idle_worker_never_calls_policy`（idle stop+close，service 调用 0）、`test_stop_after_policy_discards_result_and_exits`（policy 中 stop，丢弃结果优雅退出）、`test_late_result_after_shutdown_is_discarded`（shutdown 中关闭结果队列，丢结果不抛/不挂）、`test_unexpected_closed_result_queue_is_queue_invariant`（未 stop 关队列 → `QUEUE_INVARIANT` fatal + `result_queue_drop_count>=1` 退出）。所有场景均在 timeout 内有界收敛（均 `not is_alive()`）。
- [x] **worker 不拥有 request 策略、cursor、fallback、safety、permit 或 publish。**
      代码无 `SafetyGuard/ActionPublisher/create_timer/create_publisher/rclpy/torch.load/import yaml`；不构造 ROS 节点/定时器/发布器，无 cursor/active-pending/safety/fallback/permit 决策（见模块 docstring 硬边界与 §4 L2 不负责项）。
- [x] **C22 幂等；正常 shutdown 无 live thread。**
      `test_idempotent_stop`（连续两次 `stop()` 无副作用）、`test_no_live_thread_after_clean_shutdown`（`stop()+close()+join(timeout)` 后 `not is_alive()`）。

## 6. FAIL_LOCAL 扫描结果（card §3）

未命中任何 FAIL_LOCAL 项：无线程泄漏、无异常杀 worker、均产 error result、无限频 busy wait / 无 wall-clock sleep、shutdown 后不写 queue（late result 丢弃或 fatal 后终止循环）、不吞 `BaseException`、全部测试与扫描通过。

## 7. 修复请求（Fix Requests）

**无。** 本轮无需任何源码/测试/卡片修改。

## 8. 给 MAIN AGENT 的指示

deploy_052 达到 **PASS_LOCAL**。请 MAIN AGENT 将 L3 任务文件归档至：
`DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/`
（当前 active 路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_052_InferenceWorker串行异步执行.md`）。
归档后可解锁 deploy_053～055 的上游依赖。

## 9. 未验证项（如实登记，非阻断）

- 真实 `ActInferenceService`（torch policy 加载 + 端到端推理）：本 L3 仅用 fake inference port，属 `fake-policy` 验收模式；真实 policy 与 ROS/robot 行为属后续 Gate，本环境不适用。
- 多 worker 共享同一 service 的全局最大并发：本实现保证单 worker 串行；若 ControlLoop 未来启动多 worker 共享 service，需上游保证 service 线程安全或额外序列化（非本 L3 范围）。
- cursor/active-pending（`RUNTIME_PREFETCH_SWITCH` / `WORKER_RESULT_CORRELATION`）由 deploy_053 实现并验收。
