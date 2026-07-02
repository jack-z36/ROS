---
tags:
  - term-explainer
  - pi05
  - data-read-write
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# SharedBuffer.chunk_result_queue

> [!abstract] 核心定义
> 保存最新 `ActionChunk` 的结果队列，上游由 `InferenceWorker` 写入，下游由 `ControlLoop` 读取。

## 数据流向

| 方向 | 数据源 | 具体内容 | 格式/类型 |
|------|--------|----------|-----------|
| 写入 | InferenceWorker._run_request() | ActionChunk | LatestQueue[ActionChunk] |
| 读取 | ControlLoop._collect_result() | latest ActionChunk | None | ActionChunk | None |

> [!note] 注
> 这里只保留该术语实际涉及的读写方向。

## 读写逻辑

1. **写入阶段**：推理完成后调用 `result_queue.put_latest(chunk)`。
2. **读取阶段**：控制循环用 `get_latest_or_none()` 取最新 chunk。

## 数据流图

```mermaid
flowchart LR
    A[InferenceWorker] -->|写入| B[chunk_result_queue]
    B -->|读取| C[ControlLoop]
```

## 具象隐喻

> [!tip] 生活场景类比
> 像后厨出菜口：厨房放上最新的菜，前台只拿最新那盘。
