# L3 微元任务：定义 Step 时间轴生成摘要类型

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：统一 Step 时间轴生成器  
L3 编号：service_s3_007  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_007_定义Step时间轴生成摘要类型.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_007
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_007_定义Step时间轴生成摘要类型.md
  group: service-s3-g3
  branch: service-s3
  wave: 1
  parallel_group: service-s3-g3-p1
  depends_on: [service_s3_002, service_s3_004]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_008]
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
定义 StepTimelineGenerationSummary 的代码类型 / schema，并补充 JSON 序列化与非法状态测试。
```

## 4. 本次不做

- 不实现 Step 时间轴生成算法。
- 不读取 MCAP_A、catalog 或 validation summary 文件。
- 不接入 `./start_data_clean.sh --dev` 菜单。
- 不修改场景三配置、输入盘点服务或字段对齐逻辑。

## 5. 执行对象

- [[StepTimelineGenerationSummary]]
- [[StepTimeline]]
- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]
- [[Scene3AlignmentConfig]]

## 6. 执行依赖

- `service_s3_002` 必须已完成并归档，确保 [[StepTimeline]] 类型已落地。
- `service_s3_004` 必须已完成并归档，确保 [[SourceTopicCatalog]] 与 [[McapAInputValidationSummary]] 类型已落地。
- 必须沿用已有 `src/data_clean/schemas/` 的 dataclass / enum / serialization 风格。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：对齐契约与配置定义、MCAP_A 输入盘点与校验器
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimelineGenerationSummary.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- StepTimeline 引用或 timeline_id
- SourceTopicCatalog 引用
- McapAInputValidationSummary 引用
- Scene3AlignmentConfig 引用
- status、failure_reasons、target_step_hz、baseline intersection、step_count、first/last step 时间
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得修改上游类型语义；停止并在执行摘要中记录需要 Win 端同步的接口缺口
```

## 8. 预期改动形态

- 在既有场景三 schema 模块中新增 `StepTimelineGenerationSummary` 类型和必要状态 / reason 常量。
- 通过 `data_clean.schemas` 或明确模块路径导出该类型。
- 新增或更新测试，覆盖成功摘要、失败摘要、JSON 序列化和非法状态 / reason 处理。
- 必要时更新 `src/data_clean/data_clean_architecture.md` 的 schemas 目录说明。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `StepTimelineGenerationSummary` | dataclass / schema | 复用 `src/data_clean/schemas/alignment_index.py` 或既有 StepTimeline 所在模块 | service_s3_008、service_s3_009、report 生成器 |
| `StepTimelineGenerationStatus` | enum / Literal | 同上 | summary status 校验 |
| `StepTimelineGenerationFailureReason` | enum / Literal | 同上 | 失败摘要、测试和开发者入口 |
| `TimestampRoundingPolicy` | enum / Literal | 同上 | 记录非整纳秒频率处理策略 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `status` | string | `generated` / `failed` | 无 | 只允许固定取值 |
| `failure_reasons` | list[string] | 失败原因 | `[]` | `failed` 时至少一项，`generated` 时为空 |
| `source_topic_catalog_ref` | string | catalog 引用 | 无 | 必填 |
| `input_validation_summary_ref` | string | validation summary 引用 | 无 | 必填 |
| `config_ref` | string | 配置引用 | 无 | 必填 |
| `timeline_ref` | string/null | 成功时间轴引用 | `null` | 成功时非空，失败时为空 |
| `target_step_hz` | number | 实际目标频率 | 无 | 必须大于 0，除非表达无效输入失败时按实现约定保留原值 |
| `baseline_intersection_start_ns` | integer/null | 共同有效区间起点 | `null` | 成功时非空 |
| `baseline_intersection_end_ns` | integer/null | 共同有效区间终点 | `null` | 成功时非空 |
| `timestamp_rounding_policy` | string | 纳秒取整策略 | `rational_accumulation_round_to_ns` | 固定取值 |
| `include_start` | bool | 是否包含起点 | `true` | 首版固定 true |
| `force_include_end` | bool | 是否强制包含终点 | `false` | 首版固定 false |
| `step_count` | integer | step 数 | `0` | 成功时大于等于 1 |
| `first_step_time_ns` | integer/null | 第一条 step 时间 | `null` | 成功时等于起点 |
| `last_step_time_ns` | integer/null | 最后一条 step 时间 | `null` | 成功时不超过终点 |

## 10. 数据定义验收重点

- 能从 `data_clean.schemas` 或明确模块路径 import。
- 成功摘要能表达 `status=generated`、空 `failure_reasons`、非空 `timeline_ref` 和 `step_count >= 1`。
- 失败摘要能表达 `status=failed`、非空 `failure_reasons`、空 `timeline_ref` 和 `step_count=0`。
- reason 至少覆盖 `input_not_consumable`、`missing_baseline_intersection`、`invalid_target_step_hz`、`invalid_time_range`。
- JSON 序列化字段名使用 snake_case，并与 L2 数据定义一致。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimelineGenerationSummary.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
6. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_004_定义MCAP_A输入盘点与校验类型.md`
3. 如果上述任务尚未归档，必须停止执行本 L3，不得改读 active 版本后继续实现。

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
2. `src/data_clean/schemas/alignment_input.py`
3. `src/data_clean/schemas/alignment_config.py`
4. `src/data_clean/schemas/__init__.py`
5. `src/data_clean/tests/`
6. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：失败摘要测试 -> 最小类型实现 -> 成功摘要测试 -> JSON 序列化测试 -> 非法状态 / reason 测试 -> 导出和架构文档更新。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | 不直接接入开发者入口，但由 `scene3_step_timeline_check` 间接覆盖 |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否，本 L3 只定义类型 |
| 是否允许保存覆盖到配置文件 | 默认否；本 L3 不涉及 |
| 最终人工验收提示 | 本 L3 完成后仍需 service_s3_009 接入开发者入口，再由用户运行 `scene3_step_timeline_check` |

## 14. 允许修改

- `src/data_clean/schemas/alignment_index.py`
- `src/data_clean/schemas/__init__.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止修改 [[StepTimeline]]、[[SourceTopicCatalog]]、[[McapAInputValidationSummary]] 的既有字段语义。
- 禁止实现时间轴生成服务或开发者入口。
- 禁止写入 `asset/阶段二：数据清洗/` 真实数据产物。
- 禁止修改 `DOCS/阶段二：数据清洗/执行记录/`、共享 `当前进度.md` 或共享 `执行记录.md`。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas import StepTimelineGenerationSummary

ok = StepTimelineGenerationSummary(
    status="generated",
    failure_reasons=[],
    source_topic_catalog_ref="source_topic_catalog.json",
    input_validation_summary_ref="mcap_a_input_validation_summary.json",
    config_ref="scene3_alignment_config.yaml",
    timeline_ref="step_timeline.json",
    target_step_hz=15,
    baseline_intersection_start_ns=100,
    baseline_intersection_end_ns=200,
    step_count=1,
    first_step_time_ns=100,
    last_step_time_ns=100,
)
assert ok.status == "generated"
PY
```

## 17. 成功标准

- [ ] 已新增或更新 `StepTimelineGenerationSummary` 代码类型 / schema。
- [ ] 成功和失败摘要的合法性规则符合 L2 数据定义。
- [ ] JSON 序列化和 `data_clean.schemas` 导出可用。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 从 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/` 移到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/`
- 移动后如果 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/` 已经为空，删除该空 active 功能组目录
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

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
