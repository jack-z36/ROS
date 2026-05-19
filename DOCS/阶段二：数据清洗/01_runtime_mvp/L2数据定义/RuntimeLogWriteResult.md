# RuntimeLogWriteResult

## 定义

`RuntimeLogWriteResult` 是结构化日志模块写入 `run_log.json` 后返回的写入结果摘要。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[08_结构化日志模块]]

## 现实语义

`RuntimeLogWriteResult` 表示“这次日志文件是否成功写出、写到了哪里、写了多少事件、失败时错在哪里”。它让调度、manifest、错误摘要和 smoke test 能以结构化方式确认日志写入状态。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行标识。 |
| `run_log_path` | [[RunArtifactPath]] 或 path | 是 | 实际写出的日志文件路径。 |
| `status` | [[RunStatus]] | 是 | 日志写入状态。 |
| `event_count` | integer | 是 | 写入的 [[RuntimeLogEvent]] 数量。 |
| `written_at` | datetime 或空 | 否 | 写入完成时间。 |
| `error` | [[RuntimeErrorRef]] 或空 | 否 | 写入失败时的错误引用。 |

## 有效性规则

- `run_log_path` 必须位于 [[RunDirectory]] 下。
- 写入成功时 `event_count` 必须大于或等于 1。
- 写入失败时必须提供 [[RuntimeErrorRef]]。
- `status` 只表达日志写入状态，不得覆盖整个 [[PipelineResult]] 的最终状态。

## 上游来源

- 结构化日志模块根据 [[RunLogFile]] 写入结果生成。
- [[RunArtifactPath]] 或 [[RunDirectoryLayout]].`run_log_path` 提供写入目标。

## 下游消费者

- [[PipelineResult]] 的 `run_log_path` 字段。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不保存完整日志内容。
- 不替代 [[RunLogFile]]。
- 不判断业务场景是否成功。
- 不创建 run 目录。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 日志写入失败时是否还能继续写 error summary | 影响失败链路兜底策略。 | 交给功能9设计；功能8只返回写入失败错误引用。 | Manifest 与错误摘要模块设计时确认。 |

## 相关链接

- [[RunLogFile]]
- [[RuntimeLogEvent]]
- [[RunArtifactPath]]
- [[RunDirectory]]
- [[PipelineResult]]
- [[08_结构化日志模块]]
