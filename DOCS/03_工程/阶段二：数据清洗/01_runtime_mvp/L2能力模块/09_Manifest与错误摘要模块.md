# L2 能力模块说明：Manifest 与错误摘要模块

## 1. 能力名称

```text
Runtime MVP / Manifest 与错误摘要模块
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：`runtime_mvp`  
场景：Runtime MVP，不归入 `02_service` 的具体业务场景  
模块类别：数据读写类 + 数据定义类  
来源功能模块清单：[[功能模块清单]]

## 3. 一句话目标

```text
在 Runtime 运行结束时，成功路径写出 processing_manifest.json，失败路径写出 error_summary.json，并统一写出 run_result.json。
```

## 4. 能力角色

```text
本能力是 Runtime MVP 的结束态追溯写入模块，负责把运行结果固化为可查、可验收、可交接的 JSON 文件。
```

它消费 [[RunContext]]、[[RunDirectoryLayout]]、[[RunArtifactPath]]、[[ConfigSnapshot]]、[[RunLogFile]]、[[RuntimeLogWriteResult]]、[[RuntimeStepRecord]]、[[SceneResult]]、[[PipelineResult]] 和 [[RuntimeErrorRef]]，产出 [[ProcessingManifest]]、[[ErrorSummary]] 与 [[RunResultIndex]]。它不写结构化日志本体，也不实现任何真实数据清洗算法。

已按 `$grill-me` 约束完成意图澄清：从功能模块清单、Runtime 六件套和上游数据定义可确定功能9的边界是“结束态追溯文件写入”，不是日志采集、配置加载、调度或业务产物生成；本轮无需额外追问。

## 5. 上游关系

- 来自 [[01_Runtime运行上下文定义]] 的 [[RunContext]]、[[RunStatus]]、[[SceneName]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeErrorRef]] 和 [[RuntimeStepRecord]]。
- 来自 [[02_Run目录管理模块]] 的 [[RunDirectory]]、[[RunDirectoryLayout]] 和 [[RunArtifactPath]]，用于确定 `processing_manifest.json`、`error_summary.json` 和 `run_result.json` 的写入位置。
- 来自 [[03_配置加载与配置快照模块]] 的 [[ConfigSnapshot]]，用于 manifest 和失败摘要中的配置追溯。
- 来自 [[06_场景注册与Service调度模块]] 的 [[SceneResult]] 与 [[PipelineResult]]。
- 来自 [[07_Fake Service模块]] 的 fake 输出声明和失败 [[RuntimeErrorRef]]。
- 来自 [[08_结构化日志模块]] 的 [[RunLogFile]]、[[RuntimeLogWriteResult]]、`run_log.json` 路径和日志事件语义；功能9只读取日志路径与写入结果，不重新定义完整日志 schema。

## 6. 下游关系

- Runtime smoke test 模块检查成功路径是否写出 [[ProcessingManifest]] 和 [[RunResultIndex]]。
- Runtime smoke test 模块检查失败路径是否写出 [[ErrorSummary]] 和 [[RunResultIndex]]。
- UI 或入口脚本读取 [[RunResultIndex]] 向用户展示本次运行结果入口。
- 后续真实 Service 接入时，使用 [[ProcessingManifest]] 解释某次运行配置、输入、输出和 service 模式。

## 7. 上游接口对齐检查

开发本能力前，必须先按 `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md` 检查直接上游功能。

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
| --- | --- | --- | --- | --- |
| [[01_Runtime运行上下文定义]] | [[RunContext]]、[[RunStatus]]、[[SceneName]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeErrorRef]]、[[RuntimeStepRecord]] | 读取运行身份、最终状态、场景结果、失败引用和步骤记录 | 已对齐 | 复用 |
| [[02_Run目录管理模块]] | [[RunDirectory]]、[[RunDirectoryLayout]]、[[RunArtifactPath]] | 确定 manifest、error summary 和 run result 的目标路径 | 已对齐 | 复用 |
| [[03_配置加载与配置快照模块]] | [[ConfigSnapshot]] | 在 manifest 和 error summary 中记录本次配置快照路径 | 已对齐 | 复用 |
| [[06_场景注册与Service调度模块]] | [[SceneResult]]、[[PipelineResult]] | 根据最终结果判断成功写 manifest 或失败写 error summary | 已对齐 | 复用 |
| [[07_Fake Service模块]] | [[FakeServiceResult]]、[[RuntimeErrorRef]] | fake 成功输出进入 manifest，fake 失败错误进入 error summary | 已对齐 | 复用 |
| [[08_结构化日志模块]] | [[RunLogFile]]、[[RuntimeLogWriteResult]]、[[RuntimeLogEvent]]、[[RunArtifactPath]] | 本能力需要引用 run log 路径、日志写入状态和失败定位信息 | 已对齐 | 复用功能8日志文件与写入结果语义；不重新定义完整日志 schema |

## 8. 职责边界

本能力负责：

1. 定义 [[ProcessingManifest]]、[[ErrorSummary]] 和 [[RunResultIndex]] 的文件语义。
2. 在成功路径写入 `processing_manifest.json`。
3. 在失败路径写入 `error_summary.json`。
4. 无论成功或失败，都写入 `run_result.json` 作为统一结果索引。
5. 保证这些文件只写在本次 [[RunDirectory]] 下，不覆盖其他 run。
6. 保证失败摘要能定位失败场景、失败步骤和 [[RuntimeErrorRef]]。

本能力不负责：

1. 写入或维护 `run_log.json` 的完整事件流。
2. 创建 run 目录或决定 run 目录命名。
3. 加载配置、保存 `config_snapshot.yaml` 或校验配置内容。
4. 调用 fake service 或真实 service。
5. 生成、修改或校验真实 MCAP、Parquet、HDF5、Zarr 等业务产物。
6. 定义 canonical dataset 的生产级 manifest。

## 9. 读写职责

本能力负责的读写动作：

| 动作 | 读取来源 | 写入目标 | 格式 | 下游消费者 |
| --- | --- | --- | --- | --- |
| 写成功追溯清单 | [[RunContext]]、[[ConfigSnapshot]]、[[SceneResult]]、[[PipelineResult]]、[[RunArtifactPath]] | `processing_manifest.json` | JSON | Runtime smoke test、后续追溯 |
| 写失败摘要 | [[RunContext]]、[[RuntimeErrorRef]]、[[SceneResult]]、[[PipelineResult]]、[[RunArtifactPath]] | `error_summary.json` | JSON | Runtime smoke test、UI 失败反馈、人工排错 |
| 写统一结果索引 | [[PipelineResult]]、[[ProcessingManifest]] 或 [[ErrorSummary]]、[[RunDirectoryLayout]] | `run_result.json` | JSON | UI、smoke test、后续 Agent |

## 10. 路径与命名规则

| 文件 / 目录 | 路径来源 | 命名规则 | 是否允许覆盖 | 创建时机 |
| --- | --- | --- | --- | --- |
| `processing_manifest.json` | [[RunDirectoryLayout]].`processing_manifest_path` | 固定文件名 | 同一 run 内不允许重复覆盖已完成文件 | [[PipelineResult]] 成功后 |
| `error_summary.json` | [[RunDirectoryLayout]].`error_summary_path` | 固定文件名 | 同一 run 内不允许重复覆盖已完成文件 | [[PipelineResult]] 失败后 |
| `run_result.json` | [[RunDirectoryLayout]].`run_result_path` | 固定文件名 | 同一 run 内只允许最终写一次 | manifest 或 error summary 写入后 |

## 11. 文件格式与内容契约

| 文件 | 格式 | 必填内容 | 可选内容 | 校验方式 |
| --- | --- | --- | --- | --- |
| `processing_manifest.json` | JSON | `schema_version`、`run_id`、`status`、`target_scenes`、`config_snapshot_path`、`run_log_path`、`scene_results`、`created_at` | `input_artifacts`、`output_artifacts`、`tool_versions`、`metadata` | 必填字段非空；状态为成功；路径在本次 [[RunDirectory]] 下 |
| `error_summary.json` | JSON | `schema_version`、`run_id`、`status`、`failed_step`、`error`、`run_log_path`、`message`、`created_at` | `failed_scene`、`config_snapshot_path`、`scene_results`、`suggested_next_action` | 必填字段非空；状态为失败；`error` 满足 [[RuntimeErrorRef]] 规则 |
| `run_result.json` | JSON | `schema_version`、`run_id`、`status`、`run_dir`、`run_log_path`、`scene_results`、`created_at` | `manifest_path`、`error_summary_path` | 成功时有 `manifest_path`；失败时有 `error_summary_path` |

## 12. 覆盖策略与幂等性

- 重复运行时如何处理：由 [[02_Run目录管理模块]] 创建新的 [[RunDirectory]]；功能9不复用旧 run。
- 是否允许覆盖已有文件：同一 run 内不允许覆盖已经成功写完的 `processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 如何避免污染旧 run：所有目标路径必须来自本次 [[RunDirectoryLayout]]，不得从用户输入路径拼接任意输出位置。
- 临时文件或半成品如何处理：L3 实现时应优先采用临时文件写入后原子替换，或在写入失败时留下清楚的 [[RuntimeErrorRef]]。

## 13. 失败处理

| 失败情况 | 判断方式 | 处理策略 | 错误信息要求 | 是否写入报告 |
| --- | --- | --- | --- | --- |
| 目标路径不在本次 [[RunDirectory]] 下 | 路径归属检查失败 | 拒绝写入并生成 [[RuntimeErrorRef]] | 包含目标路径和 run 目录 | 是，尽量写入 [[ErrorSummary]]；若错误摘要路径自身非法，则返回内存态错误 |
| 成功路径缺少 [[ConfigSnapshot]] 或 [[SceneResult]] | manifest 必填字段缺失 | 不写 manifest，转为失败路径 | 指明缺失字段 | 是 |
| 失败路径缺少 [[RuntimeErrorRef]] | error summary 必填字段缺失 | 生成包装错误引用 | 指明原始失败没有结构化错误 | 是 |
| JSON 序列化失败 | 写入前序列化异常 | 停止写入，返回写入失败错误 | 包含字段名或不可序列化类型 | 是，若可行写入最小错误摘要 |
| `run_result.json` 写入失败 | 文件写入异常 | 返回最终失败，提示用户查看 run 目录 | 包含目标路径 | 否或写入失败状态由内存态 [[PipelineResult]] 携带 |

## 14. 数据定义范围

本能力需要定义的数据概念：

| 数据概念 | 类型 | 现实语义 | 原子定义文档 | 下游使用者 |
| --- | --- | --- | --- | --- |
| [[ProcessingManifest]] | report / JSON schema | 成功运行的追溯清单 | `L2数据定义/ProcessingManifest.md` | Runtime smoke test、后续追溯 |
| [[ErrorSummary]] | report / JSON schema | 失败运行的结构化摘要 | `L2数据定义/ErrorSummary.md` | Runtime smoke test、UI、人工排错 |
| [[RunResultIndex]] | report / JSON schema | 每次运行的统一结果入口 | `L2数据定义/RunResultIndex.md` | UI、smoke test、后续 Agent |

## 15. 字段表

| 字段 | 类型 | 现实含义 | 是否必需 | 默认值 | 合法值 / 范围 | 无效时如何表达 |
| --- | --- | --- | --- | --- | --- | --- |
| `schema_version` | string | 文件结构版本 | 是 | 无 | 非空稳定字符串 | 写入失败或生成 [[RuntimeErrorRef]] |
| `run_id` | string | 运行唯一标识 | 是 | 无 | 与 [[RunContext]] 一致 | 写入失败 |
| `status` | [[RunStatus]] | 运行最终状态 | 是 | 无 | 成功或失败结束态 | 写入失败 |
| `scene_results` | list of [[SceneResult]] | 已执行场景摘要 | 是 | 空列表仅允许未进入场景的失败 | 每项满足 [[SceneResult]] | 写入失败或包装错误 |
| `error` | [[RuntimeErrorRef]] | 失败定位 | 失败文件必需 | 无 | 满足 [[RuntimeErrorRef]] 规则 | 包装为 `missing_runtime_error_ref` |
| `created_at` | datetime | 文件写入时间 | 是 | 写入时刻 | 可序列化时间 | 写入失败 |

## 16. 序列化与兼容性要求

- 是否需要序列化：需要。
- 序列化格式：JSON，UTF-8。
- 字段命名风格：snake_case。
- 版本兼容要求：所有文件必须包含 `schema_version`，后续新增字段应优先向后兼容。
- 缺失字段处理：必填字段缺失不得静默省略，必须失败并返回 [[RuntimeErrorRef]]。

## 17. 有效性规则

| 规则 | 判断方式 | 失败表达 | 是否阻塞下游 |
| --- | --- | --- | --- |
| 成功路径必须写 manifest | [[PipelineResult]].`status` 成功 | `processing_manifest_write_failed` | 是 |
| 失败路径必须写 error summary | [[PipelineResult]].`status` 失败 | `error_summary_write_failed` | 是 |
| 每次结束必须写 run result | manifest 或 error summary 写入后 | `run_result_write_failed` | 是 |
| 文件路径不得逃逸 run 目录 | 路径归属检查 | `run_artifact_path_escape` | 是 |
| JSON 必须可解析 | 写入后可重新读取并解析 | `runtime_result_json_invalid` | 是 |

## 18. 使用边界

本数据定义只表达：

- Runtime MVP 结束态追溯文件的最小稳定结构。
- fake service 和真实 service 都可复用的运行结果索引。
- 成功和失败两条路径的文件写入边界。

本数据定义不表达：

- 结构化日志完整事件 schema。
- 业务场景内部 report schema。
- canonical dataset 的生产级 processing manifest。
- Git、环境、依赖版本的最终采集策略。

## 19. 整体完成标准

- [ ] 已建立 [[ProcessingManifest]]、[[ErrorSummary]] 和 [[RunResultIndex]] 的原子数据定义。
- [ ] 本 L2 能力模块说明中出现的数据概念均使用 Obsidian 双向链接。
- [ ] 已按 grill-me 约束完成意图澄清：功能9只做 manifest、error summary 和 run result 的结束态写入，不实现日志采集、调度或业务算法。
- [ ] 已明确成功路径写 `processing_manifest.json`，失败路径写 `error_summary.json`，两者都写 `run_result.json`。
- [ ] 已明确功能9复用 [[08_结构化日志模块]] 的 [[RunLogFile]] 和 [[RuntimeLogWriteResult]]，不自行定义完整日志 schema。
- [ ] 已明确所有文件必须写入本次 [[RunDirectory]] 下。

## 20. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- |
| runtime_mvp_026 | 定义 Manifest 与错误摘要 Types | 数据定义类 | 本 L2、[[ProcessingManifest]]、[[ErrorSummary]]、[[RunResultIndex]] | manifest、error summary、run result 相关 Types 或等价结构 | `src/data_clean/schemas/` 或 `src/data_clean/runtime/` 中合适位置 | 能构造成功 manifest、失败 error summary 和 run result；必填字段缺失失败清楚 |
| runtime_mvp_027 | 实现成功路径 processing_manifest 写入器 | 数据读写类 | [[RunContext]]、[[ConfigSnapshot]]、[[RunLogFile]]、[[RuntimeLogWriteResult]]、[[PipelineResult]]、[[RunDirectoryLayout]] | `processing_manifest.json` | `src/data_clean/runtime/` 中合适位置 | 成功结果写出可解析 JSON，路径必须在 run 目录下 |
| runtime_mvp_028 | 实现失败路径 error_summary 写入器 | 数据读写类 | [[RunContext]]、[[RuntimeErrorRef]]、[[RunLogFile]]、[[RuntimeLogWriteResult]]、[[PipelineResult]]、[[RunDirectoryLayout]] | `error_summary.json` | `src/data_clean/runtime/` 中合适位置 | 失败结果写出可解析 JSON，错误码、失败步骤和日志路径可断言 |
| runtime_mvp_029 | 实现 run_result 统一结果索引 | 数据读写类 | [[PipelineResult]]、[[ProcessingManifest]] 或 [[ErrorSummary]]、[[RunDirectoryLayout]] | `run_result.json` | `src/data_clean/runtime/` 中合适位置 | 成功索引指向 manifest，失败索引指向 error summary |

## 21. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 功能8日志写入失败时功能9如何兜底 | 影响 `error_summary.json` 是否还能写出最小失败摘要。 | 功能9 L2 先要求消费 [[RuntimeLogWriteResult]]；若日志写入失败，错误摘要应至少记录该错误引用和预期日志路径。 | 生成功能9 L3 前确认。 |
| 失败时是否也写 `processing_manifest.json` | 影响失败路径追溯文件数量和索引互斥规则。 | Runtime MVP 第一版成功写 manifest，失败写 error summary。 | 后续真实 Service 全流程设计时确认。 |
| 是否记录代码版本、Git commit 和依赖版本 | 影响长期复现能力。 | 第一版放入 [[ProcessingManifest]].`tool_versions` 可选字段，不作为 P0 验收。 | Runtime smoke test 或真实 Service 接入前确认。 |

## 22. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 每个 L3 必须有明确输入、输出、修改边界、验收命令和成功标准。
4. 每个 L3 必须写明“本次不做什么”。
5. 每个 L3 不能跨越本 L2 的能力边界。
6. 如果需要修改本 L2 之外的模块，必须在 L3 文档中显式说明原因。
