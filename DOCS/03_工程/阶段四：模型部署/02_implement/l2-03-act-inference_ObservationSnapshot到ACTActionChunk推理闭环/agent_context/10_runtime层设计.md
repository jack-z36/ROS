# runtime 层设计：L2-03

## 1. 本 L2 不在该层新增源码产物

`runtime/` 负责时间、线程、queue、持续循环、运行状态和失败策略。L2-03 是一次性的同步 service，不新增 runtime 文件。

## 2. L2-06 与 L2-03 的调用边界

```text
L2-06:
  1. 接收 L2-01 的四项启动资源。
  2. 创建并持有 ActInferenceService。
  3. 在自己的 worker/运行轴中决定何时调用 service 总入口。
  4. 为调用建立 request/time/error/latency 记录。
  5. 接收 ActionChunk，维护 active chunk/cursor。

L2-03:
  1. 接收一次 ObservationSnapshot。
  2. 同步返回 ActionChunk 或抛异常。
  3. 不知道 request、时间、队列或后续消费状态。
```

## 3. 明确归 L2-06 的运行对象

```text
worker/thread/timer
latest observation buffer
request/in-flight/result records
latest-only queues
request_id, timestamps, latency, metrics
active ActionChunk, cursor, selected raw step
fallback/stop/retry policy
ROS status/metrics publication
```

`ActionChunk` 虽由 L2-03 创建，但 L2-06 接收后可把它放进自己的 result record；运行元数据不能写回 L2-03 type。

## 4. 并发约束

L2-03 不创建 lock，也不承诺同一 policy 实例可被并发调用。L2-06 应默认把同一个 `ActInferenceService` 的前向调用串行化；若后续需要多 policy 并发，必须由 L2-06 新设计资源所有权和隔离方式。

## 5. 验收

- L2-03 不新增 `src/model_deploy/act/runtime/*.py`。
- service/types 中无 `Thread`、queue、timer、event、cursor、metrics、fallback 实现。
- `ActionChunk` 只有 actions。
- 集成测试证明 L2-03 异常向调用方传播，而不是在 L2-03 内转成 runtime 状态。

## 6. 边界声明

Pi0.5 `InferenceWorker`、`LatestQueue`、`SharedBuffer` 和 `RuntimeMetrics` 是参考源码中的 runtime 实现，不是当前 L2-03 可复用产物。
