# SceneDispatchPlan

## 定义

`SceneDispatchPlan` 是 Runtime 在真正调用 service 前形成的场景执行计划。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[06_场景注册与Service调度模块]]

## 现实语义

`SceneDispatchPlan` 表示“本次 Runtime 要按什么顺序执行哪些场景、每个场景使用哪个 service 绑定、执行前必须满足哪些预检查结果”。它把用户选择的目标场景转换成可执行的调度顺序。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `run_id` | string | 是 | 对应 [[RunContext]] 的运行标识。 |
| `target_scenes` | list of [[SceneName]] | 是 | 本次计划执行的场景顺序。 |
| `bindings` | list of [[ServiceBinding]] | 是 | 每个目标场景对应的 service 绑定。 |
| `precheck_summaries` | map of [[SceneName]] to [[InputArtifactPrecheckSummary]] | 是 | 每个目标场景调度前的输入预检查结果。 |
| `stop_on_failure` | boolean | 是 | 单场景或全流程遇到失败时是否停止后续场景。 |
| `service_mode` | [[ServiceMode]] | 是 | 本计划调用 fake 还是真实 service。 |

## 有效性规则

- `target_scenes` 必须非空。
- `bindings` 必须覆盖 `target_scenes` 中的每个场景。
- 所有 `precheck_summaries` 必须为成功状态，计划才允许进入执行。
- 全流程模式下，`target_scenes` 默认顺序必须符合 [[SceneName]] 定义的阶段二顺序。
- `service_mode` 必须与 [[RunContext]] 和 [[ServiceRegistry]] 一致。

## 上游来源

- [[RunContext]] 提供目标场景、运行模式、运行 ID 和 [[ServiceMode]]。
- [[ServiceRegistry]] 提供每个场景的 [[ServiceBinding]]。
- 输入产物预检查模块提供 [[InputArtifactPrecheckSummary]]。

## 下游消费者

- [[06_场景注册与Service调度模块]]
- 结构化日志模块。
- Runtime smoke test 模块。

## 不负责

- 不执行 service。
- 不保存完整运行日志。
- 不定义 fake service 的内部行为。
- 不负责从配置中解析输入路径。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 全流程遇到单个场景失败后是否允许 partial success | 影响 `stop_on_failure` 默认值。 | Runtime MVP 第一版默认失败即停止，不引入 partial success。 | 真实全流程接入前确认。 |

## 相关链接

- [[RunContext]]
- [[ServiceRegistry]]
- [[ServiceBinding]]
- [[InputArtifactPrecheckSummary]]
- [[SceneResult]]
- [[PipelineResult]]
- [[06_场景注册与Service调度模块]]
