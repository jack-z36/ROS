# ACT 微元设计与协作：L2-06

## 1. 目标源码树

```text
src/model_deploy/act/runtime/
├── __init__.py               # A1-A4/C1-C4 的稳定 UI facade
├── inference_channel.py      # InferenceRequest/Result + LatestQueue
├── runtime_metrics.py        # RuntimeMetrics + frozen snapshot
├── inference_worker.py       # 串行调用 L2-03
└── control_loop.py           # active/pending/cursor/fallback/publish reducer

src/model_deploy/act/ui/
├── __init__.py               # ActDeployNode public facade
└── act_deploy_node.py        # composition、timer、permit、metrics、shutdown
```

`types/config/repo/service` 不新增 L2-06 源码；分别复用公共类型、L2-01 配置、上游资源加载和 L2-03～05 service。L2-06 的 request/result/metrics 只描述自身线程与调度生命周期，因此留在 `runtime/`，不冒充跨 L2 业务语言。

## 2. class 与编排微元

| ID / ACT 微元 | 3.5 类型 | target layer | target file | function/class | inputs | outputs | side effects | Pi0.5 reference |
|---|---|---|---|---|---|---|---|---|
| A1 `LatestQueue[T]` | class 打包 | runtime | `runtime/inference_channel.py` | class | 无参构造，`CAPACITY=1` | thread-safe channel | 修改 deque/Condition/closed | `shared_buffer.py:71-102` |
| A2 `RuntimeMetrics` | class 打包 | runtime | `runtime/runtime_metrics.py` | class | event fields | frozen snapshot | 原子累计指标 | `shared_buffer.py:106-153` |
| A3 `InferenceWorker` | class 打包 | runtime | `runtime/inference_worker.py` | class | service、queues、metrics、clock | result envelope | thread/start/stop/join | `inference_worker.py:15-91` |
| A4 `ControlLoop` | class 打包 | runtime | `runtime/control_loop.py` | class | runtime config、startup command switch、ports、queues、metrics | publish result 或 None | 修改调度状态、调用外部 port | `control_loop.py:59-333` |
| A5 `ActDeployNode` | class 打包 | ui | `ui/act_deploy_node.py` | class | typed resources、permit source、monotonic clock | ROS node | timer/metrics/lifecycle | `pi05_vla_deploy_node.py:42-218` |
| B1 worker run | 编排函数 | runtime | `runtime/inference_worker.py` | `InferenceWorker.run` | request queue、stop event | 连续 result | 阻塞 wait、限频、写 result queue | `InferenceWorker.run` |
| B2 execute request | 编排函数 | runtime | 同上 | `_execute_request` | InferenceRequest | success/error InferenceResult | 仅同步调用 L2-03；不写 queue | `_run_request` |
| B3 central tick | 编排函数 | runtime | `runtime/control_loop.py` | `ControlLoop.tick` | monotonic/ROS time、CommandPermit | ActionPublishResult 或 None | 一拍状态迁移 | `ControlLoop.tick` |
| B4 collect result | 编排函数 | runtime | 同上 | `_collect_latest_result` | result queue、in-flight id、discard flag | pending 或 tick-local reason | 终结匹配 in-flight、记录 metrics | `_collect_result` |
| B5 submit inference | 编排函数 | runtime | 同上 | `_maybe_submit_inference` | fresh observation、state | InferenceRequest 或 skip | request queue 写入 | `_maybe_submit_request` |
| B6 choose normal candidate | 编排函数 | runtime | 同上 | `_choose_candidate` | active、cursor、execute horizon | `(C26 selection | None, reason)` | 仅正常路径推进 cursor | `_next_raw_action` |
| B7 safety and publish | 编排函数 | runtime | 同上 | `_safety_and_publish` | C26 selection、observation、permit、clocks | ActionPublishResult | 调 L2-04/L2-05 | `tick/_fallback`，接口重写 |
| B8 apply fallback | 编排函数 | runtime | 同上 | `_apply_fallback` | FallbackReason、fresh observation、monotonic_s、state/policy | C26 selection 或 None | 唯一解释 fallback policy、记录 metrics | `_fallback`，语义重写 |
| B9 UI control tick | 编排函数 | ui | `ui/act_deploy_node.py` | `_control_tick` | ROS timer、permit source、clocks | 调用 B3 | 读取 permit/clock | node `_control_tick` |
| B10 shutdown | 编排函数 | ui | 同上 | `_shutdown_runtime` | timer/loop/queues/worker | `bool`（join success） | 串行 stopping/cancel/stop/close/join | node `shutdown` |
| B11 process main | 编排函数 | ui | 同上 | `main` | CLI argv、L2-01 repo public functions、ROS | exit code `0/1` | load/init/spin/finally shutdown | node `main`，按 ACT 边界重写 |
| B12 startup preflight | 编排函数 | ui | 同上 | `run_startup_preflight` | DeployConfig、ActRuntimeResources、PolicyInputSpec、pipeline contracts、permit topology | `None` 或 `StartupContractError(code)` | 无外部 I/O；失败阻止 ROS runtime 启动 | 新增 ACT 接缝 Gate |

## 3. 原子微元

| ID / ACT 微元 | 3.5 类型 | target file / owner | inputs | outputs / 修改 | 外部副作用 |
|---|---|---|---|---|---|
| C1 `InferenceRequest` | 数据 | `inference_channel.py` | request id、ObservationSnapshot、submit time、trigger cursor | frozen request | 无 |
| C2 `InferenceResult` | 数据 | `inference_channel.py` | id、capture/submit/start/complete、chunk XOR error | frozen result | 无 |
| C3 `FallbackReason` | 数据 | `control_loop.py` | 失败分类 | stable Enum | 无 |
| C4 `RuntimeMetricsSnapshot` | 数据 | `runtime_metrics.py` | counters/gauges/last + deferred reason | frozen snapshot | 无 |
| C5 queue state | 数据 | A1 | deque、Condition、closed、maxsize | RAM channel state | 无 |
| C6 metrics state | 数据 | A2 | counters、latency、last/deferred fallback、last error/outcome | mutable guarded state | 无 |
| C7 ControlLoop state | 数据 | A4 | active/pending/cursor/in-flight/discard-in-flight/last tick time/previous+source time/deferred fallback/output/runtime fault/stopping/tick id | cross-tick state | 无 |
| C8 `put_latest` | 内部状态更新函数 | A1 | item | replace/append，返回淘汰数 | 唤醒 waiter |
| C9 `take_latest` | 内部状态更新函数 | A1 | timeout | `T | None`，取出唯一项 | 可阻塞 Condition |
| C10 `close` | 内部状态更新函数 | A1 | — | closed=True、清空并计入 dropped、返回清除数 | 唤醒 waiter |
| C11 `record_event` | 内部状态更新函数 | A2 | event + values | 原子累计/替换 | 无 |
| C12 `snapshot` | 计算函数 | A2 | guarded metrics state | RuntimeMetricsSnapshot | 无进程外读写 |
| C13 `validate_inference_result` | 计算函数 | `control_loop.py` | result、expected id、now、RuntimeConfig | ok/reason | 无进程外读写 |
| C14 `should_submit_inference` | 计算函数 | 同上 | active/pending/in-flight/cursor/config/fresh obs | bool + trigger reason | 无进程外读写 |
| C15 `_activate_pending` | 内部状态更新函数 | A4 | pending、monotonic_s | active/cursor 更新或 CHUNK_EXPIRED reason | 无 |
| C16 `_invalidate_chunks` | 内部状态更新函数 | A4 | reason、clear_previous flag | 清 active/pending；有 outstanding 时只置 discard flag | 无 |
| C17 `_take_cursor_action` | 内部状态更新函数 | A4 | active、limit | 独立 `float32 (16,)` copy，cursor+=1 | 无 |
| C18 `build_action_publish_request` | 计算函数 | `control_loop.py` | action id、SafetyResult、permit、two clocks | ActionPublishRequest | 无进程外读写 |
| C19 `_apply_publish_outcome` | 内部状态更新函数 | A4 | ActionPublishRequest、result XOR error、SafetyResult、C26、monotonic_s | previous+source time/chunk/fault/deferred reason/metrics 更新 | 无 |
| C20 `_publish_runtime_metrics` | 数据读写函数 | A5 | RuntimeMetricsSnapshot | `/act/metrics` JSON | ROS publish |
| C21 `build_arg_parser` | 计算函数 | `act_deploy_node.py` | CLI schema | ArgumentParser | 无进程外读写；`parse_args` 由 B11 调用 |
| C22 `InferenceWorker.stop` | 内部状态更新函数 | A3 | — | 幂等设置 stop event | 唤醒由 C10 完成 |
| C23 `ControlLoop.begin_stopping` | 内部状态更新函数 | A4 | — | 幂等设置 stopping/metrics | 无 |
| C24 `ControlLoop._next_action_id` | 内部状态更新函数 | A4 | tick sequence | `act-{sequence:012d}` | sequence += 1 |
| C25 `ControlLoop.latch_runtime_fault` | 内部状态更新函数 | A4 | FallbackReason、detail | 清运行状态并锁存 runtime fault | 无；B9/内部 B3 可调用 |
| C26 `CandidateSelection` | 数据 | `control_loop.py` | action、source capture time、normal/hold/continue source | frozen tick-local provenance | 无 |

## 4. runtime 内部数据契约

```python
@dataclass(frozen=True)
class InferenceRequest:
    request_id: int
    observation: ObservationSnapshot
    submitted_at_s: float          # monotonic
    trigger_cursor: int

@dataclass(frozen=True)
class InferenceResult:
    request_id: int
    observation_captured_at_s: float  # monotonic，来自已修复的 snapshot
    submitted_at_s: float
    started_at_s: float
    completed_at_s: float
    chunk: ActionChunk | None
    error_type: str | None
    error_message: str | None
```

`InferenceResult` 不变量：

- success：`chunk is not None` 且 error 字段均为 `None`；
- failure：`chunk is None` 且 `error_type/error_message` 均为非空字符串；
- `observation_captured_at_s <= submitted_at_s <= started_at_s <= completed_at_s`；
- 不保存 exception/traceback/policy；
- `ActionChunk` 仍只含 actions。

`LatestQueue` 合同：

```python
put_latest(item) -> int
take_latest(timeout_s: float | None = 0.0) -> T | None
close() -> int
```

worker 使用阻塞 take；ControlLoop 使用 `timeout_s=0`。request/result queue 使用同一关闭语义：`close()` 在 lock 下先标记 closed，再清空全部待处理项并计入 dropped，返回清除数并唤醒所有 waiter；关闭后的 `take_latest()` 一律返回 `None`，`put_latest()` 抛稳定 `RuntimeError("queue is closed")`，不允许 1ms busy polling。淘汰/关闭清除数只由 C8/C10 返回并交给 metrics，不塞进 C9 返回值。

## 5. `ControlLoop.tick` 精确接口

```python
def tick(
    self,
    *,
    monotonic_s: float,
    ros_time_s: float,
    command_permit: CommandPermit,
) -> ActionPublishResult | None:
```

构造期注入：`RuntimeConfig`、独立 `max_observation_age_s`、startup-only `command_output_enabled`、`observation_provider`、request/result queue、`RuntimeMetrics`、`SafetyGuard`、绑定的 `publish_action`。A4 只用该 bool 对 L2-05 result 做交叉校验，不拥有或热切换 gate；它不持有 policy、不 import UI、不直接 ROS publish。

## 6. tick 状态机

```text
tick(now, ros_time, permit)
  1. 若 stopping 或 output fault latch：只记 metrics，返回 None
  2. B4 非阻塞收最新 InferenceResult
     - 只有匹配 in-flight id 的 terminal result 可清 in-flight并推进 last-completed
     - error result 记录错误、不产生 chunk；active 仍合法时不强制 fallback
     - discard-in-flight=True 时终结 request 并丢弃其 success chunk，再复位 flag
     - stale/旧 id 丢弃；未知更大 id 调 C25 锁存 runtime fault
  3. C13 校验 success result：时间顺序、age、shape/dtype/finite
  4. 合法 result 只放 pending
  5. C15 作为 B3 直接步骤：active 缺失或到 horizon 时激活既有 pending
  6. 每拍重新检查 active age；过期立即 C16 失效
  7. 读取 fresh ObservationSnapshot
  8. C14 决定 B5 是否提交 fresh request
  9. 无 fresh observation：不消费新模型 action，进入 B8
 10. B6 只在 normal horizon 内选择 candidate；不可选则把确定 reason 交 B8
 11. B8 是 hold/continue/safe-stop 的唯一解释者；有 candidate 才继续 B7
 12. B7 调真实 L2-04：
       filter_action(candidate,
                     previous_safe_action=previous,
                     latest_observation=observation)
 13. C18 构造 ActionPublishRequest
 14. 调绑定的 ActionPublisher.publish
 15. C19 按六种 outcome 更新 previous/chunk/fault/metrics
```

## 7. request、prefetch 与 chunk 切换

提交 request 必须同时满足：未 stopping、无 fault latch、无 in-flight、无 pending、observation 新鲜，并且“无 active”或 `active_cursor >= execute_horizon - prefetch_steps`。

- worker 负责限制相邻 inference start 至 `inference_hz`；ControlLoop 不 sleep。
- 新结果先进入 pending，不立即截断 active。
- active 缺失或 `cursor >= execute_horizon` 时 pending 从 cursor 0 激活。
- 正常路径绝不消费 horizon 之后 row。
- `continue_old_chunk` 可在 pending 未到时继续到 `chunk_size`，但每拍仍检查 observation freshness 和 action age；pending 到达后下一 tick 优先切换。
- `_take_cursor_action` 必须返回 copy，不能把 `ActionChunk.actions` 可写 view 交给 L2-04。
- 第一版不计算 aligned index，不 blend，不跨 chunk 融合。

## 8. age、乱序与错误

`validate_inference_result` 检查：

1. result id 等于 in-flight id 且大于 last completed id；
2. success/error XOR 与时间顺序合法；
3. `now - observation_captured_at_s` 位于 `[0, max_action_age_sec]`；
4. chunk shape 精确 `(runtime.chunk_size, runtime.action_dim)`；
5. dtype `float32`、所有值 finite；
6. active/pending 在激活和每次消费前重新算 age。

worker 捕获普通 `Exception` 并形成 failure `InferenceResult`；不吞 `KeyboardInterrupt/SystemExit`。成功和失败的匹配 terminal result 都更新 last-completed。prefetch error 到达时，若 active 仍新鲜且 cursor 未到 normal horizon，本 tick 继续 B6 normal；只有没有合法 normal candidate 时，才以 `INFERENCE_ERROR` 进入 B8。policy 调用不可强杀，shutdown 时等待有界 timeout，调用完成后若 channel 已关闭则丢弃结果并退出。

## 9. safety、publish 与 fallback

正常/hold/continue 的动作都必须走：

```text
candidate
  -> SafetyGuard.filter_action
  -> SafetyResult
  -> ActionPublishRequest(action_id, permit, two clocks)
  -> ActionPublisher.publish
  -> ActionPublishResult reducer
```

非 safety 失败只写 L2-06 metrics，不能制造假的 `SafetyResult`。Safety REJECTED 可以调用一次 L2-05 输出真实 rejected status，同一 tick 不再发第二动作。`safe_stop` 是逐 tick fail-closed：本 tick 无 fallback action、无 L2-05 command，下一 tick 可在 fresh observation 下恢复；它不是永久 latch，也不是硬件 stop 成功证明。永久禁止 command 的 latch 只由 `PARTIAL/FAILED` 等明确输出故障触发。

publish reducer 以 `01_L2功能边界.md §7` 为准；尤其 `PARTIAL/FAILED` 必须 fault latch，`BLOCKED/REJECTED` 必须失效 chunk，`OBSERVED` 只在启动期 command-disabled 进程中更新虚拟 previous。

`REJECTED/BLOCKED` 的下一拍 reason 不得丢失：C19 同步写一次性 deferred fallback state 与 metrics gauge，B6 在没有合法 normal candidate 时才交 B8；新 normal 恢复则同步清除二者。L2-05 result 的 action id、safety status、outcome/failure stage 自相矛盾时以 `PUBLISH_RESULT_INVARIANT` 锁存 runtime port fault，不是 fallback。

## 10. 创建与关闭顺序

```text
Creation order:
  B11 解析 --config / --enable-command-output
  -> L2-01 typed config + canonical ActRuntimeResources
  -> L2-03 ActInferenceService（消费同一 PolicyInputSpec）
  -> rclpy.init / 创建 A5
  -> L2-02 observation pipeline（消费同一 PolicyInputSpec）
  -> L2-04 SafetyGuard + L2-06 LatestQueue/RuntimeMetrics/未启动 InferenceWorker
  -> B12 对资源、pipeline、permit、queue 做无 I/O 交叉校验
  -> L2-05 ActionPublisher/metrics publisher + L2-06 ControlLoop
  -> ActDeployNode start worker
  -> 最后创建 control timer / metrics timer
  -> 任一构造步骤失败：B10 回收已有 runtime，A5 自销毁半构造 ROS Node 后 re-raise

Shutdown order:
  在 A5 lifecycle/tick lock 内 C23 ControlLoop.begin_stopping
  -> cancel control/metrics timers
  -> C22 worker.stop（先设置 stop event）
  -> close/清空 request queue 并唤醒 worker
  -> bounded join
  -> close result queue
  -> join 成功才写 STOPPED；timeout 写 SHUTDOWN_TIMEOUT + last_error，Gate FAIL
  -> 销毁 ROS handles

State owner:
  L2-02 owns observation；L2-06 owns inference runtime/cursor/fallback/metrics；L2-03/04/05 不保存调度状态。

Pure RAM calculations:
  C12/C13/C14/C18。

External boundary reads/writes:
  B9 读取 ROS/monotonic clock 与 CommandPermitSource；B7 通过 publish port 触发 L2-05 ROS I/O；C20 只写 /act/metrics。

Runtime orchestration point:
  A4/B3 ControlLoop.tick；A5/B9 仅提供 timer 驱动和外部事实。

Failure propagation:
  policy Exception -> error InferenceResult -> B4 终结 in-flight；active 仍合法则继续 normal，否则 B8；SafetyResult.REJECTED -> L2-05 rejected status + 下一 tick fallback；L2-04/observation/queue/id invariant -> runtime fault latch；publish callable exception 或 PARTIAL/FAILED -> output fault latch；startup failure -> worker/timer 均不启动；join timeout -> SHUTDOWN_TIMEOUT/FAIL，禁止伪写 STOPPED。
```

## 11. 前置修复边界

L2-06 L3 不得通过硬编码 camera key、转置 snapshot、猜 gripper message、绕过 `load_deploy_config` 或自行加载 policy 来“修通”上游。`01_L2功能边界.md §8` 的 P0 项必须在原 owner L2 修复并由 `04_L2验收机制.md` 的真实接缝 Gate 证明。

本文件中的 A/B/C 编号必须与 `03a_功能微元总览与组织结构.md` 完全一致。
