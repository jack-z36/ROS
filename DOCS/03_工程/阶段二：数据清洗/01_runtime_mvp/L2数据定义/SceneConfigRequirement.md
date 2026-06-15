# SceneConfigRequirement

## 定义

`SceneConfigRequirement` 是某个阶段二场景在 Runtime 调度前需要满足的 Runtime 级最小配置要求。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[04_配置预检查模块]]

## 现实语义

`SceneConfigRequirement` 表示“如果用户要跑某个场景，配置里至少需要具备哪些 Runtime 级配置入口”。它帮助 Runtime 在调度前区分全局配置问题和场景配置块问题，也为后续真实 Service 接入留下统一入口。它不提前承担 Service 业务级必填字段校验。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 是 | 适用场景。 |
| `required_sections` | list of string | 是 | Runtime 调度前必须能定位的配置块。 |
| `required_fields` | list of string | 是 | Runtime 调度前必须能定位的字段路径。 |
| `required_semantics` | list of string | 否 | Runtime 级跨字段语义要求；不包含真实 Service 算法正确性。 |
| `notes` | string 或空 | 否 | 暂未稳定的场景需求说明。 |

## 有效性规则

- `scene_name` 必须来自 [[SceneName]]。
- `required_sections` 和 `required_fields` 可以随 Service 场景成熟逐步扩展，但不得与上游配置对象字段冲突。
- 第一版不得把 MCAP topic 语义、滤波参数、IK 参数、MuJoCo 参数或 exporter 细节写成 Runtime 阻塞条件。
- 第一版 Runtime MVP 可优先覆盖 `scene1` 和 fake 全流程所需的最小配置；未稳定的真实场景要求必须显式标注。

## 上游来源

- 阶段二五场景目标和背景文档。
- [[EffectiveRuntimeConfig]]
- 现有场景一配置解析与校验能力。

## 下游消费者

- [[ConfigPrecheckRule]]
- [[ConfigPrecheckResult]]
- 输入产物预检查模块。
- 场景注册与 Service 调度模块。
- Runtime smoke test 模块。

## 不负责

- 不定义真实 Service 算法参数。
- 不检查输入文件是否存在。
- 不替代 `config/data_clean/` 中的真实配置文件。
- 不新增阶段二场景。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 场景二到场景五的真实配置字段尚未稳定 | 影响全流程真实模式的严格校验。 | Runtime MVP 第一版只定义可 fake 调度的最小要求，把真实 Service 深层要求留给对应 Service L2。 | 对应 Service 场景开发时确认。 |

## 相关链接

- [[SceneName]]
- [[ConfigPrecheckRule]]
- [[ConfigPrecheckResult]]
- [[EffectiveRuntimeConfig]]
- [[04_配置预检查模块]]
