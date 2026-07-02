---
tags:
  - 附件
---

# InferenceWorker (推理后台线程)

> [!abstract]
> 一个 daemon 线程：以 `inference_hz` 频率从 `inference_request_queue` 拉最新请求、调 `policy.predict_action_chunk(observation)`、把结果 `ActionChunk` 推入 `chunk_result_queue`，全程不打 ROS 时钟。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `InferenceWorker(threading.Thread)` |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/inference_worker.py:15-91` |
| 启动 | `pi05_vla_deploy_node.py:89` (`self.inference_worker.start()`) |
| 关闭 | `pi05_vla_deploy_node.py:97-98` (`stop()` + `join(timeout=2.0)`) |
| 现实含义 | 模型推理通常 50-200ms，远长于 control 30Hz，**必须异步**才能保持控制节奏 |

## 线程循环（`run`）

```text
while not _stop_event.is_set():
    request = request_queue.get_latest_or_none()    # 拉最新，无则 None
    if request is None:
        _stop_event.wait(0.001)                       # 1ms 短等
        continue

    # 节流：保证两次推理间隔 >= 1/inference_hz
    remaining = period_s - (now - _last_infer_start_s)
    if remaining > 0.0:
        _stop_event.wait(remaining)                   # 长等直到 period 满

    _run_request(request)                             # 调模型 + 推结果
```

## `_run_request` 步骤

1. `infer_start = time.monotonic()`
2. 调 `policy_runtime.predict_action_chunk(request.observation)`，异常 → `record_inference_error` + 返回
3. 构造 `ActionChunk(actions, obs_time, infer_start_time, ready_time, action_dt, request_id)`
4. 算 `latency_s = ready_time - infer_start`
5. `record_inference_latency(latency_s)` + `record_chunk_result()` + `result_queue.put_latest(chunk)`

## 关键设计决策

- **`_stop_event.wait` 替代 sleep**：可被 `stop()` 立即唤醒，shutdown 延迟 < period
- **不调 ROS 时钟**：所有时间是 `time.monotonic()`，避免 ROS spin 抢线程
- **异常吞咽 + 计数**：模型崩溃不能拖垮整节点，错误计入 `inference_error_count` + `last_error`
- **`predict_action_chunk` 一次性输出 30 步**：避免每步都跑模型，符合 Pi0.5/ACT 的 chunked 输出

## 关键约束

- **daemon=True**：节点退出时主线程不会等这个 worker，shutdown 必须显式 `join(timeout=2.0)`
- **`period_s` 来自 `inference_hz`**：是 1/Hz，不是 1/control_hz
- **动作 dt 来自 `control_hz`**：30Hz → action_dt = 1/30 ≈ 0.033s
- **LatestQueue 容量=1**：旧请求自动被新请求覆盖，不会堆积
- 与 [[SharedBuffer 线程安全桥接]]、[[ActionChunk 动作块 dataclass]]、[[ControlLoop 控制循环驱动]] 紧密配合
