# RuntimeLogEvent

## 定义

`RuntimeLogEvent` 是写入 [[RunLogFile]] 的单条结构化日志事件。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[08_结构化日志模块]]

## 现实语义

`RuntimeLogEvent` 表示“Runtime 在某个时刻发生的一件可追溯事情”。它可以由 [[RuntimeStepRecord]]、[[SceneDispatchEvent]]、[[SceneResult]]、[[PipelineResult]] 或 [[RuntimeErrorRef]] 转换而来，用统一格式进入 `run_log.json`。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `event_id` | string | 是 | 单次 run 内唯一的事件标识。 |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行标识。 |
| `event_type` | string | 是 | 事件类型，例如 `runtime_step`、`dispatch_event`、`scene_result`、`pipeline_result`、`error`。 |
| `step_name` | string 或空 | 否 | Runtime 步骤名称。 |
| `scene_name` | [[SceneName]] 或空 | 否 | 场景相关事件对应的场景。 |
| `status` | [[RunStatus]] | 是 | 事件发生后的状态。 |
| `message` | string | 否 | 人类可读短说明。 |
| `details` | map | 否 | 机器可读补充信息。 |
| `error` | [[RuntimeErrorRef]] 或空 | 否 | 失败事件对应的错误引用。 |
| `created_at` | datetime | 是 | 事件时间。 |

## 有效性规则

- `event_id` 在单个 [[RunLogFile]] 内必须唯一。
- `event_type` 必须来自受控集合，不能随意写自然语言句子。
- `status` 必须使用 [[RunStatus]]。
- 场景相关事件应填写 `scene_name`。
- 失败事件必须能关联 [[RuntimeErrorRef]]。
- `details` 只能存放可序列化摘要，不能保存完整业务数据或大文件内容。

## 上游来源

- [[RuntimeStepRecord]] 转换为 `runtime_step` 事件。
- [[SceneDispatchEvent]] 转换为 `dispatch_event` 事件。
- [[SceneResult]] 转换为 `scene_result` 事件。
- [[PipelineResult]] 转换为 `pipeline_result` 事件。
- [[RuntimeErrorRef]] 转换为 `error` 事件或嵌入失败事件。

## 下游消费者

- [[RunLogFile]]。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不保存完整 traceback。
- 不替代 [[RuntimeStepRecord]] 或 [[SceneDispatchEvent]] 的来源语义。
- 不负责文件写入策略。
- 不表达真实数据产物 schema。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `event_type` 是否需要在代码层做枚举 | 影响测试断言和后续错误摘要筛选。 | L2 先固定受控集合语义；L3 数据定义任务中收敛。 | `runtime_mvp_023` 执行时确认。 |

## 相关链接

- [[RunLogFile]]
- [[RuntimeStepRecord]]
- [[SceneDispatchEvent]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RuntimeErrorRef]]
- [[08_结构化日志模块]]
