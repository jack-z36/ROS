# InputArtifactCheckResult

## 定义

`InputArtifactCheckResult` 是单个输入产物需求经过预检查后的结果。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[05_输入产物预检查模块]]

## 现实语义

`InputArtifactCheckResult` 表示“某个场景需要的某个输入产物是否满足最小运行边界”。它是输入产物预检查模块给调度、日志和错误摘要的最小可消费结果。

## 字段或取值

| 字段 | 类型语义 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| `requirement` | [[InputArtifactRequirement]] | 是 | 本次检查对应的输入需求。 |
| `candidate_path` | path string 或空 | 否 | 从 [[EffectiveRuntimeConfig]] 或入口覆盖项解析出的候选路径。 |
| `status` | [[RunStatus]] 或受控字符串 | 是 | 第一版建议取 `succeeded` 或 `failed`。 |
| `exists` | boolean | 是 | 路径是否存在。 |
| `readable` | boolean | 是 | 路径是否可读。 |
| `kind_matches` | boolean | 是 | 文件/目录类型是否符合 `required_kind`。 |
| `error` | [[RuntimeErrorRef]] 或空 | 否 | 失败时的结构化错误引用。 |

## 有效性规则

- 成功时 `candidate_path` 必须非空，且 `exists`、`readable`、`kind_matches` 均为 true。
- 失败时 `error` 必须存在，且 `step_name` 能定位到输入产物预检查。
- `candidate_path` 为空时不能标记为成功。
- 第一版不把“路径存在但业务内容不合法”标记为成功或失败；深度内容校验由后续 Service 或 contract test 承担。

## 上游来源

- 输入产物预检查模块读取 [[InputArtifactRequirement]]。
- 输入产物预检查模块从 [[EffectiveRuntimeConfig]] 中解析候选路径。
- 文件系统最小边界检查生成存在性、可读性和类型匹配结果。

## 下游消费者

- [[InputArtifactPrecheckSummary]]
- 场景注册与 Service 调度模块。
- 结构化日志模块。
- Manifest 与错误摘要模块。
- Runtime smoke test 模块。

## 不负责

- 不保存完整异常 traceback。
- 不解释 MCAP topic、Parquet schema 或 dataset index。
- 不创建缺失产物。
- 不自动运行上游场景。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `status` 是否复用 [[RunStatus]] 还是单独定义检查状态 | 影响代码 Type 设计。 | 文档允许复用 [[RunStatus]] 或受控字符串；L3 数据定义任务需收敛。 | `runtime_mvp_010` 执行时确认。 |

## 相关链接

- [[InputArtifactRequirement]]
- [[InputArtifactPrecheckSummary]]
- [[RuntimeErrorRef]]
- [[RunStatus]]
- [[05_输入产物预检查模块]]

