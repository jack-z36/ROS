# ServiceBinding

## 定义

`ServiceBinding` 是单个 [[SceneName]] 到一个可调用 service 的绑定描述。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[06_场景注册与Service调度模块]]

## 现实语义

`ServiceBinding` 表示“当 Runtime 要执行某个场景时，应该调用哪个 service，以及这个 service 宣称消费和产出哪些路径语义”。它是 [[ServiceRegistry]] 中的最小注册单元。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 是 | 该绑定对应的阶段二场景。 |
| `service_mode` | [[ServiceMode]] | 是 | fake 或真实 service。 |
| `callable_ref` | callable 标识或对象引用 | 是 | Runtime 实现层可调用的 service 入口。 |
| `expected_inputs` | list of [[InputArtifactRequirement]] 或语义名 | 否 | 该 service 期望消费的输入产物。 |
| `declared_outputs` | map | 否 | 该 service 可能生成或声明的输出路径语义。 |
| `supports_smoke` | boolean | 否 | 是否支持 Runtime smoke test 使用。 |

## 有效性规则

- `scene_name` 必须是受控 [[SceneName]]。
- `service_mode` 必须与所属 [[ServiceRegistry]] 一致。
- `callable_ref` 在装配完成后必须可调用；不可调用时注册表构建或调度前检查应失败。
- 第一版允许 `expected_inputs` 为空，但不得因此跳过 [[InputArtifactPrecheckSummary]] 的放行判断。

## 上游来源

- fake service 模块提供 fake 绑定。
- 真实 Service 场景后续提供真实绑定。
- 输入产物预检查模块提供 [[InputArtifactRequirement]] 语义作为绑定可选说明。

## 下游消费者

- [[ServiceRegistry]]
- [[SceneDispatchPlan]]
- [[06_场景注册与Service调度模块]]
- 结构化日志模块。

## 不负责

- 不保存运行结果。
- 不执行输入产物预检查。
- 不决定全流程场景顺序。
- 不生成用户可见菜单。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `callable_ref` 最终使用函数、对象还是协议接口 | 影响代码实现形态。 | L2 只固定“可调用入口”语义；L3 执行时结合现有代码结构收敛。 | 首个调度 L3 执行时确认。 |

## 相关链接

- [[ServiceRegistry]]
- [[SceneDispatchPlan]]
- [[SceneName]]
- [[ServiceMode]]
- [[InputArtifactRequirement]]
- [[06_场景注册与Service调度模块]]
