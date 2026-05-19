# L2 能力模块说明：场景注册与 Service 调度模块

## 1. 能力名称

```text
Runtime MVP / 场景注册与 Service 调度模块
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：`runtime_mvp`  
场景：Runtime MVP，不归入 `02_service` 的具体业务场景  
模块类别：流程编排类  
来源功能模块清单：[[功能模块清单]]

## 3. 一句话目标

```text
根据本次运行选择的目标场景，从 Service 注册表中找到可调用绑定，并按单场景或全流程顺序统一调度 fake service 或真实 service。
```

## 4. 能力角色

```text
本能力是 Runtime MVP 的主调度枢纽，负责把“预检查已通过的运行请求”转换成可执行的场景调用顺序和最终运行结果。
```

它消费 [[RunContext]]、[[ConfigPrecheckResult]]、[[InputArtifactPrecheckSummary]] 和 [[ServiceRegistry]]，形成 [[SceneDispatchPlan]]，调用每个 [[ServiceBinding]]，并汇总 [[SceneResult]] 与 [[PipelineResult]]。它不实现任何场景业务算法。

## 5. 上游关系

- 来自 [[01_Runtime运行上下文定义]] 的 [[RunContext]]、[[SceneName]]、[[RunMode]]、[[ServiceMode]]、[[RunStatus]]、[[SceneResult]]、[[PipelineResult]] 和 [[RuntimeErrorRef]]。
- 来自 [[04_配置预检查模块]] 的 [[ConfigPrecheckResult]]，作为是否允许进入输入产物预检查和调度的前提。
- 来自 [[05_输入产物预检查模块]] 的 [[InputArtifactPrecheckSummary]]，作为是否允许调用对应场景 service 的直接前提。
- 来自 [[07_Fake Service模块]] 的 [[FakeServicePlan]]、[[FakeServiceResult]] 和 [[FakeServiceBehavior]]；功能6通过 [[ServiceBinding]] 调用 fake service，并把 fake 结果汇总为 [[SceneResult]]。
- 来自后续真实 Service 场景的 [[ServiceBinding]]。
- 已按 `$grill-me` 约束完成意图澄清：仓库现有功能模块清单、Runtime 六件套、上游 L2 与产物架构文档已经能回答功能6的目标、输入、输出、上下游和边界；本轮无需额外追问。

## 6. 下游关系

- [[07_Fake Service模块]] 会通过 [[ServiceRegistry]] 被本能力调用，用于跑通 Runtime MVP 空流程。
- 真实 Service 场景后续接入时复用同一调度骨架。
- 结构化日志模块消费 [[SceneDispatchEvent]]、[[SceneResult]] 和 [[PipelineResult]]。
- Manifest 与错误摘要模块消费 [[PipelineResult]] 和失败时的 [[RuntimeErrorRef]]。
- Runtime smoke test 模块验证单场景 fake 调度、全流程 fake 调度、注册缺失、预检查失败停止和 service 失败停止。

## 7. 上游接口对齐检查

开发本能力前，必须先按 `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md` 检查直接上游功能。

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
| --- | --- | --- | --- | --- |
| [[01_Runtime运行上下文定义]] | [[RunContext]]、[[SceneName]]、[[RunMode]]、[[ServiceMode]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeErrorRef]] | 读取目标场景和运行模式，生成场景结果和最终结果 | 已对齐 | 复用 |
| [[04_配置预检查模块]] | [[ConfigPrecheckResult]] | 配置预检查失败时不得进入调度 | 已对齐 | 复用 |
| [[05_输入产物预检查模块]] | [[InputArtifactPrecheckSummary]] | 每个目标场景必须输入预检查通过后才能调用 service | 已对齐 | 复用 |
| [[07_Fake Service模块]] | [[FakeServicePlan]]、[[FakeServiceResult]]、[[FakeServiceBehavior]] | Runtime MVP 第一版主要调度 fake service，并将 fake 结果汇总为 [[SceneResult]] | 已对齐 | 复用功能7语义；本能力补足注册表和调度计划接口 |
| 后续真实 Service 场景 | 真实 service 的 [[ServiceBinding]] 或等价可调用入口 | 后续接入真实清洗、验证、对齐、dataset 和导出能力 | 缺定义 | 本能力只保留扩展位，不在 Runtime 中实现真实业务算法 |

## 8. 职责边界

本能力负责：

1. 构建或消费 [[ServiceRegistry]]，确认目标 [[SceneName]] 有可调用 [[ServiceBinding]]。
2. 根据 [[RunContext]] 生成 [[SceneDispatchPlan]]。
3. 在配置预检查和输入产物预检查都通过后，按单场景或全流程顺序调用 service。
4. 将每个场景的调用结果整理为 [[SceneResult]]。
5. 将本次运行汇总为 [[PipelineResult]]。
6. 在注册缺失、预检查失败或 service 失败时生成 [[RuntimeErrorRef]] 并停止后续调度。
7. 产生 [[SceneDispatchEvent]] 供后续结构化日志模块消费。

本能力不负责：

1. 实现 fake service 或真实 service 的业务行为。
2. 读取、解析或写入 MCAP、Parquet、JSON、YAML 等业务产物。
3. 检查配置字段和输入产物路径。
4. 写入 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
5. 实现 UI 菜单、进度条或交互提示。

## 9. 编排职责

本能力负责调度的模块：

| 被调模块 | 调用目的 | 输入依赖 | 输出去向 |
| --- | --- | --- | --- |
| 配置预检查模块 | 确认生效配置可进入 Runtime 后续流程 | [[RunContext]]、[[EffectiveRuntimeConfig]]、[[ConfigSnapshot]] | 通过/失败状态影响是否继续调度 |
| 输入产物预检查模块 | 确认每个目标场景的直接输入产物满足最小边界 | [[RunContext]]、[[EffectiveRuntimeConfig]]、[[InputArtifactRequirement]] | [[InputArtifactPrecheckSummary]] 进入 [[SceneDispatchPlan]] |
| [[ServiceRegistry]] | 查找目标场景对应 service | [[SceneName]]、[[ServiceMode]] | [[ServiceBinding]] 进入 [[SceneDispatchPlan]] |
| fake service 或真实 service | 执行单个场景的可调用能力 | [[RunContext]]、目标 [[SceneName]]、预检查结果 | [[SceneResult]] |
| 结果汇总器或等价 Runtime 汇总逻辑 | 汇总整次运行状态 | 多个 [[SceneResult]]、[[RunContext]] | [[PipelineResult]] |

## 10. 调用顺序

```text
入口：收到已初始化的 RunContext
↓
步骤 1：确认配置预检查结果通过
↓
步骤 2：为每个目标 SceneName 确认输入产物预检查结果通过
↓
步骤 3：从 ServiceRegistry 中查找每个目标场景的 ServiceBinding
↓
步骤 4：生成 SceneDispatchPlan
↓
步骤 5：按 SceneDispatchPlan 顺序逐个调用 service
↓
步骤 6：每个场景结束后生成 SceneResult 和 SceneDispatchEvent
↓
步骤 7：遇到失败则停止后续场景，并记录 RuntimeErrorRef
↓
步骤 8：汇总 PipelineResult
↓
完成 / 失败
```

## 11. 依赖关系

| 步骤 | 前置条件 | 依赖产物 | 缺失时处理 |
| --- | --- | --- | --- |
| 配置预检查放行 | [[EffectiveRuntimeConfig]] 已加载，[[ConfigSnapshot]] 已生成或有语义引用 | [[ConfigPrecheckResult]] | 生成配置预检查未通过错误，不进入调度 |
| 输入产物预检查放行 | 目标场景已确定，配置预检查通过 | [[InputArtifactPrecheckSummary]] | 生成输入预检查未通过错误，不调用 service |
| 注册表查找 | [[ServiceRegistry]] 已装配，[[ServiceMode]] 已确定 | [[ServiceBinding]] | 生成 `service_not_registered` 类错误 |
| 单场景执行 | 该场景绑定存在且预检查通过 | [[SceneDispatchPlan]]、[[ServiceBinding]] | 调用失败时生成失败 [[SceneResult]] |
| 全流程执行 | `target_scenes` 顺序有效 | 多个 [[SceneResult]] | 任一场景失败时停止后续场景 |

## 12. 失败策略

| 失败点 | 是否继续后续步骤 | 状态记录 | 错误摘要 | 用户可见反馈 |
| --- | --- | --- | --- | --- |
| 配置预检查失败 | 否 | [[RunStatus]] 进入 failed 或等价失败状态 | [[RuntimeErrorRef]] 指向配置预检查步骤 | 提示配置未通过，后续不调度 |
| 输入产物预检查失败 | 否 | 当前目标场景未执行 | [[RuntimeErrorRef]] 指向输入产物预检查步骤 | 提示缺输入或输入不可读 |
| 目标场景未注册 | 否 | 生成失败 [[SceneResult]] 或空场景失败结果 | `service_not_registered` | 提示当前场景尚未接入 service |
| service 调用抛出异常或返回失败 | 单场景直接失败；全流程停止后续场景 | 当前 [[SceneResult]] 失败，[[PipelineResult]] 失败 | service 返回或 Runtime 包装的 [[RuntimeErrorRef]] | 提示失败场景、失败步骤和日志入口 |
| 结果汇总失败 | 否 | [[PipelineResult]] 失败或无法生成时保留错误引用 | `pipeline_result_build_failed` | 提示运行结果汇总失败 |

## 13. 状态流转

| 状态 | 进入条件 | 退出条件 | 记录位置 |
| --- | --- | --- | --- |
| pending | [[RunContext]] 已创建但未开始调度 | 开始预检查或计划创建 | [[RunContext]] |
| prechecking | 配置或输入预检查正在执行 | 预检查通过或失败 | [[SceneDispatchEvent]]，后续 run log |
| planned | [[SceneDispatchPlan]] 已生成 | 开始第一个场景执行 | [[SceneDispatchPlan]]，[[SceneDispatchEvent]] |
| running | 正在调用某个 [[ServiceBinding]] | 该场景成功或失败 | [[RunContext]].`active_scene`，[[SceneDispatchEvent]] |
| succeeded | 所有目标场景执行成功 | 汇总 [[PipelineResult]] | [[SceneResult]]，[[PipelineResult]] |
| failed | 任一阻塞错误或 service 失败 | 汇总失败结果 | [[RuntimeErrorRef]]，[[SceneResult]]，[[PipelineResult]] |

## 14. 恢复与停止边界

- 可恢复情况：Runtime MVP 第一版不自动恢复；用户可在修正配置、输入或注册后重新运行。
- 必须停止情况：配置预检查失败、输入产物预检查失败、目标场景未注册、service 执行失败、全流程中任一场景失败。
- 不负责恢复的情况：自动补齐缺失输入、自动运行上游真实场景、重试失败 service、跳过失败场景继续生成 canonical dataset。

## 15. 整体完成标准

- [ ] 已建立 [[ServiceRegistry]]、[[ServiceBinding]]、[[SceneDispatchPlan]] 和 [[SceneDispatchEvent]] 的原子数据定义。
- [ ] 本 L2 能力模块说明中出现的数据概念均使用 Obsidian 双向链接。
- [ ] 已按 grill-me 约束完成意图澄清：功能6只做场景注册、计划生成、调度调用和结果汇总，不实现 fake service 或真实业务算法。
- [ ] 已明确直接消费 [[ConfigPrecheckResult]] 和 [[InputArtifactPrecheckSummary]] 的放行结果。
- [ ] 已明确目标场景未注册、预检查失败、service 失败时必须停止后续调度。
- [ ] 已明确输出 [[SceneResult]]、[[PipelineResult]] 和 [[SceneDispatchEvent]]，但不写运行日志、manifest 或错误摘要文件。

## 16. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- |
| runtime_mvp_013 | 定义 Service 注册与调度 Types | 数据定义类 | 本 L2、[[ServiceRegistry]]、[[ServiceBinding]]、[[SceneDispatchPlan]]、[[SceneDispatchEvent]] | 注册与调度相关 Types 或等价结构 | `src/data_clean/schemas/` 或 `src/data_clean/runtime/` 中合适位置 | 能构造注册表、绑定、调度计划和调度事件，非法场景或模式必须失败清楚 |
| runtime_mvp_014 | 实现场景 Service 注册表 | 流程编排类 | [[SceneName]]、[[ServiceMode]]、[[ServiceBinding]] | 可查询的 [[ServiceRegistry]] | `src/data_clean/runtime/` | 已注册场景可取到绑定；未注册场景返回结构化错误 |
| runtime_mvp_015 | 实现单场景调度器 | 流程编排类 | [[RunContext]]、[[ServiceRegistry]]、[[InputArtifactPrecheckSummary]] | 单个 [[SceneResult]] 和 [[SceneDispatchEvent]] | `src/data_clean/runtime/` | 预检查通过时调用绑定；预检查失败或注册缺失时不调用 service |
| runtime_mvp_016 | 实现全流程调度器与结果汇总 | 流程编排类 | [[SceneDispatchPlan]]、多个 [[SceneResult]] | [[PipelineResult]] | `src/data_clean/runtime/` | fake 全流程按场景顺序执行；任一场景失败时停止后续场景并汇总失败 |

## 17. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| fake service 的最终 callable 代码接口尚未定义 | 影响 [[ServiceBinding]].`callable_ref` 的代码形态。 | 功能7已定义 [[FakeServicePlan]] 和 [[FakeServiceResult]] 语义；代码层 callable 形态在调度 L3 执行时收敛。 | `runtime_mvp_014` 或功能7 L3 执行时确认。 |
| 真实 Service 返回值是否直接等同 [[SceneResult]] | 影响真实 Service 接入时是否需要 adapter。 | Runtime MVP 第一版允许通过 [[ServiceBinding]] 或 adapter 转成 [[SceneResult]]。 | 真实 Service 接入前确认。 |
| 全流程是否允许部分成功 | 影响 [[PipelineResult]] 状态和恢复策略。 | 第一版失败即停止，不引入 partial success。 | 真实生产全流程设计时确认。 |

## 18. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 每个 L3 必须有明确输入、输出、修改边界、验收命令和成功标准。
4. 每个 L3 必须写明“本次不做什么”。
5. 每个 L3 不能跨越本 L2 的能力边界。
6. 如果需要修改本 L2 之外的模块，必须在 L3 文档中显式说明原因。
