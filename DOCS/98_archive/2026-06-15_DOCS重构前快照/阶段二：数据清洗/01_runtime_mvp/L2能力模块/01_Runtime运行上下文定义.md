# L2 能力模块说明：Runtime 运行上下文定义

## 1. 能力名称

```text
Runtime MVP / Runtime 运行上下文定义
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：`runtime_mvp`  
场景：Runtime MVP，不归入 `02_service` 的具体业务场景  
模块类别：数据定义类  
来源功能模块清单：[[功能模块清单]]

## 3. 一句话目标

```text
定义 Runtime MVP 一次运行所需的最小数据语义，让后续 run 目录、配置快照、预检查、调度、日志、manifest 和错误摘要共享同一份运行事实。
```

## 4. 能力角色

```text
本能力是 Runtime MVP 的数据语义基座，负责定义“运行上下文”和相关结果、状态、错误引用等概念长什么样。
```

它不负责真正创建目录、读取配置、检查输入、调用 Service 或写出报告；这些动作由后续 L2 模块实现。本能力只负责把这些模块共同依赖的数据概念先定义清楚。

## 5. 上游关系

- 来自阶段二宏观蓝图的入口模式：开发者端 `./start_data_clean.sh --dev` 与用户端 `./start_data_clean.sh`。
- 来自 Runtime MVP 功能模块清单的主干顺序：运行上下文 -> run 目录 -> 配置 -> 预检查 -> 调度 -> 日志/manifest/error summary。
- 来自阶段二文件存放规范的路径边界：Runtime 运行记录、真实数据产物和调试产物必须隔离。
- 来自用户选择或默认入口策略的运行模式、目标场景、输入路径、配置路径和输出根目录。

## 6. 下游关系

- Run 目录管理模块需要读取 [[RunContext]] 中的 `run_id`、[[RunMode]]、目标 [[SceneName]] 和输出位置，并回填 run 目录语义。
- 配置加载与配置快照模块需要读取 [[RunContext]] 的配置来源，并回填配置快照路径。
- 配置预检查和输入产物预检查模块需要读取 [[RunMode]]、目标 [[SceneName]] 和输入路径语义。
- 场景注册与 Service 调度模块需要读取 [[ServiceMode]] 和目标 [[SceneName]]，并产出 [[SceneResult]]。
- 结构化日志模块需要记录 [[RuntimeStepRecord]]、[[RunStatus]] 和错误上下文。
- Manifest 与错误摘要模块需要消费 [[RunContext]]、[[SceneResult]]、[[PipelineResult]] 和 [[RuntimeErrorRef]]。
- Runtime smoke test 模块需要验证以上数据概念在成功和失败路径中都可追溯。

## 7. 职责边界

本能力负责：

1. 定义 Runtime 运行上下文相关数据概念。
2. 明确每个数据概念的现实语义、字段或取值、有效性规则和上下游关系。
3. 为后续 L3 任务提供 Types、状态流转结果和错误引用的语义依据。

本能力不负责：

1. 创建 `src/data_clean/runs/{run_id}/`。
2. 读取 YAML/JSON 配置内容。
3. 检查 raw、cleaned、validated、aligned 或 canonical dataset 是否真实存在。
4. 调用 fake service 或真实 service。
5. 写出 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。

## 8. 数据定义范围

本能力需要定义的数据概念：

| 数据概念 | 类型 | 现实语义 | 原子定义文档 | 下游使用者 |
| --- | --- | --- | --- | --- |
| [[RunContext]] | dataclass / model | 一次 Runtime 运行的完整上下文快照。 | `L2数据定义/RunContext.md` | Run 目录、配置快照、预检查、调度、日志、manifest、错误摘要。 |
| [[RunStatus]] | enum | 运行、场景结果或步骤记录的状态。 | `L2数据定义/RunStatus.md` | [[RunContext]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]]。 |
| [[RunMode]] | enum | 区分开发者/生产、单场景/全流程的运行模式。 | `L2数据定义/RunMode.md` | [[RunContext]]、配置预检查、调度、UI。 |
| [[SceneName]] | enum | 阶段二五个业务场景的统一短名称。 | `L2数据定义/SceneName.md` | [[RunContext]]、[[SceneResult]]、调度、输入预检查、日志。 |
| [[ServiceMode]] | enum | 本次调度使用 fake service 还是真实 service。 | `L2数据定义/ServiceMode.md` | [[RunContext]]、调度、fake service、smoke test。 |
| [[SceneResult]] | dataclass / model | 单个场景执行后的最小结果摘要。 | `L2数据定义/SceneResult.md` | [[PipelineResult]]、日志、manifest、错误摘要。 |
| [[PipelineResult]] | dataclass / model | 单场景或全流程结束后的最终结果摘要。 | `L2数据定义/PipelineResult.md` | UI 结束反馈、run result、manifest、错误摘要。 |
| [[RuntimeStepRecord]] | dataclass / log event | Runtime 某个执行步骤的结构化记录。 | `L2数据定义/RuntimeStepRecord.md` | 结构化日志、错误定位、smoke test。 |
| [[RuntimeErrorRef]] | report ref / error object | 失败时可定位的结构化错误引用。 | `L2数据定义/RuntimeErrorRef.md` | [[SceneResult]]、[[PipelineResult]]、错误摘要、UI 失败反馈。 |

## 9. 字段表

本 L2 的字段细节分散在各原子数据定义文档中维护，避免重新形成一个“大而全”汇总定义。这里仅列出跨概念共享的关键字段语义。

| 字段 | 类型 | 现实含义 | 是否必需 | 默认值 | 合法值 / 范围 | 无效时如何表达 |
| --- | --- | --- | --- | --- | --- | --- |
| `run_id` | string | 本次 Runtime 运行的唯一身份。 | 是 | 无 | 非空，运行期间稳定不变。 | 阻止创建有效 [[RunContext]]。 |
| `run_mode` | [[RunMode]] | 本次运行处于哪种入口和范围。 | 是 | 无 | 见 [[RunMode]]。 | 阻止创建有效 [[RunContext]]。 |
| `service_mode` | [[ServiceMode]] | 本次调用 fake service 还是真实 service。 | 是 | Runtime MVP 可默认 fake | `fake` 或 `real`。 | 阻止调度。 |
| `target_scenes` | list of [[SceneName]] | 本次计划执行的阶段二场景。 | 是 | 无 | 非空；全流程按 scene1 到 scene5。 | 阻止调度。 |
| `status` | [[RunStatus]] | 运行、场景或步骤的当前状态。 | 是 | `created` 或由具体步骤设置 | 见 [[RunStatus]]。 | 写入 [[RuntimeErrorRef]] 或错误摘要。 |
| `error` | [[RuntimeErrorRef]] 或空 | 失败时的定位信息。 | 失败时必需 | 空 | 必须包含错误码、步骤和一行摘要。 | 错误摘要生成失败，不允许静默吞掉。 |

## 10. 序列化与兼容性要求

- 是否需要序列化：需要。[[RunContext]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]] 和 [[RuntimeErrorRef]] 都应能进入结构化日志、manifest 或错误摘要。
- 序列化格式：Runtime MVP 第一版以 JSON 兼容结构为主；配置快照仍由配置模块决定 YAML 或 JSON。
- 字段命名风格：建议使用 snake_case，保持 Python Types、JSON 日志和文档字段一致。
- 版本兼容要求：第一版不引入显式 schema version，但后续如果 [[RunContext]] 或结果对象字段发生破坏性变化，必须补充版本字段或迁移说明。
- 缺失字段处理：必需字段缺失时不得继续调度；应生成 [[RuntimeErrorRef]]，并由后续错误摘要模块写出失败原因。

## 11. 有效性规则

| 规则 | 判断方式 | 失败表达 | 是否阻塞下游 |
| --- | --- | --- | --- |
| `run_id` 必须非空且稳定 | 创建或更新 [[RunContext]] 时检查 | [[RuntimeErrorRef]]，错误码建议表达为上下文无效 | 是 |
| `run_mode` 必须属于 [[RunMode]] | 枚举校验 | [[RuntimeErrorRef]] | 是 |
| `service_mode` 必须属于 [[ServiceMode]] | 枚举校验 | [[RuntimeErrorRef]] | 是 |
| `target_scenes` 必须非空 | 列表长度检查 | [[RuntimeErrorRef]] | 是 |
| `target_scenes` 只能使用 [[SceneName]] | 枚举校验 | [[RuntimeErrorRef]] | 是 |
| 全流程场景顺序必须稳定 | 比对 scene1 到 scene5 顺序 | [[RuntimeErrorRef]] 或构建阶段拒绝 | 是 |
| 失败状态必须可定位错误 | [[RunStatus]] 为 failed 时检查 [[RuntimeErrorRef]] | 错误摘要生成失败 | 是 |

## 12. 使用边界

本数据定义只表达：

- Runtime 运行控制所需的上下文、状态、结果、步骤记录和错误引用。
- 后续 Runtime 横切能力之间共享的最小数据语义。
- 成功和失败路径中必须可追溯的运行事实。

本数据定义不表达：

- MCAP topic 内部消息结构。
- cleaned、validated、aligned 或 canonical dataset 的业务字段语义。
- Service 内部算法中间变量。
- 文件创建、配置加载、输入检查、调度执行、日志写入或 manifest 写入动作本身。

## 13. 整体完成标准

- [ ] 已为 [[RunContext]]、[[RunStatus]]、[[RunMode]]、[[SceneName]]、[[ServiceMode]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]] 和 [[RuntimeErrorRef]] 建立原子数据定义。
- [ ] 本 L2 能力模块说明中出现的数据概念均使用 Obsidian 双向链接。
- [ ] 开发者单场景、开发者全流程、生产单场景、生产全流程都能映射到 [[RunContext]]。
- [ ] 下游 run 目录、配置快照、预检查、调度、日志、manifest 和错误摘要模块能明确消费哪些数据概念。
- [ ] 本 L2 没有混入目录创建、配置加载、输入检查或调度编排的实现职责。

## 14. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- |
| runtime_mvp_001 | 定义 Runtime 上下文 Types | 数据定义类 | 本 L2 能力说明和相关原子数据定义 | 上下文相关 Types | `src/data_clean/schemas/` 或后续确定的 Types 位置 | 类型单测或最小构造测试通过 |
| runtime_mvp_002 | 定义 Runtime 状态与模式枚举 | 数据定义类 | [[RunStatus]]、[[RunMode]]、[[ServiceMode]]、[[SceneName]] | 枚举 Types | Types 层 | 枚举合法值测试通过 |
| runtime_mvp_003 | 定义 Runtime 结果与错误引用 Types | 数据定义类 | [[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]]、[[RuntimeErrorRef]] | 结果与错误引用 Types | Types 层 | 成功和失败结果构造测试通过 |

## 15. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| `run_id` 是否采用固定格式 | 影响目录命名和日志检索 | 第一版只要求唯一、可读、可追溯 | 用户或 L3 实现前确认 |
| 是否支持部分成功状态 | 影响全流程真实 Service 接入 | Runtime MVP 第一版不支持 | 真实 Service 全流程接入前确认 |
| fake service 是否允许生产模式使用 | 影响用户端安全边界 | 第一版只用于开发者 smoke test | 用户确认 |
| 是否需要为上下文对象引入显式 schema version | 影响长期兼容和日志回放 | 第一版暂不引入 | Runtime 日志与 manifest 模块设计时确认 |

## 16. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 每个 L3 必须有明确输入、输出、修改边界、验收命令和成功标准。
4. 每个 L3 必须写明“本次不做什么”。
5. 每个 L3 不能跨越本 L2 的能力边界。
6. 如果需要修改本 L2 之外的模块，必须在 L3 文档中显式说明原因。
