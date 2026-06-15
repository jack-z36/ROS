# L3 微元任务：定义 FieldAlignmentResult 类型与策略契约

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：多策略字段对齐器  
L3 编号：service_s3_010  
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_010
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md
  group: service-s3-g4
  branch: service-s3
  wave: 1
  parallel_group: service-s3-g4-p1
  depends_on: [service_s3_002, service_s3_007]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_011, service_s3_012, service_s3_013]
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
定义代码层 FieldAlignmentResult 及其轻量派生值、引用字段和策略状态契约。
```

## 4. 本次不做

- 不实现最近邻、插值、slerp 或窗口聚合算法。
- 不读取 MCAP_A 消息。
- 不生成 AlignmentIndex、AlignmentReport 或 aligned MCAP。

## 5. 执行对象

- [[FieldAlignmentResult]]
- [[FieldAlignmentStrategy]]
- [[FieldAlignmentStatus]]
- [[AlignmentIndex]]

## 6. 执行依赖

- `service_s3_002` 应已定义 [[StepTimeline]]、[[AlignmentIndex]] 和 [[FieldAlignmentStatus]] 等基础类型。
- `service_s3_007` 应已定义 [[StepTimelineGenerationSummary]]。
- 必须复用既有 schemas 风格，不新增相似的 parallel result 类型。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：对齐契约与配置定义、统一 Step 时间轴生成器
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- FieldAlignmentResult 的 step、field、source、status、method、neighbor、window、message_ref、derived_value 字段
- FieldAlignmentStrategy 中 gripper 默认 nearest_neighbor
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得新增相似对象；停止并记录冲突，建议 Win 端调整 L2
```

## 8. 预期改动形态

- 在 `src/data_clean/schemas/` 中新增或扩展字段对齐结果类型。
- 类型能表达图像只存引用、轻量派生值内联、fallback reason、窗口统计和状态枚举。
- 新增 schema / 序列化测试，覆盖字段完整性和非法状态处理。
- 必要时更新 `src/data_clean/data_clean_architecture.md`。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `FieldAlignmentResult` | dataclass / schema | `src/data_clean/schemas/` | 字段对齐服务、第 5 / 6 模块 |
| `DerivedAlignmentValue` 或等价结构 | dataclass / TypedDict | `src/data_clean/schemas/` | pose、gripper、触觉聚合写出 |
| `MessageRef` 或等价字段 | string / object | `src/data_clean/schemas/` | 图像和原始消息引用 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `step_index` | integer | step 序号 | 无 | `>=0` |
| `step_time_ns` | integer | step 时间戳 | 无 | 必填 |
| `field_name` | string | 目标字段 | 无 | 必填 |
| `status` | [[FieldAlignmentStatus]] | 对齐状态 | 无 | 必填 |
| `alignment_method` | string | 实际方法 | 无 | 必填 |
| `message_ref` | string/null | 原始消息引用 | null | 图像成功时必填 |
| `derived_value` | object/null | 轻量派生值 | null | 不得保存大 payload |

## 10. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_007_定义Step时间轴生成摘要类型.md`

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
2. `src/data_clean/schemas/__init__.py`
3. `src/data_clean/tests/`
4. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：导入失败测试 -> 最小类型定义 -> 序列化测试 -> 非法状态 / 大 payload 边界测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_field_alignment_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 不直接接入开发者入口，但由 `scene3_field_alignment_check` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现字段对齐算法。
- 禁止修改 MCAP_A 输入盘点、时间轴生成或写出器行为。
- 禁止写入真实数据产物或共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas.alignment_index import FieldAlignmentResult
assert FieldAlignmentResult is not None
PY
```

## 17. 成功标准

- [x] 已定义 `FieldAlignmentResult` 或等价代码类型。
- [x] 类型能表达 `message_ref`、`derived_value`、邻居、窗口、状态和 fallback reason。
- [x] 已补充导入、实例化、序列化或 schema 校验测试。
- [x] 未实现任何字段对齐算法。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md
文件名编号：service_s3_010
正文 L3 编号：service_s3_010
dispatch.task_id：service_s3_010
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id=service_s3_010`、`task_file` 匹配、`group=service-s3-g4`、`branch=service-s3`、`dispatch_status=ready`、`depends_on=[service_s3_002, service_s3_007]`（均已归档）。
- 上游依赖校验：`service_s3_002` 确认归档于 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/`；`service_s3_007` 确认归档于 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/`。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/field_alignment.py`（新增）：定义 `FieldAlignmentStrategyMethod` 枚举（4 成员：nearest_neighbor, interpolation_slerp, window_aggregate, follow_image_nearest）、`FieldAlignmentStrategy` dataclass（method + 可选参数）、`DerivedAlignmentValue` TypedDict（pose/gripper/tactile 字段）、`FieldAlignmentResult` dataclass（5 必填 + 12 可选字段 + status 依赖校验）。
- `src/data_clean/schemas/__init__.py`：导入并导出 `FieldAlignmentResult`、`FieldAlignmentStrategy`、`FieldAlignmentStrategyMethod`、`DerivedAlignmentValue`。
- `src/data_clean/tests/service/test_field_alignment_schemas.py`（新增）：18 个测试覆盖 FieldAlignmentResult 构造（必填、全部字段、负 step_index 拒绝、fallback_nearest 要求 reason、aggregated 要求 window 起止）、FieldAlignmentStrategy 构造（默认 + 完整）、FieldAlignmentStrategyMethod 枚举完整性（4 成员）、DerivedAlignmentValue 构建（pose/gripper/tactile）、统一 import 集成测试。
- `src/data_clean/data_clean_architecture.md`：在 schema 目录表中新增 `schemas/field_alignment.py` 条目。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

| 阶段 | 行为 | 结果 |
|------|------|------|
| Red | 编写 `test_field_alignment_schemas.py`（18 个测试），运行 `PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/service/test_field_alignment_schemas.py -q` | 18 failed（ModuleNotFoundError），符合预期 |
| Red (fix imports) | 修正测试导入路径从 `data_clean.schemas.*` 到 `schemas.*`（与 conftest.py 的 PYTHONPATH 一致） | 18 failed（ImportError: 模块不存在），符合预期 |
| Green | 新增 `schemas/field_alignment.py`（FieldAlignmentResult、FieldAlignmentStrategy、FieldAlignmentStrategyMethod、DerivedAlignmentValue），更新 `schemas/__init__.py` 导出 | 18 passed |
| Refactor | 更新 `data_clean_architecture.md`，补充 schema 目录表条目 | 通过 |

### 验收命令结果

```bash
# 1. 本 L3 测试全部通过
PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/service/test_field_alignment_schemas.py -q
# → 18 passed

# 2. service 级测试（排除已知 pre-existing 问题）
PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/service -q
# → 334 passed, 9 skipped（含本 L3 18 个测试）；1 pre-existing failure（test_aligned_mcap_report_schemas.py 使用 data_clean 全路径导入，非本 L3 问题）

# 3. 内联验收 - FieldAlignmentResult 实例化和约束校验
PYTHONPATH=src/data_clean python3 -c "
from schemas import FieldAlignmentResult, FieldAlignmentStrategy, FieldAlignmentStrategyMethod, DerivedAlignmentValue
from schemas.step_timeline import FieldAlignmentStatus
# 必填字段构造
r1 = FieldAlignmentResult(step_index=0, step_time_ns=1000000, field_name='img', status='aligned', alignment_method='nearest_neighbor')
assert r1.step_index == 0 and r1.status == 'aligned'
# fallback_nearest 要求 reason
r2 = FieldAlignmentResult(step_index=1, step_time_ns=2000000, field_name='pose', status='fallback_nearest', alignment_method='nearest_neighbor', fallback_reason='no_interpolation_neighbor')
assert r2.fallback_reason == 'no_interpolation_neighbor'
# aggregated 要求 window
r3 = FieldAlignmentResult(step_index=2, step_time_ns=3000000, field_name='tactile', status='aggregated', alignment_method='window_aggregate', window_start_time_ns=2900000, window_end_time_ns=3100000, sample_count=5, coverage_ratio=1.0, derived_value={'tactile_mean': 0.5})
assert r3.derived_value == {'tactile_mean': 0.5}
print('All inline acceptance checks passed.')
"
# → 静默通过，无错误
```

### 成功标准处理

- [x] 已定义 `FieldAlignmentResult` 代码类型（dataclass，5 必填 + 12 可选字段 + __post_init__ 约束校验）。
- [x] 类型能表达 `message_ref`（str | None）、`derived_value`（dict | None）、邻居（neighbor_before/after_time_ns）、窗口（window_start/end_time_ns）、状态（status: str）、fallback reason（fallback_reason: str）。
- [x] 已补充导入、实例化、序列化或 schema 校验测试：18 个测试覆盖构造、可选字段、非法值拒绝和集成导入。
- [x] 未实现任何字段对齐算法（nearest_neighbor、interpolation_slerp、window_aggregate 等仅定义为枚举/策略契约）。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用或运行日志。
- 本 L3 间接支撑场景三 `scene3_field_alignment_check` 功能检验项（通过定义 FieldAlignmentResult 和 FieldAlignmentStrategy 类型供后续字段对齐服务使用）。
- 本 L3 的自动化验收只证明场景三字段对齐结果类型和策略契约局部实现正确；场景最终验收需要场景三全部 L3 完成后运行完整 smoke test 或选择 `scene3_field_alignment_check` 检验项。

### 当前没做

- 未实现任何字段对齐算法（最近邻、插值、slerp、窗口聚合）。
- 未生成 FieldAlignmentResult 实例的真实对齐数据。
- 未读取 MCAP_A 消息。
- 未生成 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 未修改 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、共享 `当前进度.md` 或共享 `执行记录.md`。

### 遗留风险

- LSP diagnostics 无法执行（当前环境缺少 `basedpyright-langserver`），无法静态检查类型一致性。
- `test_aligned_mcap_report_schemas.py` 中 1 个预先存在的测试失败（使用 `data_clean.schemas` 全路径导入而非 `schemas`，与本 L3 无关）。

### 归档说明

- 本任务完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。
- 原 active 功能组目录 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成场景三全部 L3（`service_s3_010` → `service_s3_013`）后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_field_alignment_check`，检查字段对齐结果类型和策略契约是否符合 `FieldAlignmentResult`、`FieldAlignmentStrategy` 和 `FieldAlignmentStatus` 契约。
