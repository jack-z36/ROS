# Runtime 运行上下文定义：数据定义索引

## 文档定位

本文不再承载多个数据概念的完整定义。根据 `DOCS/02_约束/阶段二任务体系/L2能力模块与数据定义约束.md`，Runtime 运行上下文相关数据必须拆成独立原子文档，并由 L2 能力模块说明通过 Obsidian 双向链接引用。

本文只作为“Runtime 运行上下文定义”这个 L2 模块的数据定义索引和迁移说明。

## 原子数据定义清单

| 数据概念 | 原子文档 | 说明 |
| --- | --- | --- |
| RunContext | [[RunContext]] | 一次 Runtime 运行的完整上下文快照。 |
| RunStatus | [[RunStatus]] | 一次运行或步骤的状态枚举。 |
| RunMode | [[RunMode]] | 本次运行所处的开发者/生产、单场景/全流程模式。 |
| SceneName | [[SceneName]] | 阶段二五个业务场景的受控名称。 |
| ServiceMode | [[ServiceMode]] | Runtime 本次调用 fake service 还是真实 service。 |
| SceneResult | [[SceneResult]] | 单个场景执行后的最小结果摘要。 |
| PipelineResult | [[PipelineResult]] | 单场景或全流程结束后的最终结果摘要。 |
| RuntimeStepRecord | [[RuntimeStepRecord]] | Runtime 每个执行步骤的结构化记录。 |
| RuntimeErrorRef | [[RuntimeErrorRef]] | 失败时可定位的结构化错误引用。 |

## 使用规则

- L2 能力模块说明中提到以上概念时，必须使用 `[[数据概念名]]`。
- 后续如果新增数据概念，先创建新的原子文档，再回到本索引补充条目。
- 本索引不替代原子文档；字段、取值、有效性规则必须写入对应原子文档。

## 相关链接

- [[01_Runtime运行上下文定义]]
- [[RunContext]]
- [[SceneResult]]
- [[PipelineResult]]

