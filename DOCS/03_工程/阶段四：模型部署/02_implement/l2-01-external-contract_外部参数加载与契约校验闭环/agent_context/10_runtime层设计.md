# runtime 层设计：L2-01

## 1. 本 L2 不在该层新增源码产物

原因：

- `runtime/` 层负责时间、线程、队列、状态机、调度。
- L2-01 只在程序启动阶段被同步调用一次。
- L2-01 不创建 timer、thread、queue、state machine，不维护 active chunk 或 cursor。

## 2. L2-01 提供给 runtime 的静态配置

L2-01 可以通过 `RuntimeConfig` 提供：

```text
control_hz
inference_hz
chunk_size
mode
fallback_policy
max_action_age_sec
```

这些字段只支持第一版 ControlLoop 的最小 cursor 直取模型：收集 ActionChunk、维护 active chunk、按 tick 取当前 step、不可用时 fallback。

## 3. 明确不提供的 runtime 平滑能力

L2-01 不提供：

```text
blend_steps
smoothstep_window
cross_chunk_fusion
rtc_alignment
action_smoothing_state
chunk_smoother_state
```

这些能力不属于第一版 L2 Gate。未来若增加，必须新增设计与验收。

## 4. 验收如何确认

- L2-01 不产生 `src/model_deploy/act/runtime/*.py` 产物。
- `RuntimeConfig` 中不存在平滑/融合/RTC 对齐字段。
- L2-06 文档负责解释 active chunk / cursor 的运行时状态。

## 5. 边界继承声明

本文件边界来自当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。
