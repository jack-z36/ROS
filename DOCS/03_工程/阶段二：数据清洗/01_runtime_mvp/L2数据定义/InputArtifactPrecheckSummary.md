# InputArtifactPrecheckSummary

## 定义

`InputArtifactPrecheckSummary` 是一次场景输入产物预检查的汇总结果。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[05_输入产物预检查模块]]

## 现实语义

`InputArtifactPrecheckSummary` 表示“当前目标场景的所有输入产物是否已经满足启动条件”。它让 Runtime 在调度 Service 前能够统一决定继续、失败、或提示用户先运行上游流程。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 是 | 本次预检查对应的目标场景。 |
| `results` | list of [[InputArtifactCheckResult]] | 是 | 每个输入产物需求的检查结果。 |
| `status` | [[RunStatus]] 或受控字符串 | 是 | 汇总状态，全部通过才可视为成功。 |
| `blocking_errors` | list of [[RuntimeErrorRef]] | 是 | 会阻止调度的错误列表。 |
| `checked_at` | datetime 或空 | 否 | 检查完成时间。 |

## 有效性规则

- `results` 至少包含目标场景需要的直接输入产物检查。
- 任一必需输入失败时，汇总状态必须为失败，并进入 `blocking_errors`。
- 全部必需输入通过时，汇总状态才能为成功。
- 汇总结果不允许静默丢弃失败项。

## 上游来源

- 输入产物预检查模块根据目标 [[SceneName]] 生成或读取 [[InputArtifactRequirement]]。
- 输入产物预检查模块执行每个 [[InputArtifactCheckResult]] 后汇总。
- 配置预检查模块未来提供已通过的配置前提。

## 下游消费者

- 场景注册与 Service 调度模块。
- [[SceneResult]]
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不代表 Service 已经执行。
- 不代表业务内容深度校验通过。
- 不生成 cleaned、validated、aligned、canonical dataset 或 exports。
- 不替代 `error_summary.json`，只提供其可消费的错误来源。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 单场景生产模式是否允许“缺输入但可运行上游流程”的非阻塞建议 | 影响 UI 与调度策略。 | Runtime MVP 第一版将缺必需输入视为阻塞错误，并在建议中提示运行上游流程。 | 场景注册与 Service 调度模块设计时确认。 |

## 相关链接

- [[InputArtifactRequirement]]
- [[InputArtifactCheckResult]]
- [[SceneResult]]
- [[RuntimeErrorRef]]
- [[05_输入产物预检查模块]]

