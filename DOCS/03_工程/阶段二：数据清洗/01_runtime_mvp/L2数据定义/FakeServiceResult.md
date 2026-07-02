# FakeServiceResult

## 定义

`FakeServiceResult` 是 fake service 执行后的结果对象，用来表达假服务模拟出的场景执行状态、输出声明和错误引用。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[07_Fake Service模块]]

## 现实语义

`FakeServiceResult` 表示“fake service 这一步给 Runtime 返回了什么”。它会被场景注册与 Service 调度模块转换或汇总为 [[SceneResult]]。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 是 | 本结果对应的场景。 |
| `behavior` | [[FakeServiceBehavior]] | 是 | 本次采用的假服务行为。 |
| `status` | [[RunStatus]] | 是 | 本次假服务执行状态。 |
| `input_summary` | map 或空 | 否 | fake service 接收到的输入摘要。 |
| `output_paths` | map of [[RunArtifactPath]] | 是 | fake service 声明的输出路径。 |
| `error` | [[RuntimeErrorRef]] 或空 | 否 | 失败时的结构化错误引用。 |
| `started_at` | datetime | 是 | fake service 开始时间。 |
| `finished_at` | datetime | 是 | fake service 结束时间。 |
| `duration_ms` | integer | 是 | fake service 耗时。 |

## 有效性规则

- `scene_name` 必须与 [[FakeServicePlan]] 一致。
- `status` 成功时 `error` 必须为空。
- `status` 失败时 `error` 必须存在，并且 `error.scene_name` 应指向同一 [[SceneName]]。
- `output_paths` 只代表 fake service 声明或占位输出，不代表真实业务产物已生成。
- `finished_at` 不得早于 `started_at`。

## 上游来源

- Fake Service 模块根据 [[FakeServicePlan]] 生成。

## 下游消费者

- 场景注册与 Service 调度模块将其转为或合并进 [[SceneResult]]。
- 结构化日志模块记录 fake service 执行事件。
- Manifest 与错误摘要模块消费成功输出或失败 [[RuntimeErrorRef]]。
- Runtime smoke test 模块断言成功和失败路径。

## 不负责

- 不保存完整业务报告。
- 不证明真实 Service 算法可用。
- 不替代 [[SceneResult]] 的 Runtime 汇总职责。
- 不写入 `run_log.json`、`processing_manifest.json` 或 `error_summary.json`。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| [[FakeServiceResult]] 与 [[SceneResult]] 是否最终合并为同一个代码类型 | 影响实现时是否新增独立 dataclass。 | L2 先保持语义分离，L3 可根据现有代码选择复用或适配。 | 执行功能7 L3 时结合代码确认。 |

## 相关链接

- [[07_Fake Service模块]]
- [[FakeServicePlan]]
- [[FakeServiceBehavior]]
- [[SceneResult]]
- [[RunStatus]]
- [[SceneName]]
- [[RunArtifactPath]]
- [[RuntimeErrorRef]]
