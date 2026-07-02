---
tags:
  - 附件
---

# SharedBuffer (线程安全桥接)

> [!abstract]
> 部署节点里 3 个并发组件 (ROS callback / ControlLoop / InferenceWorker) 共享的"信箱"：1 个最新观测槽 + 2 个 LatestQueue（请求 / 结果）+ 1 个 RuntimeMetrics。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `SharedBuffer` |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:156-242` |
| 实例位置 | `pi05_vla_deploy_node.py:42-45` |
| 现实含义 | 跨线程的"共享黑板"，避免显式传消息 |

## 字段

| 字段 | 类型 | 默认 | 含义 |
| --- | --- | --- | --- |
| `_latest_observation` | `ObservationSnapshot \| None` | None | 最新一次完整观测 |
| `inference_request_queue` | `LatestQueue[InferenceRequest]` | `maxsize=1` | 控制循环 → 推理后台 |
| `chunk_result_queue` | `LatestQueue[ActionChunk]` | `maxsize=1` | 推理后台 → 控制循环 |
| `metrics` | `RuntimeMetrics` | 默认实例 | 部署指标（计数器 + 延迟 EMA） |

## 行为约定

| 方法 | 调用方 | 行为 |
| --- | --- | --- |
| `set_observation(snapshot)` | ControlLoop | 覆盖 `_latest_observation`，旧的就 drop（计数 `dropped_observation_count`） |
| `latest_observation(max_age_s=...)` | ControlLoop | 读 `_latest_observation`，超龄返回 None |
| `record_inference_request()` | ControlLoop | `inference_request_count++` |
| `record_inference_latency(s)` | InferenceWorker | 写 `RuntimeMetrics.last_inference_latency_s` + EMA |
| `record_chunk_result()` | InferenceWorker | `chunk_result_count++` |
| `record_discarded_chunk(reason)` | ControlLoop | chunk 因过期被丢 |
| `record_chunk_switch()` | ControlLoop | 切到新 chunk |
| `record_fallback(reason)` | ControlLoop | fallback 策略被触发 |
| `record_published_action()` | ControlLoop | 成功发 action |
| `record_held_action()` | ControlLoop | fallback hold 模式 |
| `record_rejected_action(reason)` | ControlLoop | SafetyGuard 拒收 |
| `metrics_snapshot()` | Node `_publish_metrics` | 拿所有指标 dict 给 ROS /metrics topic |

## LatestQueue 的特殊语义

- **maxlen=1 + 写入时 pop 老元素**：`put_latest` 是"覆盖式入队"
- **`get_latest_or_none` 清空**：读最新 1 条后把所有老元素清掉
- **典型用途**：推理请求永远用最新观测（旧的被覆盖），不需要排队

## 锁

所有方法 `with self._lock:` 包裹，确保 `_latest_observation` 赋值和 metrics 写不会撕裂。

## 与 Pi05VlaDeployNode 的关系

```python
# pi05_vla_deploy_node.py:42-45
self.shared_buffer = SharedBuffer(
    max_inference_requests=config.runtime.max_inference_requests,
    max_pending_chunks=config.runtime.max_pending_chunks,
)
# 然后:
self.control_loop = ControlLoop(shared_buffer=self.shared_buffer, ...)
self.inference_worker = InferenceWorker(
    request_queue=self.shared_buffer.inference_request_queue,
    result_queue=self.shared_buffer.chunk_result_queue,
    shared_buffer=self.shared_buffer,
    ...
)
```

## 关键约束

- **LatestQueue maxlen >= 1**：在 `LatestQueue.__init__` 里硬校验
- **`latest_observation(max_age_s)` 是 stale 检查兜底**：ControlLoop 会再用一遍
- **metrics 是累积型**：从进程启动到关闭一直累加，部署监控只关心 `ema_inference_latency_s`、`last_error`
- 与 [[ObservationSnapshot 冻结的观测]]、[[InferenceWorker 推理后台线程]]、[[ControlLoop 控制循环驱动]] 配套
