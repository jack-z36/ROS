# ErrorSummary

## 定义

`ErrorSummary` 是 Runtime 失败时写入 `error_summary.json` 的结构化失败摘要。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[09_Manifest与错误摘要模块]]

## 现实语义

`ErrorSummary` 表示“这次运行失败在哪里、为什么失败、应该先看什么”。它把 [[RuntimeErrorRef]]、失败场景、失败步骤、已执行结果和相关日志路径组织成一个小而稳定的文件，方便用户和后续 Agent 快速定位问题。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | string | 是 | 错误摘要文件结构版本，Runtime MVP 第一版可使用 `runtime_error_summary.v1`。 |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行 ID。 |
| `status` | [[RunStatus]] | 是 | 最终失败状态。 |
| `failed_scene` | [[SceneName]] 或空 | 否 | 失败所属场景；全局步骤失败可为空。 |
| `failed_step` | string | 是 | 失败步骤名。 |
| `error` | [[RuntimeErrorRef]] | 是 | 结构化错误引用。 |
| `run_log_path` | [[RunArtifactPath]] | 是 | 对应结构化日志路径。 |
| `config_snapshot_path` | [[RunArtifactPath]] 或空 | 否 | 如果已生成配置快照，则记录路径。 |
| `scene_results` | list of [[SceneResult]] | 否 | 失败前已经产生的场景结果。 |
| `message` | string | 是 | 一行人类可读失败摘要。 |
| `suggested_next_action` | string | 否 | 下一步排查建议。 |
| `created_at` | datetime | 是 | 错误摘要写入时间。 |

## 有效性规则

- `error` 必须包含非空 `error_code`、`step_name` 和 `message`。
- `failed_step` 必须和 [[RuntimeErrorRef]].`step_name` 一致，或能解释为 Runtime 包装步骤。
- 失败发生在场景内时，`failed_scene` 必须填写。
- `run_log_path` 必须指向本次 [[RunDirectory]] 下的日志路径；如果 [[RuntimeLogWriteResult]] 表示日志写入失败，错误摘要仍应保留预期日志路径和日志写入错误。
- `message` 不能只写“运行失败”，必须包含可定位失败原因。

## 上游来源

- [[RuntimeErrorRef]] 提供失败定位。
- [[RunContext]] 提供运行身份和目标场景。
- [[SceneResult]] 或 [[PipelineResult]] 提供已执行结果。
- [[08_结构化日志模块]] 提供 [[RunLogFile]]、[[RuntimeLogWriteResult]]、`run_log.json` 路径和日志记录。

## 下游消费者

- [[RunResultIndex]]
- Runtime smoke test 模块。
- UI 或入口脚本的失败反馈。
- 人工排错和后续 Agent 接手。

## 不负责

- 不保存完整 traceback。
- 不重试失败步骤。
- 不自动修复配置、输入或 service 失败。
- 不替代完整结构化日志。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要统一错误码表 | 影响 smoke test 的断言粒度和用户排错体验。 | 先复用 [[RuntimeErrorRef]].`error_code` 的可分类字符串。 | 功能9 L3 或功能10 smoke test 设计时确认。 |
| 失败时是否也写 `processing_manifest.json` | 影响失败运行的追溯文件数量。 | Runtime MVP 第一版定义为成功写 [[ProcessingManifest]]，失败写 [[ErrorSummary]]。 | 后续真实全流程需要更强失败追溯时确认。 |

## 相关链接

- [[RunContext]]
- [[RunDirectory]]
- [[RunArtifactPath]]
- [[RuntimeErrorRef]]
- [[RunLogFile]]
- [[RuntimeLogWriteResult]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RunStatus]]
- [[09_Manifest与错误摘要模块]]
