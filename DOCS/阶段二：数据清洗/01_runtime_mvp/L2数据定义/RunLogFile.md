# RunLogFile

## 定义

`RunLogFile` 是 Runtime 每次运行写出的结构化日志文件，默认文件名为 `run_log.json`。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[08_结构化日志模块]]

## 现实语义

`RunLogFile` 表示“这次 Runtime 运行从开始到结束发生了什么”。它面向人工排错、后续验收和错误摘要定位，记录输入、配置、步骤、调度事件、Service 结果、输出路径、耗时、状态和错误引用。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行标识。 |
| `run_dir` | path | 是 | 对应 [[RunDirectory]] 的运行目录。 |
| `started_at` | datetime 或空 | 否 | Runtime 开始时间。 |
| `finished_at` | datetime 或空 | 否 | Runtime 结束时间。 |
| `status` | [[RunStatus]] | 是 | 本次运行最终或当前状态。 |
| `target_scenes` | list of [[SceneName]] | 是 | 本次目标场景列表。 |
| `config_snapshot_path` | path 或空 | 否 | 本次配置快照路径。 |
| `events` | list of [[RuntimeLogEvent]] | 是 | 按发生顺序记录的结构化日志事件。 |
| `scene_results` | list of [[SceneResult]] | 否 | 已执行场景结果摘要。 |
| `pipeline_result` | [[PipelineResult]] 或空 | 否 | 运行结束后的最终结果摘要。 |
| `errors` | list of [[RuntimeErrorRef]] | 否 | 本次运行出现的结构化错误引用。 |

## 有效性规则

- `run_id` 必须与 [[RunContext]].`run_id` 一致。
- 文件路径必须来自 [[RunDirectoryLayout]].`run_log_path`，不得写到 run 目录外。
- `events` 必须按发生顺序保存，不能只保存最后一个事件。
- 失败运行必须至少能在 `events`、`scene_results` 或 `errors` 中定位 [[RuntimeErrorRef]]。
- `RunLogFile` 必须是机器可读 JSON，不得写成纯文本日志。

## 上游来源

- [[RunContext]] 提供运行身份、目标场景、run 目录、配置快照和运行状态。
- [[RuntimeStepRecord]] 提供 Runtime 主干步骤记录。
- [[SceneDispatchEvent]] 提供调度过程事件。
- [[SceneResult]] 和 [[PipelineResult]] 提供场景与最终结果。
- [[RuntimeErrorRef]] 提供失败定位。

## 下游消费者

- Manifest 与错误摘要模块。
- Runtime smoke test 模块。
- 人工排错和后续 L3 验收。

## 不负责

- 不替代 `processing_manifest.json`。
- 不替代 `error_summary.json`。
- 不保存完整业务数据或 MCAP 内容。
- 不决定 Runtime 是否继续执行。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `run_log.json` 是否采用追加写还是结束时一次性写 | 影响异常中断时日志完整性。 | L2 只固定内容契约；L3 实现时优先设计为可在失败路径落盘。 | 功能8 L3 执行时确认。 |

## 相关链接

- [[RuntimeLogEvent]]
- [[RuntimeLogWriteResult]]
- [[RunContext]]
- [[RunDirectory]]
- [[RunDirectoryLayout]]
- [[RuntimeStepRecord]]
- [[SceneDispatchEvent]]
- [[08_结构化日志模块]]
