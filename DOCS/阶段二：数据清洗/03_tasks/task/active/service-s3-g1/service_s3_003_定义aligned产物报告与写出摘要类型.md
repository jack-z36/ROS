# L3 微元任务：定义 aligned 产物报告与写出摘要类型

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：对齐契约与配置定义  
L3 编号：service_s3_003  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_003_定义aligned产物报告与写出摘要类型.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐契约与配置定义.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_003
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_003_定义aligned产物报告与写出摘要类型.md
  group: service-s3-g1
  branch: service-s3
  wave: 3
  parallel_group: service-s3-g1-p3
  depends_on: [service_s3_002]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/data_clean/schemas/aligned_mcap.py
      - src/data_clean/schemas/__init__.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.schemas
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
定义 AlignedMcap、AlignmentReport 和 AlignedMcapWriteSummary 的代码类型 / JSON schema 契约，并补充序列化测试。
```

## 4. 本次不做

- 不实现 aligned MCAP 写出器。
- 不生成真实 `alignment_report.json` 或 `aligned.mcap`。
- 不实现 report 统计计算。
- 不接入开发者入口。

## 5. 执行对象

- [[AlignedMcap]]
- [[AlignmentReport]]
- [[AlignedMcapWriteSummary]]

## 6. 执行依赖

- `service_s3_002` 必须完成并归档，因为本 L3 的 report 需要引用 `StepTimeline`、`AlignmentIndex` 和 `FieldAlignmentStatus` 类型。
- 必须保持 aligned MCAP 是场景三输出、MCAP_A 只读不改的契约。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：service_s3_002 定义 step 时间轴与对齐索引类型
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md
- service_s3_002 实际新增的 src/data_clean/schemas/ 类型文件
当前 L3 期望消费的字段 / 文件 / 返回值：
- StepTimeline 或 StepTimelineSummary
- AlignmentIndexRecord 或 AlignmentIndex schema
- FieldAlignmentStatus
是否存在接口冲突：执行前确认
如果有冲突，本次处理策略：暂停并汇报，不得自行重写 service_s3_002 的接口
```

## 8. 预期改动形态

- 新增或更新 aligned MCAP 产物契约类型、alignment report 类型和写出摘要类型。
- JSON 序列化测试覆盖 success / failed 基本约束。
- 明确 report 只保存统计摘要，逐 step-field 明细仍由 alignment index 表达。
- 必要时更新 `src/data_clean/data_clean_architecture.md`。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `AlignedMcapArtifact` 或 `AlignedMcap` | dataclass / schema | `src/data_clean/schemas/` | 写出器、场景四 |
| `AlignmentReport` | dataclass / JSON schema | `src/data_clean/schemas/` | report 生成器、人工复查、场景四 |
| `AlignedMcapWriteSummary` | dataclass / JSON schema | `src/data_clean/schemas/` | 写出器、smoke test |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `output_aligned_mcap` | string | aligned MCAP 输出路径 | 无 | 成功时必须存在引用 |
| `alignment_index_path` | string | `alignment_index.parquet` 路径 | 无 | 成功时必须存在引用 |
| `alignment_report_path` | string | `alignment_report.json` 路径 | 无 | 成功时必须存在引用 |
| `status` | string | 写出或报告状态 | 无 | `completed` / `failed` |
| `failure_reason` | string/null | 失败原因 | null | 失败时必须非空 |
| `field_stats` | mapping | 字段级统计摘要 | empty | 不保存逐 step-field 明细 |
| `status_counts` | mapping | FieldAlignmentStatus 计数 | empty | key 应来自状态枚举 |

## 10. 数据定义验收重点

- 能 import report / summary / artifact 类型。
- 成功对象必须能引用 aligned MCAP、alignment index 和 report。
- 失败对象必须携带 `failure_reason`。
- report 类型不嵌入完整 `AlignmentIndexRecord` 列表作为主内容。
- JSON 序列化结果字段使用 snake_case。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐契约与配置定义.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcap.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_001_定义场景三配置与schema.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3任务文件身份校验约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/L3调度元数据约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
5. `DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`
6. `DOCS/阶段二：数据清洗/约束文件/L3功能组目录约束.md`
7. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`
8. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
9. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
10. `DOCS/阶段二：数据清洗/02_service/场景三/执行约束.md`

### 必读代码

1. `src/data_clean/schemas/__init__.py`
2. `src/data_clean/schemas/manifest_types.py`
3. `src/data_clean/schemas/mcap_a_writer.py`
4. `service_s3_001` 和 `service_s3_002` 新增或修改的 schema 文件
5. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验、`service_s3_002` completed 依赖校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。先写 JSON 序列化和成功/失败状态测试，再实现类型。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | 不直接接入开发者入口，但由场景三完整 smoke test 间接覆盖 |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否；本 L3 不涉及配置写回 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景三完整 smoke test |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现 aligned MCAP 写出器、report 生成器或实际 Parquet/JSON 文件写出。
- 禁止修改 MCAP_A 上游契约。
- 禁止把 report 设计成逐 step-field 明细的唯一存放处。
- 禁止修改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas import AlignmentReport, AlignedMcapWriteSummary
report = AlignmentReport(
    input_mcap_a="asset/阶段二：数据清洗/dev/mcap_validated/sample_mcap_a.mcap",
    alignment_index="asset/阶段二：数据清洗/dev/mcap_aligned/alignment_index.parquet",
    output_aligned_mcap="asset/阶段二：数据清洗/dev/mcap_aligned/sample_aligned.mcap",
    status="completed",
)
summary = AlignedMcapWriteSummary(
    input_mcap_a=report.input_mcap_a,
    output_aligned_mcap=report.output_aligned_mcap,
    alignment_index_path=report.alignment_index,
    alignment_report_path="asset/阶段二：数据清洗/dev/mcap_aligned/alignment_report.json",
    status="completed",
)
assert summary.status == "completed"
PY
```

## 17. 成功标准

- [ ] 已定义 aligned MCAP 产物契约类型。
- [ ] 已定义 alignment report 类型，且只承载统计摘要。
- [ ] 已定义 aligned MCAP 写出摘要类型，成功/失败状态约束清楚。
- [ ] 已补充 JSON 序列化和 import 测试。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 完成并更新任务文件后，将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/`。
- 移动后如果 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/` 已经为空，删除该空 active 功能组目录。
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

交接摘要必须包含模板要求的 12 项内容，尤其说明 `service_s3_001` / `service_s3_002` 依赖校验、TDD red / green / refactor、验收命令结果和建议用户后续运行场景三完整 smoke test。
