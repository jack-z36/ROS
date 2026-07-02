# PipelineResult

## 定义

`PipelineResult` 是 Runtime 单场景或全流程结束后的最终结果摘要。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`PipelineResult` 表示“这次 Runtime 运行最终是什么状态、哪些场景执行过、日志在哪里、manifest 或错误摘要在哪里”。它是 UI 结束反馈、run result 和后续验收的核心摘要。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_id` | string | 是 | 对应的 Runtime 运行 ID。 |
| `status` | [[RunStatus]] | 是 | 最终运行状态。 |
| `scene_results` | list of [[SceneResult]] | 是 | 已执行场景结果。 |
| `run_dir` | path | 是 | 本次运行记录目录。 |
| `run_log_path` | path | 是 | 结构化日志路径。 |
| `manifest_path` | path 或空 | 否 | 成功时的 manifest 路径。 |
| `error_summary_path` | path 或空 | 否 | 失败时的错误摘要路径。 |

## 有效性规则

- `run_id` 必须能对应到 [[RunContext]]。
- `scene_results` 至少包含已经执行过的场景结果。
- 成功时必须能定位 `run_log_path`，并应能定位 `manifest_path`。
- 失败时必须能定位 `error_summary_path` 或在某个 [[SceneResult]] 中找到 [[RuntimeErrorRef]]。

## 上游来源

- Runtime 在单场景或全流程结束时汇总 [[RunContext]] 和 [[SceneResult]] 生成。

## 下游消费者

- UI 结束反馈。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。
- 后续 L3 验收任务。

## 不负责

- 不保存完整 run log。
- 不保存完整 manifest。
- 不替代错误摘要文件。
- 不负责定义真实数据产物契约。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要 `partial_success` 对应的结果语义 | 影响真实全流程的失败恢复和继续执行。 | Runtime MVP 第一版不引入。 | 真实 Service 全流程接入前确认。 |

## 相关链接

- [[RunContext]]
- [[SceneResult]]
- [[RunStatus]]
- [[RuntimeErrorRef]]
- [[01_Runtime运行上下文定义]]

