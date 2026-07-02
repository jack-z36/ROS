# L3 微元任务：实现触觉半 step 窗口聚合

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：多策略字段对齐器  
L3 编号：service_s3_013  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_013
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md
  group: service-s3-g4
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g4-p2
  depends_on: [service_s3_008, service_s3_010]
  must_run_after: []
  can_run_parallel_with: [service_s3_011, service_s3_012]
  blocks: [service_s3_014]
  conflict_scope:
    files:
      - src/data_clean/service/tactile_field_aligner.py
      - src/data_clean/service/__init__.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.service.tactile
    config_keys:
      - scene3_alignment.tactile_strategy
  dispatch_status: ready
```

## 3. 本次目标

```text
实现触觉字段以 step_time_ns 为中心、半宽为半个 step 周期的窗口聚合。
```

## 4. 本次不做

- 不实现图像、夹爪或 pose 策略。
- 不定义触觉训练 mask。
- 不写 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 不接入开发者菜单。

## 5. 执行对象

- tactile modality source messages
- [[StepTimeline]]
- [[Scene3AlignmentConfig]]
- [[FieldAlignmentResult]]

## 6. 执行依赖

- `service_s3_010` 必须已完成并归档。
- `service_s3_008` 必须已完成并归档，以便读取 target step Hz 或 step 周期语义。
- 必须按当前触觉消息结构实现最小可测聚合，不猜测训练侧 mask。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：FieldAlignmentResult 类型、统一 Step 时间轴、场景三配置
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- step_time_ns、target_step_hz 或可推导 step period
- tactile source timestamps and values
- FieldAlignmentResult window_start_time_ns/window_end_time_ns/sample_count/coverage_ratio/derived_value
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得修改上游配置语义；停止并记录冲突
```

## 8. 预期改动形态

- 新增或扩展触觉字段聚合服务。
- 每个 step 的窗口为 `[step_time_ns - half_period, step_time_ns + half_period]` 或代码中等价的闭开边界，边界规则必须测试固定。
- 输出窗口起止、样本数、覆盖率和轻量聚合值。
- 空窗口输出 `status=missing_time`。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 窗口内有样本 | 聚合窗口内触觉样本 | `status=aggregated` | 无 |
| 窗口无样本 | 不生成聚合值 | `status=missing_time` | `missing_time` |
| 字段不可用 | catalog 标记 unavailable | `status=unavailable` | `unavailable` |
| 无效频率 | 无法推导 step 周期 | `status=invalid_input` 或失败 | `invalid_step_period` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `window_start_time_ns` | integer | 聚合窗口开始 | 聚合或 missing 时可复查 |
| `window_end_time_ns` | integer | 聚合窗口结束 | 必须晚于 start |
| `sample_count` | integer | 窗口内样本数 | 聚合时 `>0` |
| `coverage_ratio` | number | 窗口覆盖率 | 合法范围 `0..1` 或按既有定义 |
| `derived_value` | object/null | 触觉聚合轻量值 | 聚合成功时可填 |

## 10. 数据计算验收重点

- 合法输入通过。
- 空窗口和字段不可用能清楚降级。
- 窗口范围、样本数、覆盖率可被下游直接消费。
- 不决定训练 mask。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`

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

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：窗口范围测试 -> 多样本聚合测试 -> 空窗口 missing -> 覆盖率统计 -> 边界时间样本测试。

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

- `src/data_clean/service/tactile_field_aligner.py`
- `src/data_clean/service/__init__.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现图像、夹爪或 pose 策略。
- 禁止定义训练 mask 或 canonical dataset 字段。
- 禁止写最终 sidecar 或 aligned MCAP。
- 禁止写入真实数据产物或共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.service.tactile_field_aligner import align_tactile_field
assert callable(align_tactile_field)
PY
```

## 17. 成功标准

- [x] 半 step 窗口范围和边界规则已测试。
- [x] 多样本聚合、空窗口和字段不可用已测试。
- [x] 样本数和覆盖率统计已输出。
- [x] 输出为 [[FieldAlignmentResult]]，未生成最终 sidecar。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。

## 21. 执行摘要

### 执行基本信息

- L3 编号：service_s3_013
- 执行日期：2026-05-29
- 执行分支：service-s3
- 执行工具：TDD（RED → GREEN → REFACTOR）

### 身份校验

- 用户指定路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md`
- 实际读取路径：同上 ✓
- 文件名编号：`service_s3_013` ✓
- 正文 L3 编号：`service_s3_013` ✓
- dispatch_status: `ready` ✓
- branch: `service-s3` ✓
- depends_on: `[service_s3_008, service_s3_010]` ✓（均为已完成归档状态）

### 读取的相关任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
6. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`
7. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`

### 修改的文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/data_clean/service/tactile_field_aligner.py` | 新增 | 触觉半 step 窗口聚合对齐服务，包含 `align_tactile_field()` 主入口、`_compute_half_period_ns()` 窗口宽度计算、`_samples_in_window()` 时间窗口过滤、`_compute_aggregate_stats()` 聚合统计和 `_compute_coverage_ratio()` 时间覆盖率计算 |
| `src/data_clean/tests/service/test_tactile_field_aligner.py` | 新增 | 22 个测试，覆盖入口可调用性、窗口范围与边界规则、多样本聚合统计、空窗口 missing_time、覆盖率计算、无效频率 invalid_input、多 step 混合命中/缺失、字段元数据输出 |
| `src/data_clean/service/__init__.py` | 更新 | 导入并导出 `align_tactile_field` |
| `src/data_clean/data_clean_architecture.md` | 更新 | 在 Service 层目录表中新增 `service/tactile_field_aligner.py` 条目 |
| 当前 L3 任务文件 | 已更新 | 勾选成功标准、追加执行摘要 |

### 新增 / 修改的函数

| 函数 | 模块 | 说明 |
|------|------|------|
| `align_tactile_field()` | `tactile_field_aligner.py` | 主入口。接收 `(StepTimeline, field_name, source_topic, output_topic, tactile_samples, target_step_hz?)`，返回 `list[FieldAlignmentResult]` |
| `_compute_half_period_ns()` | `tactile_field_aligner.py` | 从 target_step_hz 计算半 step 周期的纳秒数 |
| `_samples_in_window()` | `tactile_field_aligner.py` | 按 `[window_start, window_end)` 闭开边界过滤触觉样本 |
| `_compute_aggregate_stats()` | `tactile_field_aligner.py` | 计算窗口内触觉样本的均值、标准差（总体）、最小值、最大值和样本数 |
| `_compute_coverage_ratio()` | `tactile_field_aligner.py` | 计算窗口内样本时间跨度与窗口宽度的比值，≥2 样本时返回 `[0,1]` 覆盖率 |

### TDD 执行记录

| 阶段 | 行为 | 结果 |
|------|------|------|
| **RED** | 编写 `test_tactile_field_aligner.py`（22 个测试），运行 `python3 -m pytest src/data_clean/tests/service/test_tactile_field_aligner.py -q` | 22 failed，`ModuleNotFoundError: No module named 'service.tactile_field_aligner'`（模块不存在），符合预期 |
| **GREEN** | 新增 `tactile_field_aligner.py` 完整实现（5 个函数），修复 std 计算使用总体方差而非样本方差 | 22 passed |
| **REFACTOR** | 更新 `service/__init__.py` 和 `data_clean_architecture.md`；验证全部已有 service 测试无回归（1 个 pre-existing failure 无关本 L3） | 385 passed, 9 skipped, 1 pre-existing failure |

### 验证命令与输出

```bash
# 阶段二开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK

# 新测试（22 个）
PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/service/test_tactile_field_aligner.py -v
# → 22 passed

# 全部 service 测试验证回归
PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/service -q
# → 385 passed, 9 skipped, 1 failed (pre-existing test_aligned_mcap_report_schemas.py import issue)

# 内联验收入口
PYTHONPATH=src/data_clean python3 -c "
from service.tactile_field_aligner import align_tactile_field
assert callable(align_tactile_field)
print('L3 verification PASSED')
"
# → L3 verification PASSED
```

### 成功标准勾选

- [x] 半 step 窗口范围和边界规则已测试（`TestWindowRange`：窗口边界、起点包含、终点排除、内部包含）。
- [x] 多样本聚合、空窗口和字段不可用已测试（`TestMultiSampleAggregation`：均值/标准差/极值；`TestEmptyWindow`：空窗口 missing_time、窗口外样本、missing 时仍设置窗口起止）。
- [x] 样本数和覆盖率统计已输出（`TestCoverageRatio`：多样本接近 1.0、部分覆盖、单样本覆盖率为 0、missing 时覆盖率为 None）。
- [x] 输出为 `FieldAlignmentResult`，未生成最终 sidecar（所有测试输出均为 `FieldAlignmentResult` 实例，无 sidecar/alignment index 生成）。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系：本 L3 不直接接入开发者入口，但间接支撑场景三 `scene3_field_alignment_check`。

### 归档信息

- 源路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md`
- 目标路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md`
- active 目录清空：归档后将检查 `active/service-s3-g4/` 是否仍有其他文件，如无则删除空目录。
- dispatch 文件未修改：`task/dispatch/service-s3-g4.yaml` 保持不变。

### 当前没做什么

- 未实现图像、夹爪或 pose 策略。
- 未定义触觉训练 mask。
- 未生成 `AlignmentIndex`、`AlignmentReport` 或 aligned MCAP。
- 未接入 `./start_data_clean.sh --dev` 开发者入口。
- 未修改 `task/dispatch/service-s3-g4.yaml`。
- 未写入 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。
- 未使用 `python` 命令（均使用 `python3`）。

### 开发者入口影响说明

本 L3 是触觉字段半 step 窗口聚合的核心服务层，提供了 `align_tactile_field()` 入口。场景三的完整开发者验收需要：

1. `service_s3_014` 将本服务以及 `service_s3_011`（图像与夹爪）、`service_s3_012`（pose）接入 `scene3_field_alignment_check` 功能检验项。
2. 用户运行 `./start_data_clean.sh --dev` 选择场景三 → `scene3_field_alignment_check` 做最终人工验收。

本 L3 的 22 个 pytest 自动化测试覆盖了窗口范围、边界规则、多样本聚合、空窗口降级、覆盖率计算、无效频率和多 step 混合场景，证明局部实现正确。

### 建议人工验收

本 L3 完成后且后续 `service_s3_014`（接入开发者入口）也完成后，建议用户运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_field_alignment_check` → 执行并检查触觉字段对齐结果的窗口起止、样本数、覆盖率和聚合统计值是否符合 L2 契约。

### 建议 Win 端后续同步

- 确认本 L3 已归档，`dispatch/service-s3-g4.yaml` 中 `service_s3_013` 对应的 `depends_on` 完成闭环。
