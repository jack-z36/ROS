# ProcessingManifest

## 定义

`ProcessingManifest` 是 Runtime 成功结束时写入 `processing_manifest.json` 的运行追溯清单。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[09_Manifest与错误摘要模块]]

## 现实语义

`ProcessingManifest` 表示“这次运行为什么可以被复现和解释”。它不保存完整日志，而是记录本次运行身份、配置快照、目标场景、输入输出声明、执行结果和关键版本信息，供后续数据产物解释与排错使用。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | string | 是 | manifest 文件结构版本，Runtime MVP 第一版可使用 `runtime_manifest.v1`。 |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行 ID。 |
| `run_mode` | [[RunMode]] | 是 | 本次运行模式。 |
| `service_mode` | [[ServiceMode]] | 是 | fake 或真实 service 模式。 |
| `target_scenes` | list of [[SceneName]] | 是 | 本次请求执行的场景。 |
| `status` | [[RunStatus]] | 是 | 最终运行状态；本文件只在成功路径必须写出。 |
| `config_snapshot_path` | [[RunArtifactPath]] | 是 | 本次生效配置快照路径。 |
| `run_log_path` | [[RunArtifactPath]] | 是 | 对应结构化日志路径。 |
| `scene_results` | list of [[SceneResult]] | 是 | 已执行场景的结果摘要。 |
| `input_artifacts` | map | 否 | 本次运行使用的输入产物声明。 |
| `output_artifacts` | map | 否 | 本次运行生成或声明的输出产物。 |
| `created_at` | datetime | 是 | manifest 写入时间。 |
| `tool_versions` | map | 否 | Runtime、service、依赖库等版本信息。 |
| `metadata` | map | 否 | 额外追溯信息。 |

## 有效性规则

- `run_id` 必须能对应到同一次 [[RunContext]]。
- `status` 为成功时，`scene_results` 中不得包含失败 [[SceneResult]]。
- `config_snapshot_path` 和 `run_log_path` 必须位于本次 [[RunDirectory]] 下。
- `output_artifacts` 只能记录声明和索引，不替代真实产物本体。
- fake service 的输出必须明确保持 fake 语义，不得被解释为真实业务产物完成。

## 上游来源

- [[RunContext]] 提供运行身份、模式和目标场景。
- [[ConfigSnapshot]] 提供生效配置快照路径。
- [[SceneResult]] 和 [[PipelineResult]] 提供执行结果。
- [[08_结构化日志模块]] 提供 [[RunLogFile]]、[[RuntimeLogWriteResult]]、`run_log.json` 路径和日志完成状态。

## 下游消费者

- [[RunResultIndex]]
- Runtime smoke test 模块。
- 后续真实 Service 接入后的产物追溯。
- 人工排错和执行记录核对。

## 不负责

- 不保存完整 `run_log.json`。
- 不保存失败路径的完整错误摘要。
- 不替代业务场景输出的真实 report。
- 不定义 canonical dataset 的生产级 manifest。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否要求 manifest 校验完整日志内容 | 影响功能9是否读取完整 [[RunLogFile]]。 | 第一版只要求记录 [[RuntimeLogWriteResult]] 提供的日志路径和写入状态，不重新校验完整事件流。 | 功能9 L3 生成前确认。 |
| 是否需要记录 Git commit 或代码版本 | 影响长期复现能力。 | 第一版将其放入可选 `tool_versions` 或 `metadata`。 | Runtime smoke test 或真实 Service 接入前确认。 |

## 相关链接

- [[RunContext]]
- [[RunDirectory]]
- [[RunArtifactPath]]
- [[ConfigSnapshot]]
- [[RunLogFile]]
- [[RuntimeLogWriteResult]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RunStatus]]
- [[09_Manifest与错误摘要模块]]
