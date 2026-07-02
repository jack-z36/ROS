# L2 能力模块说明：统一 Step 时间轴生成器

## 1. 能力名称

```text
统一 Step 时间轴生成器
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：service_s3  
场景：场景三：MCAP 多 topic 时间轴对齐  
模块类别：数据计算类  
来源功能模块清单：`DOCS/阶段二：数据清洗/02_service/场景三/功能模块清单.md`

## 3. 一句话目标

```text
根据上游输入盘点结论、左右图像共同有效时间范围和目标频率生成统一 Step 时间轴。
```

## 4. 能力角色

本能力是场景三 P0 主链路的时间参考层。它位于 [[MCAP_A输入盘点与校验器]] 之后、[[多策略字段对齐器]] 之前，负责把 [[SourceTopicCatalog]] 和 [[McapAInputValidationSummary]] 中已经确认的左右图像共同有效区间，按 [[Scene3AlignmentConfig]] 中的 `target_step_hz` 转换为所有目标字段共享的 [[StepTimeline]]。

已按 `grill-me` 约束完成意图澄清：本能力只消费上游可消费结论，不重复 MCAP_A topic / type / time 盘点；时间轴从 baseline intersection 起点开始，不强制包含终点；15 Hz 等非整纳秒周期使用有理数累计后取整到 ns；允许共同有效区间短到只生成 1 个 step；成功或失败都输出 [[StepTimelineGenerationSummary]]；开发者入口独立暴露 `scene3_step_timeline_check`。

## 5. 上游关系

- 直接上游是 [[MCAP_A输入盘点与校验器]] 生成的 [[SourceTopicCatalog]] 和 [[McapAInputValidationSummary]]。
- 契约上游是 [[对齐契约与配置定义]] 产出的 [[Scene3AlignmentConfig]] 和 [[StepTimeline]]。
- [[SourceTopicCatalog]] 提供 `baseline_intersection_start_ns`、`baseline_intersection_end_ns` 和 `has_baseline_intersection`。
- [[McapAInputValidationSummary]] 提供 `status`、hard fail 结论和 baseline intersection 元数据。
- [[Scene3AlignmentConfig]] 提供 `target_step_hz`、range policy、baseline policy 和配置引用。

## 6. 下游关系

- [[多策略字段对齐器]] 读取 [[StepTimeline]]，把图像、位姿、触觉和夹爪等字段投影到同一条 step 时间轴。
- [[对齐索引与报告数据生成器]] 读取 [[StepTimeline]] 和 [[StepTimelineGenerationSummary]]，汇总 step 数、起止时间和时间轴生成参数。
- aligned MCAP 与 sidecar 写出器读取 [[StepTimeline]]，按统一 step 组织 aligned MCAP 和 sidecar 输出。
- 开发者入口 `scene3_step_timeline_check` 通过 [[StepTimeline]] 和 [[StepTimelineGenerationSummary]] 判断时间轴生成是否符合预期。
- 场景三完整 smoke test 间接依赖本能力，确保后续字段对齐使用同一条时间轴。

## 7. 上游接口对齐检查

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
|---|---|---|---|---|
| 场景三对齐契约与配置定义 | [[Scene3AlignmentConfig]] | 读取 `target_step_hz`、时间轴策略和配置引用 | 已对齐 | 复用 |
| 场景三对齐契约与配置定义 | [[StepTimeline]] | 作为本能力成功输出的统一时间轴契约 | 已对齐 | 复用 |
| MCAP_A 输入盘点与校验器 | [[SourceTopicCatalog]] | 读取 baseline intersection 元数据，不重复 topic 盘点 | 已对齐 | 复用 |
| MCAP_A 输入盘点与校验器 | [[McapAInputValidationSummary]] | 判断输入是否 `consumable`，并读取 hard fail 结论 | 已对齐 | 复用 |
| 本能力新增定义 | [[StepTimelineGenerationSummary]] | 表达时间轴生成状态、失败原因和参数快照 | 已对齐 | 新增原子定义 |
| 场景三功能模块清单 | 第 3 个功能模块 | 作为本能力范围、上下游和优先级来源 | 已对齐 | 复用并细化 |

## 8. 职责边界

本能力负责：

1. 校验上游输入盘点结论是否允许生成时间轴。
2. 读取左右图像共同有效时间范围和 `target_step_hz`。
3. 按统一规则生成 [[StepTimeline]] 的 step 时间戳序列。
4. 生成 [[StepTimelineGenerationSummary]]，表达成功、失败、起止边界、频率和 step 统计。
5. 为开发者功能检验项 `scene3_step_timeline_check` 提供可机器读取的调试产物。

本能力不负责：

1. 不读取 MCAP_A 原始消息。
2. 不重复执行 topic、message type、样本数或时间戳排序盘点。
3. 不执行最近邻、插值、slerp 或窗口聚合。
4. 不生成 step-field 对齐结果、[[AlignmentIndex]] 或 [[AlignmentReport]]。
5. 不决定训练 mask、episode 构建或 canonical dataset 可用性。

## 9. 计算职责

本能力负责的判断或计算：

| 计算项 | 输入 | 输出 | 影响下游 |
|---|---|---|---|
| 上游可消费状态检查 | [[McapAInputValidationSummary]].`status` | 是否允许生成时间轴 | 阻止下游在不可消费输入上继续对齐 |
| baseline intersection 检查 | [[SourceTopicCatalog]] / [[McapAInputValidationSummary]] 的共同有效区间字段 | 起止时间或失败 reason | 决定 [[StepTimeline]] 起止范围 |
| 目标频率检查 | [[Scene3AlignmentConfig]].`target_step_hz` | 有效频率或失败 reason | 决定 step 周期 |
| step 时间戳生成 | 起止时间、`target_step_hz` | [[StepTimeline]].`step_time_ns` 序列 | 给所有目标字段提供共同参考时间 |
| 时间轴统计 | [[StepTimeline]] | [[StepTimelineGenerationSummary]].`step_count`、首尾 step 时间 | 给报告和开发者检验项提供摘要 |

## 10. 计算规则

| 规则 | 触发条件 | 计算 / 判断方式 | 结果表达 |
|---|---|---|---|
| 只消费上游结论 | 收到 [[SourceTopicCatalog]] 和 [[McapAInputValidationSummary]] | 不重新读取 MCAP_A，不重复 topic/type/time 盘点 | 输入不合法时写入 [[StepTimelineGenerationSummary]].`failure_reasons` |
| 输入必须可消费 | [[McapAInputValidationSummary]].`status != consumable` | 停止时间轴生成 | `input_not_consumable` |
| baseline intersection 必须存在 | `has_baseline_intersection=false` 或起止时间为空 | 停止时间轴生成 | `missing_baseline_intersection` |
| 目标频率必须有效 | `target_step_hz <= 0` | 停止时间轴生成 | `invalid_target_step_hz` |
| 起止区间必须有效 | `start_time_ns > end_time_ns` | 停止时间轴生成 | `invalid_time_range` |
| 时间轴包含起点 | 输入合法 | `step_0 = baseline_intersection_start_ns` | [[StepTimeline]].`step_index=0` |
| 不强制包含终点 | 周期递增后超过 `end_time_ns` | 丢弃超过终点的 step | 最后一条 `step_time_ns <= end_time_ns` |
| 非整纳秒周期防漂移 | 15 Hz 等不能整除 ns 的频率 | 使用有理数累计，再四舍五入到整数 ns | `timestamp_rounding_policy=rational_accumulation_round_to_ns` |
| 短区间允许单 step | `start_time_ns <= end_time_ns` 但不足两个周期 | 生成 1 个 step | `step_count=1`，不失败 |

## 11. 输出结果结构

| 字段 | 类型 | 含义 | 有效性要求 | 下游使用方式 |
|---|---|---|---|---|
| [[StepTimeline]] | timeline object / JSON | 统一 step 时间轴 | 成功时必须生成，step 单调递增且不超过结束时间 | 字段对齐、report、写出器读取 |
| [[StepTimelineGenerationSummary]] | summary object / JSON | 时间轴生成结论和参数快照 | 成功或失败都必须生成 | 开发者入口、report、smoke test 读取 |
| `timeline_id` | string | 本次时间轴标识 | 成功时非空 | 关联后续对齐结果 |
| `step_count` | integer | 生成 step 数 | 成功时大于等于 1，失败时为 0 | 下游统计和人工检查 |
| `step_time_ns` | list / repeated integer | 每个 step 的统一时间戳 | 单调递增，首项等于起点，末项不超过终点 | 第 4 模块逐字段对齐 |
| `failure_reasons` | list[string] | 失败原因 | 失败时至少一项，成功时为空 | 开发者入口定位问题 |

## 12. 异常与边界输入

| 边界情况 | 预期结果 | reason / error 表达 | 是否阻塞下游 |
|---|---|---|---|
| 输入 summary 为 `not_consumable` | 不生成 [[StepTimeline]]，生成失败摘要 | `input_not_consumable` | 是 |
| baseline intersection 缺失 | 不生成 [[StepTimeline]]，生成失败摘要 | `missing_baseline_intersection` | 是 |
| `target_step_hz <= 0` | 不生成 [[StepTimeline]]，生成失败摘要 | `invalid_target_step_hz` | 是 |
| `start_time_ns > end_time_ns` | 不生成 [[StepTimeline]]，生成失败摘要 | `invalid_time_range` | 是 |
| `start_time_ns == end_time_ns` | 生成 1 个 step，时间戳等于起点和终点 | 无 | 否 |
| 区间短于一个周期 | 生成 1 个 step | 无 | 否 |
| 非基准字段缺失或不可用 | 不影响时间轴生成 | 上游 warning 保留，不新增 hard fail | 否 |

## 13. 可验证样例

| 样例 | 输入特征 | 预期输出 | 验证方式 |
|---|---|---|---|
| 合法输入 | `status=consumable`，baseline intersection 存在，`target_step_hz=15` | 生成 [[StepTimeline]] 和 `status=generated` 的 [[StepTimelineGenerationSummary]] | service / contract test |
| 缺失输入 | `status=not_consumable` | 不生成 [[StepTimeline]]，失败 reason 为 `input_not_consumable` | failure test |
| 缺失 baseline | `has_baseline_intersection=false` | 不生成 [[StepTimeline]]，失败 reason 为 `missing_baseline_intersection` | failure test |
| 无效频率 | `target_step_hz=0` | 不生成 [[StepTimeline]]，失败 reason 为 `invalid_target_step_hz` | config failure test |
| 单点区间 | `start_time_ns == end_time_ns` | 生成 1 个 step，step 0 等于 start | boundary test |
| 15 Hz 长序列 | 长时间范围、非整纳秒周期 | step 时间戳不出现固定截断漂移 | precision regression test |

## 14. 整体完成标准

- [ ] [[StepTimelineGenerationSummary]] 已形成原子数据定义。
- [ ] 本能力明确复用 [[SourceTopicCatalog]]、[[McapAInputValidationSummary]]、[[Scene3AlignmentConfig]] 和 [[StepTimeline]]。
- [ ] 时间轴边界规则已明确：包含起点、不强制包含终点、所有 step 不超过结束时间。
- [ ] 15 Hz 等非整纳秒周期的有理数累计取整策略已明确。
- [ ] 输入防御边界已明确：只做契约防御检查，不重复上游 MCAP_A 盘点。
- [ ] 开发者入口 `scene3_step_timeline_check` 的输入、产物和人工验收方式已明确。

## 15. 开发者验收入口设计

| 项目 | 设计 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_step_timeline_check` / 检查统一 Step 时间轴生成是否正确 |
| 是否影响场景完整 smoke test | 是 |
| 小样本输入要求 | `source_topic_catalog.json`、`mcap_a_input_validation_summary.json`、场景三对齐配置 |
| 调试输出目录要求 | 独立 run 目录，不写正式生产输出 |
| 测试产物 | `step_timeline.json` 或等价结构化产物、`step_timeline_generation_summary.json`、运行日志 |
| 运行日志最低字段 | catalog 路径、validation summary 路径、配置来源、target step Hz、baseline intersection 起止时间、step count、失败原因、输出位置 |
| 临时覆盖配置 | 允许临时覆盖 `target_step_hz` 和输入 summary / catalog 路径；覆盖只对本次运行生效 |
| 保存覆盖到配置文件 | 默认不保存；仅开发者明确选择时允许 |
| 人工最终验收方式 | 用户运行 `./start_data_clean.sh --dev` 后选择场景三和 `scene3_step_timeline_check`，检查 step 0、step 单调性、终点边界、step count 和非整纳秒频率精度是否符合本契约 |

## 16. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 自动化验收方式 | 开发者入口验收关联 |
|---|---|---|---|---|---|---|---|
| service_s3_007 | 定义 Step 时间轴生成摘要类型 | 数据定义类 | 本 L2、[[StepTimelineGenerationSummary]]、[[StepTimeline]] | 代码类型 / schema / JSON 序列化测试 | `src/data_clean/schemas/`、`src/data_clean/tests/` | `python3` 类型导入和 JSON 序列化测试 | 间接覆盖 `scene3_step_timeline_check` |
| service_s3_008 | 实现统一 Step 时间轴生成服务 | 数据计算类 | [[SourceTopicCatalog]]、[[McapAInputValidationSummary]]、[[Scene3AlignmentConfig]] | [[StepTimeline]]、[[StepTimelineGenerationSummary]] | `src/data_clean/service/`、`src/data_clean/tests/` | `python3` service 测试，覆盖成功、失败、单 step 和 15 Hz 精度 | `scene3_step_timeline_check` |
| service_s3_009 | 接入场景三 Step 时间轴开发者检验项 | 流程编排类 | 时间轴生成服务、catalog / summary 小样本、场景三配置 | `step_timeline.json`、`step_timeline_generation_summary.json`、运行日志 | `start_data_clean.sh`、`src/data_clean/runtime/`、`src/data_clean/ui/`、`src/data_clean/tests/` | `python3` CLI / smoke 测试 | `scene3_step_timeline_check` |

## 17. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
|---|---|---|---|
| `StepTimeline` 在代码中最终采用单对象含列表还是逐 step record 序列 | 影响 schema 文件和序列化测试设计 | L2 固定语义和有效性，后续 L3 按第 1 功能组已有类型实现对齐 | 后续 L3 执行结果 |
| `step_timeline.json` 是否长期作为调试产物格式 | 影响开发者入口产物命名 | 当前允许“或等价结构化产物”，正式格式由 L3 按代码实现落定 | 后续 L3 执行结果 |
| 时间轴生成摘要是否需要被第 5 模块纳入最终 [[AlignmentReport]] | 影响 report 字段设计 | 当前作为第 5 模块可消费输入，不在本 L2 强制定义 report 字段 | 对齐索引与报告数据生成器 L2 |

## 18. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 本能力拆出的 L3 必须写入功能组 `service-s3-g3`，不得混入 `service-s3-g1` 或 `service-s3-g2`。
4. 每个 L3 必须复用 [[SourceTopicCatalog]]、[[McapAInputValidationSummary]]、[[Scene3AlignmentConfig]] 和 [[StepTimeline]]。
5. 本能力生成的代码或测试不得读取 MCAP_A 原始消息，不得重复实现 topic/type/time 盘点。
6. 时间轴生成必须包含起点、不强制包含终点，并保证最后一个 step 不超过 baseline intersection 结束时间。
7. 15 Hz 等非整纳秒周期必须使用有理数累计后取整到 ns，不得使用固定截断周期。
8. `start_time_ns <= end_time_ns` 时允许生成 1 个 step，不得把短区间直接判为失败。
9. `step_timeline.json` 和 `step_timeline_generation_summary.json` 是开发者检验项的必需调试产物或等价结构化产物。
10. 每个 Service 场景 L3 必须写明它对应或影响 `./start_data_clean.sh --dev` 下的 `scene3_step_timeline_check` 或场景三完整 smoke test。
11. L3 自动化验收只证明局部实现正确；场景最终验收必须由用户本人运行 `./start_data_clean.sh --dev` 后确认。
