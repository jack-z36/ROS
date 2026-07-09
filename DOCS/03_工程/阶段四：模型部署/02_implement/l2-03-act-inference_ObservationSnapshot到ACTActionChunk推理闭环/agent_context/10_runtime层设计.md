# runtime 层设计：L2-03

## 1. 目标源码路径

```text
src/model_deploy/act/runtime/shared_buffer.py
src/model_deploy/act/runtime/inference_worker.py
```

## 2. 层职责

`runtime/` 负责时间、线程、队列、状态机、调度。L2-03 在这一层承载：
- 跨模块共享的数据结构与缓冲（`ActionChunk` / `InferenceRequest` / `ObservationSnapshot` / `LatestQueue` / `SharedBuffer` / `RuntimeMetrics`）；
- 后台推理线程（`InferenceWorker`），异步消费 request → 推理 → 写 result + metrics。

## 3. 文件设计

### shared_buffer.py

- **职责**：定义推理链路的共享 RAM 对象与缓冲，供 L2-02 / L2-03 / L2-06 共同使用。
- **class 设计**：

| class | 封装微元 | 内部状态 | 生命周期/并发 | 为什么 class | Pi0.5 参考 |
|---|---|---|---|---|---|
| `ActionChunk`（frozen dataclass） | 数据 + 计算函数（aligned_index） | actions/obs_time/infer_start_time/ready_time/action_dt/request_id/cursor | frozen，单次创建，多消费者只读 | 聚合多字段的值对象 | `ActionChunk`（直接复用，14→16） |
| `InferenceRequest`（frozen dataclass） | 数据 | observation/obs_time/request_id/trigger_step | frozen，单次创建 | 值对象 | `InferenceRequest`（直接复用） |
| `ObservationSnapshot`（frozen dataclass） | 数据 | images/state/encoded_state/captured_at_s | frozen，单次创建 | 值对象（L2-02 也用） | `ObservationSnapshot`（直接复用） |
| `LatestQueue[T]`（Generic） | 内部状态更新函数 + 数据 | _items(deque)/_lock | 长生命周期，多线程读写 | 需要 deque + 锁 | `LatestQueue`（直接复用） |
| `SharedBuffer` | 数据 + 内部状态更新函数 | _latest_observation/inference_request_queue/chunk_result_queue/metrics/_lock | 长生命周期，多线程读写 | 聚合跨模块共享状态 + 锁 | `SharedBuffer`（直接复用） |
| `RuntimeMetrics`（dataclass） | 数据 + 计算函数 | inference_count/error_count/request_count/chunk_result_count/latency EMA/last_error | 长生命周期 | 计数器集合 + EMA | `RuntimeMetrics`（直接复用） |

- **函数设计**：

| 函数 | 类型 | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|
| `ActionChunk.__post_init__` | 计算函数 | self | 校验 rank-2 + action_dt>0 | 构造时自动触发 | 直接复用 |
| `ActionChunk.aligned_index(now)` | 计算函数 | now float | int（时间对齐 idx） | 无 | 直接复用（L2-06 第一版 cursor 直取可选用） |
| `LatestQueue.put_latest(item)` | 内部状态更新函数 | T | None | 写 deque + 丢旧 | 直接复用 |
| `LatestQueue.get_latest_or_none()` | 内部状态更新函数 | — | T / None | 取最新 + 清空 | 直接复用 |
| `SharedBuffer.record_inference_latency(latency_s)` | 内部状态更新函数 | float | None | 更新 metrics EMA | 直接复用 |
| `SharedBuffer.record_inference_error(message)` | 内部状态更新函数 | str | None | error_count++ + last_error | 直接复用 |
| `SharedBuffer.record_inference_request()` / `record_chunk_result()` | 内部状态更新函数 | — | None | 计数++ | 直接复用 |
| `RuntimeMetrics.record_latency(latency_s)` | 计算函数 | float | None | count++ + EMA | 直接复用 |
| `RuntimeMetrics.as_dict()` | 计算函数 | — | dict | 无 | 直接复用 |

- **不负责**：不做模型推理（属 repo）；不做 batch 构造（属 service）；不订阅/发布 topic（属 L2-02/L2-05）；不做单步选择/cursor 推进（属 L2-06）；不做平滑。
- **依赖方向**：`runtime` → `types`（StateSpec/ActionSpec）、`config`、`service`、`repo`（ActPolicyRuntime）。禁止 import `ui`。
- **Pi0.5 参考**：`deploy/src/pi05/deploy/runtime/shared_buffer.py`（直接复用，14→16）。
- **验收覆盖**：ActionChunk 校验非法 rank 抛异常；LatestQueue latest-only 行为；SharedBuffer record_* 计数正确；RuntimeMetrics EMA 计算。

> [!note] shared_buffer 跨 L2 共享
> `shared_buffer.py` 被 L2-02（写 latest_observation）、L2-03（读写 request/result/metrics）、L2-06（读写所有）共同使用。第一版由 L2-03 首先落地，L2-02/L2-06 import 复用。若 L2-01 在 types 层统一提供这些数据结构，则本文件改为 import 复用（见 `01_L2功能边界.md` §9 待决策项 1）。

### inference_worker.py

- **职责**：后台线程消费 `inference_request_queue`，调 `ActPolicyRuntime.predict_action_chunk`，把结果写入 `chunk_result_queue` + 更新 metrics；按 `inference_hz` 限速；失败捕获不崩溃。
- **class 设计**：

```text
InferenceWorker(threading.Thread)
  封装微元：
    - 编排函数：run（后台循环：get→限速→_run_request）、_run_request（predict→构造 chunk→record→put）
    - 内部状态更新函数：stop（set _stop_event）
  内部状态：policy_runtime/request_queue/result_queue/shared_buffer/period_s/action_dt/_stop_event/_last_infer_start_s/log_*
  生命周期：daemon 后台线程，独立运行，与 ControlLoop 并行
  并发特征：单后台线程串行调用 policy_runtime（GPU 推理不并发）；通过 LatestQueue 与 L2-06 通信
  为什么 class：需要线程生命周期 + 持有 queue 句柄 + 限速状态
  Pi0.5 参考：InferenceWorker（直接复用）
```

- **方法/函数设计**：

| 方法 | 类型 | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|
| `__init__(policy_runtime, request_queue, result_queue, shared_buffer, inference_hz, control_hz, log_*)` | 数据 | 各句柄 + hz | — | 初始化状态 + period_s/action_dt | 直接复用 |
| `run()` | 编排函数 | — | 后台循环 | get→限速→_run_request | 直接复用 |
| `_run_request(request)` | 编排函数 | InferenceRequest | None（副作用） | predict→构造 ActionChunk→record latency/count→result_queue.put_latest | 直接复用 |
| `stop()` | 内部状态更新函数 | — | None | set _stop_event | 直接复用 |

- **失败行为**：`_run_request` 用 `try/except Exception` 捕获 predict 异常 → `shared_buffer.record_inference_error(message)` + `log_warning` → `return`（继续下一个 request，不崩溃）。
- **不负责**：不决定何时提交 request（属 L2-06）；不构造 batch（属 service/repo）；不做单步选择/cursor（属 L2-06）；不做平滑。
- **依赖方向**：`runtime` → `repo`（ActPolicyRuntime）、`service`（batch_adapter，若 predict 内部调用）。禁止 import `ui`。
- **Pi0.5 参考**：`deploy/src/pi05/deploy/runtime/inference_worker.py`（直接复用）。
- **验收覆盖**：worker 消费 request→chunk 写入 result_queue→metrics 递增→不阻塞调用线程；异常注入→error_count 递增→worker 不崩溃；inference_hz 限速生效。

## 4. 与去除平滑处理的关系

- `InferenceWorker` 不包含 `blend_steps`、`smoothstep_alpha`、`_blend_next_action`、`_start_blend_or_switch` 任何平滑逻辑。
- `ActionChunk` 保留 `cursor` 字段（向后兼容），但第一版不在本 L2 推进 cursor（由 L2-06 直取）。
- `RuntimeMetrics` 不包含 `blend_active` 等平滑状态字段。

## 5. 验收如何确认

- `shared_buffer` 单测：ActionChunk 非法 rank/非法 action_dt 抛异常；LatestQueue latest-only；SharedBuffer record_* 计数；RuntimeMetrics EMA。
- `inference_worker` 单测（fake-policy）：消费→写 chunk→metrics→不阻塞；异常→error_count→不崩溃；限速。
- `rg` 检查 `runtime/` 下不存在 smoothstep/blend/cross_chunk 平滑逻辑。

## 6. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。不继承 Pi0.5 `control_loop.py` 的平滑逻辑。
