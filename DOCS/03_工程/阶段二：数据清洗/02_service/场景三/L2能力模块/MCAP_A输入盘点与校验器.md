# L2 能力模块说明：MCAP_A 输入盘点与校验器

## 1. 能力名称

```text
MCAP_A 输入盘点与校验器
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：service_s3  
场景：场景三：MCAP 多 topic 时间轴对齐  
模块类别：数据计算类  
来源功能模块清单：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/功能模块清单.md`

## 3. 一句话目标

```text
读取 MCAP_A 和写出摘要，生成 [[SourceTopicCatalog]] 与 [[McapAInputValidationSummary]]，判断上游产物是否可被场景三消费。
```

## 4. 能力角色

本能力是场景三 P0 主链路的输入守门层。它位于 [[对齐契约与配置定义]] 之后、统一 Step 时间轴生成器之前，负责把场景二输出的 [[McapA]]、[[McapAWriteSummary]] 与场景三 [[Scene3AlignmentConfig]]、[[TargetFieldMapping]] 对齐，明确哪些输入问题会阻塞时间轴生成，哪些只是字段级 warning。

已按 `grill-me` 约束完成意图澄清：本能力输出拆为 [[SourceTopicCatalog]] 和 [[McapAInputValidationSummary]]；hard fail 只围绕 MCAP_A / summary 可追溯性、左右图像基准 topic 和基准共同有效时间范围；非基准字段问题不阻塞主链路；只计算左右图像交集元数据，不生成 [[StepTimeline]]；开发者入口独立暴露 `scene3_mcap_a_input_check`。

## 5. 上游关系

- 直接上游是场景二 MCAP_A 生成器输出的 [[McapA]] 和 [[McapAWriteSummary]]。
- 契约上游是场景三 [[对齐契约与配置定义]] 产出的 [[Scene3AlignmentConfig]] 和 [[TargetFieldMapping]]。
- [[McapA]] 保留 cleaned MCAP 的 topic 名称、消息类型、时间戳排序和样本数，是本能力唯一主输入 MCAP。
- [[McapAWriteSummary]] 用于校验输入 MCAP_A 是否来自成功写出动作，以及 `timestamp_policy` / `topic_policy` 是否符合 MCAP_A 契约。
- 左右图像基准 topic 由 [[Scene3AlignmentConfig]].`baseline_image_topics` 和 [[TargetFieldMapping]] 共同确定，首版默认为 `/gopro_left/image_raw` 与 `/gopro_right/image_raw`。

## 6. 下游关系

- 统一 Step 时间轴生成器读取 [[SourceTopicCatalog]] 中的基准 topic 时间范围和共同有效时间范围元数据，生成 [[StepTimeline]]。
- 多策略字段对齐器读取 [[SourceTopicCatalog]] 判断每个目标字段是否有可用来源 topic。
- 对齐索引与报告数据生成器读取 [[McapAInputValidationSummary]] 追溯输入质量和 warning。
- aligned MCAP 与 sidecar 写出器可把 [[SourceTopicCatalog]] 和 [[McapAInputValidationSummary]] 引用写入运行摘要。
- 开发者入口 `scene3_mcap_a_input_check` 通过本能力输出定位 MCAP_A 是否可消费。

## 7. 上游接口对齐检查

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
|---|---|---|---|---|
| 场景二 MCAP_A 生成器 | [[McapA]] | 读取 topic、message type、样本数、时间范围和时间戳顺序 | 已对齐 | 复用 |
| 场景二 MCAP_A 生成器 | [[McapAWriteSummary]] | 校验写出状态、输出路径、timestamp policy 和 topic policy | 已对齐 | 复用 |
| 场景三对齐契约与配置定义 | [[Scene3AlignmentConfig]] | 读取输入路径、summary 路径、baseline image topics、target fields 和阈值配置 | 已对齐 | 复用 |
| 场景三对齐契约与配置定义 | [[TargetFieldMapping]] | 判断每个目标字段是否能匹配到 MCAP_A topic | 已对齐 | 复用 |
| 场景三功能模块清单 | 第 2 个功能模块 | 作为本能力范围、上下游和优先级来源 | 已对齐 | 复用并细化 |

## 8. 职责边界

本能力负责：

1. 读取 [[McapA]] 和 [[McapAWriteSummary]] 并做 strict 可追溯性校验。
2. 根据 [[Scene3AlignmentConfig]] 和 [[TargetFieldMapping]] 盘点 MCAP_A 的 topic、message type、样本数、时间范围和时间戳顺序。
3. 生成 [[SourceTopicCatalog]]，同时表达真实 topic 事实、字段映射结果和未映射只读 topic。
4. 计算左右图像基准 topic 的共同有效时间范围元数据。
5. 生成 [[McapAInputValidationSummary]]，区分 hard fail 与 warning。

本能力不负责：

1. 不生成 [[StepTimeline]]。
2. 不读取或改写 MCAP 消息值。
3. 不执行最近邻、插值、slerp 或窗口聚合。
4. 不写出 aligned MCAP、alignment index 或 alignment report。
5. 不决定训练 mask、episode 构建或 canonical dataset schema。

## 9. 计算职责

本能力负责的判断或计算：

| 计算项 | 输入 | 输出 | 影响下游 |
|---|---|---|---|
| MCAP_A 文件可读性校验 | [[Scene3AlignmentConfig]].`input_mcap_a` | hard fail 或继续盘点 | 决定场景三是否能开始 |
| 写出摘要一致性校验 | [[McapAWriteSummary]]、输入 MCAP_A 路径 | `summary_consistency_status`、hard fail | 保证输入可追溯到成功 MCAP_A 写出 |
| topic 事实盘点 | [[McapA]] | [[SourceTopicCatalog]].`topic_entries` | 给字段映射、时间轴和调试入口提供事实基础 |
| 字段映射检查 | [[TargetFieldMapping]]、topic 事实 | [[SourceTopicCatalog]].`field_entries` | 给下游判断字段是否可用 |
| 基准 topic 状态检查 | 左右图像 topic entries | baseline topic 状态、hard fail / warning | 决定是否能生成统一时间轴 |
| 基准共同有效时间范围计算 | 左右图像 topic 时间范围 | `baseline_intersection_start_ns`、`baseline_intersection_end_ns`、`has_baseline_intersection` | 第 3 模块生成 [[StepTimeline]] 的直接输入 |
| 未映射 topic 盘点 | MCAP_A topic 列表、target fields | `unmapped_topics` | 保留输入全貌，避免误判保留 topic 为错误 |

## 10. 计算规则

| 规则 | 触发条件 | 计算 / 判断方式 | 结果表达 |
|---|---|---|---|
| MCAP_A 必须可读 | 输入路径缺失或不可读 | 停止 topic 盘点 | [[McapAInputValidationSummary]].`hard_fail_reasons += missing_mcap_a` |
| summary 必须 strict 一致 | summary 缺失、不可读、`status != completed`、`output_mcap_a` 不匹配、policy 不符合契约 | 判定输入不可消费 | `summary_consistency_status` 和 hard fail reason |
| 左右图像基准 topic 必须存在 | 任一 baseline image topic 缺失 | 标记对应 field blocking | `missing_baseline_topic` |
| 基准 topic 时间戳必须可用 | 左右图像任一 topic 乱序 | 标记输入不可消费 | `baseline_topic_out_of_order` |
| 基准共同有效时间范围必须存在 | 左右图像起止时间无交集 | 不生成 step，由第 3 模块停止 | `missing_baseline_intersection` |
| 非基准字段不阻塞主链路 | pose / tactile / gripper 等非基准字段缺失、类型不匹配、乱序或为空 | 记录字段可用性和 warning | `optional_field_warnings`，`blocking=false` |
| 未映射 topic 保留只读盘点 | MCAP_A 中存在但未出现在 `target_fields` 中 | 记录为只读输入事实 | [[SourceTopicCatalog]].`unmapped_topics` |

## 11. 输出结果结构

| 字段 | 类型 | 含义 | 有效性要求 | 下游使用方式 |
|---|---|---|---|---|
| [[SourceTopicCatalog]] | catalog object / JSON | MCAP_A topic 事实和字段映射盘点 | 必须引用 [[McapA]]、[[McapAWriteSummary]] 和 [[Scene3AlignmentConfig]] | 第 3 / 4 / 5 / 6 模块读取 |
| [[McapAInputValidationSummary]] | summary object / JSON | 输入可消费结论、hard fail 和 warning | `status=consumable` 时 hard fail 为空且基准交集存在 | 开发者入口和 smoke test 读取 |
| `baseline_intersection_start_ns` | integer/null | 左右图像共同有效区间开始时间 | 仅在有交集时非空 | 第 3 模块生成 [[StepTimeline]] |
| `baseline_intersection_end_ns` | integer/null | 左右图像共同有效区间结束时间 | 仅在有交集时非空 | 第 3 模块生成 [[StepTimeline]] |
| `field_entries.availability` | enum string | 每个目标字段来源是否可用 | 必须区分 missing / type mismatch / timestamp unusable | 第 4 模块决定字段对齐策略 |
| `unmapped_topics` | list[string] | 未配置但存在的只读 topic | 不得作为错误处理 | 人工调试和输入全貌检查 |

## 12. 异常与边界输入

| 边界情况 | 预期结果 | reason / error 表达 | 是否阻塞下游 |
|---|---|---|---|
| MCAP_A 不存在或不可读 | 输入不可消费 | `missing_mcap_a` | 是 |
| [[McapAWriteSummary]] 不存在或不可读 | 输入不可消费 | `missing_mcap_a_write_summary` / `unreadable_mcap_a_write_summary` | 是 |
| summary `status` 不是 `completed` | 输入不可消费 | `summary_not_completed` | 是 |
| summary `output_mcap_a` 与输入路径不一致 | 输入不可消费 | `summary_output_path_mismatch` | 是 |
| summary policy 不符合 MCAP_A 契约 | 输入不可消费 | `summary_policy_mismatch` | 是 |
| 左右图像基准 topic 任一缺失 | 输入不可消费 | `missing_baseline_topic` | 是 |
| 左右图像基准 topic 乱序 | 输入不可消费 | `baseline_topic_out_of_order` | 是 |
| 左右图像无共同有效时间范围 | 输入不可消费 | `missing_baseline_intersection` | 是 |
| 非基准字段缺失 | 主链路可继续 | `optional_field_missing` | 否 |
| 非基准字段类型不匹配 | 主链路可继续，字段标记不可用 | `optional_field_type_mismatch` | 否 |
| MCAP_A 存在未配置 topic | 进入只读盘点 | `unmapped_topic` | 否 |

## 13. 可验证样例

| 样例 | 输入特征 | 预期输出 | 验证方式 |
|---|---|---|---|
| 合法输入 | MCAP_A 可读，summary completed，左右图像存在且时间范围有交集 | `status=consumable`，生成 catalog 和 summary | contract / service test |
| 缺失输入 | MCAP_A 路径不存在 | `status=not_consumable`，hard fail 包含 `missing_mcap_a` | failure test |
| summary 不一致 | summary `output_mcap_a` 指向其他文件 | `status=not_consumable`，hard fail 包含 `summary_output_path_mismatch` | failure test |
| 基准 topic 缺失 | 只有左图像或右图像 | `status=not_consumable`，hard fail 包含 `missing_baseline_topic` | failure test |
| 非基准字段缺失 | pose 或 tactile topic 缺失，左右图像正常 | `status=consumable`，warning 记录可选字段缺失 | degradation test |
| 未映射 topic | MCAP_A 含 target_fields 未声明的 topic | topic 出现在 `unmapped_topics`，不产生 hard fail | catalog test |

## 14. 整体完成标准

- [ ] [[SourceTopicCatalog]] 和 [[McapAInputValidationSummary]] 已形成原子数据定义。
- [ ] 本能力明确复用场景二 [[McapA]] / [[McapAWriteSummary]]，不重新定义 validated MCAP 输入对象。
- [ ] hard fail 与 warning 边界已明确，左右图像基准 topic 问题阻塞，非基准字段问题不阻塞主链路。
- [ ] 本能力只计算基准共同有效时间范围元数据，不生成 [[StepTimeline]]。
- [ ] 开发者入口 `scene3_mcap_a_input_check` 的输入、产物和人工验收方式已明确。

## 15. 开发者验收入口设计

| 项目 | 设计 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_mcap_a_input_check` / 检查 MCAP_A 输入是否可消费 |
| 是否影响场景完整 smoke test | 是 |
| 小样本输入要求 | MCAP_A 小样本、`mcap_a_write_summary.json`、场景三对齐配置 |
| 调试输出目录要求 | 独立 run 目录，不写正式生产输出 |
| 测试产物 | `source_topic_catalog.json`、`mcap_a_input_validation_summary.json`、运行日志 |
| 运行日志最低字段 | 输入 MCAP_A、summary 路径、配置来源、baseline image topics、target fields 数量、hard fail、warning、输出位置 |
| 临时覆盖配置 | 允许临时覆盖输入 MCAP_A、summary 路径、baseline image topics 和输出目录；覆盖只对本次运行生效 |
| 保存覆盖到配置文件 | 默认不保存；仅开发者明确选择时允许 |
| 人工最终验收方式 | 用户运行 `./start_data_clean.sh --dev` 后选择场景三和 `scene3_mcap_a_input_check`，检查 catalog、validation summary 和运行日志是否符合本契约 |

## 16. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 自动化验收方式 | 开发者入口验收关联 |
|---|---|---|---|---|---|---|---|
| service_s3_004 | 定义 MCAP_A 输入盘点与校验类型 | 数据定义类 | 本 L2、[[SourceTopicCatalog]]、[[McapAInputValidationSummary]]、[[McapA]]、[[McapAWriteSummary]] | 代码类型 / schema / 序列化测试 | `src/data_clean/schemas/`、`src/data_clean/tests/` | `python3` 类型导入和 JSON 序列化测试 | 间接覆盖 `scene3_mcap_a_input_check` |
| service_s3_005 | 实现 MCAP_A topic/time/type 盘点与输入校验服务 | 数据计算类 | [[McapA]]、[[McapAWriteSummary]]、[[Scene3AlignmentConfig]]、[[TargetFieldMapping]] | [[SourceTopicCatalog]]、[[McapAInputValidationSummary]] | `src/data_clean/service/`、`src/data_clean/repo/`、`src/data_clean/tests/` | `python3` contract / service 测试，覆盖 hard fail 与 warning | `scene3_mcap_a_input_check` |
| service_s3_006 | 接入场景三 MCAP_A 输入检验开发者入口 | 流程编排类 | 输入盘点服务、MCAP_A 小样本、场景三配置 | `source_topic_catalog.json`、`mcap_a_input_validation_summary.json`、运行日志 | `start_data_clean.sh`、`src/data_clean/runtime/`、`src/data_clean/ui/`、`src/data_clean/tests/` | `python3` CLI / smoke 测试 | `scene3_mcap_a_input_check` |

## 17. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
|---|---|---|---|
| 场景三配置文件和 schema 文件的最终代码路径 | 影响 L3 类型和配置加载落点 | L2 只固定语义，后续 L3 按现有代码目录和第 1 模块实现结果落定 | 后续 L3 执行结果 |
| MCAP reader 是否能稳定暴露 ROS message type 与 schema name 的统一字段 | 影响 `message_type` 精确比较 | L2 固定必须比较语义，L3 可按现有 MCAP 工具封装统一读取 | 后续 L3 执行结果 |
| 非基准字段乱序是否长期标记为 warning 还是 unavailable | 影响第 4 模块是否尝试对齐该字段 | 当前要求不阻塞主链路，并在 catalog 中标记字段不可用或 warning | 多策略字段对齐器 L2 |

## 18. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 每个 L3 必须复用场景二 [[McapA]] 和 [[McapAWriteSummary]]，不得新增相似输入对象。
4. 每个 L3 必须复用 [[Scene3AlignmentConfig]] 和 [[TargetFieldMapping]]，不得自行猜测 baseline topic 或 target field 字段。
5. 本能力生成的代码或测试不得生成 [[StepTimeline]]，不得实现字段对齐算法。
6. hard fail 规则必须覆盖 MCAP_A / summary strict 一致性、左右图像基准 topic 和基准共同有效时间范围。
7. 非基准字段缺失、类型不匹配或乱序不得阻塞主链路，必须写入 warning 或字段可用性状态。
8. `source_topic_catalog.json` 和 `mcap_a_input_validation_summary.json` 是开发者检验项的必需调试产物。
9. 每个 Service 场景 L3 必须写明它对应或影响 `./start_data_clean.sh --dev` 下的场景三功能检验项或场景完整 smoke test。
10. L3 自动化验收只证明局部实现正确；场景最终验收必须由用户本人运行 `./start_data_clean.sh --dev` 后确认。
