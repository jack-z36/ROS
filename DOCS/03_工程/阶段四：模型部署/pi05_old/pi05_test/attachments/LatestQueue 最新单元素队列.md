---
tags:
  - 附件
---

# LatestQueue 最新单元素队列

> [!abstract]
> 容量为 1 的线程安全队列，新元素入队时**自动丢弃**老元素，专门解决"推理 100ms 远慢于 30Hz 控制"导致的请求/结果积压。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `LatestQueue[T]` |
| 数据类型 | `Generic[T]` 类（`shared_buffer.py:71-102`） |
| 数据结构 | 内部 `deque[T](maxlen=1)` + `threading.Lock` |
| 所在文件 | `pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:71-102` |
| 现实含义 | 永远只保留"最新一封"信的信筒 |

## 为什么需要它

> 模型推理单步 50-200 ms，控制循环 33 ms / 步（30 Hz）。
> 如果用普通 `queue.Queue`：
> - 控制循环连发 5 个 `InferenceRequest` 给 worker
> - worker 还在算第一封，队列里堆了 4 封过时请求
> - 算出来时"现在该用的观测"已经在队列尾
>
> 用 `LatestQueue(maxsize=1)`：每来新请求就 `popleft()` 老请求，worker 醒来时只看到**最新一封**。

## 公开方法

| 方法 | 作用 | 关键行为 |
| --- | --- | --- |
| `put_latest(item)` | 入队 | 满了就 `popleft()` 老的，再 `append()` 新的 |
| `get_latest_or_none()` | 取最新 | 取走后 `clear()` 清空（避免积压） |
| `empty()` / `__len__()` | 查询 | 锁内读长度 |

## 示例

```python
q: LatestQueue[int] = LatestQueue(maxsize=1)
q.put_latest(1)
q.put_latest(2)   # 自动丢 1
q.put_latest(3)   # 自动丢 2
print(len(q))     # 1
print(q.get_latest_or_none())   # 3
print(q.get_latest_or_none())   # None
```

## 在数据流中的位置

- 上游：
  - `ControlLoop._maybe_submit_request()` → `request_queue.put_latest(InferenceRequest)`
  - `InferenceWorker._run_request()` → `result_queue.put_latest(ActionChunk)`
- 下游：
  - `InferenceWorker.run()` → `request_queue.get_latest_or_none()`
  - `ControlLoop._collect_result()` → `result_queue.get_latest_or_none()`

## 相关概念

- [[SharedBuffer 线程安全桥接]]：拥有两个 `LatestQueue` 实例
- [[InferenceRequest 推理请求]]：request_queue 的载荷类型
- [[ActionChunk 动作块 dataclass]]：result_queue 的载荷类型
