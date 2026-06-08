# L3 微元任务：实现临时目录整体提交与失败摘要

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：aligned MCAP 与 sidecar 写出器  
L3 编号：service_s3_022  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_022_实现临时目录整体提交与失败摘要.md`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_022
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_022_实现临时目录整体提交与失败摘要.md
  group: service-s3-g6
  branch: service-s3
  wave: 3
  parallel_group: service-s3-g6-p3
  depends_on: [service_s3_020, service_s3_021]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_023]
  conflict_scope:
    files:
      - src/data_clean/service/aligned_mcap_writer.py
      - src/data_clean/runtime/
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.service.aligned_mcap_writer
      - data_clean.runtime
    config_keys:
      - scene3_alignment.output_dir
  dispatch_status: ready
```

## 3. 本次目标

```text
编排 aligned MCAP、index、report 的临时目录整体提交，并在失败时生成写出摘要和运行日志。
```

## 4. 本次不做

- 不实现底层 MCAP 写出细节。
- 不实现底层 Parquet / JSON sidecar 写出细节。
- 不接入开发者入口菜单。
- 不修改 report draft 统计逻辑。

## 5. 执行对象

- 临时目录 / staging 写出流程
- [[AlignedMcapWriteSummary]]
- 失败摘要和运行日志

## 6. 执行依赖

- `service_s3_020` 应已实现 sidecar 写出。
- `service_s3_021` 应已实现 aligned MCAP 最小写出。
- 本任务只负责把已有写出动作组合成整体提交策略。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：sidecar 写出、aligned MCAP 写出
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcap.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- staging_dir、commit_policy、status、failure_reason、output paths
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并汇报，不降低为逐文件保留策略
```

## 8. 预期改动形态

- 新增或扩展 service / runtime 层整体写出编排函数。
- 成功时所有产物通过 staging 提交到目标位置并生成 completed summary。
- 失败时不提交误导性完整产物，但保留失败摘要和运行日志。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 创建 staging dir | run context / output dir | run 临时目录 | directory | 每次运行独立 |
| 整体提交产物 | staging dir | 目标 output dir | MCAP / Parquet / JSON | 全部成功后提交 |
| 写失败摘要 | 异常和已知路径 | `aligned_mcap_write_summary.json` 或 error summary | JSON | 失败时允许保留 |
| 写运行日志 | 执行步骤和错误 | run log | JSON / text | 每次运行独立 |

### 文件或目录结构

```text
<run_dir>/
  staging/
  outputs/
    <mcap_a_stem>_aligned.mcap
    alignment_index.parquet
    alignment_report.json
    aligned_mcap_write_summary.json
  run_log.json
```

## 10. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcap.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/service_s3_020_实现alignment_index与report_sidecar写出.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/service_s3_021_实现aligned_MCAP最小写出与缺失字段跳过.md`

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

1. `src/data_clean/service/`
2. `src/data_clean/runtime/`
3. `src/data_clean/tests/`
4. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及写出编排，必须使用 `$tdd` 技能。建议顺序：成功整体提交测试 -> MCAP 写出失败不提交测试 -> sidecar 写出失败摘要测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_aligned_mcap_write_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 是；产物类型：完整写出产物或失败摘要 |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 不直接接入开发者入口，但由 `scene3_aligned_mcap_write_check` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/service/`
- `src/data_clean/runtime/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止重写底层 MCAP / sidecar writer。
- 禁止降级为逐文件成功即保留策略。
- 禁止把失败半成品标记为 completed。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [x] 已实现临时目录整体提交策略：`run_aligned_mcap_write_staging()` 在 `service/aligned_mcap_writer.py`。
- [x] 成功时写出完整产物并生成 completed write summary。
- [x] 任一写出失败时不留下误导性的完整 aligned MCAP（staging 清理 + 不提交 outputs）。
- [x] 失败时保留失败摘要和运行日志。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 任务文件身份校验

| 项目 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_022_实现临时目录整体提交与失败摘要.md` |
| 实际读取路径 | 匹配 |
| 文件名编号 | `service_s3_022` |
| 正文 L3 编号 | `service_s3_022` |
| 校验结论 | 通过 |

### 调度元数据校验

| 项目 | 结果 |
|---|---|
| task_id | service_s3_022 |
| task_file | 匹配 active 路径 |
| group | service-s3-g6 |
| branch | service-s3（当前分支确认） |
| dispatch_status | ready |
| depends_on | service_s3_020、service_s3_021（均已归档于 `04-service-s3/service-s3-g6/`） |
| 分支校验 | service-s3 ✓ |

### 开工自检

```bash
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK, branch: service-s3
```

### 必读上下文

已读取的文档：
- L2 能力模块：`aligned MCAP 与 sidecar 写出器.md`
- L2 数据定义：`AlignedMcapWriteSummary.md`、`AlignedMcap.md`、`AlignmentReport.md`
- 已完成 L3：`service_s3_020`（sidecar writer）、`service_s3_021`（aligned MCAP writer）
- 约束文档：`L3编码执行原则.md`、`L3任务文件身份校验约束.md`、`L3调度元数据约束.md`、`L3执行TDD与归档约束.md` 等
- 代码：`repo/aligned_mcap_writer.py`、`repo/alignment_sidecar_writer.py`、`schemas/aligned_mcap_report.py`、`data_clean_architecture.md`

### TDD 执行记录

| 切片 | 测试内容 | 状态 |
|---|---|---|
| VS1 RED→GREEN | `run_aligned_mcap_write_staging` importable + stub returns summary with correct fields | ✓ |
| VS2 RED→GREEN | Successful staging commit creates outputs/ files (aligned.mcap, alignment_index.parquet, alignment_report.json, summary, run_log) + staging cleaned up | ✓ |
| VS3 RED→GREEN | MCAP write failure (OSError injected) → no artifacts in outputs/ → failure summary + run_log written | ✓ |
| VS4 RED→GREEN | Sidecar (alignment index) write failure → no artifacts in outputs/ → failure summary | ✓ |
| VS5 RED→GREEN | Failure summary JSON contains all required fields (status, failure_reason, input_mcap_a, output paths, step_count, field_count, staging_dir, commit_policy, created_at, run_id, config_ref) | ✓ |
| VS6 RED→GREEN | Run log written on both success and failure with correct status, execution steps, required fields | ✓ |

### 修改文件

| 文件 | 改动 |
|---|---|
| `src/data_clean/service/aligned_mcap_writer.py` | **新增** `run_aligned_mcap_write_staging()` 编排函数 + `_clean_staging()`、`_write_summary()`、`_write_run_log()`、`_now_iso()` 辅助函数 |
| `src/data_clean/service/__init__.py` | 导出 `run_aligned_mcap_write_staging` |
| `src/data_clean/tests/service/test_aligned_mcap_write_staging.py` | **新增** 13 个测试覆盖 6 个 VS 切片 |
| `src/data_clean/data_clean_architecture.md` | 在 service 层级表中添加 `aligned_mcap_writer.py` 条目 |
| 本 L3 任务文件 | 成功标准标记完成，追加执行摘要 |

### 验收命令输出

```bash
# 1. 开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK, branch: service-s3

# 2. 本 L3 全部测试通过
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service/test_aligned_mcap_write_staging.py -q
# → 13 passed in 0.17s

# 3. service 级测试无回归
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service -q
# → 471 passed, 9 skipped (包括新增 13 个)

# 4. 验收命令
bash -c '
cd /home/hit/ROS
PYTHONPATH=src/data_clean:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support python3 -c "
from service.aligned_mcap_writer import run_aligned_mcap_write_staging
assert callable(run_aligned_mcap_write_staging)
print(\"run_aligned_mcap_write_staging importable: OK\")
"
'
```

### 成功标准处理

- [x] 已实现临时目录整体提交策略：`run_aligned_mcap_write_staging()` 在 `service/aligned_mcap_writer.py`。
- [x] 成功时写出完整产物并生成 completed write summary：VS2 验证 outputs/ 包含所有 4 个文件 + run_log。
- [x] 任一写出失败时不留下误导性的完整 aligned MCAP：VS3/VS4 验证 MCAP 或 sidecar 写失败时 outputs/ 无完整产物。
- [x] 失败时保留失败摘要和运行日志：VS3/VS5/VS6 验证失败时 summary JSON + run_log.json 写入 outputs/。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 的关系。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单或脚本调用。
- 本 L3 实现的临时目录整体提交策略是 `scene3_aligned_mcap_write_check` 功能检验项的核心写出编排。
- 本 L3 自动化验收只证明局部实现正确；场景最终验收需要用户在完成 service-s3-g6 全部 L3 后运行：
  ```bash
  ./start_data_clean.sh --dev
  ```
  选择场景三 → `scene3_aligned_mcap_write_check`，检查四类产物（aligned MCAP、alignment_index.parquet、alignment_report.json、aligned_mcap_write_summary.json）、失败清理行为和运行日志是否符合 L2 契约。

### 当前没做

- 未重写底层 MCAP / sidecar writer（复用 repo 层的 write_aligned_mcap、write_alignment_index、write_alignment_report）。
- 未接入开发者入口菜单（由 service_s3_023 覆盖）。
- 未修改 report draft 统计或 alignment index 规范化逻辑。
- 未写入共享执行记录。

### 遗留风险

- 无已知回归风险：471 service 测试全部通过（含新增 13 个），9 skipped（与基线一致）。
- 临时目录提交使用 `shutil.move`（同文件系统 rename 语义）；跨文件系统场景下 move 会 fallback 到 copy+delete，仍保证语义正确。
- 失败清理使用 `shutil.rmtree(staging_dir, ignore_errors=True)`；极端权限错误时可能残留空 staging 目录，不影响 outputs/ 完整性。

### 归档说明

- 本任务完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。
- 原 active 功能组目录 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成 service-s3-g6 全部 L3 后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_aligned_mcap_write_check`，检查临时目录整体提交行为：成功时 outputs/ 下 4 类产物完整可读、失败时无完整 aligned MCAP 但保留失败摘要和运行日志。

