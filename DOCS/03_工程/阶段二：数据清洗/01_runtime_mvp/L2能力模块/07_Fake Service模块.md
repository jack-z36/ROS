# L2 能力模块说明：Fake Service 模块

## 1. 能力名称

```text
Runtime MVP / Fake Service 模块
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：`runtime_mvp`  
场景：Runtime MVP，不归入 `02_service` 的具体业务场景  
模块类别：数据计算类  
来源功能模块清单：[[功能模块清单]]

## 3. 一句话目标

```text
在真实 Service 尚未完成前，为 Runtime 调度链路提供可控的成功和失败假结果。
```

## 4. 能力角色

```text
本能力是 Runtime MVP 的替身业务能力，只负责模拟 Service 返回结果，用来验证调度、日志、manifest 和错误摘要链路。
```

它消费 [[FakeServicePlan]]、[[RunContext]]、目标 [[SceneName]]、[[InputArtifactPrecheckSummary]] 和本次 [[RunDirectory]]，产出 [[FakeServiceResult]]。它不读取 MCAP，不执行真实清洗算法，不把 fake 输出解释为真实数据产物完成。

已按 `$grill-me` 约束完成意图澄清：从现有文档可确定功能7的边界是“验证 Runtime 空流程”，而不是提前实现任何场景一到场景五的业务处理；成功和可控失败都必须支持，以便后续 smoke test 验证错误摘要链路。

## 5. 上游关系

- 来自 [[06_场景注册与Service调度模块]] 的调度入口、[[ServiceRegistry]]、[[ServiceBinding]] 和 [[SceneDispatchPlan]]。
- 来自 [[RunContext]] 的运行 ID、目标 [[SceneName]]、[[ServiceMode]] 和本次 [[RunDirectory]]。
- 来自 [[InputArtifactPrecheckSummary]] 的输入预检查结论；fake service 只应在预检查通过后执行。
- 来自 [[RunArtifactPath]] 的运行产物路径语义。

## 6. 下游关系

- 场景注册与 Service 调度模块消费 [[FakeServiceResult]]，并将其转换或汇总为 [[SceneResult]]。
- 结构化日志模块记录 fake service 的开始、结束、输出声明和失败错误。
- Manifest 与错误摘要模块在成功时消费 fake 输出声明，在失败时消费 [[RuntimeErrorRef]]。
- Runtime smoke test 模块使用 fake service 验证单场景成功、单场景失败和 fake 全流程。

## 7. 上游接口对齐检查

开发本能力前，必须先按 `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md` 检查直接上游功能。

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
| --- | --- | --- | --- | --- |
| [[06_场景注册与Service调度模块]] | [[ServiceRegistry]]、[[ServiceBinding]]、[[SceneDispatchPlan]]、[[SceneDispatchEvent]] | 本能力需要被调度模块调用，并把 [[FakeServiceResult]] 交回调度模块汇总为 [[SceneResult]] | 已对齐 | 复用；代码层函数名在 L3 执行时收敛 |
| [[01_Runtime运行上下文定义]] | [[RunContext]]、[[SceneName]]、[[ServiceMode]]、[[RunStatus]]、[[RuntimeErrorRef]]、[[SceneResult]] | 表达目标场景、fake/real 模式、执行状态和错误引用 | 已对齐 | 复用 |
| [[02_Run目录管理模块]] | [[RunDirectory]]、[[RunArtifactPath]] | 限制 fake 输出声明只能指向本次 run 目录或允许的调试输出位置 | 已对齐 | 复用 |
| [[05_输入产物预检查模块]] | [[InputArtifactPrecheckSummary]] | fake service 只消费预检查摘要，不自行检查输入路径 | 已对齐 | 复用 |

## 8. 职责边界

本能力负责：

1. 根据 [[FakeServicePlan]] 和 [[FakeServiceBehavior]] 生成可控的 [[FakeServiceResult]]。
2. 在成功路径中声明目标 [[SceneName]] 的假输出路径和执行耗时。
3. 在失败路径中生成可被下游消费的 [[RuntimeErrorRef]]。
4. 明确 fake service 的输出只服务 Runtime 验收，不代表真实 Service 或真实数据产物完成。

本能力不负责：

1. 读取、解析、写入或修改 MCAP、Parquet、HDF5、Zarr 等真实数据文件。
2. 实现场景一到场景五的任何真实业务算法。
3. 决定场景执行顺序、全流程失败停止策略或重试策略。
4. 写入 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
5. 校验配置、输入产物或输出产物的真实业务内容。

## 9. 计算职责

本能力负责的判断或计算：

| 计算项 | 输入 | 输出 | 影响下游 |
| --- | --- | --- | --- |
| fake 行为解析 | [[FakeServicePlan]].`behavior` | [[FakeServiceBehavior]] | 决定返回成功、失败或跳过 |
| 假输出声明 | [[SceneName]]、[[RunDirectory]]、[[RunArtifactPath]] | `output_paths` | 日志、manifest 和 smoke test 可追溯 fake 输出 |
| 成功结果生成 | [[FakeServicePlan]]、开始/结束时间 | 成功 [[FakeServiceResult]] | 调度模块可汇总为成功 [[SceneResult]] |
| 失败结果生成 | [[FakeServicePlan]]、失败原因 | 失败 [[FakeServiceResult]] + [[RuntimeErrorRef]] | 错误摘要链路可被验证 |
| 输入摘要透传 | [[InputArtifactPrecheckSummary]] | `input_summary` | 日志可说明 fake service 是在什么输入前提下执行 |

## 10. 计算规则

| 规则 | 触发条件 | 计算 / 判断方式 | 结果表达 |
| --- | --- | --- | --- |
| service mode 必须为 fake | 收到 [[FakeServicePlan]] | 如果 [[ServiceMode]] 不是 `fake`，返回失败或拒绝执行 | `fake_service_mode_mismatch` |
| 成功行为 | [[FakeServiceBehavior]] 为 `success` | 不读取真实输入，只根据目标场景和 run 目录声明假输出 | [[FakeServiceResult]].`status` 为成功 |
| 可控失败行为 | [[FakeServiceBehavior]] 为 `controlled_failure` | 构造场景内 [[RuntimeErrorRef]]，错误码稳定可断言 | [[FakeServiceResult]].`status` 为失败 |
| 跳过行为 | [[FakeServiceBehavior]] 为 `skipped` | 第一版不作为默认路径；如出现必须显式表达未执行 | 不得伪装为成功 |
| 输出路径边界 | 需要声明 fake 输出 | 输出路径只能位于本次 [[RunDirectory]] 或其 `outputs/` 语义区域 | 路径逃逸时失败 |
| 不生成真实产物 | 任意 fake 行为 | 不写入 `asset/阶段二：数据清洗/prod/` 或覆盖上游产物 | fake 输出只进入结果摘要 |

## 11. 输出结果结构

| 字段 | 类型 | 含义 | 有效性要求 | 下游使用方式 |
| --- | --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 被模拟执行的场景 | 必须与计划一致 | 调度、日志和结果汇总 |
| `behavior` | [[FakeServiceBehavior]] | 本次 fake 行为 | 必须是受控取值 | smoke test 判断路径 |
| `status` | [[RunStatus]] | fake service 执行状态 | 成功/失败必须与 error 一致 | 转换为 [[SceneResult]] |
| `input_summary` | map 或空 | 输入预检查摘要 | 不保存完整文件内容 | 日志解释 |
| `output_paths` | map of [[RunArtifactPath]] | 假输出声明 | 不得冒充真实产物 | manifest 和 smoke test |
| `error` | [[RuntimeErrorRef]] 或空 | 失败错误引用 | 失败时必填 | 错误摘要 |
| `duration_ms` | integer | 执行耗时 | 不得为负 | 日志和验收 |

## 12. 异常与边界输入

| 边界情况 | 预期结果 | reason / error 表达 | 是否阻塞下游 |
| --- | --- | --- | --- |
| 调度模式不是 fake | fake service 拒绝执行 | `fake_service_mode_mismatch` | 是 |
| 未提供目标场景 | 返回失败 | `fake_service_scene_missing` | 是 |
| 目标场景不在受控枚举内 | 返回失败 | `unknown_scene_name` | 是 |
| 输入预检查未通过却调用 fake service | 返回失败或由调度模块阻止 | `input_precheck_required` | 是 |
| 输出路径不在 run 目录边界内 | 返回失败 | `fake_output_path_escape` | 是 |
| `controlled_failure` 行为 | 返回失败 [[FakeServiceResult]] | `fake_service_controlled_failure` | 是，用于验证错误摘要 |

## 13. 可验证样例

| 样例 | 输入特征 | 预期输出 | 验证方式 |
| --- | --- | --- | --- |
| 合法输入 | [[ServiceMode]] 为 `fake`，目标 [[SceneName]] 合法，行为为 `success` | 成功 [[FakeServiceResult]]，包含目标场景和假输出声明 | 单元测试构造 [[FakeServicePlan]] 并断言状态和输出路径 |
| 缺失输入 | 缺少目标 [[SceneName]] 或输入预检查摘要未通过 | 失败 [[FakeServiceResult]]，包含 [[RuntimeErrorRef]] | 单元测试断言错误码 |
| 边界输入 | 行为为 `controlled_failure` | 稳定失败，错误码为 `fake_service_controlled_failure` | smoke test 验证错误摘要链路可触发 |

## 14. 整体完成标准

- [ ] 已建立 [[FakeServicePlan]]、[[FakeServiceBehavior]] 和 [[FakeServiceResult]] 的原子数据定义。
- [ ] 本 L2 能力模块说明中出现的数据概念均使用 Obsidian 双向链接。
- [ ] 已明确功能6调度模块已经形成 L2，当前功能7通过 [[ServiceBinding]] 接入调度，不锁死具体函数名。
- [ ] 已明确 fake service 只模拟 Runtime 调用结果，不读取、不生成真实业务数据产物。
- [ ] 已定义成功路径和可控失败路径，能支撑后续 Runtime smoke test。
- [ ] 已明确失败路径必须返回可被错误摘要消费的 [[RuntimeErrorRef]]。

## 15. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- |
| runtime_mvp_020 | 定义 Fake Service Types 与行为枚举 | 数据定义类 | 本 L2、[[FakeServicePlan]]、[[FakeServiceBehavior]]、[[FakeServiceResult]] | fake service 相关 Types 或等价结构 | `src/data_clean/schemas/` 或 `src/data_clean/runtime/` 中合适位置 | 能构造成功计划、失败计划和结果对象，失败结果必须携带 [[RuntimeErrorRef]] |
| runtime_mvp_021 | 实现 Fake Service 成功与可控失败结果生成 | 数据计算类 | [[FakeServicePlan]]、[[RunContext]]、[[RunDirectory]] | [[FakeServiceResult]] | `src/data_clean/runtime/` 或 `src/data_clean/service/` 中合适位置 | `success` 返回成功结果，`controlled_failure` 返回稳定错误码 |
| runtime_mvp_022 | 为调度模块实现 Fake Service 调用适配边界 | 流程编排类 | [[ServiceBinding]]、[[FakeServiceResult]]、[[SceneResult]] | 可被调度模块消费的 fake service 结果适配 | `src/data_clean/runtime/` 中合适位置 | 调度模块能通过绑定调用 fake service，并把 fake 结果汇总为 [[SceneResult]] |

## 16. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 功能6“场景注册与 Service 调度模块”的代码接口尚未实现 | 功能7最终由调度模块调用，代码接口会影响 L3 实现边界。 | 功能6 L2 已补齐语义接口；代码层调用方式在功能6/功能7 L3 执行时收敛。 | 调度与 fake service L3 执行时确认。 |
| fake service 是否实际创建占位输出文件 | 影响 smoke test 是否检查文件存在。 | 第一版只要求返回假输出声明；如需要落盘，拆为单独 L3，不在功能7 L2 中默认锁死。 | 生成功能7 L3 时确认。 |
| fake 全流程失败后是否继续后续场景 | 影响 [[FakeServiceBehavior]] 中 `skipped` 的使用。 | 第一版不在功能7决定，由功能6调度模块或功能10 smoke test 决定。 | 功能6或功能10设计时确认。 |

## 17. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 每个 L3 必须有明确输入、输出、修改边界、验收命令和成功标准。
4. 每个 L3 必须写明“本次不做什么”。
5. 每个 L3 不能跨越本 L2 的能力边界。
6. 如果需要修改本 L2 之外的模块，必须在 L3 文档中显式说明原因。
