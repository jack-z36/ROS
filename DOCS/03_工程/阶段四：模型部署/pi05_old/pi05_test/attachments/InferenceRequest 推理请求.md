---
tags:
  - 附件
---

# InferenceRequest 推理请求

> [!abstract]
> 控制循环向后台推理线程投递的"信封"——内容只有**一帧冻结观测** + 一些用于追踪 / 调度的元数据。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `InferenceRequest` |
| 数据类型 | `@dataclass(frozen=True)`（`shared_buffer.py:61-68`） |
| 数据结构 | 4 字段：`observation, obs_time, request_id, trigger_step` |
| 所在文件 | `pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:61-68` |
| 现实含义 | 一封"请基于此帧算 30 步动作"的信 |

## 字段含义

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `observation` | [[ObservationSnapshot 冻结的观测]] | 触发本次推理的"当时画面+状态" |
| `obs_time` | `float` | 观测采集时刻（`time.monotonic()`） |
| `request_id` | `int` | 单调递增的请求编号，用于日志关联 |
| `trigger_step` | `int` | 触发时 active chunk 的 cursor，便于诊断"是不是太晚才请求" |

## 示例

```python
from pi05.deploy.runtime.shared_buffer import InferenceRequest

req = InferenceRequest(
    observation=snapshot,        # ObservationSnapshot
    obs_time=snapshot.captured_at_s,
    request_id=42,
    trigger_step=5,              # 剩 5 步时发起
)
```

## 在数据流中的位置

- 生产方：`ControlLoop._maybe_submit_request()`，条件触发（`request_pending=False` 且 active cursor ≥ execute_horizon − prefetch_steps）
- 传送：`LatestQueue[InferenceRequest].put_latest(req)`（**只保留最新一封**）
- 消费方：`InferenceWorker.run()` 醒来后 `get_latest_or_none()` → `policy_runtime.predict_action_chunk(observation)`
- 关联产物：worker 处理后产出 [[ActionChunk 动作块 dataclass]]，`obs_time` 字段沿用请求的 `obs_time`（用于 `aligned_index` 时间对齐）

## 为什么不带"目标动作"或"提示"

> VLA 模型是**前向预测**——给定 obs → 一次性吐出 30 步 action chunk。请求里不需要"目标"，模型是反应式的（reactive）。`trigger_step` 也不是指令，只是日志维度。

## 相关概念

- [[LatestQueue 最新单元素队列]]：装载本结构的信箱
- [[ObservationSnapshot 冻结的观测]]：本结构的主载荷
- [[ActionChunk 动作块 dataclass]]：请求处理后的产物
- [[ControlLoop 控制循环驱动]]：本结构的生产方
- [[InferenceWorker 推理后台线程]]：本结构的消费方
