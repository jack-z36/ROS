# FakeServicePlan

## 定义

`FakeServicePlan` 是 fake service 执行前的计划对象，用来描述本次假服务要模拟哪个场景、采用成功还是失败行为、声明哪些假输出。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[07_Fake Service模块]]

## 现实语义

`FakeServicePlan` 表示“为了验证 Runtime 空流程，这次 fake service 应该怎样返回”。它让 fake service 的行为可控、可测试，并与真实 Service 算法结果保持边界。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 是 | 本次要模拟的阶段二场景。 |
| `service_mode` | [[ServiceMode]] | 是 | 必须为 `fake`。 |
| `behavior` | [[FakeServiceBehavior]] | 是 | 本次 fake service 的成功或失败行为。 |
| `input_summary` | map 或空 | 否 | 从 [[InputArtifactPrecheckSummary]] 提取的输入摘要，不保存完整文件内容。 |
| `declared_outputs` | map of [[RunArtifactPath]] | 是 | fake service 声明会生成或占位的输出路径。 |
| `message` | string | 否 | 面向日志和 smoke test 的简短说明。 |

## 有效性规则

- `scene_name` 必须是 [[SceneName]] 的受控取值。
- `service_mode` 必须为 `fake`，不得混用真实 Service。
- `behavior` 必须来自 [[FakeServiceBehavior]]。
- `declared_outputs` 只能指向本次 [[RunDirectory]] 或其允许的调试输出位置，不得写入真实阶段二产物目录。
- 失败行为必须能生成可追溯的 [[RuntimeErrorRef]]。

## 上游来源

- 场景注册与 Service 调度模块根据 [[RunContext]]、[[SceneName]] 和 [[InputArtifactPrecheckSummary]] 生成或传入。
- Runtime smoke test 模块可以构造特定 `behavior` 来验证成功和失败路径。

## 下游消费者

- Fake Service 模块。
- [[FakeServiceResult]]。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不表达真实业务算法参数。
- 不读取或验证 MCAP、Parquet、JSON schema 的业务内容。
- 不替代真实 Service 的输入输出契约。
- 不决定全流程调度顺序。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `declared_outputs` 是否必须实际落盘占位文件 | 影响 fake service 是否需要执行文件写入。 | 第一版允许只声明路径；如 L3 需要验证文件存在，可再拆出输出占位写入任务。 | 生成或执行功能7 L3 前确认。 |

## 相关链接

- [[07_Fake Service模块]]
- [[FakeServiceBehavior]]
- [[FakeServiceResult]]
- [[RunContext]]
- [[SceneName]]
- [[ServiceMode]]
- [[InputArtifactPrecheckSummary]]
- [[RunArtifactPath]]
- [[RunDirectory]]
- [[RuntimeErrorRef]]
