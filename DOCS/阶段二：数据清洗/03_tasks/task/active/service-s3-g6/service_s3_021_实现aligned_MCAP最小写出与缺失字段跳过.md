# L3 微元任务：实现 aligned MCAP 最小写出与缺失字段跳过

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：aligned MCAP 与 sidecar 写出器  
L3 编号：service_s3_021  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_021_实现aligned_MCAP最小写出与缺失字段跳过.md`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_021
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_021_实现aligned_MCAP最小写出与缺失字段跳过.md
  group: service-s3-g6
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g6-p2
  depends_on: [service_s3_011, service_s3_012, service_s3_013, service_s3_019]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_022, service_s3_023]
  conflict_scope:
    files:
      - src/data_clean/repo/aligned_mcap_writer.py
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
实现 aligned MCAP 最小写出，并确保 missing_time、timeout、unavailable 字段不写占位消息。
```

## 4. 本次不做

- 不写 alignment index Parquet 或 final report JSON。
- 不实现临时目录整体提交。
- 不接入开发者入口。
- 不重新执行字段对齐算法。

## 5. 执行对象

- [[AlignedMcap]]
- [[FieldAlignmentResult]]
- [[StepTimeline]]
- [[McapA]]

## 6. 执行依赖

- `service_s3_011`、`service_s3_012`、`service_s3_013` 应已能产出有效字段对齐结果。
- `service_s3_019` 应已定义写出摘要和 final report 类型。
- 必须按 [[AlignedMcap]] 契约使用 step 时间戳写主数据。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：多策略字段对齐器、aligned 写出摘要类型定义
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcap.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- FieldAlignmentResult.status、message_ref、derived_value、output_topic、step_time_ns
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并汇报，不自行发明占位消息语义
```

## 8. 预期改动形态

- 新增或扩展 MCAP 写出 repo / service。
- 只对 `aligned`、`interpolated`、`aggregated`、`fallback_nearest` 写消息。
- 对 `missing_time`、`timeout`、`unavailable` 不写空消息、不复用上一有效值。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 写 aligned MCAP | MCAP_A、FieldAlignmentResult、StepTimeline | `<mcap_a_stem>_aligned.mcap` 或测试临时路径 | MCAP | 测试使用临时目录，不覆盖 MCAP_A |

### 文件或目录结构

```text
<run_or_output_dir>/
  <mcap_a_stem>_aligned.mcap
```

## 10. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcap.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_012_实现pose插值slerp与fallback.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/service_s3_019_定义写出摘要与final报告补齐类型.md`

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

本 L3 涉及 MCAP 写出，必须使用 `$tdd` 技能。建议顺序：有效字段写入测试 -> 缺失字段跳过测试 -> 不修改 MCAP_A 测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_aligned_mcap_write_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 是；产物类型：aligned MCAP |
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

- 禁止写 alignment index Parquet 或 report JSON。
- 禁止为 missing / timeout / unavailable 写空占位。
- 禁止复用上一有效值填补缺失字段。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.repo.aligned_mcap_writer import write_aligned_mcap
assert write_aligned_mcap is not None
PY
```

## 17. 成功标准

- [ ] 已实现 aligned MCAP 最小写出。
- [ ] 有效字段状态会写入 aligned MCAP。
- [ ] `missing_time`、`timeout`、`unavailable` 不写占位消息，也不复用上一有效值。
- [ ] 未写 sidecar、report 或写出摘要。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

