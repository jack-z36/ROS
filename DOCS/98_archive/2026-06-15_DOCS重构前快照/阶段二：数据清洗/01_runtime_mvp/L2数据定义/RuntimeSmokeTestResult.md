# RuntimeSmokeTestResult

## 定义

`RuntimeSmokeTestResult` 是单个 Runtime smoke test 用例执行后的结构化结果摘要。

## 所属位置

阶段二：数据清洗 / `runtime_mvp` / [[10_Runtime smoke test模块]]

## 现实语义

它表示某个 [[RuntimeSmokeTestCase]] 是否按预期通过，并记录最终 [[PipelineResult]]、关键 [[RunArtifactPath]]、失败 [[RuntimeErrorRef]] 和验收断言结果。它服务于 Runtime MVP 验收和后续任务交接。

## 字段或取值

| 字段 | 含义 |
| --- | --- |
| `case_id` | 对应 [[RuntimeSmokeTestCase]].`case_id`。 |
| `status` | 用例执行状态，建议复用 [[RunStatus]] 或测试层等价状态。 |
| `pipeline_result` | 本用例触发的 [[PipelineResult]] 摘要。 |
| `run_directory` | 本用例产生的 [[RunDirectory]]。 |
| `observed_artifacts` | 实际观察到的 [[RunArtifactPath]] 列表或映射。 |
| `observed_error` | 失败时的 [[RuntimeErrorRef]]。 |
| `assertions` | 断言名称、期望、实际和通过状态。 |
| `duration_ms` | 用例耗时。 |

## 有效性规则

- `case_id` 必须能反查到一个 [[RuntimeSmokeTestCase]]。
- 成功结果必须至少能定位本次 [[RunDirectory]] 和 [[PipelineResult]]。
- 失败结果必须带有 [[RuntimeErrorRef]] 或说明未能生成错误引用的原因。
- `assertions` 不得只写“完成”，必须说明可观察检查点。

## 上游来源

- Runtime smoke test 执行器或等价测试代码生成本结果。
- 结果字段复用 [[PipelineResult]]、[[RunDirectory]]、[[RunArtifactPath]] 和 [[RuntimeErrorRef]]。

## 下游消费者

- 开发者查看 Runtime MVP 验收状态。
- 阶段二执行记录引用本结果总结哪些 smoke test 已通过。
- 后续真实 Service 接入前可复用 suite 作为回归基线。

## 不负责

- 不保存完整日志正文。
- 不保存真实数据产物内容。
- 不定义日志、manifest 或错误摘要文件的完整 schema。

## 相关链接

- [[RuntimeSmokeTestCase]]
- [[RuntimeSmokeTestSuite]]
- [[10_Runtime smoke test模块]]
