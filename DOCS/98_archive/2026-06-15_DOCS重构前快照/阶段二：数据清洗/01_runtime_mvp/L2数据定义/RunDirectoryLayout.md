# RunDirectoryLayout

## 定义

`RunDirectoryLayout` 是一次 Runtime 运行目录内部固定路径的语义集合。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[02_Run目录管理模块]]

## 现实语义

`RunDirectoryLayout` 表示“run 目录里哪些位置留给哪些后续模块使用”。它让配置快照、日志、manifest、错误摘要、结果索引和调试输出拥有统一落点。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_log_path` | [[RunArtifactPath]] | 是 | 结构化日志预期路径：`run_log.json`。 |
| `config_snapshot_path` | [[RunArtifactPath]] | 是 | 配置快照预期路径：`config_snapshot.yaml`。 |
| `processing_manifest_path` | [[RunArtifactPath]] | 是 | manifest 预期路径：`processing_manifest.json`。 |
| `error_summary_path` | [[RunArtifactPath]] | 是 | 错误摘要预期路径：`error_summary.json`。 |
| `run_result_path` | [[RunArtifactPath]] | 是 | 运行结果索引预期路径：`run_result.json`。 |
| `outputs_dir` | [[RunArtifactPath]] | 是 | 调试产物目录：`outputs/`。 |

## 有效性规则

- 所有路径必须位于同一个 [[RunDirectory]] 下。
- `outputs_dir` 必须在 Run 目录管理阶段创建。
- 其他文件路径由 Run 目录管理模块声明，但内容由后续模块写入。
- 不得把真实数据产物路径登记为 `outputs_dir`。

## 上游来源

- Run 目录管理模块在创建 [[RunDirectory]] 时派生本布局。

## 下游消费者

- 配置加载与配置快照模块写入 `config_snapshot.yaml`。
- 结构化日志模块写入 `run_log.json`。
- Manifest 与错误摘要模块写入 `processing_manifest.json`、`error_summary.json` 和 `run_result.json`。
- Fake Service 模块可把调试输出写入 `outputs/`。

## 不负责

- 不定义每个文件内部 schema。
- 不决定后续模块何时写入文件。
- 不表达 Service 真实数据产物目录。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `processing_manifest.json` 是否成功和失败路径都必须写 | 影响 Manifest 模块边界。 | 本布局只预留路径，不强制写入时机。 | Manifest 与错误摘要模块设计时确认。 |

## 相关链接

- [[RunDirectory]]
- [[RunArtifactPath]]
- [[RunContext]]
- [[02_Run目录管理模块]]
