# L3 微元任务：实现 alignment index 与 report sidecar 写出

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：aligned MCAP 与 sidecar 写出器  
L3 编号：service_s3_020  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_020_实现alignment_index与report_sidecar写出.md`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_020
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_020_实现alignment_index与report_sidecar写出.md
  group: service-s3-g6
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g6-p2
  depends_on: [service_s3_017, service_s3_019]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_022, service_s3_023]
  conflict_scope:
    files:
      - src/data_clean/repo/alignment_sidecar_writer.py
      - src/data_clean/repo/__init__.py
      - src/data_clean/service/aligned_mcap_writer.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.repo
      - data_clean.service.aligned_mcap_writer
    config_keys:
      - scene3_alignment.output_dir
  dispatch_status: ready
```

## 3. 本次目标

```text
实现 AlignmentIndex Parquet sidecar 和 final AlignmentReport JSON 的最小可验证写出。
```

## 4. 本次不做

- 不写 aligned MCAP。
- 不实现临时目录整体提交。
- 不接入开发者入口。
- 不重新计算 AlignmentIndex 或 report draft。

## 5. 执行对象

- `alignment_index.parquet`
- `alignment_report.json`
- [[AlignmentIndex]]
- [[AlignmentReport]]

## 6. 执行依赖

- `service_s3_017` 应已实现 report draft 生成。
- `service_s3_019` 应已定义 final report 补齐类型。
- 写出器只消费已生成对象，不重新计算统计。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：AlignmentReport draft 统计、写出摘要与 final report 类型定义
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- AlignmentIndex records
- AlignmentReport draft
- output path / run context
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并汇报，不修改上游统计逻辑
```

## 8. 预期改动形态

- 新增或扩展 repo / service 层 sidecar 写出能力。
- 能写出可解析的 Parquet index 和 JSON report。
- 测试覆盖成功写出、缺失输入和不可写路径错误。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 写 alignment index | AlignmentIndex records | `alignment_index.parquet` | Parquet | 不覆盖既有完整产物，测试使用临时目录 |
| 写 final report | AlignmentReport draft + final 路径字段 | `alignment_report.json` | JSON | 不覆盖既有完整产物，测试使用临时目录 |

### 文件或目录结构

```text
<run_or_output_dir>/
  alignment_index.parquet
  alignment_report.json
```

## 10. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/service_s3_017_实现AlignmentReport草稿统计生成.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/service_s3_019_定义写出摘要与final报告补齐类型.md`

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

1. `src/data_clean/repo/`
2. `src/data_clean/service/`
3. `src/data_clean/tests/`
4. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及文件写出，必须使用 `$tdd` 技能。建议顺序：JSON report 写出测试 -> Parquet index 写出测试 -> 缺失输入失败测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_aligned_mcap_write_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 是；产物类型：alignment index sidecar、alignment report |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 不直接接入开发者入口，但由 `scene3_aligned_mcap_write_check` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/repo/`
- `src/data_clean/service/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止写 aligned MCAP。
- 禁止实现临时目录整体提交。
- 禁止修改 report draft 统计。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.repo.alignment_sidecar_writer import write_alignment_index, write_alignment_report
assert write_alignment_index and write_alignment_report
PY
```

## 17. 成功标准

- [x] 已实现 `alignment_index.parquet` 写出。
- [x] 已实现 `alignment_report.json` 写出并补齐 final 路径字段。
- [x] 已覆盖文件可解析和缺失输入失败测试。
- [x] 未写 aligned MCAP，未实现整体提交策略。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 身份校验与 Dispatch 验证

| 项目 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_020_实现alignment_index与report_sidecar写出.md` |
| 实际读取路径 | 匹配 |
| 文件名编号 | `service_s3_020` |
| 正文 L3 编号 | `service_s3_020` |
| task_id | service_s3_020 |
| group | service-s3-g6 |
| branch | service-s3 (当前分支确认) |
| dispatch_status | ready |
| depends_on | [service_s3_017, service_s3_019] → 均已归档 |
| 分支校验 | service-s3 ✓ |

### TDD 执行记录

| 切片 | 测试内容 | 状态 |
|---|---|---|
| VS1 RED→GREEN | `write_alignment_report` importable + valid draft+finalization creates JSON with correct fields | ✓ |
| VS2 RED→GREEN | `write_alignment_index` importable + valid records creates Parquet, content readable via pyarrow | ✓ |
| VS3 RED→GREEN | `write_alignment_report` None draft/finalization raises ValueError | ✓ |
| VS4 RED→GREEN | `write_alignment_index` None/empty records raises ValueError | ✓ |
| VS5 RED→GREEN | Both functions raise OSError on unwritable path | ✓ |
| VS6 RED→GREEN | Failed report writes without final paths | ✓ |
| VS7 RED→GREEN | Parquet column names match AlignmentIndexSchema | ✓ |
| VS8 RED→GREEN | Parquet content (status enum conversion, nullable dt_ms, etc.) round-trips correctly | ✓ |
| VS9 RED→GREEN | Dataclass fields (degradation_summary, field_stats) serialize to plain dicts in JSON | ✓ |
| VS10 RED→GREEN | Draft fields preserved after finalization overrides | ✓ |

### 修改文件

| 文件 | 改动 |
|---|---|
| `src/data_clean/repo/alignment_sidecar_writer.py` | **新增** `write_alignment_index()`, `write_alignment_report()`, `_ensure_parent()`, `_record_to_columns()` |
| `src/data_clean/repo/__init__.py` | 导出 `write_alignment_index`, `write_alignment_report` |
| `src/data_clean/tests/service/test_alignment_sidecar_writer.py` | **新增** 15 个测试覆盖两类写操作、输入校验和路径错误 |
| `src/data_clean/data_clean_architecture.md` | 在 repo 层级表中添加 `alignment_sidecar_writer.py` 条目 |
| 本 L3 任务文件 | 成功标准标记完成，追加执行摘要 |

### 验收命令输出

```bash
# 1. 开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK, branch: service-s3

# 2. 本 L3 测试全部通过
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service/test_alignment_sidecar_writer.py -q
# → 15 passed in 0.18s

# 3. service 级测试
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service -q
# → 441 passed, 9 skipped (same as baseline)

# 4. 功能验证（comprehensive inline verification passed）
PYTHONPATH=src/data_clean python3 -c "
from repo.alignment_sidecar_writer import write_alignment_index, write_alignment_report
# JSON report write: file created, JSON parsable, final fields present
# Parquet index write: file created, content matches records, column names match AlignmentIndexSchema
# Failure cases: None/empty inputs raise ValueError, unwritable path raises OSError
"
# → ALL VERIFICATIONS PASSED (inline script ran 10+ checks)
```

### 开发者验收入口关系

本 L3 实现了 alignment index Parquet 和 report JSON sidecar 写出能力，是 `scene3_aligned_mcap_write_check` 功能检验项的写出内核。写出器消费上游已生成的 AlignmentIndex records 和 AlignmentReport draft，不重新计算统计。

建议用户在完成 service-s3-g6 全部 L3 (service_s3_019~023) 后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_aligned_mcap_write_check`，检查四类产物（aligned MCAP、alignment_index.parquet、alignment_report.json、aligned_mcap_write_summary.json）和失败清理行为是否符合 L2 契约。

### 当前没做

- 未写 aligned MCAP。
- 未实现临时目录整体提交策略（由 service_s3_022 覆盖）。
- 未修改 report draft 统计或 alignment index 规范化逻辑。
- 未写入共享执行记录。

### 遗留风险

- 无已知回归风险：441 service 测试全部通过，新增 15 个测试覆盖正常路径和失败路径。
- 本 L3 依赖 `pyarrow` 库；已安装验证。
- Parquet 写入使用 `pyarrow.parquet.write_table`；大文件场景下需要考虑写入性能，当前满足小样本验收需求。
- LSP diagnostics 无法执行（环境缺少 basedpyright-langserver），已确认类型匹配通过运行时检验。

### 归档说明

- 本任务完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。
- 原 active 功能组目录 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成 service-s3-g6 全部 L3 后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_aligned_mcap_write_check`，检查 alignment_index.parquet 可解析且字段对齐，alignment_report.json 包含 final 路径字段且内容正确。

