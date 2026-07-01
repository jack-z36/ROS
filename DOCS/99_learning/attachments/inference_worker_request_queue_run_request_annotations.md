---
tags:
  - program-principle
  - pi05
  - inference-worker
source:
  - pi05_test/pi05/deploy/src/pi05/deploy/runtime/inference_worker.py
  - pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py
  - pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py
---

# InferenceWorker / request_queue / `_run_request()` 注释

> [!summary]
> 这份注释解释一条很窄的链路：`ControlLoop._maybe_submit_request()` 如何把 `InferenceRequest` 写入 `request_queue`，`InferenceWorker.run()` 如何取出请求，`InferenceWorker._run_request()` 如何把一次请求变成一个 `ActionChunk`。

---

## 1. 上下游边界

```text
ControlLoop._maybe_submit_request()
    ↓ put_latest(request)
request_queue: LatestQueue[InferenceRequest]
    ↓ get_latest_or_none()
InferenceWorker.run()
    ↓
InferenceWorker._run_request(request)
    ↓
ActionChunk
    ↓ put_latest(chunk)
result_queue: LatestQueue[ActionChunk]
    ↓
ControlLoop._collect_result()
```

这段程序的职责是：**把一帧最新 observation 异步送进 VLA 模型，并把模型输出包装成动作块。**

---

## 2. 四类程序功能

| 程序功能 | 对应代码 | 作用 |
|---|---|---|
| 读取与写入数值 | `request_queue.put_latest()` / `get_latest_or_none()` / `result_queue.put_latest()` | 在线程之间传递请求和结果 |
| 编排函数 | `_maybe_submit_request()` / `run()` / `_run_request()` | 决定何时提交请求、何时推理、何时写出结果 |
| 数值加工处理 | `policy_runtime.predict_action_chunk(observation)` | 把 `ObservationSnapshot` 加工成 `(chunk_size, 14)` 动作块 |
| 数据结构定义 | `InferenceRequest` / `LatestQueue` / `ActionChunk` | 定义请求、队列、结果格式 |

---

## 3. 上游：`ControlLoop._maybe_submit_request()`

```python
observation = self.observation_provider()
if observation is None:
    return

self.request_id += 1
request = InferenceRequest(
    observation=observation,
    obs_time=observation.captured_at_s,
    request_id=self.request_id,
    trigger_step=self.active_cursor,
)
self.request_queue.put_latest(request)
```

### 输入

```python
observation: ObservationSnapshot
```

### 输出

```python
InferenceRequest
```

然后写入：

```python
request_queue: LatestQueue[InferenceRequest]
```

---

## 4. 数据结构：`InferenceRequest`

```python
@dataclass(frozen=True)
class InferenceRequest:
    observation: ObservationSnapshot
    obs_time: float
    request_id: int
    trigger_step: int
```

| 字段 | 来源 | 作用 |
|---|---|---|
| `observation` | `SharedBuffer.latest_observation()` | 真正给模型推理用的一帧完整观测 |
| `obs_time` | `observation.captured_at_s` | 后续 `ActionChunk` 的时间锚点 |
| `request_id` | `ControlLoop` 自增 | 日志、调试、请求追踪 |
| `trigger_step` | `active_cursor` | 记录发起请求时旧动作块执行到第几步 |

`InferenceRequest` 不做数值加工，只是把“要推理的数据”和“请求元信息”打包。

---

## 5. 队列：`request_queue` / `LatestQueue`

`request_queue` 不是普通 FIFO 队列，而是：

```text
只保留最新请求。
旧请求可以被丢弃。
```

写入：

```python
def put_latest(self, item):
    if len(self._items) == self._items.maxlen:
        self._items.popleft()
    self._items.append(item)
```

读取：

```python
def get_latest_or_none(self):
    if not self._items:
        return None
    latest = self._items.pop()
    self._items.clear()
    return latest
```

| 函数 | 输入 | 输出 | 语义 |
|---|---|---|---|
| `put_latest(item)` | `InferenceRequest` | 无 | 写入最新请求；满了丢旧请求 |
| `get_latest_or_none()` | 无 | `InferenceRequest | None` | 取出最新请求，并清空旧请求 |

> [!important]
> 实时机器人更关心“最新 observation”，而不是处理每一个历史 observation。所以这里故意允许旧请求被覆盖。

---

## 6. 编排函数：`InferenceWorker.run()`

```python
while not self._stop_event.is_set():
    request = self.request_queue.get_latest_or_none()
    if request is None:
        self._stop_event.wait(0.001)
        continue

    now = time.monotonic()
    remaining = self.period_s - (now - self._last_infer_start_s)
    if remaining > 0.0:
        self._stop_event.wait(remaining)

    self._run_request(request)
```

### 输入

```python
request_queue: LatestQueue[InferenceRequest]
```

### 输出

没有直接返回值。它通过调用 `_run_request(request)` 产生后续效果。

### `period_s`

```python
self.period_s = 1.0 / inference_hz
```

如果 `inference_hz = 10`：

```text
period_s = 0.1s
```

表示后台推理最多约 10 Hz。

---

## 7. 核心函数：`InferenceWorker._run_request(request)`

```python
def _run_request(self, request: InferenceRequest) -> None:
    infer_start = time.monotonic()
    self._last_infer_start_s = infer_start
    try:
        actions = self.policy_runtime.predict_action_chunk(request.observation)
    except Exception as exc:
        message = f"policy inference failed request_id={request.request_id}: {exc}"
        self.shared_buffer.record_inference_error(message)
        self.log_warning(message)
        return

    ready_time = time.monotonic()
    chunk = ActionChunk(
        actions=actions,
        obs_time=request.obs_time,
        infer_start_time=infer_start,
        ready_time=ready_time,
        action_dt=self.action_dt,
        request_id=request.request_id,
    )
    latency_s = ready_time - infer_start
    self.shared_buffer.record_inference_latency(latency_s)
    self.shared_buffer.record_chunk_result()
    self.result_queue.put_latest(chunk)
```

---

## 8. `_run_request()` 输入输出

### 输入

```python
request: InferenceRequest
```

其中最关键的是：

```python
request.observation: ObservationSnapshot
```

### 中间加工

```python
actions = self.policy_runtime.predict_action_chunk(request.observation)
```

`predict_action_chunk()` 的输入输出：

| 输入 | 输出 |
|---|---|
| `ObservationSnapshot` | `np.ndarray (chunk_size, 14)` |

这里的 `actions` 已经是**真实机器人动作空间**，不是归一化动作。

### 输出

```python
ActionChunk
```

并写入：

```python
result_queue: LatestQueue[ActionChunk]
```

---

## 9. `_run_request()` 分步注释

### 9.1 记录推理开始时间

```python
infer_start = time.monotonic()
self._last_infer_start_s = infer_start
```

作用：

```text
记录推理开始时间
用于计算 latency
也用于下一轮 run() 的 inference_hz 限频
```

### 9.2 调用模型运行时

```python
actions = self.policy_runtime.predict_action_chunk(request.observation)
```

**输入：**

```python
ObservationSnapshot
```

**输出：**

```python
np.ndarray
shape = (chunk_size, 14)
dtype = float32
数值空间 = 真实机器人动作空间
```

### 9.3 推理失败时

```python
self.shared_buffer.record_inference_error(message)
self.log_warning(message)
return
```

失败时不会生成 `ActionChunk`，也不会写入 `result_queue`。下游控制循环拿不到新动作块时，会进入 fallback。

### 9.4 包装 `ActionChunk`

```python
chunk = ActionChunk(
    actions=actions,
    obs_time=request.obs_time,
    infer_start_time=infer_start,
    ready_time=ready_time,
    action_dt=self.action_dt,
    request_id=request.request_id,
)
```

`ActionChunk` 把两类信息合并：

| 信息 | 字段 |
|---|---|
| 动作数值 | `actions` |
| 时间信息 | `obs_time` / `infer_start_time` / `ready_time` / `action_dt` |

### 9.5 写入结果队列

```python
self.result_queue.put_latest(chunk)
```

这一步把结果交给下游：

```text
InferenceWorker
    ↓
result_queue
    ↓
ControlLoop._collect_result()
```

---

## 10. 输入输出对齐表

| 阶段 | 输入 | 输出 | 程序功能 |
|---|---|---|---|
| `_maybe_submit_request()` | `ObservationSnapshot` | `InferenceRequest` | 数据结构打包 |
| `request_queue.put_latest()` | `InferenceRequest` | 队列状态更新 | 写入数值 |
| `request_queue.get_latest_or_none()` | 队列状态 | `InferenceRequest | None` | 读取数值 |
| `InferenceWorker.run()` | `InferenceRequest` | 调用 `_run_request()` | 编排函数 |
| `_run_request()` | `InferenceRequest` | `ActionChunk` | 编排函数 |
| `policy_runtime.predict_action_chunk()` | `ObservationSnapshot` | `(chunk_size, 14)` 动作块 | 数值加工处理 |
| `result_queue.put_latest()` | `ActionChunk` | 队列状态更新 | 写入数值 |

---

## 11. 一句话心智模型

> `request_queue` 是控制循环递给后台推理线程的“最新任务盒子”；`InferenceRequest` 是盒子里的任务单；`InferenceWorker.run()` 负责不断取任务；`_run_request()` 负责执行一次 VLA 推理，并把结果包装成 `ActionChunk` 放进 `result_queue`。
