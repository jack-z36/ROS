# ConfigPrecheckIssue

## 定义

`ConfigPrecheckIssue` 是配置预检查发现的单条问题记录。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[04_配置预检查模块]]

## 现实语义

`ConfigPrecheckIssue` 表示“本次生效配置中有一个会影响 Runtime 继续执行的配置问题”。它用于把缺失字段、非法场景配置、不可追溯快照路径等问题结构化表达，供后续错误摘要、结构化日志和用户排错使用。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `issue_code` | string | 是 | 可分类的问题码，例如 `missing_global_field`、`missing_scene_config`、`invalid_snapshot_path`。 |
| `severity` | string | 是 | 问题级别，第一版使用 `error` 或 `warning`。 |
| `config_path` | string | 否 | 问题对应的配置路径或字段路径。 |
| `scene_name` | [[SceneName]] 或空 | 否 | 问题归属的目标场景；全局问题可为空。 |
| `message` | string | 是 | 一行可读问题说明。 |
| `details` | map | 否 | 额外上下文，例如实际值、期望值、来源路径。 |
| `runtime_error_ref` | [[RuntimeErrorRef]] 或空 | 否 | 阻塞型问题可映射到 Runtime 错误引用。 |

## 有效性规则

- `issue_code`、`severity` 和 `message` 必须非空。
- `severity` 为 `error` 的问题必须阻止后续输入产物预检查和 Service 调度。
- 场景配置缺失类问题必须填写 `scene_name`。
- `message` 必须说明问题本身，不能只写“配置错误”。

## 上游来源

- [[EffectiveRuntimeConfig]]
- [[ConfigSnapshot]]
- [[RunContext]]
- [[ConfigPrecheckRule]]

## 下游消费者

- [[ConfigPrecheckResult]]
- 输入产物预检查模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不修复配置问题。
- 不承载完整 traceback。
- 不判断输入产物文件是否存在。
- 不描述真实 Service 算法参数的业务正确性。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `severity` 是否需要扩展为 `info` | 影响日志展示粒度。 | 第一版只固定 `error` 和 `warning`。 | 结构化日志模块设计时确认。 |

## 相关链接

- [[ConfigPrecheckResult]]
- [[ConfigPrecheckRule]]
- [[RuntimeErrorRef]]
- [[04_配置预检查模块]]
