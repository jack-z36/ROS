# L3 微元任务：定义 step 时间轴与对齐索引类型

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：对齐契约与配置定义  
L3 编号：service_s3_002  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐契约与配置定义.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_002
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md
  group: service-s3-g1
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g1-p2
  depends_on: [service_s3_001]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_003]
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
定义 StepTimeline、FieldAlignmentStatus 和 AlignmentIndex 的代码类型 / Parquet schema 契约，并补充序列化或字段完整性测试。
```

## 4. 本次不做

- 不生成真实 step 时间戳序列。
- 不实现字段对齐算法。
- 不写出真实 Parquet 文件到 `asset/`。
- 不修改开发者入口。

## 5. 执行对象

- [[StepTimeline]]
- [[FieldAlignmentStatus]]
- [[AlignmentIndex]]

## 6. 执行依赖

- `service_s3_001` 必须完成并归档，因为本 L3 依赖其配置、字段映射和策略类型。
- 必须继续复用场景三 L2 的状态枚举和 alignment index 字段定义。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：service_s3_001 定义场景三配置与 schema
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_001_定义场景三配置与schema.md
- service_s3_001 实际新增的 src/data_clean/schemas/ 类型文件
当前 L3 期望消费的字段 / 文件 / 返回值：
- Scene3AlignmentConfig.target_step_hz
- TargetFieldMapping.field_name/source_topic/output_topic/required_for_timeline
是否存在接口冲突：执行前确认
如果有冲突，本次处理策略：暂停并汇报，不得自行重写 service_s3_001 的接口
```

## 8. 预期改动形态

- 新增或更新 step timeline、alignment status、alignment index record 类型。
- 明确 `alignment_index.parquet` 的列定义，至少覆盖 L2 中列出的逐 step-field 字段。
- 增加类型 import、枚举取值和字段序列化测试。
- 必要时更新 `src/data_clean/data_clean_architecture.md`。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `StepTimeline` | dataclass / schema | `src/data_clean/schemas/` | 时间轴生成器、字段对齐器、写出器 |
| `StepTimelineSummary` | dataclass / schema | `src/data_clean/schemas/` | report 生成器 |
| `FieldAlignmentStatus` | enum / Literal | `src/data_clean/schemas/` | AlignmentIndex、report、场景四 |
| `AlignmentIndexRecord` | dataclass / schema | `src/data_clean/schemas/` | Parquet 写出、report 生成器 |
| `AlignmentIndexSchema` | 常量 / schema | `src/data_clean/schemas/` | Parquet schema 测试和写出器 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `range_policy` | string | 时间范围策略 | `required_field_intersection` | 首版固定 |
| `baseline_policy` | string | 基准策略 | `stereo_image_intersection` | 首版固定 |
| `aligned` | status | 正常最近邻对齐 | 无 | 合法枚举 |
| `interpolated` | status | 插值得到 | 无 | 合法枚举 |
| `aggregated` | status | 窗口聚合得到 | 无 | 合法枚举 |
| `fallback_nearest` | status | fallback 到最近邻 | 无 | 必须可记录 fallback_reason |
| `missing_time` | status | 时间窗口无样本 | 无 | 合法枚举 |
| `timeout` | status | 样本超过阈值 | 无 | 合法枚举 |
| `unavailable` | status | 字段不可用 | 无 | 合法枚举 |
| `invalid_input` | status | 输入无效 | 无 | 合法枚举 |
| `step_index + field_name` | composite key | 每个 step-field 主记录 | 无 | 最多一条主记录 |

## 10. 数据定义验收重点

- 能 import `StepTimeline`、`FieldAlignmentStatus`、`AlignmentIndexRecord`。
- `FieldAlignmentStatus` 完整包含 8 个首版枚举。
- `AlignmentIndexRecord` 能表达 source topic、source time、method、status、dt、neighbors、window、sample_count、coverage、fallback_reason。
- schema / dataclass 不嵌入完整图像、完整位姿序列或触觉矩阵。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐契约与配置定义.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_001_定义场景三配置与schema.md`

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3任务文件身份校验约束.md`
3. `DOCS/02_约束/阶段二任务体系/L3调度元数据约束.md`
4. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
5. `DOCS/02_约束/阶段二任务体系/功能分支接力流程.md`
6. `DOCS/02_约束/阶段二任务体系/L3功能组目录约束.md`
7. `DOCS/02_约束/阶段二任务体系/开发者验收入口约束.md`
8. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
9. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
10. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/执行约束.md`

### 必读代码

1. `src/data_clean/schemas/__init__.py`
2. `src/data_clean/schemas/pose_filter.py`
3. `src/data_clean/schemas/tactile_filter.py`
4. `service_s3_001` 新增或修改的 schema/config 文件
5. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验、`service_s3_001` completed 依赖校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。先写枚举完整性和 record 字段测试，再实现最小类型。

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

- 禁止修改 `service_s3_001` 已稳定的配置接口，除非执行前发现阻塞性错误并在摘要说明。
- 禁止实现时间轴生成算法或 Parquet 写出动作。
- 禁止写入真实 `alignment_index.parquet` 数据产物。
- 禁止修改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas import FieldAlignmentStatus
expected = {
    "aligned",
    "interpolated",
    "aggregated",
    "fallback_nearest",
    "missing_time",
    "timeout",
    "unavailable",
    "invalid_input",
}
actual = {item.value for item in FieldAlignmentStatus}
assert expected == actual
PY
```

## 17. 成功标准

- [x] 已定义 step timeline 类型或 schema：`StepTimeline`、`StepTimelineEntry`、`StepTimelineSummary` 三个 dataclass。
- [x] 已定义完整 `FieldAlignmentStatus` 首版枚举：8 个成员（aligned, interpolated, aggregated, fallback_nearest, missing_time, timeout, unavailable, invalid_input）。
- [x] 已定义 alignment index record / schema，字段覆盖 L2 契约：`AlignmentIndexRecord` (17 字段) + `AlignmentIndexSchema` (17 列常量)。
- [x] 已补充 import / 序列化 / 字段完整性测试：20 个测试覆盖 import、默认值、自定义值、成员遍历和 schema 列完整性。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 完成并更新任务文件后，将当前 L3 移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/`。
- 移动后如果 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/` 已经为空，删除该空 active 功能组目录。
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

交接摘要必须包含模板要求的 12 项内容，尤其说明 `service_s3_001` 依赖校验、TDD red / green / refactor、验收命令结果和建议用户后续运行场景三完整 smoke test。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md
文件名编号：service_s3_002
正文 L3 编号：service_s3_002
dispatch.task_id：service_s3_002
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id=service_s3_002`、`task_file` 匹配、`group=service-s3-g1`、`branch=service-s3`、`dispatch_status=ready`、`depends_on=[service_s3_001]`（已归档）。
- 上游依赖校验：`service_s3_001` 已确认归档于 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/`。
- 相关 L3 历史记录：已找到并读取 `service_s3_001` 执行摘要（345 行），确认其接口定义（Scene3AlignmentConfig、TargetFieldMapping 等）可供本 L3 消费。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/step_timeline.py`（新增）：定义 `FieldAlignmentStatus` 枚举（8 成员）、`StepTimelineEntry`、`StepTimeline`、`StepTimelineSummary`、`AlignmentIndexRecord` dataclass 和 `AlignmentIndexSchema` 常量（17 列 Parquet schema）。
- `src/data_clean/schemas/__init__.py`：导入并导出场景三 step timeline 和对齐索引全部公共类型（`StepTimeline`、`StepTimelineEntry`、`StepTimelineSummary`、`FieldAlignmentStatus`、`AlignmentIndexRecord`、`AlignmentIndexSchema`）。
- `src/data_clean/tests/service/test_step_timeline_schemas.py`（新增）：20 个测试覆盖 FieldAlignmentStatus 枚举完整性（8 成员）、StepTimeline 默认值、StepTimelineEntry 构造、StepTimelineSummary 属性、AlignmentIndexRecord 必填+可选+全部字段、AlignmentIndexSchema 列完整性和类型字符串验证、统一 import 测试。
- `src/data_clean/data_clean_architecture.md`：在 schema 目录表中新增 `schemas/step_timeline.py` 条目。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

| 阶段 | 行为 | 结果 |
|------|------|------|
| Red | 编写 `test_step_timeline_schemas.py`（20 个测试），运行 `python3 -m pytest src/data_clean/tests/service/test_step_timeline_schemas.py -q` | 20 failed，ImportError（类型不存在），符合预期 |
| Green | 新增 `schemas/step_timeline.py`（FieldAlignmentStatus、StepTimeline、StepTimelineEntry、StepTimelineSummary、AlignmentIndexRecord、AlignmentIndexSchema），更新 `schemas/__init__.py` 导出 | 20 passed |
| Refactor | 修正在 `__init__.py` 中发现的 enum 成员名大小写问题（`MISSING_TIME` → `missing_time`）；更新 `data_clean_architecture.md` | 通过 |

### 验收命令结果

```bash
# 1. 本 L3 测试全部通过
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service/test_step_timeline_schemas.py -q
# → 20 passed

# 2. service 级测试（排除已知 pre-existing 问题）
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service -q --ignore=src/data_clean/tests/service/test_alignment_input_schemas.py
# → 202 passed, 9 skipped（含本 L3 20 个测试）

# 3. 内联验收 - FieldAlignmentStatus 枚举
PYTHONPATH=src python3 -c "
from data_clean.schemas import FieldAlignmentStatus
expected = {'aligned','interpolated','aggregated','fallback_nearest',
            'missing_time','timeout','unavailable','invalid_input'}
actual = {item.value for item in FieldAlignmentStatus}
assert expected == actual
"
# → 静默通过，无错误

# 4. 内联验收 - 全部类型
PYTHONPATH=src python3 -c "
from data_clean.schemas import StepTimeline, StepTimelineEntry, StepTimelineSummary
from data_clean.schemas import FieldAlignmentStatus, AlignmentIndexRecord, AlignmentIndexSchema
tl = StepTimeline(timeline_id='t', start_time_ns=0, end_time_ns=1000)
assert tl.target_step_hz == 15
entry = StepTimelineEntry(step_index=0, step_time_ns=0)
summary = StepTimelineSummary(timeline_id='t', target_step_hz=15, actual_step_count=10, start_time_ns=0, end_time_ns=1000)
assert summary.duration_ns == 1000
rec = AlignmentIndexRecord(step_index=0, step_time_ns=0, field_name='f', alignment_method='nn', status=FieldAlignmentStatus.aligned)
assert len(AlignmentIndexSchema) == 17
"
# → 静默通过，无错误
```

### 成功标准处理

- [x] 已定义 step timeline 类型或 schema：`StepTimeline`（含 metadata 字段和 `steps` 列表）、`StepTimelineEntry`（step 级字段）、`StepTimelineSummary`（含 `duration_ns` computed property）。
- [x] 已定义完整 `FieldAlignmentStatus` 首版枚举：8 个成员（aligned, interpolated, aggregated, fallback_nearest, missing_time, timeout, unavailable, invalid_input），均已通过内联枚举完整性断言。
- [x] 已定义 alignment index record / schema，字段覆盖 L2 契约：`AlignmentIndexRecord`（17 个字段，含 status、source_topic、source_time_ns、dt_ms、neighbors、window、sample_count、coverage_ratio、fallback_reason、message_ref）+ `AlignmentIndexSchema`（17 列 Parquet 类型映射）。
- [x] 已补充 import / 序列化 / 字段完整性测试：20 个测试覆盖 import（from data_clean.schemas 和 from schemas）、默认值、枚举成员遍历、必填+可选字段构造、schema 列完整性和类型字符串验证。
- [x] 已说明本 L3 与开发者验收入口的关系。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用或运行日志。
- 本 L3 间接支撑场景三完整 smoke test（在 `./start_data_clean.sh --dev` 下选择场景三）。
- 本 L3 的自动化验收只证明场景三 step timeline、字段对齐状态和对齐索引数据定义局部实现正确；场景最终验收需要场景三全部 L3 完成后运行完整 smoke test。

### 当前没做

- 未生成真实 step 时间戳序列（时间轴生成算法留待后续 L3）。
- 未实现字段对齐算法（最近邻、插值、slerp、窗口聚合）。
- 未写出真实 Parquet 文件或 `alignment_index.parquet` 到 `asset/`。
- 未修改 `service_s3_001` 的配置接口或 `TaskFieldMapping` / `Scene3AlignmentConfig` 类型。
- 未修改 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、共享 `当前进度.md` 或共享 `执行记录.md`。

### 遗留风险

- LSP diagnostics 无法执行（当前环境缺少 `basedpyright-langserver`），无法静态检查类型一致性。
- `test_alignment_input_schemas.py` 中 25 个预先存在的测试失败（`schemas.alignment_input` 模块尚未实现，属正常），与本 L3 无关。

### 归档说明

- 本任务完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/`。
- 原 active 功能组目录 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成场景三全部 L3（`service_s3_001`、`service_s3_002`、`service_s3_003`）后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三完整 smoke test，检查 step 时间轴、字段对齐状态枚举和对齐索引 schema 是否符合 `StepTimeline`、`FieldAlignmentStatus` 和 `AlignmentIndex` 契约。
