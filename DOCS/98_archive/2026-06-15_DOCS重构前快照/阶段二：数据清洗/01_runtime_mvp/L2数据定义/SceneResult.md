# SceneResult

## 定义

`SceneResult` 是单个阶段二场景执行后的最小结果摘要。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`SceneResult` 表示“某一个场景这次跑完了吗、用了哪些输入、生成了哪些输出、失败时错在哪里”。它是 [[PipelineResult]] 的组成单元。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 是 | 本结果对应的场景。 |
| `status` | [[RunStatus]] | 是 | 该场景执行状态。 |
| `input_paths` | map | 是 | 该场景实际消费的输入路径。 |
| `output_paths` | map | 是 | 该场景实际生成或声明的输出路径。 |
| `started_at` | datetime | 是 | 场景开始时间。 |
| `finished_at` | datetime 或空 | 否 | 场景结束时间。 |
| `duration_ms` | integer 或空 | 否 | 场景耗时。 |
| `error` | [[RuntimeErrorRef]] 或空 | 否 | 失败时的结构化错误引用。 |

## 有效性规则

- `scene_name` 必须是 [[SceneName]] 中的受控取值。
- 成功时 `output_paths` 必须记录该场景声明的输出。
- 失败时 `error` 必须存在，并能定位到失败步骤。
- `status` 为结束状态时，必须能得到 `finished_at` 或等价结束时间。

## 上游来源

- 场景注册与 Service 调度模块在每个场景执行后生成。
- fake service 或真实 Service 返回的结果会被 Runtime 汇总进 `SceneResult`。

## 下游消费者

- [[PipelineResult]]
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。
- UI 结束反馈。

## 不负责

- 不保存完整业务报告内容。
- 不替代场景生成的真实数据产物或报告。
- 不描述 Service 内部算法步骤。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要在 `SceneResult` 中区分调试输出和正式输出 | 影响 run 目录与正式产物目录的追溯。 | 第一版先用 `output_paths` 记录语义化路径。 | Run 目录管理模块设计时确认。 |

## 相关链接

- [[RunContext]]
- [[SceneName]]
- [[RunStatus]]
- [[PipelineResult]]
- [[RuntimeErrorRef]]
- [[01_Runtime运行上下文定义]]

