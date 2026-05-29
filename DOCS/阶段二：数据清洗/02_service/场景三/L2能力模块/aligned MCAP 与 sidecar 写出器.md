# L2 能力模块说明：aligned MCAP 与 sidecar 写出器

## 1. 能力名称

```text
aligned MCAP 与 sidecar 写出器
```

## 2. 所属位置

阶段：阶段二：数据清洗  
L1：service_s3  
场景：场景三：MCAP 多 topic 时间轴对齐  
模块类别：数据读写类  
来源功能模块清单：`DOCS/阶段二：数据清洗/02_service/场景三/功能模块清单.md`

## 3. 一句话目标

```text
写出 aligned MCAP、alignment index sidecar、alignment report 和 aligned MCAP 写出摘要。
```

## 4. 能力角色

本能力是场景三 P0 主链路的产物持久化层。它位于 [[对齐索引与报告数据生成器]] 之后，负责把内存态字段对齐结果、[[AlignmentIndex]] 数据和 [[AlignmentReport]] draft 写成场景三正式中间产物，并生成 [[AlignedMcapWriteSummary]]。

已按 `grill-me` 约束完成意图澄清：本能力是纯读写模块，采用临时目录整体提交策略；失败时不得留下误导性的完整 aligned MCAP；aligned MCAP 对 `missing_time`、`timeout`、`unavailable` 字段不写空占位消息，缺失事实只通过 [[AlignmentIndex]] 追溯。

## 5. 上游关系

- 直接上游是 [[对齐索引与报告数据生成器]] 输出的 [[AlignmentIndex]] 数据和 [[AlignmentReport]] draft。
- 字段值上游是 [[多策略字段对齐器]] 输出的 [[FieldAlignmentResult]]，其中 `message_ref` 和轻量 `derived_value` 用于写 aligned MCAP。
- 时间轴上游是 [[StepTimeline]]。
- 契约上游是 [[Scene3AlignmentConfig]]、[[AlignedMcap]]、[[AlignmentReport]]、[[AlignmentIndex]] 和 [[AlignedMcapWriteSummary]]。
- 输入主数据来源是场景二 [[McapA]]，本能力只读不改。

## 6. 下游关系

- 场景四 LeRobotDataset v3 构建读取 [[AlignedMcap]]、[[AlignmentIndex]]、[[AlignmentReport]] 和 [[AlignedMcapWriteSummary]]。
- 开发者入口 `scene3_aligned_mcap_write_check` 通过本能力输出检查文件写出、失败清理和报告路径补齐是否正确。
- 场景三完整 smoke test 依赖本能力确认对齐链路能形成可追溯的文件产物。

## 7. 上游接口对齐检查

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
|---|---|---|---|---|
| 多策略字段对齐器 | [[FieldAlignmentResult]] | 读取 `message_ref` 和轻量 `derived_value` 写 aligned MCAP | 已对齐 | 复用 |
| 对齐索引与报告数据生成器 | [[AlignmentIndex]] | 写出 `alignment_index.parquet`，不重新计算统计事实 | 已对齐 | 复用 |
| 对齐索引与报告数据生成器 | [[AlignmentReport]] draft | 补齐输出路径、run id 和写出状态后写出 final JSON | 已对齐 | 复用并补齐 |
| 对齐契约与配置定义 | [[AlignedMcap]] / [[AlignedMcapWriteSummary]] | 作为 aligned MCAP 与写出摘要契约 | 已对齐 | 复用 |
| 场景二 MCAP_A 生成器 | [[McapA]] | 只读原始 payload 或引用来源，不修改 MCAP_A | 已对齐 | 复用 |
| 场景三功能模块清单 | 第 6 个功能模块 | 作为本能力范围、上下游和优先级来源 | 已对齐 | 复用并细化 |

## 8. 职责边界

本能力负责：

1. 按 [[StepTimeline]] 和 [[FieldAlignmentResult]] 写出 [[AlignedMcap]]。
2. 将 [[AlignmentIndex]] 数据写出为 `alignment_index.parquet`。
3. 将 [[AlignmentReport]] draft 补齐为 final report 并写出 `alignment_report.json`。
4. 生成 [[AlignedMcapWriteSummary]]。
5. 管理临时目录、整体提交、失败清理和运行日志字段。

本能力不负责：

1. 不重新执行字段对齐算法。
2. 不重新生成 [[AlignmentIndex]] 统计数据。
3. 不决定训练 mask、episode 构建或 canonical dataset schema。
4. 不修改、覆盖或回写 [[McapA]]。
5. 不为缺失、超时或不可用字段制造空占位消息。

## 9. 读写职责

| 动作 | 读取来源 | 写入目标 | 格式 | 下游消费者 |
|---|---|---|---|---|
| 写 aligned MCAP | [[McapA]]、[[StepTimeline]]、[[FieldAlignmentResult]] | [[AlignedMcap]] | MCAP | 场景四、人工复查 |
| 写 alignment index sidecar | [[AlignmentIndex]] 数据对象 | `alignment_index.parquet` | Parquet | 场景四、report、人工复查 |
| 写 final alignment report | [[AlignmentReport]] draft、写出路径和状态 | `alignment_report.json` | JSON | 场景四、smoke test |
| 写 aligned MCAP 写出摘要 | 写出动作结果、输入输出路径、失败原因 | [[AlignedMcapWriteSummary]] | JSON | 场景三 smoke test、场景四输入索引 |
| 写运行日志 | 本次运行上下文、配置、关键步骤、错误信息 | 独立 run 目录 | JSON / text | 开发者验收 |

## 10. 路径与命名规则

| 文件 / 目录 | 路径来源 | 命名规则 | 是否允许覆盖 | 创建时机 |
|---|---|---|---|---|
| aligned MCAP 输出目录 | [[Scene3AlignmentConfig]].`output_dir`，默认 `asset/阶段二：数据清洗/dev/mcap_aligned/` | 按配置和 run 上下文确定 | 不覆盖上游 MCAP_A；同 run 内由写出策略控制 | 写出前创建 |
| [[AlignedMcap]] | [[AlignedMcap]] 契约 | `<mcap_a_stem>_aligned.mcap` 或 run 唯一路径 | 不直接覆盖既有完整产物 | 临时目录写成功后提交 |
| `alignment_index.parquet` | 同 aligned 输出目录或 run outputs | 固定文件名或带 run id 变体 | 不直接覆盖既有完整产物 | 临时目录写成功后提交 |
| `alignment_report.json` | 同 aligned 输出目录或 run outputs | 固定文件名或带 run id 变体 | 不直接覆盖既有完整产物 | final report 补齐后写出 |
| `aligned_mcap_write_summary.json` | 同 aligned 输出目录或 run outputs | 固定摘要文件名 | 可在失败时写失败摘要 | 写出完成或失败时 |
| 临时写出目录 | 独立 run 目录下 temp / staging 区 | run 唯一目录 | 每次运行独立 | 正式写出前 |

## 11. 文件格式与内容契约

| 文件 | 格式 | 必填内容 | 可选内容 | 校验方式 |
|---|---|---|---|---|
| [[AlignedMcap]] | MCAP | 有效对齐、插值、聚合或 fallback 的字段消息，时间戳使用 [[StepTimeline]].`step_time_ns` | 按字段策略写出的轻量派生消息 | MCAP reader 可读、topic/time 单调性检查 |
| `alignment_index.parquet` | Parquet | [[AlignmentIndex]] 全部事实字段 | 无主数据 payload | schema / row count / uniqueness 检查 |
| `alignment_report.json` | JSON | final [[AlignmentReport]]，包含输出路径、index 路径、status、run id | 质量降级摘要、字段统计 | JSON schema / 字段存在性检查 |
| `aligned_mcap_write_summary.json` | JSON | [[AlignedMcapWriteSummary]] 必填路径、step count、field count、status、failure reason | created_at、run id | JSON schema / 文件存在性检查 |
| 运行日志 | JSON / text | 输入、配置、执行步骤、关键状态、错误信息、输出位置 | 临时目录和提交动作细节 | 开发者人工检查 |

## 12. 覆盖策略与幂等性

- 重复运行时如何处理：每次开发者检验或 smoke test 使用独立 run 目录，避免污染旧 run。
- 是否允许覆盖已有文件：默认不直接覆盖既有完整产物；如需要覆盖，必须由配置或开发者本次运行临时覆盖明确表达。
- 如何避免污染旧 run：写出前创建 run 唯一临时目录，成功后整体提交到目标输出位置。
- 临时文件或半成品如何处理：成功后清理或标记临时目录；失败时不得把半成品提交为正式 aligned 产物，但允许保留失败摘要和运行日志。

## 13. 失败处理

| 失败情况 | 判断方式 | 处理策略 | 错误信息要求 | 是否写入报告 |
|---|---|---|---|---|
| 输入 [[AlignmentIndex]] 缺失 | 输入对象为空或不可读 | 停止写出 | `missing_alignment_index` | 写失败摘要 |
| report draft 缺失 | 输入 report draft 为空或不可读 | 停止写出 | `missing_alignment_report_draft` | 写失败摘要 |
| MCAP 写出失败 | writer 抛错或输出不可读 | 不提交完整产物，记录失败 | `aligned_mcap_write_failed` | 写失败摘要和日志 |
| Parquet 写出失败 | sidecar 写出或校验失败 | 不提交完整产物，记录失败 | `alignment_index_write_failed` | 写失败摘要和日志 |
| JSON report 写出失败 | report 序列化或写出失败 | 不提交完整产物，记录失败 | `alignment_report_write_failed` | 写失败摘要和日志 |
| 整体提交失败 | 临时目录提交到目标目录失败 | 保留 temp 诊断信息，不标记 completed | `atomic_commit_failed` | 写失败摘要和日志 |

## 14. 写出规则

| 规则 | 触发条件 | 写出行为 | 结果表达 |
|---|---|---|---|
| 只写有效字段消息 | `status` 为 `aligned`、`interpolated`、`aggregated` 或 `fallback_nearest` | 按 `message_ref` 或 `derived_value` 写 aligned MCAP 消息 | aligned MCAP 中存在该字段消息 |
| 缺失字段不写占位 | `status` 为 `missing_time`、`timeout` 或 `unavailable` | 不写空消息、不复用上一有效值 | [[AlignmentIndex]] 记录缺失事实 |
| 不修改 MCAP_A | 任意写出动作 | MCAP_A 只读 | [[AlignedMcapWriteSummary]].`input_mcap_a` 引用来源 |
| final report 补齐路径 | aligned MCAP / index 写出成功 | 补齐 `output_aligned_mcap`、`alignment_index`、`run_id` 和 status | `alignment_report.json` |
| 全部成功才 completed | 所有目标文件写出并校验通过 | 提交产物并写 completed 摘要 | [[AlignedMcapWriteSummary]].`status=completed` |

## 15. 整体完成标准

- [ ] 本能力明确复用 [[FieldAlignmentResult]]、[[AlignmentIndex]]、[[AlignmentReport]]、[[AlignedMcap]] 和 [[AlignedMcapWriteSummary]]。
- [ ] 临时目录整体提交策略已明确，失败时不留下误导性的完整 aligned MCAP。
- [ ] 缺失、超时、不可用字段不写空占位消息，缺失事实只由 [[AlignmentIndex]] 表达。
- [ ] final [[AlignmentReport]] 由第 6 模块补齐输出路径、index 路径、run id 和写出状态。
- [ ] 开发者入口 `scene3_aligned_mcap_write_check` 的输入、产物和人工验收方式已明确。

## 16. 开发者验收入口设计

| 项目 | 设计 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_aligned_mcap_write_check` / 检查 aligned MCAP 与 sidecar 写出是否正确 |
| 是否影响场景完整 smoke test | 是 |
| 小样本输入要求 | MCAP_A 小样本、[[FieldAlignmentResult]]、[[AlignmentIndex]] 数据、[[AlignmentReport]] draft、场景三对齐配置、run 目录上下文 |
| 调试输出目录要求 | 独立 run 目录，不写正式生产输出 |
| 测试产物 | aligned MCAP、`alignment_index.parquet`、`alignment_report.json`、`aligned_mcap_write_summary.json`、运行日志 |
| 运行日志最低字段 | 输入 MCAP_A、配置来源、临时目录、输出目录、写出步骤、status counts、写出文件路径、失败原因 |
| 临时覆盖配置 | 允许临时覆盖输出目录、覆盖策略和输入路径；覆盖只对本次运行生效 |
| 保存覆盖到配置文件 | 默认不保存；仅开发者明确选择时允许 |
| 人工最终验收方式 | 用户运行 `./start_data_clean.sh --dev` 后选择场景三和 `scene3_aligned_mcap_write_check`，检查四类产物、失败清理行为和运行日志是否符合本契约 |

## 17. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 自动化验收方式 | 开发者入口验收关联 |
|---|---|---|---|---|---|---|---|
| service_s3_019 | 定义 aligned MCAP 写出摘要与 final report 补齐类型 | 数据定义类 | 本 L2、[[AlignedMcapWriteSummary]]、[[AlignmentReport]] | 代码类型 / schema / JSON 序列化测试 | `src/data_clean/schemas/`、`src/data_clean/tests/` | `python3` 类型导入和 JSON 序列化测试 | 间接覆盖 `scene3_aligned_mcap_write_check` |
| service_s3_020 | 实现 alignment index 和 report sidecar 写出 | 数据读写类 | [[AlignmentIndex]]、[[AlignmentReport]] draft | `alignment_index.parquet`、`alignment_report.json` | `src/data_clean/repo/`、`src/data_clean/service/`、`src/data_clean/tests/` | `python3` IO / schema 测试 | `scene3_aligned_mcap_write_check` |
| service_s3_021 | 实现 aligned MCAP 最小写出与缺失字段跳过策略 | 数据读写类 | [[McapA]]、[[FieldAlignmentResult]]、[[StepTimeline]] | [[AlignedMcap]] | `src/data_clean/repo/`、`src/data_clean/service/`、`src/data_clean/tests/` | `python3` MCAP 写出测试，覆盖有效字段写入和缺失字段不占位 | `scene3_aligned_mcap_write_check` |
| service_s3_022 | 实现临时目录整体提交与失败摘要 | 数据读写类 | 写出服务、run 上下文、失败注入样例 | [[AlignedMcapWriteSummary]]、失败摘要、运行日志 | `src/data_clean/service/`、`src/data_clean/runtime/`、`src/data_clean/tests/` | `python3` failure / atomic commit 测试 | `scene3_aligned_mcap_write_check` |
| service_s3_023 | 接入场景三 aligned MCAP 写出开发者检验项 | 流程编排类 | 写出服务、小样本输入、配置 | 四类测试产物和运行日志 | `start_data_clean.sh`、`src/data_clean/runtime/`、`src/data_clean/ui/`、`src/data_clean/tests/` | `python3` CLI / smoke 测试 | `scene3_aligned_mcap_write_check` |

## 18. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
|---|---|---|---|
| aligned MCAP 中 pose / gripper / tactile 派生值的具体 ROS message 类型 | 影响写出实现细节 | L2 固定写出边界，具体 message 编码由 L3 按现有 repo writer 能力落定 | 后续 L3 执行结果 |
| 临时目录提交是 rename 还是 copy + marker | 影响跨文件系统行为和失败恢复 | 当前固定“整体提交”语义，具体原子性由 L3 根据运行目录实现 | 后续 L3 执行结果 |
| final report 是否与 aligned MCAP 同目录还是 run outputs 下引用 | 影响路径布局 | 当前要求同一次 run 可追溯，具体路径由配置和文件存放规范共同决定 | 后续 L3 执行结果 |

## 19. 给 L3 任务生成的约束

后续从本 L2 生成 L3 任务时，必须遵守：

1. 每个 L3 只能解决一个核心目标。
2. 每个 L3 必须先判断任务类别，并使用对应 L3 类别模板。
3. 本能力拆出的 L3 必须写入功能组 `service-s3-g6`，不得混入其他功能组。
4. 每个 L3 必须复用 [[FieldAlignmentResult]]、[[AlignmentIndex]]、[[AlignmentReport]]、[[AlignedMcap]] 和 [[AlignedMcapWriteSummary]]。
5. 第 6 模块不得重新实现字段对齐算法，不得重新计算第 5 模块统计结果。
6. 写出器必须采用临时目录整体提交策略，失败时不得留下误导性的完整 aligned MCAP。
7. `missing_time`、`timeout`、`unavailable` 字段不得写空占位消息，不得复用上一有效值。
8. 每个 Service 场景 L3 必须写明它对应或影响 `./start_data_clean.sh --dev` 下的 `scene3_aligned_mcap_write_check` 或场景三完整 smoke test。
9. L3 自动化验收只证明局部实现正确；场景最终验收必须由用户本人运行 `./start_data_clean.sh --dev` 后确认。
