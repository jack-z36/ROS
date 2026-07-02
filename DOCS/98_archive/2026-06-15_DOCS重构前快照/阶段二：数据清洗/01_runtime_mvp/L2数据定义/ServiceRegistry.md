# ServiceRegistry

## 定义

`ServiceRegistry` 是 Runtime 可调度场景 service 的注册表。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[06_场景注册与Service调度模块]]

## 现实语义

`ServiceRegistry` 表示“Runtime 当前知道哪些场景可以被调度，以及每个场景应调用哪个 fake service 或真实 service”。它让调度模块不需要在流程代码中硬编码每个场景的具体调用分支。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `bindings` | map of [[SceneName]] to [[ServiceBinding]] | 是 | 每个可调度场景对应的 service 绑定。 |
| `service_mode` | [[ServiceMode]] | 是 | 当前注册表用于 fake service 还是真实 service。 |
| `registered_scenes` | list of [[SceneName]] | 是 | 注册表明确支持的场景列表。 |
| `created_at` | datetime 或空 | 否 | 注册表创建或装配时间。 |
| `metadata` | map | 否 | 调试信息或实现版本，不承载必需调度字段。 |

## 有效性规则

- `registered_scenes` 中的每个场景必须存在对应 [[ServiceBinding]]。
- [[SceneName]] 中被本次 [[RunContext]] 选中的目标场景必须能在注册表中找到绑定，否则调度必须失败。
- `service_mode` 必须与 [[RunContext]] 中的 [[ServiceMode]] 一致。
- 注册表只记录可调用入口和能力声明，不保存 service 执行结果。

## 上游来源

- Runtime 启动或测试装配过程创建注册表。
- [[ServiceMode]] 决定注册 fake service 绑定还是真实 service 绑定。
- 后续 [[07_Fake Service模块]] 和真实 Service 场景实现会向注册表提供可调用绑定。

## 下游消费者

- [[06_场景注册与Service调度模块]]
- Runtime smoke test 模块。
- 结构化日志模块可记录实际命中的绑定信息。

## 不负责

- 不执行 service。
- 不检查输入产物是否存在。
- 不生成 [[SceneResult]] 或 [[PipelineResult]]。
- 不替代 Python 依赖注入容器或复杂插件系统。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 真实 Service 接入时是否需要动态发现机制 | 影响注册表是否需要插件扫描。 | Runtime MVP 第一版使用显式注册，不做动态发现。 | 真实 Service 接入前确认。 |

## 相关链接

- [[ServiceBinding]]
- [[SceneName]]
- [[ServiceMode]]
- [[RunContext]]
- [[06_场景注册与Service调度模块]]
