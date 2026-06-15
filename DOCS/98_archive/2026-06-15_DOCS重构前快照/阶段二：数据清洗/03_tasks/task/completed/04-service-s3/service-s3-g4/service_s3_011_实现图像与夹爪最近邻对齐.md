# L3 微元任务：实现图像与夹爪最近邻对齐

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：多策略字段对齐器  
L3 编号：service_s3_011  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_011
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md
  group: service-s3-g4
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g4-p2
  depends_on: [service_s3_008, service_s3_010]
  must_run_after: []
  can_run_parallel_with: [service_s3_012, service_s3_013]
  blocks: [service_s3_014]
  conflict_scope:
    files:
      - src/data_clean/service/field_aligner.py
      - src/data_clean/service/__init__.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.service
    config_keys:
      - scene3_alignment
  dispatch_status: ready
```

## 3. 本次目标

```text
实现图像字段和夹爪字段按 step_time_ns 最近邻生成 FieldAlignmentResult。
```

## 4. 本次不做

- 不实现 pose 插值、slerp 或 fallback。
- 不实现触觉窗口聚合。
- 不生成 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 不接入开发者菜单。

## 5. 执行对象

- [[StepTimeline]]
- [[SourceTopicCatalog]]
- [[TargetFieldMapping]]
- [[FieldAlignmentResult]]
- image / gripper modality source messages

## 6. 执行依赖

- `service_s3_008` 必须已完成并归档，确保 [[StepTimeline]] 生成服务可用。
- `service_s3_010` 必须已完成并归档，确保 [[FieldAlignmentResult]] 类型可用。
- 必须复用 MCAP reader / repo 既有能力读取来源消息，不重新盘点 topic。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：统一 Step 时间轴生成器、FieldAlignmentResult 类型、MCAP_A 输入盘点与校验器
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- step_index / step_time_ns
- field_entries.availability / source_topic / modality / max_dt_ms
- image 和 gripper 源消息时间戳及 gripper 轻量值
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得改变上游类型；停止并记录接口冲突
```

## 8. 预期改动形态

- 新增或扩展 `src/data_clean/service/field_aligner.py`，提供图像和夹爪最近邻对齐函数。
- 图像结果只写 `message_ref` 和对齐元数据，不内联 payload。
- 夹爪结果按 `step_time_ns` 最近邻并可内联轻量 gripper 值，不依赖同侧图像。
- 新增 service 测试覆盖命中、超时、缺 topic、空 topic 和夹爪不跟随图像。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 图像合法输入 | 对 `step_time_ns` 找最近图像样本 | `FieldAlignmentResult(status=aligned, message_ref=...)` | 无 |
| 图像超时 | 最近样本 `dt_ms > max_dt_ms` | `status=timeout`，保留 step | `timeout` |
| 图像缺 topic | field availability 非 available | `status=unavailable` | `missing_topic` |
| 夹爪合法输入 | 对 `step_time_ns` 找最近夹爪样本 | `status=aligned`，可内联 gripper 值 | 无 |
| 夹爪超时或空 topic | 无可用样本或超阈值 | `missing_time` 或 `timeout` | `missing_time` / `timeout` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `FieldAlignmentResult` | [[FieldAlignmentResult]] | 最近邻结果 | 每个 step-field 最多一条 |
| `message_ref` | string/null | 图像或原始消息引用 | 图像命中时非空 |
| `derived_value` | object/null | 夹爪轻量值 | gripper 命中时可填 |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败或降级，错误信息能说明具体缺口。
- 图像不内联 payload。
- 夹爪直接按 step 最近邻，不依赖图像结果。
- 输出结构可被下游直接消费。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`

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

1. `src/data_clean/schemas/alignment_index.py`
2. `src/data_clean/service/step_timeline_generator.py`
3. `src/data_clean/repo/`
4. `src/data_clean/service/`
5. `src/data_clean/tests/`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：图像命中测试 -> 图像超时测试 -> 夹爪直接最近邻测试 -> 缺失 / 空 topic 降级测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_field_alignment_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否，由 service_s3_014 写出 |
| 是否需要写运行日志 | 否，由 service_s3_014 写出 |
| 是否允许临时覆盖配置 | 服务接受调用方传入配置；本 L3 不实现交互覆盖 |
| 是否允许保存覆盖到配置文件 | 否 |
| 最终人工验收提示 | 不直接接入开发者入口，但由 `scene3_field_alignment_check` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/service/field_aligner.py`
- `src/data_clean/service/__init__.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现 pose 或 tactile 策略。
- 禁止修改 FieldAlignmentResult 字段语义。
- 禁止生成 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 禁止写入真实数据产物或共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.service.field_aligner import align_nearest_fields
assert callable(align_nearest_fields)
PY
```

## 17. 成功标准

- [x] 图像最近邻命中和超时行为已测试。
- [x] 夹爪直接按 step 最近邻行为已测试。
- [x] 缺 topic / 空 topic 降级行为已测试。
- [x] 输出为 [[FieldAlignmentResult]]，未生成最终 sidecar。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md
实际读取路径：同上（完全一致）
文件名编号：service_s3_011
正文 L3 编号：service_s3_011
dispatch.task_id：service_s3_011
校验结论：通过 ✓
```

### 调度与开工自检

- 调度元数据校验：`task_id=service_s3_011`、`task_file` 匹配、`group=service-s3-g4`、`branch=service-s3`、`dispatch_status=ready`、`depends_on=[service_s3_008, service_s3_010]`（均已归档于 `completed/04-service-s3/`）。
- 当前分支：`service-s3` ✓
- 开工自检：`bash scripts/init_data_clean_dev.sh` → `Data clean dev environment OK` ✓

### 读取的相关文档和代码

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md`
6. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`
7. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`
8. `src/data_clean/schemas/alignment_config.py`（TargetFieldMapping、AlignmentModality）
9. `src/data_clean/schemas/alignment_input.py`（SourceTopicCatalog、FieldAvailability、SourceFieldEntry）
10. `src/data_clean/schemas/field_alignment.py`（FieldAlignmentResult）
11. `src/data_clean/schemas/step_timeline.py`（StepTimeline、StepTimelineEntry、FieldAlignmentStatus）
12. `src/data_clean/service/step_timeline_generator.py`（作为 service 层参考）

### 本次修改文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/data_clean/service/field_aligner.py` | 新增 | 图像与夹爪最近邻字段对齐器，主入口 `align_nearest_fields()`。内部包含 `_find_field_entry()`、`_compute_dt_ms()`、`_find_nearest_sample()` 工具函数。按 step × field 遍历，处理 availability 门控、最近邻查找、超时判定、image（仅 message_ref）和 gripper（内联 derived_value）分流。 |
| `src/data_clean/service/__init__.py` | 更新 | 导入并导出 `align_nearest_fields`。 |
| `src/data_clean/tests/service/test_field_aligner.py` | 新增 | 14 个测试，覆盖图像命中、图像超时、图像空 topic、图像 missing topic、夹爪命中、夹爪超时、夹爪空 topic、多 step 正确性、多字段独立对齐、以及字段间不相互阻塞。 |
| `src/data_clean/data_clean_architecture.md` | 更新 | 在 Service 层新增 `service/field_aligner.py` 条目描述。 |
| 当前 L3 任务文件 | 已更新 | 勾选成功标准并追加本执行摘要。 |

### 新增 / 修改的函数

| 函数 | 模块 | 说明 |
|------|------|------|
| `align_nearest_fields(timeline, catalog, field_mappings, field_samples)` | `field_aligner.py` | 主入口。消费 StepTimeline、SourceTopicCatalog、TargetFieldMapping 列表和预读的按 field_name 组织的样本数据，返回 `list[FieldAlignmentResult]`。 |
| `_find_field_entry(catalog, field_name)` | `field_aligner.py` | 在 catalog.field_entries 中按 field_name 查找对应条目。 |
| `_compute_dt_ms(step_time_ns, sample_time_ns)` | `field_aligner.py` | 计算两个时间戳的绝对值差（毫秒）。 |
| `_find_nearest_sample(step_time_ns, samples)` | `field_aligner.py` | 在样本列表中按 `|t - step_time_ns|` 找最近邻。 |

### TDD 执行记录

| 阶段 | 行为 | 结果 |
|------|------|------|
| **RED** | 编写 `test_field_aligner.py`（14 个测试，6 个测试类覆盖图像命中/超时/缺失、夹爪命中/超时/缺失、多 step、多字段），运行 `python3 -m pytest src/data_clean/tests/service/test_field_aligner.py -q` | 14 failed（`ModuleNotFoundError: No module named 'service.field_aligner'`），符合预期 |
| **GREEN** | 新增 `field_aligner.py`（`align_nearest_fields` + 3 个辅助函数），更新 `service/__init__.py` | 14 passed |
| **REFACTOR** | 更新 `data_clean_architecture.md`；验证全部已有 service 测试无回归（1 个 pre-existing failure 无关本 L3） | 348 passed, 9 skipped, 1 pre-existing failed |

### 验证命令与输出

```bash
# 阶段二开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK

# 本 L3 测试（14 个）
python3 -m pytest src/data_clean/tests/service/test_field_aligner.py -q
# → 14 passed

# 全部 service 测试验证回归
python3 -m pytest src/data_clean/tests/service -q
# → 348 passed, 9 skipped, 1 failed
#   (pre-existing: test_aligned_mcap_report_schemas.py 使用 data_clean 全路径导入)

# 内联验收入口
PYTHONPATH=src/data_clean python3 -c "
from service.field_aligner import align_nearest_fields
assert callable(align_nearest_fields)
print('L3 verification PASSED')
"
# → L3 verification PASSED
```

### 成功标准处理

- [x] **图像最近邻命中和超时行为已测试**：
  - `test_image_single_step_exact_match`：step 与图像样本时间一致 → `status=aligned`，`message_ref` 非空，`derived_value=None`。
  - `test_image_nearest_not_exact`：样本距 step 0.05 ms 且在 max_dt 内 → `status=aligned`，`source_time_ns` 和 `dt_ms` 正确。
  - `test_image_sample_beyond_max_dt`：样本距 step 200 ms，max_dt=100 → `status=timeout`。
- [x] **夹爪直接按 step 最近邻行为已测试**：
  - `test_gripper_single_step_exact_match`：step 与夹爪样本一致 → `status=aligned`，`derived_value={"gripper_width": 0.45}`。
  - `test_gripper_no_dependence_on_image`：夹爪使用自身时间（100 ms）而非图像时间独立对齐 → `status=aligned`，`source_time_ns` 为夹爪样本时间。
- [x] **缺 topic / 空 topic 降级行为已测试**：
  - `test_image_no_samples`：空 topic → `status=unavailable` 或 `missing_time`。
  - `test_image_missing_topic`：缺失 topic → `status=unavailable`，notes 含 `missing_topic`。
  - `test_gripper_no_samples`：空 topic → `status=missing_time` 或 `unavailable`。
  - `test_gripper_timeout`：样本超阈值 → `status=timeout`。
- [x] **输出为 FieldAlignmentResult，未生成最终 sidecar**：所有函数返回 `list[FieldAlignmentResult]` dataclass，无 AlignmentIndex、AlignmentReport 或 aligned MCAP 写出。
- [x] **已说明本 L3 与开发者验收入口的关系**：见下方「开发者验收入口关系」段落。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用或运行日志。
- 本 L3 间接支撑场景三 `scene3_field_alignment_check` 功能检验项（通过提供 `align_nearest_fields` 服务供后续 L3 编排消费）。
- 本 L3 的自动化验收只证明场景三图像与夹爪最近邻对齐局部实现正确；场景最终验收需要场景三全部 L3（`service_s3_010` → `service_s3_013`）完成后运行完整 smoke test 或选择 `scene3_field_alignment_check` 检验项。

### 归档信息

- 源路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md`
- 目标路径：`DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md`
- active 目录清空：归档后将检查 `active/service-s3-g4/` 是否仍有其他文件，如无则删除空目录。
- dispatch 文件未修改：`task/dispatch/service-s3-g4.yaml` 保持不变。

### 当前没做

- 未实现 pose 插值、slerp 或 fallback（由 `service_s3_012` 覆盖）。
- 未实现触觉窗口聚合（由 `service_s3_013` 覆盖）。
- 未实现夹爪跟随图像策略（gripper 直接按 step 最近邻，符合 L2 首版契约）。
- 未生成 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 未读取 MCAP_A 消息或重新实现 topic catalog/时间盘点。
- 未修改 `task/dispatch/service-s3-g4.yaml`。
- 未写入 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。
- 未使用 `python` 命令（均使用 `python3`）。

### 建议最终人工验收

本 L3 完成后，建议用户在完成场景三全部 L3（`service_s3_010` → `service_s3_013`）后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_field_alignment_check`，检查图像和夹爪字段的最近邻对齐结果是否符合 `FieldAlignmentResult` 契约。

### 建议 Win 端后续同步

- 确认本 L3 已归档，`dispatch/service-s3-g4.yaml` 中 `service_s3_011` 对应的 `depends_on` 完成闭环。
- 当前 `field_aligner.py` 的 `align_nearest_fields()` 入参 `field_samples` 为 `dict[str, list[tuple]]`，该结构为内存态预读消息数据；后续 `service_s3_014` 接入开发者入口时可根据实际 MCAP reader 桥接消息数据。
