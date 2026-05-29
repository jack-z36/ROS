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

- [ ] 已实现临时目录整体提交策略。
- [ ] 成功时写出完整产物并生成 completed write summary。
- [ ] 任一写出失败时不留下误导性的完整 aligned MCAP。
- [ ] 失败时保留失败摘要和运行日志。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

