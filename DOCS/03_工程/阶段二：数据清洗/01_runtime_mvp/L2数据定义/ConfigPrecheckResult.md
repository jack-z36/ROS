# ConfigPrecheckResult

## 定义

`ConfigPrecheckResult` 是 Runtime 配置预检查完成后的结构化结果。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[04_配置预检查模块]]

## 现实语义

`ConfigPrecheckResult` 表示“本次生效配置是否达到 Runtime 继续执行的最低门槛”。它不代表真实业务配置已经完全正确，只表示配置结构、来源、目标场景配置块和可追溯性满足后续输入产物预检查与调度的前置要求。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `passed` | boolean | 是 | 是否允许进入输入产物预检查和后续调度。 |
| `checked_scenes` | list of [[SceneName]] | 是 | 本次按 [[RunContext]] 检查过的目标场景。 |
| `issues` | list of [[ConfigPrecheckIssue]] | 是 | 检查发现的问题列表；无问题时为空列表。 |
| `checked_rules` | list of [[ConfigPrecheckRule]] 或 rule id | 否 | 本次执行过的规则集合。 |
| `effective_config_ref` | [[EffectiveRuntimeConfig]] | 是 | 本次被检查的生效配置语义对象。 |
| `config_snapshot_ref` | [[ConfigSnapshot]] 或空 | 否 | 本次配置快照引用；快照缺失时可为空并产生 issue。 |
| `created_at` | datetime 或空 | 否 | 预检查结果生成时间。 |

## 有效性规则

- `passed` 为 true 时，`issues` 中不得存在 `severity = error` 的问题。
- `checked_scenes` 必须与 [[RunContext]] 的目标场景一致。
- `effective_config_ref` 必须来自功能三产出的 [[EffectiveRuntimeConfig]]，不得重新读取一份配置。
- 只要配置来源、快照或场景配置块不可追溯，必须产生阻塞型 [[ConfigPrecheckIssue]]。

## 上游来源

- [[RunContext]]
- [[EffectiveRuntimeConfig]]
- [[ConfigSnapshot]]
- [[ConfigPrecheckRule]]

## 下游消费者

- 输入产物预检查模块。
- 场景注册与 Service 调度模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不保存配置快照文件。
- 不检查 MCAP、parquet、HDF5 或 Zarr 文件是否存在。
- 不判断 Service 内部算法参数是否物理合理。
- 不替代 [[RuntimeErrorRef]] 或 `error_summary.json`。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 是否需要把 `warnings` 单独拆字段 | 影响后续日志和 UI 展示。 | 第一版统一放入 `issues`，通过 `severity` 区分。 | 结构化日志模块设计时确认。 |

## 相关链接

- [[ConfigPrecheckIssue]]
- [[ConfigPrecheckRule]]
- [[EffectiveRuntimeConfig]]
- [[ConfigSnapshot]]
- [[04_配置预检查模块]]
