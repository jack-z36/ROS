# L3 微元任务：定义 AlignmentReport 阶段字段与统计类型

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：对齐索引与报告数据生成器  
L3 编号：service_s3_015  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_015_定义AlignmentReport阶段字段与统计类型.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_015
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_015_定义AlignmentReport阶段字段与统计类型.md
  group: service-s3-g5
  branch: service-s3
  wave: 1
  parallel_group: service-s3-g5-p1
  depends_on: [service_s3_002, service_s3_010]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_016, service_s3_017]
  conflict_scope:
    files:
      - src/data_clean/schemas/alignment_index.py
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
定义代码层 AlignmentReport draft/final 阶段字段、统计对象和 status / degradation 语义。
```

## 4. 本次不做

- 不实现 AlignmentIndex 规范化计算。
- 不实现 report 统计生成服务。
- 不写 Parquet、JSON、MCAP 或写出摘要文件。

## 5. 执行对象

- [[AlignmentReport]]
- [[AlignmentIndex]]
- [[FieldAlignmentStatus]]
- report draft / final 阶段字段契约

## 6. 执行依赖

- `service_s3_002` 应已定义 [[AlignmentIndex]] 和 [[FieldAlignmentStatus]] 基础类型。
- `service_s3_010` 应已定义 [[FieldAlignmentResult]] 类型。
- 必须复用现有 schemas 风格，不新增与 [[AlignmentReport]] 平行的 `AlignmentReportDraft` 原子概念。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：对齐契约与配置定义、多策略字段对齐器
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- AlignmentReport draft 阶段字段：输入引用、配置引用、timeline 摘要、field_stats、status_counts、degradation_summary、failure_reason
- AlignmentReport final 阶段字段：output_aligned_mcap、alignment_index、run_id、status
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得拆出新的报告概念；停止并建议 Win 端调整 L2 / 数据定义
```

## 8. 预期改动形态

- 在 `src/data_clean/schemas/` 中新增或扩展 AlignmentReport 相关类型。
- 类型能表达 draft 阶段最终路径为空、final 阶段路径必填。
- 补充 schema / 序列化测试，覆盖 completed、degraded、failed 状态。
- 必要时更新 `src/data_clean/data_clean_architecture.md`。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `AlignmentReport` | dataclass / schema | `src/data_clean/schemas/` | report 统计服务、sidecar 写出器 |
| `AlignmentFieldStats` | dataclass / TypedDict | `src/data_clean/schemas/` | report draft 生成服务 |
| `AlignmentDegradationSummary` | dataclass / TypedDict | `src/data_clean/schemas/` | report draft 生成服务、场景四质量统计 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `status` | enum string | `completed` / `degraded` / `failed` | 无 | 必填 |
| `field_stats` | object | 字段级误差和质量统计 | 空对象 | draft / final 均可读 |
| `status_counts` | object | FieldAlignmentStatus 计数 | 空对象 | key 必须是合法状态 |
| `degradation_summary` | object | 缺失、超时、fallback、unavailable 摘要 | 空对象 | 不表达训练 mask |
| `output_aligned_mcap` | string/null | final 阶段 aligned MCAP 路径 | null | final completed 时必填 |
| `alignment_index` | string/null | final 阶段 index 路径 | null | final completed 时必填 |

## 10. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`

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

1. `src/data_clean/schemas/`
2. `src/data_clean/tests/`
3. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：导入失败测试 -> 最小报告类型 -> draft/final 序列化测试 -> 非法 status 测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_alignment_report_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 不直接接入开发者入口，但由 `scene3_alignment_report_check` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现 report 统计服务。
- 禁止写出 Parquet、JSON、MCAP 或真实数据产物。
- 禁止新增 `AlignmentReportDraft` 原子概念替代 [[AlignmentReport]]。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas import AlignmentReport
assert AlignmentReport is not None
PY
```

## 17. 成功标准

- [ ] 已定义 `AlignmentReport` 或等价代码类型。
- [ ] 类型能表达 draft 阶段输出路径为空、final 阶段输出路径补齐。
- [ ] 已覆盖 `completed` / `degraded` / `failed` 状态和 `degradation_summary`。
- [ ] 未实现 AlignmentIndex 规范化、report 统计服务或任何写出动作。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/`。如果 `active/service-s3-g5/` 为空，删除该空目录。不得写共享执行记录。

