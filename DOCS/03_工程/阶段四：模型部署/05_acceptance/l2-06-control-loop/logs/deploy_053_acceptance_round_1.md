# deploy_053 验收报告 — 第 1 轮

- L2：l2-06-control-loop
- L3：deploy_053（ControlLoop 中央调度状态机）
- 验收模式：`direct-local`（辅助 `downstream-l2` / DEFER 到 deploy_055 的 ROS timer）
- 验收 Agent：只读（进程内 FakePublisher / fake clock / real SafetyGuard）
- 轮次：1 / 上限 3

## 结论

**PASS_LOCAL**

本地全部必跑命令通过，负面扫描 0 匹配，范围核查确认 053 自有改动仅限
`runtime/control_loop.py`（新增）、`runtime/__init__.py`（增量）、`tests/runtime/test_control_loop.py`（新增）。
ROS timer / 真实 topic 可见性由 deploy_055 补验（DEFER_TO_L2_GATE，不替代本卡 local PASS）。

## 命令与输出

### 1. 必跑 4 文件测试（-v）

```
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/runtime/test_inference_channel.py \
  src/model_deploy/act/tests/runtime/test_runtime_metrics.py \
  src/model_deploy/act/tests/runtime/test_inference_worker.py \
  src/model_deploy/act/tests/runtime/test_control_loop.py -v
```

结果：**88 passed, 1 warning**（既有 warning = test_inference_worker 的 KeyboardInterrupt 测试，
属既有、与 053 无关）。
其中 `test_control_loop.py` = 31 个用例全部 PASS（与执行摘要 §18.2 一致；执行代理申报 31 passed 已核实）。

### 2. 广度回归

```
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```

结果：**783 passed, 4 skipped, 0 failed, 2 warnings**（既有 warnings）。
本任务未引入任何新失败。

### 3. 负面扫描（grep -rEn，runtime/ 全目录）

```
grep -rEn "publish_safe|emit_fallback|\.filter\(|\.accepted|ControlDecision|ControlCommand|smoothstep|blend|aligned|RTC|rclpy|create_publisher" \
  src/model_deploy/act/runtime
```

结果：**0 匹配（exit 1）**，覆盖整个 `runtime/` 树（含被消费的端口文件）。
- `\.filter\(` 正确不命中 `filter_action(`（control_loop.py 第 460/807 行对
  `self._safety_port.filter_action(...)` 的合法调用未被误报）。
- control_loop.py 仅通过注入端口调用 public seam，未自行定义 publish/smoothing/ROS/status-writer 逻辑，
  也未以 `.accepted` 等别名伪造。

## 验收卡 §3 检查清单（PASS_LOCAL）

- [x] tick 非阻塞且最多一个 outstanding；matching success/error 均终结 request。
  — `TestOutstandingRequest::test_only_one_outstanding_across_ticks`、`TestCorrelation::test_matched_success_*`、
    `test_matched_error_triggers_fallback_no_latch`；`_maybe_submit_inference` 守卫 `_outstanding_request_id`。
- [x] active/pending/prefetch/horizon/continue/age/乱序 由 fake clock 完整覆盖。
  — `TestCursorHorizonAge`（normal 停在 execute_horizon、continue 越过到 chunk_size、stale 丢弃+fallback）、
    `_activate_pending` age 复验；`_collect_chunk_result` 对 unknown/stale id 锁存 RUNTIME_FAULT。
- [x] normal/continue/hold action 与 previous 深复制；重复发布不刷新 source age。
  — `select_candidate`/`_deep_copy_spec` 深复制；`_store_safe_action(refresh_source=False)` 用于 hold；
    `TestFallbackModes::test_hold_does_not_refresh_source_age` 明确验证。
- [x] 每 candidate safety=1、publish<=1；非 safety 失败不伪造 SafetyResult。
  — `TestSafetyPublishContract::test_one_safety_and_one_publish_per_candidate`；
    inference error 仅置 `INFERENCE_ERROR` fallback reason，不构造 SafetyResult。
- [x] 六 outcome + failure provenance/echo 矩阵正确；矛盾锁存 PUBLISH_RESULT_INVARIANT。
  — `TestSixOutcomeReducer`（6 种 outcome 参数化：PUBLISHED/OBSERVED/BLOCKED→NORMAL，REJECTED→FALLBACK，
    PARTIAL/FAILED→OUTPUT_FAULT；reason_code/failure_stage/failed_topic 路径）；
    `test_publish_result_invariant_on_echo_mismatch`（篡改 action_id → RUNTIME_FAULT 锁存）。
- [x] deferred reason、output/runtime fault、safe-stop 可恢复边界符合设计。
  — `test_deferred_reason_delivered_once_then_recoverable`（一次性交付，OBSERVED 后清除）；
    `_latch_output_fault`（PARTIAL/FAILED）、`_latch_runtime_fault`（invariant）分离锁存；
    safe-stop 本 tick 无输出、可恢复、不声称物理 stop（`_run_fallback` 末尾分支）。
- [x] 无 UI/ROS/status-writer/smoothing/假接口污染。
  — 负面扫描 0 匹配；control_loop.py 仅依赖注入的 `safety_port`/`publish_port`/`observation_port`。
- [x] 无超出 L3 允许范围的改动。

## 范围核查（053 自有改动）

git 工作树含多个兄弟任务（056-060）未提交改动。针对 053 自身：

| 文件 | 状态 | 归属 |
|---|---|---|
| `src/model_deploy/act/runtime/control_loop.py` | `??` 新增 | **053** ✅ |
| `src/model_deploy/act/runtime/__init__.py` | `M` 增量（仅新增 re-export，未改既有模块） | **053** ✅ |
| `src/model_deploy/act/tests/runtime/test_control_loop.py` | `??` 新增 | **053** ✅ |
| `inference_channel.py` / `inference_worker.py` / `runtime_metrics.py` | `??` 新增（上游 051/052/056-060 交付物，被 053 消费） | 非 053 修改 ✅ |
| `observation_buffer.py` | `M`（deploy_057 范围，含已知 latent bug） | 非 053 ✅ |
| `service/` `types/` `ui/` 等 | 兄弟任务改动，非 053 | 非 053 ✅ |

确认：053 未修改 inference_channel.py / runtime_metrics.py / inference_worker.py / observation_buffer.py，
也未触碰 service / types / ui 源码。

## 已消费 public 端口契约核对

- `SafetyGuard.filter_action(candidate, previous_safe_action=, latest_observation=) -> SafetyResult` ✅
  （signature 与调用一致，位于 `service/safety_guard.py`）。
- `ActionPublishRequest`（action_id, safety_result, command_permit, ros_time_s, monotonic_s）
  与 `ActionPublishResult`（action_id, safety_status, command_output_enabled, command_permitted,
  outcome, reason_code, failure_stage, failed_topic）字段与 control_loop.py 用法一致 ✅。
- `CommandPermit.allowed` 被读取 ✅；`PublishOutcome` 六枚举齐备 ✅。
- `InferenceRequest` / `InferenceResult` / `LatestQueue`（inference_channel.py）、
  `RuntimeMetrics`（runtime_metrics.py）、worker 单串行轴（inference_worker.py）均按已验收 public seam 使用 ✅。

## 观察项（非 053 失败）

- 执行代理标出的 latent bug `ObservationBuffer._default_monotonic_clock` 返回 `time.monotonic`（缺 `()`）
  位于 `observation_buffer.py`，属 deploy_057（已 accepted）范围。
  已确认 `control_loop.py` **不依赖**该默认：其通过注入 `observation_port: Callable[[], Optional[ObservationSnapshot]]`
  获取观测，从未引用 `ObservationBuffer` 或 `_default_monotonic_clock`。故不计入 053 失败，仅作记录。

## 修复请求（Fix Requests）

无。本轮无需重跑。

## 解锁条件 / 后续

- deploy_053 已 PASS_LOCAL，按卡 §4 可解锁 deploy_054（ROS timer / 生命周期驱动）与 deploy_055（真实跨 L2 tracer）。
- **MAIN AGENT 必须将 L3 任务文件归档至**
  `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/`
  （当前在 `.../03_tasks/task/active/l2-06-control-loop/deploy_053_ControlLoop中央调度状态机.md`）。
- ROS timer / 真实 policy forward / 真实 ActionPublisher / 硬件 driver 未在本地执行（dry-run-only，符合 robot_risk），
  由 deploy_055 在 L2 gate 补验；本卡不宣称真机/ROS 通过。
