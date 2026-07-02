# InputArtifactRequirement

## 定义

`InputArtifactRequirement` 是 Runtime MVP 中某个场景在执行前必须满足的输入产物需求。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[05_输入产物预检查模块]]

## 现实语义

`InputArtifactRequirement` 表示“当前要运行的场景需要哪个上游产物”。它让输入产物预检查模块能够按场景判断 raw MCAP、cleaned MCAP、validated MCAP、aligned MCAP 或 canonical dataset 是否存在、可读，并能在缺失时给出明确失败原因。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 是 | 本需求归属的目标场景。 |
| `artifact_role` | string | 是 | 输入产物角色，例如 `raw_mcap`、`cleaned_mcap`、`validated_mcap`、`aligned_mcap`、`canonical_dataset`。 |
| `path_config_key` | string | 是 | 在 [[EffectiveRuntimeConfig]] 中定位路径的配置键或语义键。 |
| `required_kind` | string | 是 | 期望路径类型，第一版取值为 `file` 或 `directory`。 |
| `required_for_modes` | list | 是 | 哪些 [[RunMode]] 下需要该产物。 |
| `allow_manual_override` | boolean | 是 | 缺上游产物时是否允许用户手动指定等价输入。 |
| `description` | string | 否 | 给日志、错误摘要或 UI 使用的人类可读说明。 |

## 有效性规则

- `scene_name` 必须是 [[SceneName]] 的受控取值。
- `artifact_role` 必须非空，并能被下游错误信息复用。
- `path_config_key` 必须能在 [[EffectiveRuntimeConfig]] 的 `effective_data` 中定位到候选路径，或明确允许由入口参数补充。
- `required_kind` 第一版只允许 `file` 或 `directory`。
- Runtime MVP 第一版只检查存在性和可读边界，不检查 MCAP topic、Parquet schema 或 canonical dataset 完整性。

## 上游来源

- 阶段二产物架构设计中的 raw、cleaned、validated、aligned、canonical dataset 和 exports 产物契约。
- Runtime MVP 功能模块清单中的功能5。
- 配置预检查模块未来确认后的生效配置字段。

## 下游消费者

- [[InputArtifactCheckResult]]
- [[InputArtifactPrecheckSummary]]
- 场景注册与 Service 调度模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。

## 不负责

- 不保存真实数据产物内容。
- 不定义业务级 topic/schema 校验规则。
- 不替代配置预检查模块判断配置字段是否完整。
- 不替代 Service 场景自己的深度输入契约校验。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| [[EffectiveRuntimeConfig]] 中输入路径键名尚未由功能4冻结 | 影响代码实现时如何从配置中取路径。 | 本定义先使用 `path_config_key` 表达语义键，L3 执行时必须先对齐功能4或拆接口任务。 | 功能4 L2/L3 或首次实现功能5前确认。 |
| full pipeline 模式是否允许使用已存在中间产物跳过上游场景 | 影响输入依赖计算。 | 第一版按目标场景需要的直接输入产物检查，不做跳步策略。 | 场景调度模块设计时确认。 |

## 相关链接

- [[05_输入产物预检查模块]]
- [[InputArtifactCheckResult]]
- [[InputArtifactPrecheckSummary]]
- [[EffectiveRuntimeConfig]]
- [[SceneName]]

