# RunResultIndex

## 定义

`RunResultIndex` 是 Runtime 每次运行结束时写入 `run_result.json` 的结果索引。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[09_Manifest与错误摘要模块]]

## 现实语义

`RunResultIndex` 表示“这次运行结束后，用户和后续模块应该去哪里看结果”。它把 [[PipelineResult]] 中的关键路径固化到 run 目录下，统一指向 `run_log.json`、`processing_manifest.json` 或 `error_summary.json`。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | string | 是 | 结果索引结构版本，Runtime MVP 第一版可使用 `runtime_run_result.v1`。 |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行 ID。 |
| `status` | [[RunStatus]] | 是 | 本次运行最终状态。 |
| `run_dir` | [[RunDirectory]] | 是 | 本次运行记录目录。 |
| `run_log_path` | [[RunArtifactPath]] | 是 | 结构化日志路径。 |
| `manifest_path` | [[RunArtifactPath]] 或空 | 否 | 成功时指向 [[ProcessingManifest]] 文件。 |
| `error_summary_path` | [[RunArtifactPath]] 或空 | 否 | 失败时指向 [[ErrorSummary]] 文件。 |
| `scene_results` | list of [[SceneResult]] | 是 | 已执行场景摘要。 |
| `created_at` | datetime | 是 | 结果索引写入时间。 |

## 有效性规则

- `run_id` 必须和 [[PipelineResult]].`run_id` 一致。
- 成功时必须填写 `manifest_path`，且 `error_summary_path` 应为空。
- 失败时必须填写 `error_summary_path`，`manifest_path` 可为空。
- `run_log_path` 必须始终填写。
- 所有路径必须位于本次 [[RunDirectory]] 下。

## 上游来源

- [[PipelineResult]] 提供最终状态、场景结果和关键路径。
- [[ProcessingManifest]] 或 [[ErrorSummary]] 的写入结果提供对应路径。
- [[RunDirectoryLayout]] 提供 `run_result.json` 的目标路径。

## 下游消费者

- Runtime smoke test 模块。
- UI 或入口脚本结束反馈。
- 后续 Agent 快速判断本次运行产物。

## 不负责

- 不保存完整 manifest 或错误摘要内容。
- 不表达真实业务产物 schema。
- 不判断数据是否可训练。
- 不替代 [[PipelineResult]] 的内存态结果。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否允许失败运行同时拥有 manifest 和 error summary | 影响索引字段互斥规则。 | Runtime MVP 第一版按成功/失败二选一处理。 | 真实 Service 全流程接入前确认。 |

## 相关链接

- [[RunContext]]
- [[RunDirectory]]
- [[RunDirectoryLayout]]
- [[RunArtifactPath]]
- [[PipelineResult]]
- [[ProcessingManifest]]
- [[ErrorSummary]]
- [[09_Manifest与错误摘要模块]]
