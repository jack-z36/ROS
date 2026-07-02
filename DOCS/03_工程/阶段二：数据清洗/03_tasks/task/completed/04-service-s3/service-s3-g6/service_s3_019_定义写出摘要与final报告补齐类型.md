# L3 微元任务：定义写出摘要与 final 报告补齐类型

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：aligned MCAP 与 sidecar 写出器  
L3 编号：service_s3_019  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_019_定义写出摘要与final报告补齐类型.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_019
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_019_定义写出摘要与final报告补齐类型.md
  group: service-s3-g6
  branch: service-s3
  wave: 1
  parallel_group: service-s3-g6-p1
  depends_on: [service_s3_003, service_s3_015]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_020, service_s3_021, service_s3_022]
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
定义 AlignedMcapWriteSummary 和 AlignmentReport final 补齐所需的代码层字段契约。
```

## 4. 本次不做

- 不实现任何文件写出。
- 不实现临时目录整体提交。
- 不写 aligned MCAP、Parquet、JSON 或真实数据产物。

## 5. 执行对象

- [[AlignedMcapWriteSummary]]
- [[AlignmentReport]]
- [[AlignedMcap]]

## 6. 执行依赖

- `service_s3_003` 应已定义 aligned 产物、report 和写出摘要基础类型。
- `service_s3_015` 应已定义 [[AlignmentReport]] draft/final 阶段字段。
- 必须保留 [[AlignmentReport]] 单一概念，不新增平行 final report 类型。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：对齐契约与配置定义、对齐索引与报告数据生成器
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcap.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- output_aligned_mcap、alignment_index_path、alignment_report_path、status、failure_reason、staging_dir、commit_policy、run_id
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并建议 Win 端调整数据定义，不自行拆分相似类型
```

## 8. 预期改动形态

- 在 `src/data_clean/schemas/` 中新增或扩展写出摘要和 final report 补齐类型。
- 类型能表达临时目录整体提交策略、失败摘要和 completed / failed 状态。
- 补充导入、实例化和 JSON 序列化测试。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `AlignedMcapWriteSummary` | dataclass / schema | `src/data_clean/schemas/` | 写出器、smoke test、场景四输入索引 |
| `AlignmentReportFinalization` 或等价函数输入类型 | dataclass / TypedDict | `src/data_clean/schemas/` | sidecar 写出器 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `output_aligned_mcap` | string/null | aligned MCAP 输出路径 | null | completed 时必填 |
| `alignment_index_path` | string/null | index sidecar 路径 | null | completed 时必填 |
| `alignment_report_path` | string/null | final report 路径 | null | completed 时必填 |
| `staging_dir` | string/null | 临时写出目录 | null | 失败诊断可保留 |
| `commit_policy` | string | 写出提交策略 | `staging_atomic_commit` | 必填 |
| `status` | enum string | `completed` / `failed` | 无 | 必填 |

## 10. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcap.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_003_定义aligned产物报告与写出摘要类型.md`
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

1. `src/data_clean/schemas/`
2. `src/data_clean/tests/`
3. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：导入失败测试 -> 最小类型定义 -> completed 必填路径测试 -> failed 摘要测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_aligned_mcap_write_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 不直接接入开发者入口，但由 `scene3_aligned_mcap_write_check` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止写出文件或真实数据产物。
- 禁止实现 sidecar / MCAP 写出服务。
- 禁止修改字段对齐或 report draft 统计逻辑。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas import AlignedMcapWriteSummary
assert AlignedMcapWriteSummary is not None
PY
```

## 17. 成功标准

- [x] 已定义 `AlignedMcapWriteSummary` 或等价代码类型。
- [x] 类型能表达 staging dir、commit policy、completed / failed 状态和失败原因。
- [x] 已定义 final report 路径补齐所需字段。
- [x] 未实现任何文件写出行为。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_019_定义写出摘要与final报告补齐类型.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_019_定义写出摘要与final报告补齐类型.md
文件名编号：service_s3_019
正文 L3 编号：service_s3_019
dispatch.task_id：service_s3_019
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id=service_s3_019`、`task_file` 匹配、`group=service-s3-g6`、`branch=service-s3`、`dispatch_status=ready`、`depends_on=[service_s3_003, service_s3_015]`（均已归档）。
- 上游依赖校验：`service_s3_003` 确认归档于 `04-service-s3/service-s3-g1/`，`service_s3_015` 确认归档于 `04-service-s3/service-s3-g5/`。
- 相关 L3 历史记录：已读取 `service_s3_003` 和 `service_s3_015` 执行摘要，确认 AlignedMcap、AlignmentReport、AlignedMcapWriteSummary 等基础类型已就绪。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/aligned_mcap_report.py`：扩展 `AlignedMcapWriteSummary`（`output_aligned_mcap`/`alignment_index_path`/`alignment_report_path` 改为 `str | None`，`commit_policy` 默认值改为 `staging_atomic_commit`，添加 `__post_init__` 校验 status 和 completed 必填路径）；新增 `AlignmentReportFinalization` dataclass（含 status、output_aligned_mcap、alignment_index、run_id、failure_reason 字段和 `__post_init__` 校验）。
- `src/data_clean/schemas/__init__.py`：导出 `AlignmentReportFinalization`。
- `src/data_clean/tests/service/test_aligned_mcap_report_schemas.py`：新增 4 个测试（`test_summary_nullable_output_paths`、`test_summary_invalid_status_raises`、`test_summary_completed_requires_paths`、`TestAlignmentReportFinalization` 4 个测试）。
- `src/data_clean/data_clean_architecture.md`：在 `schemas/aligned_mcap_report.py` 条目中加入 `AlignmentReportFinalization`。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

| 阶段 | 行为 | 结果 |
|------|------|------|
| VS1 RED | 编写 3 个 AlignedMcapWriteSummary 测试（nullable paths、invalid status、completed requires paths），更新 commit_policy 默认值断言 | 3 failed，类型尚不支持新行为 |
| VS1 GREEN | 修改 AlignedMcapWriteSummary：字段类型 `str` → `str | None`，default `None`；commit_policy 默认 `staging_atomic_commit`；添加 `__post_init__` 校验 | 3 → passed |
| VS2 RED | 编写 4 个 AlignmentReportFinalization 测试（import、nullable defaults、completed requires paths、invalid status） | 4 failed，类型不存在 |
| VS2 GREEN | 新增 `AlignmentReportFinalization` dataclass 含 `__post_init__` 校验，更新 `__init__.py` 导出 | 4 → passed |
| VS3 | 更新 `data_clean_architecture.md`，新增 `AlignmentReportFinalization` 到文档条目 | 通过 |
| Full Sweep | `python3 -m pytest src/data_clean/tests/service -q` | 426 passed, 9 skipped, 0 failed |

### 验收命令结果

```bash
# 1. 开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK

# 2. 本 L3 测试全部通过
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service/test_aligned_mcap_report_schemas.py -q
# → 42 passed

# 3. service 级测试
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service -q
# → 426 passed, 9 skipped

# 4. L3 指定验收命令
PYTHONPATH=src python3 - <<'PY'
from data_clean.schemas import AlignedMcapWriteSummary
assert AlignedMcapWriteSummary is not None
PY
# → 静默通过，无错误

# 5. 扩展内联验收（完整验证见正文上方）
PYTHONPATH=src python3 inline_verification.py
# → ALL VERIFICATIONS PASSED
```

### 成功标准处理

- [x] 已定义 `AlignedMcapWriteSummary` 或等价代码类型：扩展了现有 dataclass，支持 `str | None` 路径，添加 `__post_init__` 校验。
- [x] 类型能表达 staging dir、commit policy、completed / failed 状态和失败原因：`AlignedMcapWriteSummary` 包含 `staging_dir`、`commit_policy`（默认 `staging_atomic_commit`）、`status`（`completed`/`failed`）和 `failure_reason`。
- [x] 已定义 final report 路径补齐所需字段：新增 `AlignmentReportFinalization` dataclass，含 `output_aligned_mcap`、`alignment_index`、`run_id`、`status`、`failure_reason`。
- [x] 未实现任何文件写出行为：纯数据定义类，无 IO 逻辑。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用或运行日志。
- 本 L3 间接支撑 `scene3_aligned_mcap_write_check` 功能检验项（写出摘要类型和 final report 补齐类型是该检验项的数据契约基础）。
- 本 L3 的自动化验收只证明数据定义正确；场景最终验收需要用户在完成 service-s3-g6 全部 L3 后运行 `./start_data_clean.sh --dev` 选择场景三 → `scene3_aligned_mcap_write_check` 确认。

### 当前没做

- 未实现任何文件写出服务（MCAP、Parquet、JSON）。
- 未实现 sidecar 写出逻辑。
- 未修改字段对齐或 report draft 统计逻辑。
- 未写入 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、共享 `当前进度.md` 或共享 `执行记录.md`。

### 遗留风险

- LSP diagnostics 无法执行（当前环境缺少 `basedpyright-langserver`），无法静态检查类型一致性。
- 所有 426 个 service 测试通过，无新增失败。

### 归档说明

- 本任务完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。
- 原 active 功能组目录 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成 service-s3-g6 全部 L3 后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_aligned_mcap_write_check`，检查写出摘要类型和 final report 补齐类型是否符合 `AlignedMcapWriteSummary` 和 `AlignmentReportFinalization` 契约。

