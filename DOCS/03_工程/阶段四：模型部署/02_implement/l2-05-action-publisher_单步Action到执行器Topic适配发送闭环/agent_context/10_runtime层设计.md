# runtime 层设计：L2-05

> [!info] 元信息
> - 消费对象：L3 生成、L2-06 协作与边界验收 Agent。
> - 权威性：确认 L2-05 不拥有 runtime 产物。
> - 上游来源：L2-06 拥有 tick、时间、许可、fallback 和全局状态。
> - 不负责范围：不创建 timer/thread/queue/state machine。
> - 读取时机：任何人提议在 L2-05 增加 runtime 文件时。

## 1. 结论

本 L2 不在该层新增源码产物。

原因：

- L2-05 是被 L2-06 同步调用的输出端口。
- action_id、ROS/单调时间、`CommandPermit`、调用时机、fallback、retry、全局 metrics 均由 L2-06 拥有。
- CLI 在启动装配中形成 C7；L2-05 不运行独立 CLI/timer 状态机。
- 夹爪 cache 是 A1 publisher-local 输出协议状态，不构成 runtime 调度器。

验收如何确认：

- L2-05 不修改 `src/model_deploy/act/runtime/`。
- A1/B1/B2/B3 不创建 timer、thread、queue 或自增 action ID。
- publish 失败只返回 C6，不自行 retry/hold/shutdown。
- L2-06 可用 mock port 同步调用 B3 并消费 result。

## 2. L2-05 与 L2-06 RAM 接口

```text
L2-06 owns:
  action_id
  ros_time_s + monotonic_s
  raw gate/deadman/estop/driver readiness
  C1 CommandPermit final decision
  fallback/retry/global metrics

L2-05 owns:
  B3 publish(request) -> C6 ActionPublishResult
  publisher handles
  gripper deadband cache
  last local result
```

L2-06 只能调用 B3；不得分别调用 B1/B2，否则会把 L2-05 内部实现泄漏进 ControlLoop。

## 3. class / function / 输入输出

```text
本层无 class。
本层无函数。
本层不创建新的数据微元。
本层无外部副作用。
```

## 4. 依赖关系

L2-05 ui 不反向 import runtime。L2-06 通过 types 中的 C1/C2/C6 与 L2-05 协作，不依赖 service/ui 私有类型 C8。

## 5. Pi0.5 参考

- Pi0.5 `ControlLoop` 的 chunk/cursor/fallback/blend 属 L2-06，不迁入 L2-05。
- CommandMux timer/mode/timeout 属 L2-06/driver 参考，不迁入 L2-05。
- 旧 bridge 自建 deadman timer 的模式明确不复用。

## 6. 验收覆盖

- static no-artifact scan。
- 禁止 runtime import、timer/thread/queue/retry。
- mock L2-06 只通过 `ActionPublisher.publish(request)` 协作。
- C6 能完整表达 OBSERVED/BLOCKED/PARTIAL/FAILED 供 L2-06 决策。

## 7. 边界继承声明

本结论继承当前 L1/L2 功能边界，不从旧 layer-based runtime 卡片推导。无 runtime 产物是中央调度所有权的直接结果。
