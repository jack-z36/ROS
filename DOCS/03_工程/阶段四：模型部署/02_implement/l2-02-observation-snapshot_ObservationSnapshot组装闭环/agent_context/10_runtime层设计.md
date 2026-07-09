# runtime 层设计：L2-02

## 1. 目标源码路径

```text
src/model_deploy/act/runtime/observation_buffer.py
```

## 2. 层职责

`runtime/` 负责时间、状态、队列和调度语义。L2-02 的 runtime 层只保存 latest-only observation，并提供按 max age 读取最新 snapshot 的能力。

它不保存推理请求队列、不保存 action chunk 队列、不维护 ControlLoop cursor。

## 3. 文件设计

### `ObservationMetrics`

- 职责：记录 observation 侧可观察 counters。
- class：dataclass。
- 字段建议：`observation_ready_count`、`replaced_observation_count`、`stale_observation_count`、`last_missing_fields`、`last_error`、`updated_at_s`。
- 不负责：统一发布 `/act/status` 或 `/act/metrics`。

### `ObservationBuffer`

- 职责：latest-only 保存完整 snapshot。
- class：普通 class。
- 内部状态：`_latest_observation`、`_lock`、`metrics`。
- 为什么是 class：需要跨 callback 和 control tick 保存共享状态，并保证读写一致。

函数设计：

| 函数 | 输入 | 输出 | 副作用 | 错误行为 |
|---|---|---|---|---|
| `set_observation(observation)` | `ObservationSnapshot` | 无 | 覆盖 latest observation，更新 counters | snapshot 非法时拒绝 |
| `latest_observation(max_age_s=None)` | max age | `ObservationSnapshot` 或 `None` | stale 时可更新 stale counter | 无 snapshot 返回 `None` |
| `record_missing_fields(fields)` | list[str] | 无 | 更新 diagnostics | 无 |
| `metrics_snapshot()` | 无 | dict | 无 | 无 |

## 4. 输入输出

| 输入 | 输出 |
|---|---|
| service 层生成的 `ObservationSnapshot` | L2-06 可读取的 latest observation |

## 5. 副作用

只修改当前 Python 进程 RAM 中的 latest slot 和 metrics counters。

## 6. 依赖关系

允许依赖：

- `types/observation.py`
- 标准库 `threading`、`time`

禁止依赖：

- `ui/` 和 ROS packages
- `service/observation_collector.py`
- L2-03 inference queue
- L2-06 ControlLoop

## 7. Pi0.5 参考

- `SharedBuffer.set_observation`
- `SharedBuffer.latest_observation`
- `RuntimeMetrics.dropped_observation_count`

ACT 只抽取 observation latest slot，不搬运 Pi0.5 的 request queue、chunk queue 和 full metrics。

## 8. 验收覆盖

- 连续写入 A/B 后读取 B。
- `max_age_s` 生效。
- 无 snapshot 时返回 `None`。
- runtime 层无 ROS import。

## 9. 边界继承声明

本文件服务当前 L1/L2 功能边界，不从旧 layer-based L2 卡片继承任务边界。

