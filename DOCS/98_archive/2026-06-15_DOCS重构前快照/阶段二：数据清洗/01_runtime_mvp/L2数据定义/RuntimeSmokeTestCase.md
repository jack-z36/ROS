# RuntimeSmokeTestCase

## 定义

`RuntimeSmokeTestCase` 是 Runtime MVP 中一个可独立执行的 smoke test 用例定义。

## 所属位置

阶段二：数据清洗 / `runtime_mvp` / [[10_Runtime smoke test模块]]

## 现实语义

它表示一次最小验收动作，例如单场景 fake run、fake 全流程、缺配置、缺输入或 fake service 可控失败。每个用例只验证一个 Runtime 端到端行为，不承载真实 Service 算法正确性。

## 字段或取值

| 字段 | 含义 |
| --- | --- |
| `case_id` | 用例稳定标识，例如 `single_scene_fake_success`。 |
| `title` | 人类可读用例名称。 |
| `target_scenes` | 本用例要运行的 [[SceneName]] 列表。 |
| `run_mode` | 本用例使用的 [[RunMode]]。 |
| `service_mode` | 本用例使用的 [[ServiceMode]]，Runtime MVP 第一版应为 fake。 |
| `config_setup` | 本用例对 [[EffectiveRuntimeConfig]] 或 [[ConfigSnapshot]] 的前置要求。 |
| `input_setup` | 本用例对 [[InputArtifactPrecheckSummary]] 的前置要求。 |
| `fake_service_setup` | 本用例对 [[FakeServicePlan]] 和 [[FakeServiceBehavior]] 的前置要求。 |
| `expected_status` | 期望最终 [[RunStatus]]。 |
| `expected_error_code` | 失败用例期望的 [[RuntimeErrorRef]] 错误码。 |
| `expected_artifacts` | 期望出现的 [[RunArtifactPath]] 或运行记录语义。 |

## 有效性规则

- `case_id` 必须稳定、唯一、可用于测试报告定位。
- `target_scenes` 必须非空，且只能引用已定义 [[SceneName]]。
- Runtime MVP 第一版的 `service_mode` 必须显式为 fake，不能默认误用真实 Service。
- 失败用例必须写明 `expected_error_code`。
- 成功用例不得要求真实 cleaned/validated/aligned/canonical/export 数据产物存在。

## 上游来源

- [[10_Runtime smoke test模块]] 首次定义本概念。
- 用例前置条件复用 [[RunContext]]、[[ConfigPrecheckResult]]、[[InputArtifactPrecheckSummary]]、[[SceneDispatchPlan]]、[[FakeServicePlan]] 和 [[FakeServiceResult]]。

## 下游消费者

- 后续 Runtime smoke test L3 任务会把本定义落成测试用例或等价测试数据。
- [[RuntimeSmokeTestSuite]] 聚合多个用例。
- [[RuntimeSmokeTestResult]] 记录每个用例执行后的结果。

## 不负责

- 不定义真实 Service 的业务输入输出。
- 不定义 `run_log.json`、`processing_manifest.json` 或 `error_summary.json` 的完整文件 schema。
- 不承担测试执行器的代码接口设计。

## 相关链接

- [[RuntimeSmokeTestSuite]]
- [[RuntimeSmokeTestResult]]
- [[10_Runtime smoke test模块]]
