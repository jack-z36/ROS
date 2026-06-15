# ServiceMode

## 定义

`ServiceMode` 是 Runtime 本次调度调用 fake service 还是真实 service 的模式枚举。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`ServiceMode` 回答“这次 Runtime 只是验证空流程，还是要调用真实业务处理能力”。它让 fake pipeline 的验收语义和真实清洗能力的完成语义保持分离。

## 字段或取值

| 取值 | 语义 |
| --- | --- |
| `fake` | 调用 fake service，只验证 Runtime 调度链路。 |
| `real` | 调用真实 Service，执行对应业务场景。 |

## 有效性规则

- 只能使用本文列出的受控取值。
- Runtime MVP 第一版允许开发者 smoke test 默认使用 `fake`。
- `fake` 不能被当作真实业务算法完成。

## 上游来源

- 开发者模式可选择或默认使用 fake service。
- 后续真实 Service 接入后，生产模式应使用 real service。

## 下游消费者

- [[RunContext]]
- 场景注册与 Service 调度模块。
- Fake Service 模块。
- Runtime smoke test 模块。
- Manifest 与错误摘要模块。

## 不负责

- 不描述 fake service 生成哪些假产物。
- 不描述真实 Service 的算法。
- 不决定运行模式；运行模式由 [[RunMode]] 承载。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 生产模式是否允许使用 `fake` | 影响用户端安全边界。 | Runtime MVP 阶段只把 fake 用于开发者 smoke test。 | 用户确认。 |

## 相关链接

- [[RunContext]]
- [[RunMode]]
- [[SceneName]]
- [[01_Runtime运行上下文定义]]

