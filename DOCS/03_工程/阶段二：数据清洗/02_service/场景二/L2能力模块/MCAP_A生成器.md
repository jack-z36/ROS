# L2 能力模块说明：MCAP_A 生成器

## 1. 能力名称

```text
MCAP_A 生成器
```

## 2. 所属位置

阶段：阶段二：数据清洗
L1：service_s2
场景：场景二：硬件数据可靠性验证
模块类别：数据读写类
来源功能模块清单：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/功能模块清单.md`

## 3. 一句话目标

```text
将补全和滤波后的位姿、触觉、夹爪主数据写入保留 cleaned MCAP topic/time 结构的 [[McapA|MCAP_A]]，并通过 sidecar [[McapAWriteSummary]] 追溯写出过程。
```

## 4. 能力角色

本能力是场景二 P0 主数据链路的 validated MCAP 统一 Runtime 与写出层。它创建一个运行上下文，一次加载分析样本并在 RAM 内依次调用检测、处置、修复和滤波阶段，最后把结果落成 [[McapA|MCAP_A]]。

已按 `grill-me` 约束完成意图澄清：MCAP_A 保留 cleaned MCAP 原 topic 结构；默认写入 `asset/阶段二：数据清洗/dev/mcap_validated/`；追溯信息写 sidecar JSON；缺少 [[SignalRepairResult]]、[[PoseFilterResult]] 或 [[TactileFilterResult]] 时严格失败，不生成 MCAP_A。

## 5. 上游关系

- 直接上游是 [[数据补全器]]、[[位姿滤波器]] 和 [[触觉滤波器]]。
- 来源 MCAP 是场景一 [[CleanedMcap]]。
- 夹爪主数据来自 [[SignalRepairResult]] 中的补全后 gripper 序列引用。
- 位姿主数据来自 [[PoseFilterResult]] 中的滤波后 pose 序列引用。
- 触觉主数据来自 [[TactileFilterResult]] 中的滤波后 tactile 序列引用。
- 写出策略来自 [[McapAWriteConfig]]。

## 6. 下游关系

- 场景三直接读取 MCAP_A 中保持 source-frame 语义的 TCP pose；未来 IK 如需 arm-base 输入，应在其自身边界显式转换。
- 场景三时间轴对齐消费 [[McapA|MCAP_A]] 作为 validated 主 MCAP。
- Parquet 标注与验证报告生成器消费 [[McapAWriteSummary]] 和上游审计结果。
- 开发者入口 `scene2_mcap_a_writer` 展示 MCAP_A 写出结果、topic 对齐统计和运行日志。

## 7. 上游接口对齐检查

| 上游功能 | 上游接口 / 产物 | 本能力如何依赖 | 对齐状态 | 处理方式 |
|---|---|---|---|---|
| 场景一 cleaned MCAP 契约 | [[CleanedMcap]] | 作为复制 topic、消息类型、时间戳和未处理 topic 的来源 | 已对齐 | 复用 |
| 数据补全器 | [[SignalRepairResult]] | 读取 `output_sequence_refs` 中的 gripper 补全后序列，校验 `timestamp_policy=preserve_original` | 已对齐 | 复用 |
| 位姿滤波器 | [[PoseFilterResult]] | 读取 `output_sequence_refs` 中的 pose 滤波后序列和 topic 样本统计 | 已对齐 | 复用 |
| 触觉滤波器 | [[TactileFilterResult]] | 读取 `output_sequence_refs` 中的 tactile 滤波后序列和 topic 样本统计 | 已对齐 | 复用 |
| MCAP_A 数据概念 | [[McapA]] | 固化输出语义、默认落点和禁止事项 | 已对齐 | 本 L2 更新并复用 |

## 8. 职责边界

本能力负责：

1. 在唯一运行上下文中读取一次 [[CleanedMcap]] 分析样本，产生共享的 [[SignalRepairResult]]、[[PoseFilterResult]] 和 [[TactileFilterResult]]。
2. 按物理顺序流式复制 cleaned MCAP 的 topic、schema、时间与未处理消息。
3. 以完整 [[SignalSampleRef]] 精确定位 pose/tactile/gripper 消息，每项替换必须恰好命中一次。
4. 写出后校验 topic、schema、消息数、log/publish time 和 sequence 与源文件一致。
6. 写出 [[McapA|MCAP_A]] 和 sidecar [[McapAWriteSummary]]。

本能力不负责：

1. 不重新做异常检测、补全或滤波。
2. 不新增 processed topic、audit topic 或 MCAP metadata 审计块。
3. 不保存关节角；IK 和 MCAP_B 属于第 6 个功能模块。
4. 不决定 mask、episode 丢弃或 canonical dataset 结构。
5. 不修改场景三、场景四或训练导出契约。

## 9. 读写职责

| 动作 | 读取来源 | 写入目标 | 格式 | 下游消费者 |
|---|---|---|---|---|
| 读取 cleaned MCAP | [[CleanedMcap]] | 内存中的 MCAP 复制流 | MCAP | MCAP_A 写出器 |
| 读取上游结果 | [[SignalRepairResult]]、[[PoseFilterResult]]、[[TactileFilterResult]] | 上游序列引用和统计 | JSON / 内存对象 | MCAP_A 写出器 |
| 写出 MCAP_A | cleaned MCAP 结构 + 处理后主数据序列 | [[McapA]] | MCAP | IK 求解、场景三、报告生成器 |
| 写出摘要 | 写出过程、替换统计、失败状态 | [[McapAWriteSummary]] | JSON | 报告生成器、开发者入口 |

## 10. 路径与命名规则

| 文件 / 目录 | 路径来源 | 命名规则 | 是否允许覆盖 | 创建时机 |
|---|---|---|---|---|
| MCAP_A 默认目录 | [[McapAWriteConfig]].`output_dir` | `asset/阶段二：数据清洗/dev/mcap_validated/` | 目录可创建 | 写出前 |
| MCAP_A 文件 | cleaned MCAP stem | `<stem>_mcap_a.mcap` | 默认不覆盖 | 上游输入全部校验通过后 |
| 写出摘要 | MCAP_A 文件同级或开发者 run artifacts | `mcap_a_write_summary.json` | 同一 run 内可覆盖临时产物 | 写出完成或失败后 |
| 开发者调试产物 | 独立 run 输出目录 | `artifacts/mcap_a/` | 只影响本次 run | 开发者功能检验时 |

## 11. 文件格式与内容契约

| 文件 | 格式 | 必填内容 | 可选内容 | 校验方式 |
|---|---|---|---|---|
| [[McapA]] | MCAP | 与 [[CleanedMcap]] 对齐的 topic、消息类型、时间戳、样本数；替换后的 pose/tactile/gripper 主数据 | 其他原样复制 topic | topic / type / timestamp / sample count contract test |
| [[McapAWriteSummary]] | JSON | 输入 cleaned MCAP、输出 MCAP_A、三类上游结果引用、替换 topic 统计、复制 topic 统计、status、failure_reason、run_id | created_at、配置引用 | JSON schema / dataclass 序列化测试 |
| 运行日志 | JSON / text | 输入、配置、执行步骤、关键状态、错误信息、输出位置 | 耗时、topic 明细 | 开发者入口 smoke test |

## 12. 覆盖策略与幂等性

- 重复运行时如何处理：默认生成同名目标前先检查是否已存在；存在时失败并提示用户换输出目录或显式覆盖。
- 是否允许覆盖已有文件：默认不允许；开发者功能检验的 run 内临时产物允许覆盖同一 run 的半成品。
- 如何避免污染旧 run：开发者功能检验必须写入独立 run 目录，正式 validated 产物写入 `dev/mcap_validated/`。
- 临时文件或半成品如何处理：MCAP 写出应先写临时文件，成功后原子改名；失败时删除临时文件或在摘要中显式标记。

## 13. 失败处理

| 失败情况 | 判断方式 | 处理策略 | 错误信息要求 | 是否写入报告 |
|---|---|---|---|---|
| cleaned MCAP 缺失 | 输入路径不存在或不可读 | 不生成 MCAP_A | `missing_cleaned_mcap` | 是，写入 summary / run log |
| [[SignalRepairResult]] 缺失 | 未提供或无法解析 | strict 失败，不生成 MCAP_A | `missing_signal_repair_result` | 是 |
| [[PoseFilterResult]] 缺失 | 未提供或无法解析 | strict 失败，不生成 MCAP_A | `missing_pose_filter_result` | 是 |
| [[TactileFilterResult]] 缺失 | 未提供或无法解析 | strict 失败，不生成 MCAP_A | `missing_tactile_filter_result` | 是 |
| 时间策略不匹配 | 任一上游 `timestamp_policy != preserve_original` | 失败，不写 MCAP_A | `unsupported_timestamp_policy` | 是 |
| 稳定引用未命中或重复命中 | topic/index/时间/sequence/channel 不一致 | 删除临时文件，整次写出失败 | `replacement_identity_mismatch` | 是 |
| 输出目标已存在 | 目标文件已存在且未允许覆盖 | 失败，不覆盖旧文件 | `output_exists` | 是 |

## 14. 整体完成标准

- [x] [[McapA]]、[[McapAWriteConfig]] 和 [[McapAWriteSummary]] 已形成或更新为原子数据定义。
- [x] 主 Runtime 只执行一次分析读取、检测和修复，独立开发者入口复用相同 RAM 阶段函数。
- [x] MCAP_A topic、schema、时间、sequence 和样本数与 cleaned MCAP 对齐。
- [x] 缺少必需流、上游结果或稳定引用合同失配时严格失败。
- [x] 开发者入口能查看 MCAP_A、写出摘要和运行日志。

## 15. 开发者验收入口设计

| 项目 | 设计 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二：硬件数据可靠性验证 |
| 对应功能检验项 | `scene2_mcap_a_writer` / 检查 MCAP_A 写出 |
| 是否影响场景完整 smoke test | 是 |
| 小样本输入要求 | cleaned MCAP 小样本、`signal_repair_result.json`、`pose_filter_result.json`、`tactile_filter_result.json` |
| 调试输出目录要求 | 独立 run 目录，不写正式生产输出 |
| 测试产物 | `artifacts/mcap_a/<stem>_mcap_a.mcap`、`artifacts/mcap_a_write_summary.json`、运行日志 |
| 运行日志最低字段 | 输入 cleaned MCAP、三类上游结果引用、写出配置、topic 替换统计、错误信息、输出位置 |
| 临时覆盖配置 | 允许临时覆盖输出目录和覆盖策略；覆盖只对本次运行生效 |
| 保存覆盖到配置文件 | 默认不保存；仅开发者明确选择时允许 |
| 人工最终验收方式 | 用户运行 `./start_data_clean.sh --dev` 后选择场景二和 `scene2_mcap_a_writer`，检查输出 MCAP topic 结构、样本数、时间戳、替换统计和 sidecar 追溯 |

## 16. 可拆分的 L3 任务清单

| L3 编号 | L3 任务名称 | 任务类别 | 输入 | 输出 | 主要修改范围 | 自动化验收方式 | 开发者入口验收关联 |
|---|---|---|---|---|---|---|---|
| service_s2_017 | 定义 MCAP_A 写出配置摘要和契约 | 数据定义类 | 本 L2、[[McapA]]、上游结果定义 | [[McapAWriteConfig]]、[[McapAWriteSummary]]、代码类型 / schema | `src/data_clean/schemas/`、`src/data_clean/tests/`、场景二 L2 数据定义 | `python3` 导入与序列化测试 | 间接覆盖 `scene2_mcap_a_writer` |
| service_s2_018 | 实现 MCAP_A 复制替换写出器 | 数据读写类 | [[CleanedMcap]]、[[SignalRepairResult]]、[[PoseFilterResult]]、[[TactileFilterResult]] | [[McapA]]、[[McapAWriteSummary]] | `src/data_clean/repo/`、`src/data_clean/service/`、`src/data_clean/tests/` | `python3` MCAP 复制替换契约测试 | `scene2_mcap_a_writer` |
| service_s2_019 | 补充 MCAP_A 契约与场景三兼容验收 | 数据读写类 | [[McapA]] 小样本、写出摘要 | topic/time/sample count 合同测试和场景三读取兼容检查 | `src/data_clean/tests/contract/`、必要测试 fixture | `python3` contract / compatibility 测试 | 间接覆盖场景二 smoke test |
| service_s2_020 | 接入 MCAP_A 开发者功能检验项 | 流程编排类 | cleaned MCAP、三类上游结果、写出配置 | `mcap_a` 调试产物、summary、运行日志 | `start_data_clean.sh`、`src/data_clean/runtime/`、`src/data_clean/ui/`、`src/data_clean/tests/` | `python3` smoke 或 CLI 测试 | `scene2_mcap_a_writer` |

## 17. 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
|---|---|---|---|
| 上游 `output_sequence_refs` 的最终物理格式 | 影响写出器如何加载处理后序列 | L2 固定语义，L3 先按上游已落地类型对接；缺格式时先失败提示 | 上游 L3 执行结果 |
| 是否允许生产模式覆盖已有 MCAP_A | 影响数据安全 | 默认不允许覆盖，显式配置才可变更 | 用户 |
| 场景三读取入口的最终接口名称 | 影响兼容测试落点 | L3 先做最小可读兼容检查，具体入口按场景三 L2/L3 对齐 | 场景三规划 |
| MCAP_A 是否需要长期保留 ValidatedMcap 别名 | 影响命名一致性 | 当前以 [[McapA]] 为主，ValidatedMcap 只作为解释性别名 | 用户 / 后续文档整理 |

## 18. 给 L3 任务生成的约束

1. 每个 L3 只能解决一个核心目标。
2. MCAP_A L3 不得重新做异常检测、补全或滤波。
3. MCAP_A 写出必须保留 cleaned MCAP 的 topic 名称、消息类型、时间戳排序和样本数。
4. 缺少 [[SignalRepairResult]]、[[PoseFilterResult]] 或 [[TactileFilterResult]] 时必须失败，不得部分写出。
5. 不得新增 processed topic、audit topic 或 MCAP metadata 审计块。
6. 写出摘要必须使用 sidecar [[McapAWriteSummary]]。
7. 输出路径必须遵守 `asset/阶段二：数据清洗/dev/mcap_validated/` 或开发者 run 隔离输出目录。
8. 每个 Service 场景 L3 必须写明它对应或影响 `./start_data_clean.sh --dev` 下的场景二功能检验项或场景完整 smoke test。
9. L3 自动化验收只证明局部实现正确；场景最终验收必须由用户本人运行 `./start_data_clean.sh --dev` 后确认。
