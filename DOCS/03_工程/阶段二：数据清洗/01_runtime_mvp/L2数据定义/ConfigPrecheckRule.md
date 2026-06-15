# ConfigPrecheckRule

## 定义

`ConfigPrecheckRule` 是配置预检查模块执行的一条 Runtime 级检查规则。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[04_配置预检查模块]]

## 现实语义

`ConfigPrecheckRule` 表示“为了判断配置是否达到 Runtime 继续执行门槛，需要检查的一条规则”。它把配置预检查限定在 Runtime 级结构、场景配置块、来源和快照可追溯性上，避免功能四提前扩张成 Service 业务参数校验器。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `rule_id` | string | 是 | 稳定规则标识，例如 `effective_config_exists`、`snapshot_is_traceable`、`target_scene_config_exists`。 |
| `scope` | string | 是 | 规则作用域，第一版使用 `global` 或 `scene`。 |
| `required` | boolean | 是 | 规则失败是否阻塞后续执行。 |
| `description` | string | 是 | 规则要检查什么。 |
| `failure_issue_code` | string | 是 | 规则失败时生成的 [[ConfigPrecheckIssue]] 问题码。 |

## 有效性规则

- `rule_id` 必须稳定，方便测试和日志引用。
- `scope = scene` 的规则必须能对 [[RunContext]] 中每个目标 [[SceneName]] 独立判断。
- 第一版规则不得进入真实业务算法参数校验，例如 topic 语义、滤波参数、IK 参数或 MuJoCo 参数。
- `required = true` 的规则失败时，必须让 [[ConfigPrecheckResult]] 的 `passed` 为 false。

## 上游来源

- [[04_配置预检查模块]] 定义的 Runtime 级检查边界。
- 用户确认的设计结论：功能四不提前检查 Service 业务级必填字段。
- [[EffectiveRuntimeConfig]]、[[ConfigSnapshot]] 和 [[RunContext]] 的现有数据定义。

## 下游消费者

- [[ConfigPrecheckResult]]
- [[ConfigPrecheckIssue]]
- Runtime smoke test 模块。

## 不负责

- 不定义完整配置 schema。
- 不描述文件读写动作。
- 不检查输入产物存在性。
- 不替代 Service 场景自己的配置校验。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 规则集合是否需要机器可读 schema 文件 | 影响后续是否能用数据驱动方式执行检查。 | 第一版 L2 固定语义，L3 实现时可先写成代码常量。 | L3 生成或执行前确认。 |

## 相关链接

- [[ConfigPrecheckResult]]
- [[ConfigPrecheckIssue]]
- [[RunContext]]
- [[04_配置预检查模块]]
