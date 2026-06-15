# L3 微元任务：实现 AlignmentReport 草稿统计生成

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：对齐索引与报告数据生成器  
L3 编号：service_s3_017  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_017_实现AlignmentReport草稿统计生成.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_017
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_017_实现AlignmentReport草稿统计生成.md
  group: service-s3-g5
  branch: service-s3
  wave: 3
  parallel_group: service-s3-g5-p3
  depends_on: [service_s3_015, service_s3_016]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_018, service_s3_020]
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
实现基于 AlignmentIndex、timeline 和输入摘要的 AlignmentReport draft 统计生成。
```

## 4. 本次不做

- 不写 `alignment_report.json`。
- 不补齐 final 输出路径。
- 不写 aligned MCAP 或 alignment index sidecar。
- 不决定训练 mask 或 episode 可用性。

## 5. 执行对象

- [[AlignmentIndex]]
- [[AlignmentReport]]
- [[StepTimeline]]
- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]

## 6. 执行依赖

- `service_s3_015` 应已定义 [[AlignmentReport]] draft/final 类型。
- `service_s3_016` 应已实现 AlignmentIndex records 规范化。
- report draft 不要求最终输出路径，由第 6 模块补齐。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：AlignmentIndex 规范化、时间轴生成、输入盘点
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- AlignmentIndex records、step timeline 摘要、输入 summary、配置引用
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并汇报，不能自行修改上游接口
```

## 8. 预期改动形态

- 新增或扩展 service 层 report draft 统计函数。
- 输出 draft [[AlignmentReport]]，包含 field_stats、status_counts、degradation_summary、failure_reason。
- 测试覆盖 completed、degraded、failed 统计边界。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | 根据 index 统计状态、字段和 dt / window 指标 | completed 或 degraded report draft | 无 |
| 缺失输入 | index 或 timeline 缺失 | failed draft | `missing_alignment_index` / `missing_step_timeline` |
| 边界输入 | 存在 missing / timeout / fallback / unavailable | 进入 degradation_summary，不判定训练失败 | 无 |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `status_counts` | object | 状态计数 | 覆盖出现过的合法状态 |
| `field_stats` | object | 字段级统计 | 可机器读取 |
| `degradation_summary` | object | 降级摘要 | 不表达训练 mask |
| `failure_reason` | string/null | 失败原因 | 失败时必填 |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/service_s3_015_定义AlignmentReport阶段字段与统计类型.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/service_s3_016_实现AlignmentIndex规范化与唯一性检查.md`

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

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：status counts 测试 -> field stats 测试 -> degradation summary 测试 -> 缺失输入失败测试。

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

- 禁止写文件或真实数据产物。
- 禁止补齐 final output paths。
- 禁止实现 sidecar 写出器或 aligned MCAP 写出器。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.service.alignment_report import build_alignment_report_draft
assert build_alignment_report_draft is not None
PY
```

## 17. 成功标准

- [x] 已实现 AlignmentReport draft 统计生成。
- [x] 已覆盖 status_counts、field_stats 和 degradation_summary。
- [x] 缺失、超时、fallback、unavailable 只进入质量统计，不做训练裁决。
- [x] 未写 JSON、Parquet、MCAP 或写出摘要。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/`。如果 `active/service-s3-g5/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 身份校验与 Dispatch 验证

| 项目 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_017_实现AlignmentReport草稿统计生成.md` |
| 实际读取路径 | 匹配 |
| 文件名编号 | `service_s3_017` |
| 正文 L3 编号 | `service_s3_017` |
| task_id | service_s3_017 |
| group | service-s3-g5 |
| branch | service-s3 (当前分支确认) |
| dispatch_status | ready |
| depends_on | [service_s3_015, service_s3_016] → 均已归档 |
| 分支校验 | service-s3 ✓ |

### TDD 执行记录

| 切片 | 测试内容 | 状态 |
|---|---|---|
| VS1 RED→GREEN | `build_alignment_report_draft` importable + minimal valid input returns AlignmentReport | ✓ |
| VS2 RED→GREEN | `status_counts` 正确统计各 FieldAlignmentStatus 出现次数 | ✓ |
| VS3 RED→GREEN | `field_stats` 按 field_name 分组计算 AlignmentFieldStats (count, avg_dt_ms, max_dt_ms, coverage_ratio) | ✓ |
| VS4 RED→GREEN | `degradation_summary` 聚合 missing/timeout/fallback/unavailable 事实，含 per-field 列表和 fallback_reason_counts | ✓ |
| VS5 RED→GREEN | None/空 index records → failed draft with `missing_alignment_index` | ✓ |
| VS6 RED→GREEN | None timeline → failed draft with `missing_step_timeline` | ✓ |

### 修改文件

| 文件 | 改动 |
|---|---|
| `src/data_clean/service/alignment_report.py` | **新增** `build_alignment_report_draft()`, `_compute_status_counts()`, `_compute_field_stats()`, `_compute_degradation_summary()`, `_compute_timeline_summary()` |
| `src/data_clean/service/__init__.py` | 导出 `build_alignment_report_draft` |
| `src/data_clean/tests/service/test_alignment_report_draft.py` | **新增** 9 个测试覆盖 importable、minimal valid input、status_counts、field_stats、degradation_summary、no-degradation、missing index (None/empty)、missing timeline |
| 本 L3 任务文件 | 成功标准标记完成，追加执行摘要 |

### 验收命令输出

```bash
# 开工自检
bash scripts/init_data_clean_dev.sh
# → Git branch OK: service-s3, Python imports OK, start_data_clean.sh --help OK

# 全部服务层测试（含本 L3 新增）
python3 -m pytest src/data_clean/tests/service/test_alignment_report_draft.py -v -q
# → 9 passed in 0.10s

# 功能验证
PYTHONPATH=src/data_clean python3 -c "
from service.alignment_report import build_alignment_report_draft
# ... validates status_counts, field_stats, degradation_summary, failed cases ...
# → ALL ACCEPTANCE CHECKS PASSED
"
```

### 与开发者验收入口的关系

本 L3 实现了 AlignmentReport draft 统计生成服务，是 `scene3_alignment_report_check` 功能检验项的直接计算内核。输出 AlignmentReport draft 对象包含 status_counts、field_stats、degradation_summary 和 failure_reason，可直接被第 6 模块 (aligned MCAP 与 sidecar 写出器) 消费，补齐 final 字段后落盘为 `alignment_report.json`。建议用户在完成 service-s3-g5 全部 L3 (service_s3_015~018) 后运行 `./start_data_clean.sh --dev` 选择场景三 → `scene3_alignment_report_check` 做最终人工验收。

### 遗留风险

- `data_clean.service.alignment_report` 的包路径导入 (`from data_clean.service.alignment_report import ...`) 需要 `PYTHONPATH=src/data_clean`，这是 data_clean 全库的一致约定（非本模块特有）。
- 新的统计函数由本 L3 首次实现，在 service_s3_018 接入开发者菜单前只能通过单元测试验证；建议后续 L3 在集成场景中进一步验证统计准确性。

