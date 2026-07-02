---
tags:
  - 附件
---

# ActionChunk (动作块 dataclass)

> [!abstract]
> 推理后台线程的一次输出：30×14 动作矩阵 + 时间元数据。`ControlLoop` 用 `aligned_index(now)` 算"现在该执行 chunk 的第几步"。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `ActionChunk` |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:32-58` |
| 构造位置 | `inference_worker.py:75-82` |
| 现实含义 | "模型一次想 30 步 (0.5 秒 @ 60Hz)，但我们只执行前 10 步 (0.33 秒 @ 30Hz) 就开始预取新 chunk" |

## 字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `actions` | `np.float32[chunk_size, action_dim]` | 30×14 动作矩阵 |
| `obs_time` | `float` | 产生这次推理的观测 captured_at_s（monotonic） |
| `infer_start_time` | `float` | 模型开始推理的 monotonic 时间 |
| `ready_time` | `float` | 模型输出就绪的 monotonic 时间 |
| `action_dt` | `float` | 相邻两步动作的时间间隔（= 1/control_hz） |
| `request_id` | `int` | 唯一请求 ID，便于日志关联 |
| `cursor` | `int` | 当前执行到的索引，ControlLoop 内部使用 |

## `aligned_index` 行为

```python
def aligned_index(self, now: float) -> int:
    raw_idx = int((float(now) - float(self.obs_time)) / float(self.action_dt))
    return int(np.clip(raw_idx, 0, max(0, self.chunk_size - 1)))
```

- `now < obs_time` → 返回 0（没到观测时间，先不执行）
- `now > obs_time + (chunk_size-1)*action_dt` → 返回 chunk_size-1（chunk 全部用完还在用）
- 中间 → 按 dt 等距前进

## 校验（`__post_init__`）

- `actions.ndim == 2`（必须是 rank-2 矩阵）
- `action_dt > 0`（必须正数）
- `actions` 自动转 `np.float32`

## 在数据流中的位置

```text
InferenceWorker._run_request
    ↓
policy.predict_action_chunk(observation)  →  np.float32[30, 14]
    ↓
ActionChunk(actions, obs_time=..., ready_time=..., action_dt=1/30)
    ↓
chunk_result_queue.put_latest(chunk)
    ↓
ControlLoop.tick()  →  chunk.aligned_index(now)  →  chunk.actions[idx]  →  发布
```

## 关键约束

- **`obs_time` 必须用 monotonic**：和 ObservationSnapshot.captured_at_s 在同一时钟域
- **chunk 不在过期时立即丢弃**：先调 `aligned_index` 截断到末尾，再让 ControlLoop 的 stale 检查触发 fallback
- **`request_id` 用于日志关联**：方便排查"这次发到下位机的动作对应哪次推理"
- 与 [[InferenceWorker 推理后台线程]]、[[ControlLoop 控制循环驱动]] 上下游
