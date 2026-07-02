---
tags:
  - 附件
---

# RuntimeMetrics 运行时指标

> [!abstract]
> 部署运行时计数器与延迟统计的容器，由 `SharedBuffer` 拥有，被 `ControlLoop` / `InferenceWorker` / `SafetyGuard` 增量更新，每秒 1 次以 JSON 发布到 `/pi05_vla/metrics`。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `RuntimeMetrics` |
| 数据类型 | `@dataclass`（非 frozen，可变） |
| 数据结构 | 17 个计数/标量字段 |
| 所在文件 | `pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:105-153` |
| 现实含义 | 部署期"黑匣子"——回答"系统跑得怎么样" |

## 字段速查（17 项）

| 字段 | 类型 | 记录什么 | 谁在 +1 |
| --- | --- | --- | --- |
| `inference_count` | `int` | 推理成功次数 | `record_latency()`（被 worker 调） |
| `inference_error_count` | `int` | 推理抛异常的次数 | `record_inference_error()` |
| `inference_request_count` | `int` | 控制环推了几次请求 | `record_inference_request()` |
| `chunk_result_count` | `int` | worker 推了几次结果 | `record_chunk_result()` |
| `discarded_chunk_count` | `int` | 被丢的 chunk 数 | `record_discarded_chunk()` |
| `chunk_switch_count` | `int` | active chunk 切换次数 | `record_chunk_switch()` |
| `fallback_count` | `int` | fallback 触发次数 | `record_fallback()` |
| `dropped_observation_count` | `int` | 被覆盖的旧观测数 | `SharedBuffer.set_observation()` |
| `published_action_count` | `int` | 实际发布命令数 | `record_published_action()` |
| `held_action_count` | `int` | fallback 时沿用上次动作的次数 | `record_held_action()` |
| `rejected_action_count` | `int` | SafetyGuard 拒绝的次数 | `record_rejected_action()` |
| `last_inference_latency_s` | `float` | 最近一次推理耗时 | `record_latency()` |
| `ema_inference_latency_s` | `float` | 指数滑动平均（α=0.2） | `record_latency()` |
| `last_action_age_s` | `float` | 最近一次 action 的"陈旧度" | （更新方见 control_loop） |
| `last_error` | `str \| None` | 最近一次错误的描述 | 多个 `record_*_error/discarded/fallback` |
| `updated_at_s` | `float` | 上次更新时间戳 | 所有 record 方法 |

## EMA 公式

$$\text{ema}_{t} = 0.8 \cdot \text{ema}_{t-1} + 0.2 \cdot \text{latency}_{t}$$

> 0.2 是新样本权重（`shared_buffer.py:132`），等效半衰期约 `log(0.5)/log(0.8) ≈ 3` 次推理。

## 示例

```python
m = RuntimeMetrics()
m.record_latency(0.15)   # 150 ms
m.record_latency(0.20)
print(m.inference_count)               # 2
print(m.last_inference_latency_s)      # 0.2
print(m.ema_inference_latency_s)       # 0.16  (0.8*0.15 + 0.2*0.20)
print(m.as_dict()["ema_inference_latency_s"])  # 同上
```

## 在数据流中的位置

- 上游：所有 `record_*` 调用方（worker / control_loop / safety_guard）
- 下游：
  - `SharedBuffer.metrics_snapshot()` → `_publish_metrics()` 每秒 1 次
  - 序列化为 `std_msgs/String(JSON)` 发布到 `/pi05_vla/metrics` 与 `/pi05_vla/status`

## 相关概念

- [[SharedBuffer 线程安全桥接]]：持有 `self.metrics` 实例
- [[ControlLoop 控制循环驱动]]：调用 `record_inference_request / record_chunk_switch / record_fallback`
- [[InferenceWorker 推理后台线程]]：调用 `record_inference_latency / record_inference_error / record_chunk_result`
- [[SafetyGuard 安全校验器]]：拒绝时由 ControlLoop 调 `record_rejected_action`
