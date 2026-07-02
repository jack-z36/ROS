---
tags:
  - term-explainer
  - pi05
  - data-read-write
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# request_queue

> [!abstract] 核心定义
> 线程间传递最新 `InferenceRequest` 的 `LatestQueue`，主要职责是写入最新请求和读出最新请求。

## 数据流向

| 方向 | 数据源 | 具体内容 | 格式/类型 |
|------|--------|----------|-----------|
| 写入 | ControlLoop._maybe_submit_request() | InferenceRequest | LatestQueue[InferenceRequest] |
| 读取 | InferenceWorker.run() | latest InferenceRequest | None | InferenceRequest | None |

> [!note] 注
> 这里只保留该术语实际涉及的读写方向。

## 读写逻辑

1. **写入阶段**：`put_latest(request)` 写入最新请求，队列满时丢掉旧请求。
2. **读取阶段**：`get_latest_or_none()` 取出最新请求并清空其他项。

## 数据流图

```mermaid
flowchart LR
    A[ControlLoop] -->|写入| B[request_queue]
    B -->|读取| C[InferenceWorker]
```

## 具象隐喻

> [!tip] 生活场景类比
> 像只能放一张任务单的窗口：新单来了就覆盖旧单，因为机器人只需要最新观测。
