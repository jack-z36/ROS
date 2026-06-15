# FakeServiceBehavior

## 定义

`FakeServiceBehavior` 是 fake service 的受控行为枚举，用来指定假服务返回成功、可控失败或占位跳过。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[07_Fake Service模块]]

## 现实语义

`FakeServiceBehavior` 回答“这次 fake service 要模拟哪一种结果”。它服务 Runtime smoke test，确保成功路径和失败摘要路径都能被稳定触发。

## 字段或取值

| 取值 | 语义 |
| --- | --- |
| `success` | 模拟目标场景成功执行，返回成功的 [[FakeServiceResult]]。 |
| `controlled_failure` | 模拟目标场景内部失败，返回带 [[RuntimeErrorRef]] 的失败结果。 |
| `skipped` | 模拟当前 fake service 不执行，仅用于后续全流程跳过策略验证；Runtime MVP 第一版不作为默认行为。 |

## 有效性规则

- 只能使用本文列出的受控取值。
- Runtime MVP smoke test 至少应覆盖 `success` 和 `controlled_failure`。
- `skipped` 不得被伪装为成功；如果进入 [[SceneResult]]，状态必须能表达未执行或被跳过。
- 真实 Service 不消费本枚举。

## 上游来源

- Runtime smoke test 模块指定。
- 开发者模式配置或临时覆盖可以在后续用于选择 fake service 行为。
- 场景注册与 Service 调度模块可把默认行为设为 `success`。

## 下游消费者

- [[FakeServicePlan]]
- [[FakeServiceResult]]
- 场景注册与 Service 调度模块。
- Runtime smoke test 模块。
- Manifest 与错误摘要模块。

## 不负责

- 不表达真实业务错误类型。
- 不决定错误摘要文件格式。
- 不替代 [[RunStatus]]。
- 不描述输出文件布局。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `skipped` 是否进入 Runtime MVP 第一版 | 影响全流程失败后是否继续执行后续场景。 | 先保留为概念，不作为功能7第一批 L3 的必做项。 | 场景注册与 Service 调度模块设计时确认。 |

## 相关链接

- [[07_Fake Service模块]]
- [[FakeServicePlan]]
- [[FakeServiceResult]]
- [[RuntimeErrorRef]]
- [[SceneResult]]
- [[RunStatus]]
