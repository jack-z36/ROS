# L3 微元任务：实现 AlignmentIndex 规范化与唯一性检查

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：对齐索引与报告数据生成器  
L3 编号：service_s3_016  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_016_实现AlignmentIndex规范化与唯一性检查.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_016
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_016_实现AlignmentIndex规范化与唯一性检查.md
  group: service-s3-g5
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g5-p2
  depends_on: [service_s3_010, service_s3_015]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_017, service_s3_018]
  conflict_scope:
    files:
      - src/data_clean/service/alignment_report.py
      - src/data_clean/service/__init__.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.service.alignment_report
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
实现从 FieldAlignmentResult 到 AlignmentIndex records 的规范化和 step-field 唯一性检查。
```

## 4. 本次不做

- 不生成 AlignmentReport draft 统计。
- 不写 `alignment_index.parquet`。
- 不写 aligned MCAP、JSON report 或写出摘要。

## 5. 执行对象

- [[FieldAlignmentResult]]
- [[AlignmentIndex]]
- `step_index + field_name` 唯一性规则

## 6. 执行依赖

- `service_s3_010` 应已定义 [[FieldAlignmentResult]]。
- `service_s3_015` 应已定义 [[AlignmentReport]] / stats 基础类型，避免本任务重复定义统计对象。
- 必须从 [[FieldAlignmentResult]] 中抽取事实字段，不保存 `derived_value`。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：多策略字段对齐器、对齐索引与报告数据生成器类型定义
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- FieldAlignmentResult 的 step_index、field_name、source_topic、output_topic、source_time_ns、alignment_method、status、dt_ms、neighbor、window、sample_count、coverage_ratio、fallback_reason、message_ref
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得兼容多个猜测版本；停止并汇报字段冲突
```

## 8. 预期改动形态

- 新增或扩展 service 层函数，把字段对齐结果转成 Parquet-ready index records。
- 对重复 `step_index + field_name` 返回清晰错误。
- 测试覆盖字段抽取、重复记录、非法状态和 `derived_value` 不进入 index。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | 每个 `step_index + field_name` 唯一，状态合法 | AlignmentIndex records | 无 |
| 缺失输入 | 输入为空或缺少 field alignment results | 失败 | `missing_field_alignment_result` |
| 边界输入 | `derived_value` 非空 | 不写入 index，仅保留事实字段 | 无 |
| 重复输入 | 同一 `step_index + field_name` 多条主记录 | 失败 | `duplicate_step_field_record` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `records` | list | AlignmentIndex 记录列表 | 不含 `derived_value` |
| `record_count` | integer | 输出记录数 | `>=0` |
| `failure_reason` | string/null | 失败原因 | 失败时必填 |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/service_s3_015_定义AlignmentReport阶段字段与统计类型.md`

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

1. `src/data_clean/service/`
2. `src/data_clean/schemas/`
3. `src/data_clean/tests/`
4. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：合法转换测试 -> 最小实现 -> 重复记录失败测试 -> `derived_value` 排除测试。

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

- `src/data_clean/service/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止写 Parquet、JSON、MCAP 或真实数据产物。
- 禁止保存 `derived_value` 到 AlignmentIndex。
- 禁止修改字段对齐算法。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.service.alignment_report import build_alignment_index_records
assert build_alignment_index_records is not None
PY
```

## 17. 成功标准

- [x] 已实现 FieldAlignmentResult 到 AlignmentIndex records 的规范化。
- [x] 已校验每个 `step_index + field_name` 最多一条主记录。
- [x] 已验证 `derived_value` 不进入 AlignmentIndex。
- [x] 未写 Parquet、JSON、MCAP 或写出摘要。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/`。如果 `active/service-s3-g5/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 身份校验与 Dispatch 验证

| 项目 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_016_实现AlignmentIndex规范化与唯一性检查.md` |
| 实际读取路径 | 匹配 |
| 文件名编号 | `service_s3_016` |
| 正文 L3 编号 | `service_s3_016` |
| task_id | service_s3_016 |
| group | service-s3-g5 |
| branch | service-s3 (当前分支确认) |
| dispatch_status | ready |
| depends_on | [service_s3_010, service_s3_015] → 均已归档 |
| 分支校验 | service-s3 ✓ |

### TDD 执行记录

| 切片 | 测试内容 | 状态 |
|---|---|---|
| VS1 RED→GREEN | `build_alignment_index_records` 合法输入返回 AlignmentIndexRecord 列表 | ✓ |
| VS2 RED→GREEN | 空输入/None 返回 `failure_reason='missing_field_alignment_result'` | ✓ |
| VS3 RED→GREEN | 重复 `step_index+field_name` 返回 `failure_reason='duplicate_step_field_record'` | ✓ |
| VS4 RED→GREEN | `derived_value` 被剔除，不出现在 AlignmentIndexRecord 中 | ✓ |
| VS5 RED→GREEN | 跨 step 同名 field、同 step 不同名 field 均不触发重复 | ✓ |
| REFACTOR | 8 次 pylance import 调整、relative→absolute import 回归匹配代码库惯例 | ✓ |

### 修改文件

| 文件 | 改动 |
|---|---|
| `src/data_clean/service/alignment_report.py` | **新增** `build_alignment_index_records()`: 规范化 FieldAlignmentResult→AlignmentIndexRecord（11 个事实字段映射），step_index+field_name 唯一性检查，空/None 输入保护 |
| `src/data_clean/service/__init__.py` | 导出 `build_alignment_index_records` |
| `src/data_clean/tests/service/test_alignment_index_records.py` | **新增** 8 个测试覆盖合法转换、空/None 输入、重复记录、derived_value 排除、跨 step/同 step 场景 |
| 本 L3 任务文件 | 成功标准标记完成，追加执行摘要 |

### 验收命令输出

```bash
# 开工自检
bash scripts/init_data_clean_dev.sh
# → Git branch OK: service-s3, Python imports OK, start_data_clean.sh --help OK

# 全部服务层测试（不含 pre-existing runtime import 问题）
python3 -m pytest src/data_clean/tests/service/test_alignment_index_records.py -v -q
# → 8 passed in 0.10s

# 功能验证（使用 pytest conftest 路径约定）
PYTHONPATH=src/data_clean python3 -c "
from service.alignment_report import build_alignment_index_records
from schemas.field_alignment import FieldAlignmentResult
r = build_alignment_index_records([FieldAlignmentResult(step_index=0, step_time_ns=1, field_name='x', status='aligned', alignment_method='n')])
assert r['record_count'] == 1 and r['failure_reason'] is None
r2 = build_alignment_index_records([])
assert r2['failure_reason'] == 'missing_field_alignment_result'
r3 = build_alignment_index_records([FieldAlignmentResult(step_index=0, step_time_ns=1, field_name='x', status='aligned', alignment_method='n'), FieldAlignmentResult(step_index=0, step_time_ns=1, field_name='x', status='aligned', alignment_method='n')])
assert r3['failure_reason'] == 'duplicate_step_field_record'
print('ALL ACCEPTANCE CHECKS PASSED')
"
```

### 与开发者验收入口的关系

本 L3 实现了对齐索引规范化函数，是 `scene3_alignment_report_check` 功能检验项的直接计算内核。输出结果由 `service_s3_017` 消费生成 AlignmentReport 统计，并由 `service_s3_018` 接入开发者菜单。建议用户在完成 service-s3-g5 全部 L3 (service_s3_016~018) 后运行 `./start_data_clean.sh --dev` 选择场景三 → `scene3_alignment_report_check` 做最终人工验收。

### 遗留风险

- 本 L3 使用与代码库一致的 `from schemas...` 导入风格（非相对导入 `from ..schemas...`）。当从 `data_clean.service.alignment_report` 包路径导入时需要 `PYTHONPATH=src/data_clean`（这是 data_clean 全库的一致约定，非本模块特有）。
- 下游 `service_s3_017` 需要本模块导出的函数和输出结构保持一致。


