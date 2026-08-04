# runtime 层设计：L2-06

## 1. 目标源码与层职责

```text
src/model_deploy/act/runtime/inference_channel.py
src/model_deploy/act/runtime/runtime_metrics.py
src/model_deploy/act/runtime/inference_worker.py
src/model_deploy/act/runtime/control_loop.py
src/model_deploy/act/runtime/__init__.py
```

runtime 层负责时间相关状态、线程、queue、active/pending chunk、cursor、fallback 和 publish outcome reducer。它可依赖 types/config/service 和注入的 callable port，但不得 import UI、解析 ROS message 或访问文件。

覆盖微元：A1-A4、B1-B8、C1-C19、C22-C26。

`runtime/__init__.py` 是 UI 唯一导入 L2-06 runtime object 的 facade，增量导出 `InferenceRequest`、`InferenceResult`、`LatestQueue`、`RuntimeMetrics`、`RuntimeMetricsSnapshot`、`InferenceWorker`、`ControlLoop`；不删除/遮蔽 L2-02 已有 `runtime.observation_buffer` 模块导入路径，不导出 C5-C7 mutable state 或私有 helper。runtime 内部依赖上游时只使用 `model_deploy.act.types`、`model_deploy.act.config`、`model_deploy.act.service`/明确 public module，不访问下划线字段。

## 2. `inference_channel.py`

### 2.1 C1 `InferenceRequest` 数据

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `request_id` | 单调递增正整数 | `int` |
| `observation` | frozen object reference | `ObservationSnapshot` |
| `submitted_at_s` | monotonic seconds、finite、非负 | `float` |
| `trigger_cursor` | 提交时 active cursor、非负 | `int` |

### 2.2 C2 `InferenceResult` 数据

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `request_id` | 与 C1 相同 | `int` |
| `observation_captured_at_s` | monotonic capture seconds | `float` |
| `submitted_at_s` | monotonic submit seconds | `float` |
| `started_at_s` | monotonic inference start | `float` |
| `completed_at_s` | monotonic completion | `float` |
| `chunk` | success object 或 None | `ActionChunk | None` |
| `error_type` | stable exception class name 或 None | `str | None` |
| `error_message` | bounded diagnostic text 或 None | `str | None` |

success/error 必须 XOR；四类时间必须单调有序。failure 的 `error_type=type(exc).__name__`，`error_message=(str(exc) or error_type)[:512]`。C2 不保存 exception、traceback、policy 或 ROS 对象。

### 2.3 A1 `LatestQueue[T]`

构造合同冻结为无参 `LatestQueue()`，public `ClassVar[int] CAPACITY = 1`；第一版不接收可变 maxsize，也不根据 config 创建更大 queue。B12 只读该 public class constant 并要求两个 config 字段均为 1，不反射 `_items.maxlen`。

| C5 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `_items` | `deque(maxlen=1)` | generic `T` references |
| `_condition` | lock + waiter condition | `threading.Condition` |
| `_closed` | closed flag | `bool` |
| `_dropped_count` | 淘汰累计 | `int` |

- C8 `put_latest(item) -> int`：在 Condition 下淘汰旧项、追加最新项、唤醒 waiter，返回本次淘汰数；closed 后抛 `RuntimeError("queue is closed")`。
- C9 `take_latest(timeout_s=0) -> item|None`：worker 用 `None` 阻塞等待，ControlLoop 用 0 非阻塞；未关闭时取出唯一项，关闭后不再交付关闭前残留项并返回 `None`。drop 数由 C8/C10 的返回值单独记录。
- C9 timeout 合同：`None` 等到 item/close，`0` 立即返回，正数按 monotonic deadline 有界等待，负数抛 `ValueError`；Condition 需用 while 处理 spurious wakeup。
- C10 `close() -> int`：在同一 Condition 临界区置 `_closed=True`、清空全部待处理项、把清除数计入 dropped、`notify_all()` 并返回清除数。close 必须幂等：重复调用返回 0、不重复计数，closed 后 C8 始终抛同一类型/消息的 `RuntimeError`。request/result queue 使用完全相同的语义；shutdown 不允许 busy polling。
- side effects 仅限进程内线程同步，不访问进程外资源。

## 3. `runtime_metrics.py`

### 3.1 A2/C6 mutable metrics state

构造签名语义为 `RuntimeMetrics(clock: Callable[[], float])`，注入 A5 的同一 monotonic callable；C11 用它更新 `updated_at_s`。至少冻结下列字段；实现可用 dataclass + Lock，但不能把 mutable 实例交给 UI：

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `runtime_status` | `STARTING/WAITING_OBSERVATION/WAITING_INFERENCE/EXECUTING/FALLBACK/OUTPUT_FAULT/RUNTIME_FAULT/STOPPING/STOPPED/SHUTDOWN_TIMEOUT` | `str` |
| `tick_count` | 累计计数 | `int` |
| `request_submitted_count` | 累计计数 | `int` |
| `inference_success_count` / `inference_error_count` | 累计计数 | `int` |
| `result_discarded_count` / `chunk_activated_count` | 累计计数 | `int` |
| `request_queue_drop_count` / `result_queue_drop_count` | C8 非 shutdown 淘汰累计 | `int` |
| `shutdown_queue_cleared_count` | C10 shutdown 清除累计 | `int` |
| `action_candidate_count` / `safety_rejected_count` / `fallback_count` | 累计计数 | `int` |
| `publish_outcome_counts` | 六种 `PublishOutcome -> count` | `dict[str,int]` |
| `active_request_id` / `pending_request_id` / `in_flight_request_id` | optional gauges | `int | None` |
| `active_cursor` / `active_chunk_size` | non-negative gauges | `int` |
| `output_fault_latched` | fail-closed latch | `bool` |
| `runtime_fault_latched` | invariant/port/queue fail-closed latch | `bool` |
| `worker_fatal_reason` | worker 线程报告的稳定致命 code 或 None | `str | None` |
| `last_fallback_reason` | C3 enum value 或 None | `str | None` |
| `deferred_fallback_reason` | 尚未由 B8 消费的一次性 C3 reason gauge | `str | None` |
| `last_action_id` | 最近一次候选的稳定 id | `str | None` |
| `last_candidate_source` / `last_candidate_source_captured_at_s` | normal/hold/continue provenance | `str | None` / `float | None` |
| `last_safety_finding_codes` | 最近一次真实 SafetyResult findings | `tuple[str,...]` |
| `last_publish_outcome` / `last_publish_reason_code` | 最近一次 L2-05 可见事实 | `str | None` |
| `last_publish_failure_stage` / `last_publish_failed_topic` | L2-05 P0-10 修复后提供的 provenance | `str | None` |
| `last_error` | 最多 512 chars 的 diagnostic 或 None | `str | None` |
| `last_inference_latency_s` | non-negative seconds | `float` |
| `updated_at_s` | monotonic seconds | `float` |

`runtime_status` 单 writer 规则：A5/B10 只写 `STARTING/STOPPING/STOPPED/SHUTDOWN_TIMEOUT`，A4/B3 写 `WAITING_OBSERVATION/WAITING_INFERENCE/EXECUTING/FALLBACK/OUTPUT_FAULT/RUNTIME_FAULT`。优先级为 `SHUTDOWN_TIMEOUT > STOPPED > STOPPING > RUNTIME_FAULT > OUTPUT_FAULT > 本 tick 状态`；进入 stopping 后 B3 不得把状态改回 executing/fallback。

### 3.2 C4 snapshot

C4 `RuntimeMetricsSnapshot` 是以上字段的 frozen copy；dict 字段转 immutable mapping 或 tuple pairs。C11 `record_event` 在 lock 下累计/替换；C12 `snapshot` 在 lock 下复制后返回，不读写外部资源。

## 4. `inference_worker.py`

### 4.1 A3 class state

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `_service` | 已构造 L2-03 service reference | `ActInferenceService` |
| `_request_queue` / `_result_queue` | A1 references | `LatestQueue[InferenceRequest/Result]` |
| `_metrics` | A2 reference | `RuntimeMetrics` |
| `_period_s` | `1 / inference_hz` | `float` |
| `_clock` | monotonic callable | `Callable[[],float]` |
| `_stop_event` | stop flag/event | `threading.Event` |
| `_last_inference_start_s` | last start gauge | `float` |
| thread contract | A3 继承 `threading.Thread`，构造时固定 `daemon=True` | lifecycle policy |

### 4.2 B1 `run`

- 调用条件：A5 已完成全部 preflight 后 `worker.start()`。
- 步骤：C9 阻塞取 request → 醒来后检查 stop → stop-aware 等待 inference period → 调 B2 前再次检查 stop → B2 → 再检查 stop → C8 写 result → C11 记录。
- 限频按 start-to-start：先读 `now=clock()`；任一 start/complete clock read 非 finite、为负数或相对上一个 worker timestamp 倒退，都记录 `worker_fatal_reason=CLOCK_INVALID` 并退出；否则 `remaining = max(0, last_start + period - now)`，用 `_stop_event.wait(remaining)`。首次 request 立即开始，policy 本身超过 period 时不额外 sleep。
- skip：stop/closed 时不取新 request；policy 正在运行不能强杀，完成后若 stop 已置位则不写 result 并退出。result queue 因 shutdown 已 closed 的晚到结果同样丢弃。
- 失败：非 shutdown 期间 C8 返回非零淘汰数，或 result queue 意外 closed/put failure，必须通过 A2 记录 `result_queue_drop_count`/`worker_fatal_reason=QUEUE_INVARIANT` 后退出；A3 不跨线程写 `runtime_status`，由下一次 B9/B3 调 C25 锁存。普通 policy 异常由 B2 转 C2，不杀 worker。

C22 `InferenceWorker.stop() -> None` 只做幂等 `_stop_event.set()`；A3 的 `start()/join(timeout)/is_alive()` 采用 `threading.Thread` 标准合同。`daemon=True` 只保证 join timeout 后进程可有界退出，不把 timeout 变成 PASS。

### 4.3 B2 `_execute_request`

```text
InferenceRequest
  -> started_at_s
  -> ActInferenceService.predict_action_chunk(observation)
  -> completed_at_s
  -> success C2(chunk) OR error C2(error_type/error_message)
```

同一 service 最大并发调用数必须始终为 1；不在 worker 决定 cursor、safety、fallback、permit 或 publish。`KeyboardInterrupt/SystemExit` 不吞。

## 5. `control_loop.py`

### 5.1 C3 `FallbackReason`

稳定 Enum 至少包含：

```text
NO_FRESH_OBSERVATION
WAITING_FOR_FIRST_CHUNK
INFERENCE_ERROR
RESULT_STALE
RESULT_OUT_OF_ORDER
RESULT_INVARIANT
QUEUE_INVARIANT
WORKER_TERMINATED
CLOCK_INVALID
OBSERVATION_PROVIDER_ERROR
SAFETY_PORT_ERROR
PUBLISH_RESULT_INVARIANT
CHUNK_INVALID
CHUNK_EXPIRED
CHUNK_HORIZON_EXHAUSTED
CHUNK_EXHAUSTED
SAFETY_REJECTED
COMMAND_BLOCKED
PUBLISH_PARTIAL
PUBLISH_FAILED
OUTPUT_FAULT_LATCHED
RUNTIME_FAULT_LATCHED
RUNTIME_STOPPING
```

### 5.2 C26 `CandidateSelection`

```python
@dataclass(frozen=True)
class CandidateSelection:
    action: np.ndarray                 # owned float32 copy, exact (16,)
    source_captured_at_s: float        # original model observation capture
    source: Literal["normal", "hold_last_action", "continue_old_chunk"]
```

C26 只活在一个 tick 内。构造时验证 action shape/dtype/finite、source time finite/nonnegative；normal/continue 从 active C2 的 `observation_captured_at_s` 取值，hold 继承 `_previous_source_captured_at_s`。不得把 publish time 写回 source time。

### 5.3 A4/C7 ControlLoop state

| 变量名 | 内部存储结构 | 内部存储的数据类型 |
|---|---|---|
| `_config` | immutable config reference | `RuntimeConfig` |
| `_max_observation_age_s` | positive seconds | `float` |
| `_command_output_enabled` | 从 L2-01 startup config 注入、仅供 result 交叉校验 | `bool` |
| `_observation_provider` | bound callable | `Callable[[float|None], ObservationSnapshot|None]` |
| `_request_queue` / `_result_queue` | A1 references | typed LatestQueue |
| `_metrics` | A2 reference | RuntimeMetrics |
| `_safety_guard` | L2-04 service reference | SafetyGuard |
| `_publish_action` | bound L2-05 callable | `Callable[[ActionPublishRequest],ActionPublishResult]` |
| `_active_result` / `_pending_result` | validated C2 slots | `InferenceResult | None` |
| `_active_cursor` | next row index | `int` |
| `_in_flight_request_id` | one current request 或 None | `int | None` |
| `_discard_in_flight` | 当前 outstanding terminal result 是否必须丢弃 | `bool` |
| `_next_request_id` / `_last_completed_request_id` | monotonic ids | `int` |
| `_last_tick_monotonic_s` | 上一次已接受 tick 时间或 None | `float | None` |
| `_previous_safe_action` | confirmed/virtual safe reference | `ActionSpec | None` |
| `_previous_source_captured_at_s` | previous 动作最初模型 observation capture time | `float | None` |
| `_deferred_fallback_reason` | C19 留给下一个可决策 tick 的一次性 reason | `FallbackReason | None` |
| `_output_fault_latched` / `_runtime_fault_latched` / `_stopping` | fail-closed flags | `bool` |
| `_tick_sequence` | action id/metrics sequence | `int` |

### 5.4 B3 `tick`

```python
tick(*, monotonic_s: float, ros_time_s: float,
     command_permit: CommandPermit) -> ActionPublishResult | None
```

- 调用条件：A5 control timer；三项输入已由 UI 验证 finite/typed。
- 首个状态步骤要求 `monotonic_s >= _last_tick_monotonic_s`；时钟倒退立即 C25 `CLOCK_INVALID`，不读 observation、不提交、不发布。合法时才更新 `_last_tick_monotonic_s`；ROS time 只要 finite/nonnegative，不用于 age/限频。
- 步骤：B4 → C15/age → observation read → C14/B5 → B6 → 必要时 B8 → 有 candidate 才 B7/C19。
- observation provider 返回后必须二次校验：只接受 `None | ObservationSnapshot`，capture 必须 finite/nonnegative。`age > max_observation_age_s` 说明 provider 违反 freshness port，调 C25 `OBSERVATION_PROVIDER_ERROR`；`capture - monotonic_s > 1/control_hz` 调 C25 `CLOCK_INVALID`；`0 < capture - monotonic_s <= 1/control_hz` 视为并发 callback 刚完成，本 tick 当作 `NO_FRESH_OBSERVATION` 延后消费，保证 C1 始终 `capture <= submitted_at_s`。其他合法 snapshot 才可交 C14/B5 与 B7。
- tick 起点若 metrics 显示 `worker_fatal_reason`，先要求它可精确映射到 C3 已定义的 `CLOCK_INVALID/QUEUE_INVARIANT`，再以原 reason 调 C25；未知 code 按 `WORKER_TERMINATED` 锁存并保留原文。任一非 shutdown request/result queue drop 则调 C25 `QUEUE_INVARIANT`；容量 1 + 单 outstanding 下正常运行不允许淘汰。
- skip：stopping/output fault/runtime fault 时不提交 request、不选 action、不调用 publisher。
- 失败：普通 runtime port 异常转 metrics/fault；不能让 ROS timer 静默吞掉且继续 command。

### 5.5 B4 `_collect_latest_result`

- 非阻塞 C9 后，无结果返回 `None`，不得在 tick 等 worker。
- 旧 id 只计 discarded；未知更大 id 锁存 `_runtime_fault_latched`。只有等于 `_in_flight_request_id` 的 terminal result 可清 in-flight，并且成功/失败都把 `_last_completed_request_id` 推进到该 id。
- 匹配 id 后先由 C13 验证 success/error XOR、时间和 success payload；malformed XOR/时间 envelope 仍终结 request，但调用 C25 `RESULT_INVARIANT` 锁存 runtime fault，不得按 success/error 分支猜测。stale/invalid chunk 作为可诊断 terminal reason，不进入 pending。
- `_discard_in_flight=True` 时，匹配结果仅用于终结 outstanding：成功 chunk 丢弃、error 仍计 inference error，随后清 id并复位 flag，统一返回 None，不重新触发已处理原因的 fallback。
- discard flag 为 False 的 matching failure 不产生 pending，返回 tick-local `INFERENCE_ERROR`。matching success 通过 C13 后只写 `_pending_result`；C13 拒绝时返回对应 stale/invalid reason且不产生 pending。B4 不调用 C15。
- B3 仅在 B6 没有合法 normal candidate 时使用 B4 返回的 error/invalid reason进入 B8；prefetch error 不得截断仍合法的 active chunk。

### 5.6 C13 `validate_inference_result`

- 输入：C2、expected/current ids、`now`、RuntimeConfig。
- 输出：`(ok: bool, reason: FallbackReason | None)`；无进程外读写。
- 检查：id、success/error XOR、时间顺序、capture-age、精确 `(chunk_size,action_dim)`、float32、finite。

### 5.7 C14 / B5 submit

- C14 输入：active/pending/in-flight/cursor/fault/stopping、fresh observation、horizon/prefetch。
- 输出：bool + trigger reason；无进程外读写。
- true 条件：无 fault/stopping、`_in_flight_request_id is None`、无 pending、observation fresh，且无 active 或进入 prefetch window。`_discard_in_flight=True` 时 id 必然仍非 None，因此不得提交第二个 outstanding request。
- B5 只在 C14 为 true 时创建单调 C1、写 request queue，且仅在 C8 成功返回 0 后设置 in-flight/累计 submitted。C8 返回非零淘汰时先累计 `request_queue_drop_count`；queue closed/put failure 保留 bounded error；两者都调用 C25 `QUEUE_INVARIANT`，不设置新 in-flight，也不同步调用 L2-03。

### 5.8 C15-C17、C23-C25 状态更新

- C15 `_activate_pending`：B3 的直接子步骤；active 缺失或到 normal horizon 时，先以当前 `monotonic_s` 重算 pending capture-age，仍合法才替换 active、pending=None、cursor=0并累计 switch；过期则丢弃并返回 `CHUNK_EXPIRED`。即使本 tick B4 没收到结果，也必须检查既有 pending。
- C16 `_invalidate_chunks`：按 reason 清 active/pending，必要时清 previous；若存在 in-flight，只置 `_discard_in_flight=True`，绝不清 `_in_flight_request_id`。
- C17 `_take_cursor_action`：在 normal/continue limit 内返回独立 `(16,) float32` copy 后 cursor+=1；不返回 view。
- C23 `begin_stopping() -> None`：幂等置 `_stopping=True` 并更新 metrics；B10 不直接修改 A4 私有字段。
- C24 `_next_action_id() -> str`：在 tick 串行区将 `_tick_sequence += 1`，返回 `act-{sequence:012d}`。只在即将调用 B7 的 candidate 上生成；status-only tick 不消耗 id。
- C25 `latch_runtime_fault(reason, detail) -> None`：只允许 A4 内部或持有 A5 lifecycle lock 的 B9 调用；幂等清 active/pending/previous+source time/deferred fallback state+gauge，若有 outstanding 置 discard flag，写 `_runtime_fault_latched=True/RUNTIME_FAULT` 与最多 512 chars detail。无本进程 reset API，只能重启。

### 5.9 B6 normal candidate

- 输入仅为 active/cursor/execute horizon 和当前 tick reason，不读取 `fallback_policy`。
- active 新鲜且 `cursor < execute_horizon` 时调用 C17（limit=horizon），用 active result capture time 包装 C26 后返回。
- 选到新鲜 normal candidate 时同步清空已过时的 `_deferred_fallback_reason` 与 A2 `deferred_fallback_reason` gauge。其他情况返回 `(None, FallbackReason)`；reason 优先级为 `NO_FRESH_OBSERVATION` > 本 tick result/age failure > 一次性 deferred reason > waiting/horizon/exhausted。deferred reason 只在实际交给 B8 时从 state/gauge 同步消费；无 fresh observation 时保留，但一旦 normal 恢复就不得再回放旧错误。
- B6 不允许 hold previous，也不允许越 horizon 读取 active。

### 5.10 B7/C18/C19 publish 链

C18 纯构造：

```python
build_action_publish_request(
    action_id: str,
    safety_result: SafetyResult,
    command_permit: CommandPermit,
    ros_time_s: float,
    monotonic_s: float,
) -> ActionPublishRequest
```

B7 顺序严格为 `C26.action -> C24 action id -> filter_action -> C18 -> publish_action -> C19`。Safety 意外异常调用 C25；Safety REJECTED 可 publish 一次 rejected status。publish port 意外抛异常时以 `result=None, publish_error=exc` 调 C19，锁存 `PUBLISH_FAILED` output fault，不伪造 `ActionPublishResult`。

C19 签名语义冻结为：

```python
_apply_publish_outcome(
    *,
    request: ActionPublishRequest,
    result: ActionPublishResult | None,
    publish_error: Exception | None,
    safety_result: SafetyResult,
    selection: CandidateSelection,
    monotonic_s: float,
) -> None
```

`result` 与 `publish_error` 必须恰有一个非 None。有 result 时先验证 `result.action_id == request.action_id`、`result.safety_status == safety_result.status`、`result.command_output_enabled == self._command_output_enabled`、`result.command_permitted == request.command_permit.allowed`，再按 L2-05 的真实顺序核验 outcome/provenance：

| 条件 / 失败位置 | 唯一允许的 outcome 与 provenance |
|---|---|
| safety 为 `REJECTED` | `REJECTED`；非空 reason、stage=`safety`、topic=None |
| safety 为 PASS/ADJUSTED，payload/message 构造失败 | `FAILED`；非空 reason、stage=`command_build`、topic=None；该步骤先于 gate，所以不受 switch/permit 限制 |
| safety 为 PASS/ADJUSTED，policy-action publish 失败 | `FAILED`；非空 reason、stage=`policy_publish`、failed topic 非空；该 publish 先于 gate，所以不受 switch/permit 限制 |
| 前置步骤成功，startup switch=false | `OBSERVED`；stage/topic=None |
| 前置步骤成功，switch=true 且 permit deny | `BLOCKED`；stage/topic=None，reason 保留 permit reason |
| 前置步骤成功，switch=true 且 permit allow，command 全部成功 | `PUBLISHED`；stage/topic=None |
| 同上，command publish 已有部分成功后失败 | `PARTIAL`；非空 reason、stage=`command_publish`、failed topic 非空 |
| 同上，首个 command publish 即失败 | `FAILED`；非空 reason、stage=`command_publish`、failed topic 非空 |

任一公共结果自相矛盾调 C25 `PUBLISH_RESULT_INVARIANT` 锁存 runtime port fault，不猜测修补。通过后状态表严格采用 `01_L2功能边界.md §7`；有 exception 时清 chunk/previous/deferred state+gauge、锁存 output fault并保存 bounded error。cursor 在发布前已暂时递增；非成功 terminal 通过清 chunk而不是回滚可变 array。`REJECTED` 同步写一次性 `_deferred_fallback_reason=SAFETY_REJECTED` 与 gauge，`BLOCKED` 写 `COMMAND_BLOCKED`；`PARTIAL/FAILED` 清 deferred state+gauge 并锁存 output fault；`PUBLISHED/OBSERVED` 清 deferred state+gauge 并更新 previous，更新时必须用 `split_action(safety_result.action.as_vector())` 深复制，并写 `_previous_source_captured_at_s=selection.source_captured_at_s`；重复 hold/publish 不得刷新原始 age。清 previous 时 source time 同步置 None。`PUBLISHED` 仍不代表 driver accepted。

### 5.11 B8 fallback

- 签名语义：`_apply_fallback(reason, *, observation, monotonic_s) -> CandidateSelection | None`；observation 已由 B3 freshness 检查。
- B8 是唯一读取 `fallback_policy` 的微元；它只返回 C26 或 None，不直接调用 B7/L2-05。
- `NO_FRESH_OBSERVATION`：任何 policy 均返回 None，只记录可恢复的 status/metrics。
- `hold_last_action`：previous 与 source time 均存在、observation fresh，且 `0 <= monotonic_s - previous_source_captured_at_s <= max_action_age_sec` 时，才用 `previous.as_vector()` 的独立 float32 copy + 原 source time 构造 C26；重复 hold 不续期。
- `continue_old_chunk`：active 未过期、有剩余 row、observation fresh才调用 C17（limit=chunk_size），以 active capture time 构造 C26；pending 到达后优先 C15 切换。
- `safe_stop`：本 tick 返回 None、记录 fail-closed reason；不锁存、不禁止下一 tick 用 fresh observation 恢复。主动硬件 stop 需要另行 driver port，不能把逐 tick no-output 写成物理 stop 已成功。
- `PARTIAL/FAILED` fault latch 优先于所有 fallback。

## 6. 依赖、副作用与验收

依赖方向：`inference_channel -> L2-02/03 types`；`worker -> L2-03 service`；`control_loop -> L2-04 service + L2-05 public types + bound callable`；runtime 不 import UI/repo。

副作用：A1/A2/A4 仅 RAM/lock；A3 调 policy；A4 通过注入 port 触发 L2-05 I/O。所有副作用必须可由 Gate 替换外部边界而保留真实业务对象。

Pi0.5 参考：`shared_buffer.py:61-153`、`inference_worker.py:15-91`、`control_loop.py:37-333`。删除 blend/aligned/ControlCommand，修复 error-result 与当前 public API。

验收至少覆盖：`WORKER_TICK_NONBLOCKING`、`WORKER_SERIAL_POLICY`、`WORKER_RESULT_CORRELATION`、`WORKER_ERROR_RECOVERY`、`INFLIGHT_INVALIDATION_SERIAL`、`CHUNK_AGE_FROM_ENVELOPE`、`CANDIDATE_PROVENANCE_AGE`、`RUNTIME_PREFETCH_SWITCH`、`ACTION_COPY_ISOLATION`、`CONTROL_OUTCOME_REDUCER`、`RUNTIME_REASON_PRESERVED`、`FALLBACK_MATRIX`、`PARTIAL_FAILED_LATCH`、`RUNTIME_INVARIANT_LATCH`、`WORKER_SHUTDOWN`、`RUNTIME_NO_UI_IMPORT`、`PUBLIC_CONTRACT_IMPORTS`。

本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。
