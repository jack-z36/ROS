# L3 微元任务：定义 MCAP_A 输入盘点与校验类型

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：MCAP_A 输入盘点与校验器  
L3 编号：service_s3_004  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_004_定义MCAP_A输入盘点与校验类型.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/MCAP_A输入盘点与校验器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_004
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_004_定义MCAP_A输入盘点与校验类型.md
  group: service-s3-g2
  branch: service-s3
  wave: 1
  parallel_group: service-s3-g2-p1
  depends_on: [service_s3_001]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_005]
  conflict_scope:
    files:
      - src/data_clean/schemas/alignment_input.py
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
定义 SourceTopicCatalog 与 McapAInputValidationSummary 的代码类型、状态取值和 JSON 序列化测试。
```

## 4. 本次不做

- 不读取 MCAP_A 文件。
- 不实现 summary strict 一致性校验。
- 不实现开发者菜单或 run 目录写出。
- 不生成 [[StepTimeline]] 或执行字段对齐。

## 5. 执行对象

- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]
- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- 场景二 [[McapA]] / [[McapAWriteSummary]] 引用字段

## 6. 执行依赖

- `service_s3_001` 必须已完成并归档，确保 [[Scene3AlignmentConfig]] 和 [[TargetFieldMapping]] 的代码类型可复用。
- 必须遵守 `src/data_clean` 的 `Schemas -> Config -> Repo -> Service -> Runtime -> UI` 单向依赖。
- 必须先盘点现有 `src/data_clean/schemas/` 的 dataclass / enum / Literal 风格。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景三对齐契约与配置定义、场景二 MCAP_A 生成器
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐契约与配置定义.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- Scene3AlignmentConfig.input_mcap_a
- Scene3AlignmentConfig.mcap_a_write_summary
- Scene3AlignmentConfig.baseline_image_topics
- Scene3AlignmentConfig.target_fields
- TargetFieldMapping.field_name/source_topic/message_type/modality/required_for_timeline
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得修改上游类型语义；停止并在执行摘要中说明冲突字段
```

## 8. 预期改动形态

- 新增 `src/data_clean/schemas/alignment_input.py`，定义 catalog / validation summary 相关 dataclass 与状态取值。
- 更新 `src/data_clean/schemas/__init__.py`，导出本 L3 新增类型。
- 新增 focused schema 测试，验证默认值、非法状态、JSON 序列化和 import。
- 必要时更新 `src/data_clean/data_clean_architecture.md` 的 schemas 目录说明。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `TopicTimestampOrder` | Literal / enum | `src/data_clean/schemas/alignment_input.py` | catalog、输入校验服务 |
| `FieldAvailability` | Literal / enum | `src/data_clean/schemas/alignment_input.py` | 字段映射检查、字段对齐器 |
| `InputValidationStatus` | Literal / enum | `src/data_clean/schemas/alignment_input.py` | validation summary、开发者入口 |
| `SummaryConsistencyStatus` | Literal / enum | `src/data_clean/schemas/alignment_input.py` | summary strict 校验 |
| `SourceTopicEntry` | dataclass / schema | `src/data_clean/schemas/alignment_input.py` | [[SourceTopicCatalog]] |
| `SourceFieldEntry` | dataclass / schema | `src/data_clean/schemas/alignment_input.py` | [[SourceTopicCatalog]] |
| `SourceTopicCatalog` | dataclass / schema | `src/data_clean/schemas/alignment_input.py` | service_s3_005、service_s3_006 |
| `McapAInputValidationSummary` | dataclass / schema | `src/data_clean/schemas/alignment_input.py` | service_s3_005、service_s3_006 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `timestamp_order` | enum string | topic 时间戳状态 | 无 | `ordered` / `duplicate_only` / `out_of_order` / `empty` |
| `availability` | enum string | 字段来源可用性 | 无 | `available` / `missing_topic` / `type_mismatch` / `timestamp_unusable` / `empty_topic` |
| `status` | enum string | MCAP_A 输入可消费结论 | 无 | `consumable` / `not_consumable` |
| `summary_consistency_status` | enum string | summary 一致性状态 | 无 | `consistent` / `missing` / `unreadable` / `status_failed` / `path_mismatch` / `policy_mismatch` |
| `hard_fail_reasons` | list[string] | 阻塞原因 | `[]` | `status=consumable` 时必须为空 |
| `warnings` | list[string] | 非阻塞问题 | `[]` | 不得改变 `status` |
| `baseline_intersection_start_ns/end_ns` | integer/null | 左右图像共同有效区间元数据 | `None` | 只表达交集，不生成 step |

## 10. 数据定义验收重点

- 能从 `data_clean.schemas` 或明确模块路径 import 新增类型。
- `SourceTopicCatalog` 能表达 topic 事实、字段映射结果和 `unmapped_topics`。
- `McapAInputValidationSummary` 在 `status=consumable` 且 hard fail 非空时会失败。
- JSON 序列化输出使用 snake_case 字段名，不嵌入完整 MCAP 消息。
- 类型定义只依赖 schemas 层，不反向依赖 repo/service/runtime/ui。

## 11. 现有程序盘点

- `src/data_clean/schemas/mcap_a_writer.py` 已定义 `MCAP_A_WriterConfig`、`MCAP_A_WritePlan`、`MCAP_A_OutputContract`、`MCAP_A_WriterResult`，可作为 dataclass 风格参考；它不表达场景三输入盘点结果。
- `src/data_clean/schemas/__init__.py` 是 schema 对外导出入口，新增类型需要按现有导出习惯处理。
- `src/data_clean/schemas/` 已有 runtime、repair、pose_filter、tactile_filter 等模块，本 L3 不应把场景三输入类型塞进不相关模块。
- `service_s3_001` 预期会新增 `Scene3AlignmentConfig` / `TargetFieldMapping`；本 L3 必须复用其类型或字段语义，不重新定义一套配置对象。

## 12. 本 L3 的真实改造边界

- 允许新增场景三输入盘点相关 schema 类型和测试。
- 允许为 JSON 序列化增加轻量 helper，但 helper 必须留在 schemas 层或测试中。
- 禁止读取 MCAP、解析 MCAP channel、校验 summary 文件或写 run 产物。
- 禁止修改场景二 MCAP_A writer 类型来适配本任务。
- 禁止实现开发者入口。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/MCAP_A输入盘点与校验器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md`
6. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
7. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_001_定义场景三配置与schema.md`
2. 如果该归档任务不存在，必须停止并汇报 `service_s3_001` 尚未完成，不得绕过依赖。

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

1. `src/data_clean/schemas/__init__.py`
2. `src/data_clean/schemas/mcap_a_writer.py`
3. `src/data_clean/schemas/alignment_config.py`
4. `src/data_clean/tests/`
5. `src/data_clean/data_clean_architecture.md`

## 14. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：import 失败测试 -> 最小类型实现 -> 约束失败测试 -> JSON 序列化测试 -> 导出和架构文档更新。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | 不直接接入开发者入口，但由 `scene3_mcap_a_input_check` 间接覆盖 |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 不涉及 |
| 是否允许保存覆盖到配置文件 | 否 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景三功能检验项或完整 smoke test |

## 16. 允许修改

- `src/data_clean/schemas/alignment_input.py`
- `src/data_clean/schemas/__init__.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改场景二 MCAP_A 写出器和契约。
- 禁止实现 MCAP 读取、输入盘点服务或开发者入口。
- 禁止写入真实数据产物到 `asset/阶段二：数据清洗/`。
- 禁止写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas import McapAInputValidationSummary, SourceTopicCatalog

summary = McapAInputValidationSummary(
    input_mcap_a="sample_mcap_a.mcap",
    mcap_a_write_summary="mcap_a_write_summary.json",
    config_ref="scene3_alignment",
    catalog_ref="source_topic_catalog.json",
    status="consumable",
    summary_consistency_status="consistent",
    baseline_topics_present=True,
    baseline_topics_ordered=True,
    has_baseline_intersection=True,
)
catalog = SourceTopicCatalog(
    source_mcap_a="sample_mcap_a.mcap",
    summary_ref="mcap_a_write_summary.json",
    config_ref="scene3_alignment",
)
assert summary.status == "consumable"
assert catalog.source_mcap_a.endswith(".mcap")
PY
```

## 19. 成功标准

- [x] 已新增 `SourceTopicCatalog`、`McapAInputValidationSummary` 及必要子类型（TopicTimestampOrder, FieldAvailability, InputValidationStatus, SummaryConsistencyStatus, SourceTopicEntry, SourceFieldEntry）。
- [x] 新增类型可 import、可实例化、可 JSON 序列化。
- [x] `status=consumable` 时 hard fail 非空会被拒绝。
- [x] 未引入 schemas 层到 repo/service/runtime/ui 的反向依赖（alignment_input.py 只依赖 enum 和 dataclass，零依赖）。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 20. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 完成并更新任务文件后，将当前 L3 移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/`。
- 移动后如果 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/` 已经为空，删除该空 active 功能组目录。
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

交接摘要必须包含模板要求的 12 项内容，尤其说明已读取 `service_s3_001` 的完成记录、TDD red / green / refactor、验收命令结果和建议用户后续运行 `scene3_mcap_a_input_check`。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_004_定义MCAP_A输入盘点与校验类型.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_004_定义MCAP_A输入盘点与校验类型.md
文件名编号：service_s3_004
正文 L3 编号：service_s3_004
dispatch.task_id：service_s3_004
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id=service_s3_004`、`task_file` 匹配、`group=service-s3-g2`、`branch=service-s3`、`dispatch_status=ready`、`depends_on=[service_s3_001]`（已归档于 `completed/04-service-s3/service-s3-g1/`），均允许执行；当前分支为 `service-s3`。
- 上游依赖：`depends_on=[service_s3_001]` 已完成并归档。
- 相关 L3 历史记录：已找到并读取 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_001_定义场景三配置与schema.md`，其执行模式、代码风格和 `Scene3AlignmentConfig`/`TargetFieldMapping` 类型作为本 L3 的复用基础。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/alignment_input.py`（新增）：定义 `TopicTimestampOrder`、`FieldAvailability`、`InputValidationStatus`、`SummaryConsistencyStatus` 枚举，`SourceTopicEntry`、`SourceFieldEntry` 子类型 dataclass，`SourceTopicCatalog` 和 `McapAInputValidationSummary` 主类型 dataclass，含 `__post_init__` 中的 consumable + hard_fail 约束校验。
- `src/data_clean/schemas/__init__.py`：导出场景三输入盘点公共类型（`FieldAvailability`、`InputValidationStatus`、`McapAInputValidationSummary`、`SourceFieldEntry`、`SourceTopicCatalog`、`SourceTopicEntry`、`SummaryConsistencyStatus`、`TopicTimestampOrder`）。
- `src/data_clean/tests/service/test_alignment_input_schemas.py`（新增）：25 个测试覆盖枚举值、dataclass 构造、默认值、约束校验（consumable + non-empty hard_fail → ValueError）和 JSON 序列化（通过 `dataclasses.asdict`）。
- `src/data_clean/data_clean_architecture.md`：在 schema 目录表中新增 `schemas/alignment_input.py` 条目。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

| 阶段 | 行为 | 结果 |
|------|------|------|
| Red | 编写 `test_alignment_input_schemas.py`（25 个测试），运行 `python3 -m pytest src/data_clean/tests/service/test_alignment_input_schemas.py -q` | 25 failed（类型不存在），符合预期 |
| Green | 新增 `schemas/alignment_input.py`（4 枚举 + 2 子类型 + 2 主类型 dataclass + validation），更新 `schemas/__init__.py` 导出 | 23 passed, 2 failed（JSON 序列化测试：`default=str` 无法处理嵌套 dataclass） |
| Green fix | 将 JSON 序列化测试从 `json.dumps(obj, default=str)` 改为 `json.dumps(asdict(obj))` | 25 passed |
| Refactor | 更新 `data_clean_architecture.md` 增加 `schemas/alignment_input.py` 条目 | 通过 |

### 验收命令结果

```bash
# 1. 本 L3 全部测试通过
cd /home/hit/ROS && PYTHONPATH=src python3 -m pytest src/data_clean/tests/service/test_alignment_input_schemas.py -q
# → 25 passed

# 2. 全量测试（排除已知 runtime 模块缺失问题）
cd /home/hit/ROS && PYTHONPATH=src python3 -m pytest src/data_clean/tests -q --tb=line --ignore=src/data_clean/tests/runtime
# → 341 passed, 9 skipped, 2 failed（2 个失败为 pre-existing contract test 问题，非本 L3 导致）

# 3. L3 验收内联测试
PYTHONPATH=src python3 - <<'PY'
from data_clean.schemas import McapAInputValidationSummary, SourceTopicCatalog

summary = McapAInputValidationSummary(
    input_mcap_a="sample_mcap_a.mcap",
    mcap_a_write_summary="mcap_a_write_summary.json",
    config_ref="scene3_alignment",
    catalog_ref="source_topic_catalog.json",
    status="consumable",
    summary_consistency_status="consistent",
    baseline_topics_present=True,
    baseline_topics_ordered=True,
    has_baseline_intersection=True,
)
catalog = SourceTopicCatalog(
    source_mcap_a="sample_mcap_a.mcap",
    summary_ref="mcap_a_write_summary.json",
    config_ref="scene3_alignment",
)
assert summary.status == "consumable"
assert catalog.source_mcap_a.endswith(".mcap")
print("Inline verification PASSED")
PY
# → Inline verification PASSED
```

### 成功标准处理

- [x] 已新增 `SourceTopicCatalog`、`McapAInputValidationSummary` 及必要子类型：完整实现 4 枚举（TopicTimestampOrder、FieldAvailability、InputValidationStatus、SummaryConsistencyStatus）、2 子类型（SourceTopicEntry、SourceFieldEntry）、2 主类型 dataclass（SourceTopicCatalog、McapAInputValidationSummary），共 8 个新类型。
- [x] 新增类型可 import、可实例化、可 JSON 序列化：两种 import 路径（`from schemas import ...` 和 `from data_clean.schemas import ...`）均可用，25 个测试全部通过。
- [x] `status=consumable` 时 hard fail 非空会被拒绝：`McapAInputValidationSummary.__post_init__` 中校验，测试 `test_consumable_with_nonempty_hard_fail_raises` 覆盖。
- [x] 未引入 schemas 层到 repo/service/runtime/ui 的反向依赖：`alignment_input.py` 只依赖 Python 标准库（`dataclasses`、`enum`），零内部依赖。
- [x] 已说明本 L3 与开发者验收入口的关系。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用或运行日志。
- 本 L3 类型定义间接支撑 `scene3_mcap_a_input_check` 功能检验项（在 `./start_data_clean.sh --dev` 下选择场景三）。
- 本 L3 的自动化验收只证明 MCAP_A 输入盘点与校验类型局部实现正确；场景最终验收需要场景三全部 L3 完成后运行完整 smoke test。

### 当前没做

- 未读取 MCAP_A 文件。
- 未实现 summary strict 一致性校验逻辑（只定义了 SummaryConsistencyStatus 枚举）。
- 未实现开发者菜单或 run 目录写出。
- 未生成 StepTimeline 或执行字段对齐。
- 未修改场景二 MCAP_A writer/contract 类型。
- 未写入 `asset/阶段二：数据清洗/` 真实数据产物。
- 未修改 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、共享 `当前进度.md` 或共享 `执行记录.md`。

### 遗留风险

- LSP diagnostics 无法执行（当前环境缺少 `basedpyright-langserver`），无法静态检查类型一致性。
- `test_common_frame_impact.py` 中 2 个预先存在的 contract 测试失败，与本 L3 无关。
- `PYTHONPATH=src` 需要在 repo 根目录设置，由 `start_data_clean.sh` 自动处理。

### 归档说明

- 本任务完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/`。
- 原 active 功能组目录 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成场景三全部 L3（`service_s3_001` ~ `service_s3_006`）后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_mcap_a_input_check` 功能检验项，检查 `source_topic_catalog.json` 和 `mcap_a_input_validation_summary.json` 的结构和字段是否符合 `SourceTopicCatalog`/`McapAInputValidationSummary` 契约。
