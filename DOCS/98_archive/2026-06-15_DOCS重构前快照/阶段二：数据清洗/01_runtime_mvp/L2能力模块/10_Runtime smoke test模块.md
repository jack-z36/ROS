# L2 能力模块说明：Runtime smoke test 模块

## 1. 能力名称

```text
Runtime MVP / Runtime smoke test 模块
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：`runtime_mvp`  
场景：Runtime MVP，不归入 `02_service` 的具体业务场景  
模块类别：流程编排类 + 数据计算类  
来源功能模块清单：[[功能模块清单]]

## 3. 一句话目标

```text
用一组最小 smoke test 验证 Runtime MVP 的 fake 单场景、fake 全流程、缺配置、缺输入和失败摘要链路是否可观察、可追溯、可回归。
```

## 4. 能力角色

```text
本能力是 Runtime MVP 的验收层，负责把前 1-9 个 Runtime 模块串成可重复执行的最小端到端检查。
```

它通过 [[RuntimeSmokeTestSuite]] 组织多个 [[RuntimeSmokeTestCase]]，执行后产出 [[RuntimeSmokeTestResult]]。它复用 [[RunContext]]、[[RunDirectory]]、[[EffectiveRuntimeConfig]]、[[ConfigPrecheckResult]]、[[InputArtifactPrecheckSummary]]、[[SceneDispatchPlan]]、[[FakeServicePlan]]、[[FakeServiceResult]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]] 和 [[RuntimeErrorRef]]，但不重新定义这些上游接口。

已按 `$grill-me` 约束完成意图澄清：仓库现有功能模块清单、Runtime 六件套和功能1-9 L2 已经能回答功能10的核心目标、输入、输出和边界；功能10消费功能8与功能9已经定义的日志、manifest 和错误摘要语义，但不自行冻结其代码接口。

## 5. 上游关系

- 来自 [[01_Runtime运行上下文定义]] 的 [[RunContext]]、[[RunMode]]、[[ServiceMode]]、[[SceneName]]、[[RunStatus]]、[[RuntimeStepRecord]]、[[SceneResult]]、[[PipelineResult]] 和 [[RuntimeErrorRef]]。
- 来自 [[02_Run目录管理模块]] 的 [[RunDirectory]]、[[RunDirectoryLayout]] 和 [[RunArtifactPath]]。
- 来自 [[03_配置加载与配置快照模块]] 的 [[RuntimeConfigSource]]、[[ConfigOverrideSet]]、[[EffectiveRuntimeConfig]] 和 [[ConfigSnapshot]]。
- 来自 [[04_配置预检查模块]] 的 [[ConfigPrecheckRule]]、[[ConfigPrecheckIssue]]、[[ConfigPrecheckResult]] 和 [[SceneConfigRequirement]]。
- 来自 [[05_输入产物预检查模块]] 的 [[InputArtifactRequirement]]、[[InputArtifactCheckResult]] 和 [[InputArtifactPrecheckSummary]]。
- 来自 [[06_场景注册与Service调度模块]] 的 [[ServiceRegistry]]、[[ServiceBinding]]、[[SceneDispatchPlan]] 和 [[SceneDispatchEvent]]。
- 来自 [[07_Fake Service模块]] 的 [[FakeServicePlan]]、[[FakeServiceBehavior]] 和 [[FakeServiceResult]]。
- 后续来自结构化日志模块的运行日志产物，以及来自 Manifest 与错误摘要模块的 manifest / error summary 产物。

## 6. 下游关系

- Runtime MVP 阶段验收依赖本能力判断最小闭环是否成立。
- 后续真实 Service 接入时，可复用本能力作为 Runtime 层回归基线。
- 阶段二执行记录可引用 [[RuntimeSmokeTestResult]] 说明哪些 Runtime 行为已被验证。

## 7. 上游接口对齐检查

开发本能力前，必须先按 `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md` 检查直接上游功能。

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
| --- | --- | --- | --- | --- |
| [[01_Runtime运行上下文定义]] | [[RunContext]]、[[RunMode]]、[[ServiceMode]]、[[SceneName]]、[[RunStatus]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeErrorRef]] | 构造 smoke test 运行上下文，并断言最终运行状态、结果和错误引用 | 已对齐 | 复用 |
| [[02_Run目录管理模块]] | [[RunDirectory]]、[[RunDirectoryLayout]]、[[RunArtifactPath]] | 每个 smoke test 必须创建独立 run 目录，并检查关键产物路径 | 已对齐 | 复用 |
| [[03_配置加载与配置快照模块]] | [[EffectiveRuntimeConfig]]、[[ConfigSnapshot]]、[[ConfigOverrideSet]] | 成功用例需要有效配置；缺配置用例需要构造可预期失败 | 已对齐 | 复用 |
| [[04_配置预检查模块]] | [[ConfigPrecheckResult]]、[[ConfigPrecheckIssue]] | 缺配置用例必须失败在配置预检查阶段 | 已对齐 | 复用 |
| [[05_输入产物预检查模块]] | [[InputArtifactRequirement]]、[[InputArtifactPrecheckSummary]] | 缺输入用例必须失败在输入产物预检查阶段 | 已对齐 | 复用 |
| [[06_场景注册与Service调度模块]] | [[ServiceRegistry]]、[[SceneDispatchPlan]]、[[SceneDispatchEvent]]、[[PipelineResult]] | 单场景和全流程 smoke test 通过调度模块触发 fake service | 已对齐 | 复用 |
| [[07_Fake Service模块]] | [[FakeServicePlan]]、[[FakeServiceBehavior]]、[[FakeServiceResult]] | 成功和可控失败用例均依赖 fake service 产生稳定结果 | 已对齐 | 复用 |
| [[08_结构化日志模块]] | [[RunLogFile]]、[[RuntimeLogWriteResult]]、`run_log.json` | smoke test 需要检查成功和失败均留下可追溯日志 | 已对齐 | 复用功能8 L2；代码层接口由 `runtime_mvp_023` 到 `runtime_mvp_025` 实现 |
| [[09_Manifest与错误摘要模块]] | [[ProcessingManifest]]、[[ErrorSummary]]、[[RunResultIndex]] | 成功用例检查 manifest，失败用例检查 error summary | 已对齐 | 复用功能9 L2；代码层接口由 `runtime_mvp_026` 到 `runtime_mvp_029` 实现 |

## 8. 职责边界

本能力负责：

1. 定义 Runtime MVP 第一版必须覆盖的 [[RuntimeSmokeTestSuite]]。
2. 定义每个 [[RuntimeSmokeTestCase]] 的目标、前置条件、预期状态、预期错误和可观察产物。
3. 执行或指导后续 L3 实现 smoke test 编排，覆盖单场景 fake 成功、fake 全流程成功、缺配置、缺输入和 fake service 可控失败摘要。
4. 将每个用例的实际结果表达为 [[RuntimeSmokeTestResult]]。
5. 明确 smoke test 通过只代表 Runtime 骨架闭环通过，不代表真实 Service 业务算法完成。

本能力不负责：

1. 实现真实清洗、验证、对齐、canonical dataset 构建或训练格式导出算法。
2. 定义结构化日志模块的完整文件 schema。
3. 定义 `processing_manifest.json` 和 `error_summary.json` 的完整文件 schema。
4. 修改 `./start_data_clean.sh --dev` 入口。
5. 生成或覆盖真实数据产物。

## 9. 编排职责

本能力负责调度的模块：

| 被调模块 | 调用目的 | 输入依赖 | 输出去向 |
| --- | --- | --- | --- |
| Run 目录管理模块 | 为每个 smoke test 用例创建隔离运行目录 | [[RuntimeSmokeTestCase]]、[[RunContext]] | [[RunDirectory]] 进入 [[RuntimeSmokeTestResult]] |
| 配置加载与配置快照模块 | 为成功/失败用例提供生效配置或缺配置场景 | [[RuntimeConfigSource]]、[[ConfigOverrideSet]] | [[EffectiveRuntimeConfig]]、[[ConfigSnapshot]] |
| 配置预检查模块 | 验证缺配置失败是否停在正确阶段 | [[EffectiveRuntimeConfig]]、[[SceneConfigRequirement]] | [[ConfigPrecheckResult]] |
| 输入产物预检查模块 | 验证缺输入失败是否停在正确阶段 | [[InputArtifactRequirement]] | [[InputArtifactPrecheckSummary]] |
| 场景注册与 Service 调度模块 | 触发单场景或全流程 fake 调度 | [[ServiceRegistry]]、[[SceneDispatchPlan]] | [[SceneResult]]、[[PipelineResult]] |
| Fake Service 模块 | 生成成功或可控失败假结果 | [[FakeServicePlan]]、[[FakeServiceBehavior]] | [[FakeServiceResult]] |
| 结构化日志模块 | 验证运行过程有可追溯日志 | 调度事件、结果、错误 | 后续 `run_log.json` 或等价产物 |
| Manifest 与错误摘要模块 | 验证成功 manifest 和失败 error summary | 配置快照、结果、错误 | 后续 `processing_manifest.json` / `error_summary.json` 或等价产物 |

## 10. 调用顺序

```text
入口：选择 RuntimeSmokeTestSuite
↓
步骤 1：加载 RuntimeSmokeTestCase 列表
↓
步骤 2：为当前 case 构造 RunContext、配置和输入前置条件
↓
步骤 3：创建独立 RunDirectory
↓
步骤 4：执行配置加载、配置预检查和输入产物预检查
↓
步骤 5：按 case 要求执行单场景或全流程 fake 调度
↓
步骤 6：收集 PipelineResult、错误引用和关键运行产物
↓
步骤 7：按 case 的期望状态、期望错误码和期望产物做断言
↓
步骤 8：生成 RuntimeSmokeTestResult
↓
完成 suite 汇总 / 失败
```

## 11. 依赖关系

| 步骤 | 前置条件 | 依赖产物 | 缺失时处理 |
| --- | --- | --- | --- |
| 加载 smoke suite | 功能10数据定义已存在 | [[RuntimeSmokeTestSuite]] | 不能执行 smoke test，提示 suite 未定义 |
| 构造成功用例 | 功能1-7代码接口可用 | [[RunContext]]、[[ServiceRegistry]]、[[FakeServicePlan]] | 标记为 Runtime 主干未就绪 |
| 构造缺配置用例 | 配置预检查接口可用 | [[ConfigPrecheckResult]] | 不能验证缺配置失败路径 |
| 构造缺输入用例 | 输入产物预检查接口可用 | [[InputArtifactPrecheckSummary]] | 不能验证缺输入失败路径 |
| 验证失败摘要 | [[ErrorSummary]] 写入接口可用 | `error_summary.json` 或等价产物 | L2 已定义；等待功能9 L3 实现 |
| 验证成功 manifest | [[ProcessingManifest]] 写入接口可用 | `processing_manifest.json` 或等价产物 | L2 已定义；等待功能9 L3 实现 |
| 验证 run log | [[RunLogFile]] 写入接口可用 | `run_log.json` 或等价产物 | L2 已定义；等待功能8 L3 实现 |

## 12. 失败策略

| 失败点 | 是否继续后续步骤 | 状态记录 | 错误摘要 | 用户可见反馈 |
| --- | --- | --- | --- | --- |
| suite 定义无效 | 否 | [[RuntimeSmokeTestResult]] 标记 suite setup failed | 测试层错误引用 | 提示 smoke test 定义错误 |
| 单个 case 前置构造失败 | 继续其他 case，suite 最终失败 | 该 case 失败 | 测试层错误引用 | 提示用例前置条件无法构造 |
| 缺配置用例没有失败 | 继续其他 case，suite 最终失败 | 该 case 失败 | 记录期望失败未发生 | 提示配置预检查链路失效 |
| 缺输入用例没有失败 | 继续其他 case，suite 最终失败 | 该 case 失败 | 记录期望失败未发生 | 提示输入预检查链路失效 |
| fake service 可控失败未生成错误摘要 | 继续其他 case，suite 最终失败 | 该 case 失败 | 记录缺少错误摘要产物 | 提示错误摘要链路未闭环 |
| 全流程 fake 失败后仍继续后续场景 | 继续其他 case，suite 最终失败 | 该 case 失败 | 记录失败停止策略错误 | 提示调度失败停止策略失效 |

## 13. 状态流转

| 状态 | 进入条件 | 退出条件 | 记录位置 |
| --- | --- | --- | --- |
| planned | [[RuntimeSmokeTestSuite]] 已选择 | 开始执行第一个 case | suite 执行摘要 |
| setting_up | 正在构造 case 前置条件 | 前置条件构造完成或失败 | [[RuntimeSmokeTestResult]] |
| running | 当前 case 正在调用 Runtime 主流程 | Runtime 返回 [[PipelineResult]] 或异常 | [[RuntimeSmokeTestResult]] |
| asserting | 正在比较期望与实际结果 | 所有断言完成 | [[RuntimeSmokeTestResult]].`assertions` |
| passed | case 所有断言通过 | suite 汇总 | [[RuntimeSmokeTestResult]] |
| failed | case 任一断言失败或运行异常 | suite 汇总 | [[RuntimeSmokeTestResult]] |

## 14. 恢复与停止边界

- 可恢复情况：单个 case 失败后，可以继续执行 suite 中其他独立 case，并在 suite 汇总中报告失败。
- 必须停止情况：suite 定义不可解析、测试运行目录无法创建、基础 Runtime 类型不可导入。
- 不负责恢复的情况：自动修复配置、自动创建缺失输入、自动补写日志/manifest/error summary 文件。

## 15. 计算职责

本能力负责的判断或计算：

| 计算项 | 输入 | 输出 | 影响下游 |
| --- | --- | --- | --- |
| 用例期望判断 | [[RuntimeSmokeTestCase]]、[[PipelineResult]] | 断言通过/失败 | 决定 [[RuntimeSmokeTestResult]] |
| 错误码匹配 | [[RuntimeSmokeTestCase]].`expected_error_code`、[[RuntimeErrorRef]] | 匹配结果 | 验证错误摘要链路 |
| 产物存在性判断 | [[RuntimeSmokeTestCase]].`expected_artifacts`、[[RunArtifactPath]] | 产物检查结果 | 验证 run 目录、日志、manifest 和 error summary |
| suite 汇总 | 多个 [[RuntimeSmokeTestResult]] | suite 通过/失败 | Runtime MVP 验收 |

## 16. 计算规则

| 规则 | 触发条件 | 计算 / 判断方式 | 结果表达 |
| --- | --- | --- | --- |
| 单场景 fake 成功 | 目标场景为一个 [[SceneName]]，fake service 行为为成功 | [[PipelineResult]] 必须成功，且只执行目标场景 | [[RuntimeSmokeTestResult]] 通过 |
| fake 全流程成功 | 目标为全流程，所有 fake service 行为为成功 | 场景按约定顺序成功执行 | [[RuntimeSmokeTestResult]] 通过 |
| 缺配置失败 | 用例故意缺少 Runtime 级必需配置 | 必须停在配置预检查，且不调用 service | [[RuntimeSmokeTestResult]] 通过 |
| 缺输入失败 | 用例故意缺少目标场景输入产物 | 必须停在输入产物预检查，且不调用 service | [[RuntimeSmokeTestResult]] 通过 |
| 可控失败摘要 | fake service 行为为 `controlled_failure` | [[PipelineResult]] 失败，错误码稳定，后续场景停止 | [[RuntimeSmokeTestResult]] 通过 |
| 成功产物追溯 | 运行成功 | run 目录内应能定位 [[RunLogFile]] 和 [[ProcessingManifest]] | [[RuntimeSmokeTestResult]] 通过或等待功能8/9 L3 |
| 失败产物追溯 | 运行失败 | run 目录内应能定位 [[RunLogFile]] 和 [[ErrorSummary]] | [[RuntimeSmokeTestResult]] 通过或等待功能8/9 L3 |

## 17. 输出结果结构

| 字段 | 类型 | 含义 | 有效性要求 | 下游使用方式 |
| --- | --- | --- | --- | --- |
| `case_id` | string | smoke test 用例标识 | 必须来自 [[RuntimeSmokeTestCase]] | 定位失败用例 |
| `status` | [[RunStatus]] 或测试层状态 | 用例通过/失败/阻塞 | 必须能区分失败和未执行 | suite 汇总 |
| `pipeline_result` | [[PipelineResult]] 或空 | Runtime 主流程结果 | 主流程执行后应存在 | 判断运行状态 |
| `run_directory` | [[RunDirectory]] 或空 | 本用例运行目录 | 目录创建成功后应存在 | 检查产物 |
| `observed_artifacts` | map of [[RunArtifactPath]] | 观察到的运行产物 | 不得指向 raw MCAP 覆盖路径 | 追溯和断言 |
| `observed_error` | [[RuntimeErrorRef]] 或空 | 观察到的错误引用 | 失败用例应存在 | 错误码断言 |
| `assertions` | list | 每条断言结果 | 必须包含期望和实际 | 调试失败 |

## 18. 异常与边界输入

| 边界情况 | 预期结果 | reason / error 表达 | 是否阻塞下游 |
| --- | --- | --- | --- |
| 没有任何 smoke case | suite setup 失败 | `smoke_suite_empty` | 是 |
| case 引用未知场景 | case setup 失败 | `smoke_case_unknown_scene` | 是，仅阻塞该 case |
| case 要求真实 service | case setup 失败 | `smoke_case_real_service_not_allowed` | 是，仅阻塞该 case |
| 期望错误码为空但用例期望失败 | case 定义无效 | `smoke_case_expected_error_missing` | 是，仅阻塞该 case |
| 功能8/9代码接口尚未实现 | 对日志、manifest、error summary 断言标记为阻塞 | `smoke_upstream_artifact_interface_missing` | 是，阻塞最终 MVP 验收 |

## 19. 可验证样例

| 样例 | 输入特征 | 预期输出 | 验证方式 |
| --- | --- | --- | --- |
| 合法输入 | 单个目标场景，配置和输入预检查通过，fake service 成功 | [[PipelineResult]] 成功，生成 [[RuntimeSmokeTestResult]] | 后续 L3 用测试断言状态和目标场景数量 |
| 缺失输入 | 输入产物不存在或不可读 | [[PipelineResult]] 失败，service 不被调用 | 后续 L3 用测试断言错误码和调用次数 |
| 边界输入 | fake service 可控失败 | 后续场景停止，错误引用稳定 | 后续 L3 用测试断言 [[RuntimeErrorRef]] 和失败摘要产物 |

## 20. 整体完成标准

- [ ] 已建立 [[RuntimeSmokeTestCase]]、[[RuntimeSmokeTestSuite]] 和 [[RuntimeSmokeTestResult]] 的原子数据定义。
- [ ] 本 L2 能力模块说明中出现的数据概念均使用 Obsidian 双向链接。
- [ ] 已明确功能10覆盖单场景 fake 成功、fake 全流程成功、缺配置、缺输入和 fake service 可控失败。
- [ ] 已明确功能10复用功能8的 [[RunLogFile]] / [[RuntimeLogWriteResult]] 与功能9的 [[ProcessingManifest]] / [[ErrorSummary]] / [[RunResultIndex]]，不自行冻结其代码接口。
- [ ] 已明确 smoke test 通过只代表 Runtime MVP 调度和追溯骨架通过，不代表真实业务算法完成。

## 21. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- |
| runtime_mvp_030 | 定义 Runtime smoke test Types 与 suite 契约 | 数据定义类 | 本 L2、[[RuntimeSmokeTestCase]]、[[RuntimeSmokeTestSuite]]、[[RuntimeSmokeTestResult]] | smoke test 相关 Types 或等价测试数据结构 | `src/data_clean/schemas/` 或 `src/data_clean/tests/` 中合适位置 | 能构造 suite、case 和 result；非法 case 必须失败清楚 |
| runtime_mvp_031 | 实现单场景 fake 成功与 fake 全流程 smoke test | 流程编排类 | [[ServiceRegistry]]、[[FakeServicePlan]]、[[SceneDispatchPlan]] | 成功路径 [[RuntimeSmokeTestResult]] | `src/data_clean/tests/runtime/` 和必要 Runtime 接口 | 单场景和全流程 fake 成功均通过，且生成独立 run 目录 |
| runtime_mvp_032 | 实现缺配置与缺输入失败 smoke test | 数据计算类 | [[ConfigPrecheckResult]]、[[InputArtifactPrecheckSummary]] | 失败路径 [[RuntimeSmokeTestResult]] | `src/data_clean/tests/runtime/` 和必要 Runtime 接口 | 缺配置不调用 service；缺输入不调用 service；错误码稳定 |
| runtime_mvp_033 | 实现 fake service 可控失败与错误摘要 smoke test | 流程编排类 | [[FakeServiceBehavior]]、[[RuntimeErrorRef]]、[[ErrorSummary]]、[[RunResultIndex]] | 失败摘要路径 [[RuntimeSmokeTestResult]] | `src/data_clean/tests/runtime/` 和必要 Runtime/Repo 接口 | controlled_failure 生成失败 [[PipelineResult]]，后续场景停止，并能定位错误摘要产物 |

## 22. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 功能8结构化日志代码接口尚未实现 | smoke test 需要真实检查 `run_log.json`，但当前只有 L2 文件契约。 | 功能10 L3 必须依赖功能8对应 L3 的实现结果，或先保持阻塞断言。 | 功能8 L3 执行后确认。 |
| 功能9 Manifest 与错误摘要代码接口尚未实现 | 成功 manifest 和失败 error summary 是 Runtime MVP 完整验收条件。 | 功能10 L3 必须依赖功能9对应 L3 的实现结果，或先保持阻塞断言。 | 功能9 L3 执行后确认。 |
| smoke test 是否通过 CLI 入口执行 | 影响是否需要修改 `./start_data_clean.sh --dev`。 | Runtime MVP L2 第一版不修改启动脚本；后续若需要入口级验收，单独拆 L3。 | 生成功能10 L3 时确认。 |
| 测试框架和命令形式 | 影响 L3 验收命令。 | L3 中按现有项目测试环境选择，Python 命令必须使用 `python3`。 | 功能10 L3 执行时确认。 |

## 23. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 每个 L3 必须有明确输入、输出、修改边界、验收命令和成功标准。
4. 每个 L3 必须写明“本次不做什么”。
5. 每个 L3 不能跨越本 L2 的能力边界。
6. 如果需要修改本 L2 之外的模块，必须在 L3 文档中显式说明原因。
7. 涉及代码的 L3 必须使用 `$tdd`，并遵守 `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`。
