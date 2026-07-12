# runtime 层设计：L2-05

> [!info] 元信息
> - 消费对象：L3 生成、L2-06 协作与边界验收 Agent。
> - 权威性：本文确认 L2-05 不拥有 runtime 产物。
> - 上游来源：L2-06 拥有时间、tick、授权、fallback 和全局状态。
> - 不负责范围：不创建 timer/thread/queue/state machine。
> - 读取时机：任何人提议在 L2-05 增加 runtime 文件时。
> - 冲突处理：runtime 需求必须移回 L2-06 或重新确认 L1 边界。

## 1. 结论

本 L2 不在该层新增源码产物。

原因：L2-05 是被 L2-06 同步调用的输出边界。action_id、ROS/单调时间、最终发布授权、调用时机、fallback、重试、全局 metrics、shutdown 顺序均由 L2-06 拥有。L2-05 只持有设备防刷所需的最小 publisher-local 状态，该状态随 UI publisher 生命周期存在，不构成 runtime 调度器。

验收如何确认：

- L2-05 不修改 `src/model_deploy/act/runtime/`。
- `ActionPublisher` 不创建 timer、thread、queue 或自增 tick/action ID。
- publish 失败只返回结果，不自行 retry/hold/shutdown。
- L2-06 可用一个 mock port 调用 `publish(request)` 并消费结果。

## 2. L2-05 与 L2-06 接口

```text
L2-06 owns:
  action_id + ros_time_s + monotonic_s
  raw gate/deadman/estop/driver readiness
  PublishAuthorization final decision
  fallback/retry/global metrics

L2-05 owns:
  synchronous publish(request) -> ActionPublishResult
  publisher handles + gripper deadband cache + last local result
```

夹爪 deadband cache 位于 UI class，是输出协议最小状态；它不允许演变为通用 scheduler、retry queue 或 fallback state。

## 3. Pi0.5 参考

- Pi0.5 `ControlLoop`、CommandMux timer/mode/timeout 都是 L2-06/外部 driver 参考，不迁入 L2-05。
- 旧 bridge 自己创建 deadman timer 的模式明确不复用。

## 4. 边界继承声明

本结论继承当前功能边界，不从旧 layer-based runtime 卡片推导。无 runtime 产物是中央调度所有权的直接结果。
