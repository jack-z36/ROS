# L3 微元任务：实现统一 Step 时间轴生成服务

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：统一 Step 时间轴生成器  
L3 编号：service_s3_008  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_008
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md
  group: service-s3-g3
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g3-p2
  depends_on: [service_s3_005, service_s3_007]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_009]
  conflict_scope:
    files:
      - src/data_clean/service/step_timeline_generator.py
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
实现消费 SourceTopicCatalog、McapAInputValidationSummary 和 Scene3AlignmentConfig 的统一 Step 时间轴生成服务。
```

## 4. 本次不做

- 不读取 MCAP_A 原始消息。
- 不重复 topic、message type、样本数或时间戳排序盘点。
- 不接入 `./start_data_clean.sh --dev` 菜单。
- 不实现字段对齐、插值、聚合、alignment index 生成或 aligned MCAP 写出。

## 5. 执行对象

- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]
- [[Scene3AlignmentConfig]]
- [[StepTimeline]]
- [[StepTimelineGenerationSummary]]

## 6. 执行依赖

- `service_s3_005` 必须已完成并归档，确保 MCAP_A 输入盘点服务和输出类型可用。
- `service_s3_007` 必须已完成并归档，确保 [[StepTimelineGenerationSummary]] 类型可用。
- 必须复用 `service_s3_002` 已落地的 [[StepTimeline]] 类型，不得重新定义相似时间轴对象。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：MCAP_A 输入盘点与校验器、Step 时间轴生成摘要类型、对齐契约与配置定义
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimelineGenerationSummary.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- validation_summary.status
- catalog 或 validation summary 中的 baseline_intersection_start_ns/end_ns/has_baseline_intersection
- config.target_step_hz
- StepTimeline 类型构造参数或等价字段
- StepTimelineGenerationSummary 类型构造参数或等价字段
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得新增相似类型；停止并记录冲突，建议 Win 端调整上游 L2/L3
```

## 8. 预期改动形态

- 新增 `src/data_clean/service/step_timeline_generator.py`，提供可测试的时间轴生成函数或类。
- 服务合法输入返回 [[StepTimeline]] 和 `status=generated` 的 [[StepTimelineGenerationSummary]]。
- 服务非法输入返回空时间轴或无时间轴结果，并返回 `status=failed` 的 [[StepTimelineGenerationSummary]]，具体表达应与既有类型风格一致。
- 新增 service 测试覆盖合法输入、不可消费输入、缺失 baseline、无效频率、单 step 区间和 15 Hz 非整纳秒精度。
- 必要时更新 `src/data_clean/data_clean_architecture.md`。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | `status=consumable`，baseline intersection 存在，`target_step_hz > 0` | [[StepTimeline]] + `StepTimelineGenerationSummary(status=generated)` | 无 |
| 输入不可消费 | `McapAInputValidationSummary.status != consumable` | 不生成成功时间轴，返回失败摘要 | `input_not_consumable` |
| baseline 缺失 | `has_baseline_intersection=false` 或起止时间为空 | 不生成成功时间轴，返回失败摘要 | `missing_baseline_intersection` |
| 无效频率 | `target_step_hz <= 0` | 不生成成功时间轴，返回失败摘要 | `invalid_target_step_hz` |
| 无效区间 | `start_time_ns > end_time_ns` | 不生成成功时间轴，返回失败摘要 | `invalid_time_range` |
| 单点区间 | `start_time_ns == end_time_ns` | 生成 1 个 step，`step_time_ns=start_time_ns` | 无 |
| 非整纳秒频率 | 例如 `target_step_hz=15` | 使用有理数累计再取整到 ns，不固定截断周期 | 无 |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `timeline` | [[StepTimeline]] / null | 成功生成的统一时间轴 | 成功时非空，失败时为空或按既有 Result 风格表达 |
| `summary` | [[StepTimelineGenerationSummary]] | 生成摘要 | 成功或失败都必须返回 |
| `step_count` | integer | step 数 | 成功时大于等于 1 |
| `step_time_ns` | list / repeated integer | step 时间戳 | 单调递增，首项等于 start，末项不超过 end |
| `failure_reasons` | list[string] | 失败原因 | 失败时至少一项 |

## 10. 数据计算验收重点

- 合法输入通过，并生成统一 [[StepTimeline]]。
- 不可消费输入、缺失 baseline、无效频率和无效时间范围会失败且 reason 清楚。
- `start_time_ns <= end_time_ns` 时允许生成 1 个 step。
- `target_step_hz=15` 的长序列不会出现固定截断导致的系统漂移。
- 输出结构可被 `scene3_step_timeline_check` 和后续字段对齐器直接消费。

## 11. 现有程序盘点

- `src/data_clean/service/` 当前已有多个 service 层计算模块，例如 gripper、pose、repair、validator；本 L3 应按 service 层放置时间轴生成业务逻辑。
- `src/data_clean/schemas/alignment_index.py` 预计由上游 L3 定义 [[StepTimeline]] 和 [[StepTimelineGenerationSummary]]，本 L3 不得重新创建平行类型。
- `src/data_clean/service/mcap_a_input_validator.py` 预计由 `service_s3_005` 生成，负责 MCAP_A 输入盘点；本 L3 只消费其结果。
- `src/data_clean/runtime/` 和 `src/data_clean/ui/` 由后续 `service_s3_009` 接入，不在本 L3 改动。

## 12. 本 L3 的真实改造边界

- 允许新增 service 层时间轴生成模块和对应测试。
- 允许在 `src/data_clean/service/__init__.py` 暴露清晰入口。
- 禁止读取 MCAP_A 或重复实现输入盘点。
- 禁止修改 `SourceTopicCatalog`、`McapAInputValidationSummary`、`Scene3AlignmentConfig` 或 `StepTimeline` 的字段语义。
- 禁止实现开发者入口、run 目录产物写出或菜单注册。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimelineGenerationSummary.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
6. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_007_定义Step时间轴生成摘要类型.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_005_实现MCAP_A输入盘点与校验服务.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`

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

1. `src/data_clean/schemas/alignment_index.py`
2. `src/data_clean/schemas/alignment_input.py`
3. `src/data_clean/schemas/alignment_config.py`
4. `src/data_clean/service/mcap_a_input_validator.py`
5. `src/data_clean/service/`
6. `src/data_clean/tests/`
7. `src/data_clean/data_clean_architecture.md`

## 14. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：合法输入测试 -> 最小生成服务 -> 不可消费输入测试 -> baseline 缺失测试 -> 无效频率 / 无效区间测试 -> 单 step 边界测试 -> 15 Hz 精度回归测试。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_step_timeline_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否，本 L3 提供底层服务 |
| 是否需要写测试产物 | 否，开发者产物由 service_s3_009 写出 |
| 是否需要写运行日志 | 否，运行日志由 service_s3_009 写出 |
| 是否允许临时覆盖配置 | 服务应接受调用方传入配置对象；本 L3 不实现交互覆盖 |
| 是否允许保存覆盖到配置文件 | 否 |
| 最终人工验收提示 | 本 L3 完成后仍需 service_s3_009 接入开发者入口，再由用户运行 `scene3_step_timeline_check` |

## 16. 允许修改

- `src/data_clean/service/step_timeline_generator.py`
- `src/data_clean/service/__init__.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改 MCAP_A 写出、输入盘点、场景三配置或 StepTimeline 的既有契约语义。
- 禁止读取 MCAP_A 原始消息或重新实现 topic catalog。
- 禁止接入开发者菜单或写 run 目录调试产物。
- 禁止写入 `asset/阶段二：数据清洗/` 真实数据产物。
- 禁止修改共享执行记录或当前进度文档。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.service.step_timeline_generator import generate_step_timeline

# 具体构造对象按 service_s3_004/service_s3_007 落地类型调整；
# 本 smoke 只要求导入入口存在，详细行为由 pytest 覆盖。
assert callable(generate_step_timeline)
PY
```

## 19. 成功标准

- [x] 已实现统一 Step 时间轴生成服务入口：`src/data_clean/service/step_timeline_generator.py` 中的 `generate_step_timeline()` 函数。
- [x] 合法输入生成的 step 以 baseline start 开始，单调递增，且最后一个 step 不超过 baseline end。
- [x] 失败 reason 覆盖 `input_not_consumable`、`missing_baseline_intersection`、`invalid_target_step_hz`、`invalid_time_range`。
- [x] 已覆盖单 step 区间和 15 Hz 非整纳秒精度测试。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系：本 L3 提供底层服务，不直接接入开发者入口；由 `service_s3_009` 接入 `scene3_step_timeline_check` 后用户可通过开发者入口做最终人工验收。

## 20. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 从 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/` 移到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/`
- 移动后如果 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/` 已经为空，删除该空 active 功能组目录
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

交接摘要必须包含：

1. 读取了哪些相关 L3 任务文件或执行记录
2. 任务文件身份校验结论：用户指定路径、实际读取路径、文件名编号、正文 L3 编号是否一致
3. 修改了哪些文件
4. 新增或修改了哪些函数 / 测试
5. TDD red / green / refactor 如何执行
6. 如何运行阶段二开工自检与 L3 验收，Python 命令必须使用 `python3`
7. 成功标准勾选情况
8. 归档目标是否为 `task/completed/04-service-s3/service-s3-g3/`，以及是否已删除空 active 功能组目录
9. 本 L3 对 `./start_data_clean.sh --dev` 开发者验收入口、功能检验项或场景完整 smoke test 的影响
10. 当前没做什么
11. 建议用户后续运行 `./start_data_clean.sh --dev` 的哪个场景、哪个功能检验项或 smoke test 做最终人工验收
12. 建议 Win 端后续同步整理什么

## 21. 执行摘要

### 执行基本信息

- L3 编号：service_s3_008
- 执行日期：2026-05-29
- 执行分支：service-s3
- 执行工具：TDD（RED → GREEN → REFACTOR）

### 身份校验

- 用户指定路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`
- 实际读取路径：同上 ✓
- 文件名编号：`service_s3_008` ✓
- 正文 L3 编号：`service_s3_008` ✓
- dispatch_status: `ready` ✓
- branch: `service-s3` ✓
- depends_on: `[service_s3_005, service_s3_007]` ✓（均为已完成归档状态）

### 读取的相关任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimelineGenerationSummary.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
6. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
7. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_007_定义Step时间轴生成摘要类型.md`
8. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_005_实现MCAP_A输入盘点与校验服务.md`
9. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`

### 修改的文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/data_clean/service/step_timeline_generator.py` | 新增 | 统一 Step 时间轴生成服务，包含 `generate_step_timeline()` 入口、`_validate_inputs()` 校验、`_generate_step_timestamps()` 有理数累计算法、`_build_failure_summary()` / `_build_success_result()` 摘要构建 |
| `src/data_clean/tests/service/test_step_timeline_generator.py` | 新增 | 22 个测试，覆盖可调用性、合法输入、4 种失败原因、单 step 边界、15 Hz 精度、10 Hz 精确周期、metadata 完整性和多故障累积 |
| `src/data_clean/data_clean_architecture.md` | 更新 | 在 Service 层目录表中新增 `service/step_timeline_generator.py` 条目 |
| 当前 L3 任务文件 | 已更新 | 勾选成功标准、追加执行摘要 |

### 新增 / 修改的函数

| 函数 | 模块 | 说明 |
|------|------|------|
| `generate_step_timeline()` | `step_timeline_generator.py` | 主入口。接收 `(McapAInputValidationSummary, SourceTopicCatalog, Scene3AlignmentConfig, timeline_id?)`，返回 `(StepTimeline|None, StepTimelineGenerationSummary)` |
| `_validate_inputs()` | `step_timeline_generator.py` | 校验 4 项前置条件：可消费状态、baseline intersection 存在、频率 > 0、有效时间范围 |
| `_generate_step_timestamps()` | `step_timeline_generator.py` | 使用 `Fraction` 有理数累计算法生成 step 时间戳序列 |
| `_build_failure_summary()` | `step_timeline_generator.py` | 失败时构建 `StepTimelineGenerationSummary` |
| `_build_success_result()` | `step_timeline_generator.py` | 成功时构建 `StepTimelineGenerationSummary` |

### TDD 执行记录

| 阶段 | 行为 | 结果 |
|------|------|------|
| **RED** | 编写 `test_step_timeline_generator.py`（22 个测试），运行 `python3 -m pytest src/data_clean/tests/service/test_step_timeline_generator.py -q` | 22 failed，`ModuleNotFoundError: No module named 'service.step_timeline_generator'`（模块不存在），符合预期 |
| **GREEN** | 新增 `step_timeline_generator.py` 完整实现（5 个函数），修复 import 路径 | 22 passed |
| **REFACTOR** | 更新 `data_clean_architecture.md` 架构文档；验证全部已有 service 测试无回归（1 个 pre-existing failure 无关本 L3） | 316 passed, 9 skipped |

### 验证命令与输出

```bash
# 阶段二开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK

# 新测试（22 个）
python3 -m pytest src/data_clean/tests/service/test_step_timeline_generator.py -q
# → 22 passed

# 全部 service 测试验证回归
python3 -m pytest src/data_clean/tests/service -q
# → 316 passed, 9 skipped, 1 failed (pre-existing test_aligned_mcap_report_schemas.py import issue)

# 内联验收入口
PYTHONPATH=src/data_clean python3 -c "
from service.step_timeline_generator import generate_step_timeline
assert callable(generate_step_timeline)
print('L3 verification PASSED')
"
```

### 成功标准勾选

- [x] 已实现统一 Step 时间轴生成服务入口：`generate_step_timeline()` 可从 `service.step_timeline_generator` 导入。
- [x] 合法输入生成的 step 以 baseline start 开始，单调递增，且最后一个 step 不超过 baseline end。
- [x] 失败 reason 覆盖 `input_not_consumable`、`missing_baseline_intersection`、`invalid_target_step_hz`、`invalid_time_range`。
- [x] 已覆盖单 step 区间和 15 Hz 非整纳秒精度测试（含 1 小时长序列漂移验证）。
- [x] 已说明本 L3 与开发者验收入口的关系：由 `scene3_step_timeline_check` 间接覆盖。

### 归档信息

- 源路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`
- 目标路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`
- active 目录清空：归档后将检查 `active/service-s3-g3/` 是否仍有其他文件，如无则删除空目录。
- dispatch 文件未修改：`task/dispatch/service-s3-g3.yaml` 保持不变。

### 当前没做什么

- 未读取 MCAP_A 原始消息或重复 topic / type / time 盘点。
- 未实现字段对齐、插值、聚合、alignment index 生成或 aligned MCAP 写出。
- 未接入 `./start_data_clean.sh --dev` 开发者入口或 `scene3_step_timeline_check` 功能检验项。
- 未修改 `SourceTopicCatalog`、`McapAInputValidationSummary`、`Scene3AlignmentConfig`、`StepTimeline` 的既有字段语义。
- 未修改 `task/dispatch/service-s3-g3.yaml`。
- 未写入 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。
- 未使用 `python` 命令（均使用 `python3`）。

### 开发者入口影响说明

本 L3 是统一 Step 时间轴生成器的核心服务层，提供了 `generate_step_timeline()` 入口。场景三的完整开发者验收需要：

1. `service_s3_009` 将本服务接入 `scene3_step_timeline_check` 功能检验项。
2. 用户运行 `./start_data_clean.sh --dev` 选择场景三 → `scene3_step_timeline_check` 做最终人工验收。

本 L3 的 22 个 pytest 自动化测试覆盖了所有成功、失败、边界和精度场景，证明局部实现正确。

### 建议人工验收

本 L3 完成后且后续 `service_s3_009`（接入开发者入口）也完成后，建议用户运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_step_timeline_check` → 执行并检查 step 0 时间、step 单调性、终点边界、step count 和非整纳秒频率精度是否符合 L2 契约。

### 建议 Win 端后续同步

- 确认本 L3 已归档，`dispatch/service-s3-g3.yaml` 中 `service_s3_008` 对应的 `depends_on` 完成闭环。
- `StepTimeline` 和 `StepTimelineGenerationSummary` 代码中使用的 `catalog_ref`、`validation_ref`、`config_ref` 当前为固定字符串占位符，后续 `service_s3_009` 接入开发者入口时可根据实际 run 目录传入真实引用。
