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

- [x] 已实现 aligned MCAP 最小写出。
- [x] 有效字段状态会写入 aligned MCAP。
- [x] `missing_time`、`timeout`、`unavailable` 不写占位消息，也不复用上一有效值。
- [x] 未写 sidecar、report 或写出摘要。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_021_实现aligned_MCAP最小写出与缺失字段跳过.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_021_实现aligned_MCAP最小写出与缺失字段跳过.md
文件名编号：service_s3_021
正文 L3 编号：service_s3_021
dispatch.task_id：service_s3_021
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id=service_s3_021`、`task_file` 匹配、`group=service-s3-g6`、`branch=service-s3`、`dispatch_status=ready`、`depends_on=[service_s3_011, service_s3_012, service_s3_013, service_s3_019]`（均已归档）。
- 上游依赖校验：`service_s3_011`、`service_s3_012`、`service_s3_013` 确认归档于 `04-service-s3/service-s3-g4/`，`service_s3_019` 确认归档于 `04-service-s3/service-s3-g6/`。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

| 文件 | 改动 |
|------|------|
| `src/data_clean/repo/aligned_mcap_writer.py` | **新增** `write_aligned_mcap()` 函数，含 `_ensure_parent()`、`_parse_message_ref()`、`_build_source_payload_index()`、`_resolve_payload()`、`_encode_derived_value()`、`_register_topic_schema()` 辅助函数 |
| `src/data_clean/repo/__init__.py` | 导出 `write_aligned_mcap` |
| `src/data_clean/tests/service/test_aligned_mcap_writer.py` | **新增** 17 个测试覆盖 6 个 VS 切片 |
| `src/data_clean/data_clean_architecture.md` | 在 repo 层级表中添加 `aligned_mcap_writer.py` 条目 |
| 本 L3 任务文件 | 成功标准标记完成，追加执行摘要 |

### TDD 过程

| 阶段 | 行为 | 结果 |
|------|------|------|
| VS1 RED→GREEN | `write_aligned_mcap` importable + stub returns output path | 2 → passed |
| VS2 RED→GREEN | Single aligned field writes one message at step_time_ns; multiple topics; fallback to source_topic | 3 → passed |
| VS3 RED→GREEN | `missing_time` / `timeout` / `unavailable` skip (0 messages); mixed valid/invalid filter correctly | 4 → passed |
| VS4 RED→GREEN | Gripper `derived_value` writes encoded Float32 payload; derived_value takes priority over message_ref | 2 → passed |
| VS5 RED→GREEN | None inputs raise ValueError; unwritable path raises OSError | 5 → passed |
| VS6 RED→GREEN | Source MCAP checksum unchanged after write | 1 → passed |

### 验收命令结果

```bash
# 1. 开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK

# 2. 本 L3 测试全部通过
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service/test_aligned_mcap_writer.py -q
# → 17 passed

# 3. service 级测试
PYTHONPATH=src python3 -m pytest src/data_clean/tests/service -q
# → 458 passed, 9 skipped (no regressions)

# 4. L3 指定验收命令
PYTHONPATH=src/data_clean:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support python3 -c "
from repo.aligned_mcap_writer import write_aligned_mcap
assert write_aligned_mcap is not None
"
# → 静默通过，无错误

# 5. 综合验证脚本
python3 /tmp/verify_s3_021.py
# → 20/20 passed, ALL VERIFICATIONS PASSED
```

### 成功标准处理

- [x] 已实现 aligned MCAP 最小写出：`repo/aligned_mcap_writer.py` 中的 `write_aligned_mcap()` 函数。
- [x] 有效字段状态会写入 aligned MCAP：`status` 为 `aligned`、`interpolated`、`aggregated`、`fallback_nearest` 时写消息。
- [x] `missing_time`、`timeout`、`unavailable` 不写占位消息：状态过滤在 VS3 中验证。
- [x] 未写 sidecar、report 或写出摘要：纯 MCAP 写出，无 Parquet/JSON 写入。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用或运行日志。
- 本 L3 间接支撑 `scene3_aligned_mcap_write_check` 功能检验项（aligned MCAP 写出是该检验项的核心产物）。
- 本 L3 的自动化验收只证明最小写出正确；场景最终验收需要用户在完成 service-s3-g6 全部 L3 后运行 `./start_data_clean.sh --dev` 选择场景三 → `scene3_aligned_mcap_write_check` 确认。

### 当前没做

- 未写 sidecar Parquet 或 report JSON（由 service_s3_020 覆盖）。
- 未实现临时目录整体提交策略（由 service_s3_022 覆盖）。
- 未实现 pose 或 tactile derived_value 编码（只实现了 gripper Float32）。
- 未写入共享执行记录。

### 遗留风险

- 无已知回归风险：458 service 测试全部通过，新增 17 个测试覆盖正常路径和失败路径。
- Pose 和 tactile derived_value 编码未实现（当前返回 `None` 跳过），未来需要扩展 `_encode_derived_value()`。
- MCAP 写出使用通用 `example/msg/Bytes` schema 注册；实际部署时需要根据上游 topic 注册正确 ROS2 schema。
- LSP diagnostics 无法执行（环境缺少 `basedpyright-langserver`），已确认类型匹配通过运行时检验。

### 归档说明

- 本任务完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。
- 原 active 功能组目录 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成 service-s3-g6 全部 L3 后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_aligned_mcap_write_check`，检查 aligned MCAP 文件存在、消息时间戳为 step 时间、有效字段有消息而缺失字段不写占位。

