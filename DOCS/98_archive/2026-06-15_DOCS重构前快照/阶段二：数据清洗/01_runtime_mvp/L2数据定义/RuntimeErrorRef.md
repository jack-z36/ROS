# RuntimeErrorRef

## 定义

`RuntimeErrorRef` 是 Runtime 失败时可定位的结构化错误引用。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`RuntimeErrorRef` 表示“这次失败在哪里、为什么失败、下一步应该检查什么”。它让错误摘要、结构化日志和 UI 失败反馈不只返回笼统异常。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `error_code` | string | 是 | 可分类的错误码。 |
| `scene_name` | [[SceneName]] 或空 | 否 | 失败所属场景。 |
| `step_name` | string | 是 | 失败所属步骤。 |
| `message` | string | 是 | 一行失败摘要。 |
| `details` | map | 否 | 失败上下文。 |
| `suggested_next_action` | string | 否 | 给用户或开发者的下一步建议。 |

## 有效性规则

- `error_code`、`step_name` 和 `message` 必须非空。
- 场景内失败必须填写 `scene_name`。
- `message` 应简短明确，不能只写“运行失败”。
- `details` 可以为空，但不能替代必需字段。

## 上游来源

- 配置加载失败。
- 配置预检查失败。
- 输入产物预检查失败。
- Service 调度失败。
- fake service 或真实 Service 返回失败。
- Runtime 状态迁移非法。

## 下游消费者

- [[SceneResult]]
- [[PipelineResult]]
- Manifest 与错误摘要模块。
- 结构化日志模块。
- UI 失败反馈。

## 不负责

- 不保存完整 traceback。
- 不替代 `error_summary.json`。
- 不修复错误，只定位错误。
- 不承载业务报告。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `error_code` 是否需要统一错误码表 | 影响后续自动化测试和排错体验。 | 第一版只要求可分类字符串。 | Manifest 与错误摘要模块设计时确认。 |

## 相关链接

- [[RunContext]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RuntimeStepRecord]]
- [[RunStatus]]
- [[01_Runtime运行上下文定义]]

