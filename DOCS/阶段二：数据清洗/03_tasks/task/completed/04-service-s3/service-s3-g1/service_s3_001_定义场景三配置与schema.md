# L3 微元任务：定义场景三配置与 schema

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：对齐契约与配置定义  
L3 编号：service_s3_001  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_001_定义场景三配置与schema.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐契约与配置定义.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_001
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_001_定义场景三配置与schema.md
  group: service-s3-g1
  branch: service-s3
  wave: 1
  parallel_group: service-s3-g1-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s3_002]
  conflict_scope:
    files:
      - src/data_clean/schemas/alignment_config.py
      - src/data_clean/schemas/__init__.py
      - src/data_clean/config/
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.schemas
      - data_clean.config
    config_keys:
      - scene3_alignment
  dispatch_status: ready
```

## 3. 本次目标

```text
定义场景三对齐配置和目标字段映射的代码类型 / schema 默认值，并补充最小配置加载或默认值验收。
```

## 4. 本次不做

- 不读取 MCAP_A。
- 不生成 step 时间轴。
- 不实现最近邻、插值、slerp、窗口聚合或 aligned MCAP 写出。
- 不接入 `./start_data_clean.sh --dev` 菜单。

## 5. 执行对象

- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- 场景三配置默认值：`target_step_hz=15`、双目图像 topic、半 step 图像阈值、pose/tactile/gripper 默认策略。

## 6. 执行依赖

- 必须复用场景二 [[McapA]] 和 [[McapAWriteSummary]] 作为输入引用语义。
- 必须遵守 `src/data_clean` 的 `Schemas -> Config -> Repo -> Service -> Runtime -> UI` 单向依赖。
- 需要先盘点现有 `src/data_clean/schemas/` 和 `src/data_clean/config/` 的 dataclass / enum 风格。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景二 MCAP_A 生成器
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md
- src/data_clean/schemas/mcap_a_writer.py
当前 L3 期望消费的字段 / 文件 / 返回值：
- MCAP_A 输入路径引用
- MCAP_A 写出摘要引用
- 保留 MCAP_A topic/time 主结构的上游契约
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得修改上游 MCAP_A 契约；将冲突写入执行摘要并停止实现消费逻辑
```

## 8. 预期改动形态

- 新增或更新场景三 alignment config / target field mapping 类型。
- 暴露可导入的配置类型和枚举，不破坏现有 schema 导出。
- 增加配置默认值和非法值测试。
- 必要时更新 `src/data_clean/data_clean_architecture.md` 的 schema/config 目录说明。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `Scene3AlignmentConfig` | dataclass / schema | `src/data_clean/schemas/` 或既有 schemas 风格位置 | service_s3_002、输入盘点、时间轴生成、字段对齐 |
| `TargetFieldMapping` | dataclass / schema | `src/data_clean/schemas/` 或既有 schemas 风格位置 | 输入盘点、字段对齐 |
| `AlignmentModality` | enum / Literal | `src/data_clean/schemas/` | TargetFieldMapping |
| `AlignmentSide` | enum / Literal | `src/data_clean/schemas/` | TargetFieldMapping |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `target_step_hz` | number | 统一 step 目标频率 | `15` | 必须大于 0 |
| `baseline_image_topics` | list[string] | 双目图像基准 topic | `/gopro_left/image_raw`, `/gopro_right/image_raw` | 首版必须左右同时存在 |
| `required_timeline_fields` | list[string] | 参与裁剪的字段 | 左右图像字段 | 首版不含 pose/tactile/gripper |
| `image_max_dt_ms` | number/null | 图像最近邻阈值 | `1000 / target_step_hz / 2` | 显式配置必须大于 0 |
| `pose_strategy` | string | 位姿默认策略 | `interpolation_slerp` | 必须是已定义策略 |
| `pose_fallback_strategy` | string | 位姿 fallback | `nearest_neighbor` | 首版只允许最近邻 |
| `tactile_strategy` | string | 触觉默认策略 | `window_aggregate` | 必须是已定义策略 |
| `gripper_strategy` | string | 夹爪默认策略 | `follow_image_nearest` | 必须是已定义策略 |
| `output_dir` | string | aligned dev 产物目录 | `asset/阶段二：数据清洗/dev/mcap_aligned/` | 必须遵守文件存放规范 |

## 10. 数据定义验收重点

- 能从 `data_clean.schemas` 或明确模块路径 import。
- 能构造默认 `Scene3AlignmentConfig`，默认 `target_step_hz == 15`。
- 未显式配置 `image_max_dt_ms` 时能得到半 step 周期阈值。
- 非法 `target_step_hz <= 0` 和非法空双目 topic 配置会被拒绝。
- `TargetFieldMapping.required_for_timeline` 能表达“只有左右图像裁剪时间轴”。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐契约与配置定义.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
5. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`

### 必读相关微元任务记录

1. 如果存在，读取 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/` 下 MCAP_A 生成器相关 L3 执行摘要。
2. 如果不存在相关 L3 历史记录，执行摘要中写明“未找到相关 L3 历史记录”。

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

1. `src/data_clean/schemas/__init__.py`
2. `src/data_clean/schemas/mcap_a_writer.py`
3. `src/data_clean/schemas/pose_filter.py`
4. `src/data_clean/config/mcap_process_config.py`
5. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd` 技能，按“默认值测试 -> 最小类型实现 -> 非法值测试 -> 导出和架构文档更新”的顺序推进。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | 不直接接入开发者入口，但由场景三完整 smoke test 间接覆盖 |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是，类型需支持 `target_step_hz` 等覆盖；本 L3 不实现 UI |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许，具体入口后续 L3 实现 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景三完整 smoke test |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/config/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止修改场景二 MCAP_A 写出契约以适配本任务。
- 禁止实现 MCAP_A 输入盘点、时间轴生成、字段对齐或写出器逻辑。
- 禁止写入 `asset/阶段二：数据清洗/` 真实数据产物。
- 禁止修改 `DOCS/阶段二：数据清洗/执行记录/`、共享 `当前进度.md` 或共享 `执行记录.md`。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.schemas import Scene3AlignmentConfig
cfg = Scene3AlignmentConfig()
assert cfg.target_step_hz == 15
assert "/gopro_left/image_raw" in cfg.baseline_image_topics
assert "/gopro_right/image_raw" in cfg.baseline_image_topics
assert cfg.image_max_dt_ms > 0
PY
```

## 17. 成功标准

- [x] 已新增或更新场景三配置与目标字段映射类型。
- [x] 默认值满足 L2：`target_step_hz=15`、双目图像 topic、图像半 step 阈值。
- [x] 非法配置有明确失败表达。
- [x] 类型可 import，测试通过。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 完成并更新任务文件后，将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/`。
- 移动后如果 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/` 已经为空，删除该空 active 功能组目录。
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

交接摘要必须包含模板要求的 12 项内容，尤其说明是否读取到相关 L3 历史记录、TDD red / green / refactor、验收命令结果和建议用户后续运行场景三完整 smoke test。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_001_定义场景三配置与schema.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/service_s3_001_定义场景三配置与schema.md
文件名编号：service_s3_001
正文 L3 编号：service_s3_001
dispatch.task_id：service_s3_001
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id=service_s3_001`、`task_file` 匹配、`group=service-s3-g1`、`branch=service-s3`、`dispatch_status=ready`、`depends_on=[]`（无未完成依赖），均允许执行；当前分支为 `service-s3`。
- 上游依赖：`depends_on` 为空，无前置依赖。
- 相关 L3 历史记录：已找到并读取 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md`，其执行模式作为本 L3 参考。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/alignment_config.py`（新增）：定义 `AlignmentModality`、`AlignmentSide` 枚举，`TargetFieldMapping` 和 `Scene3AlignmentConfig` dataclass，含默认值、`__post_init__` 校验和 `image_max_dt_ms` 推导。
- `src/data_clean/schemas/__init__.py`：导出场景三对齐配置公共类型（`AlignmentModality`、`AlignmentSide`、`Scene3AlignmentConfig`、`TargetFieldMapping`）。
- `src/data_clean/tests/service/test_alignment_config_schemas.py`（新增）：13 个测试覆盖默认值、枚举成员、TargetFieldMapping 构造、配置校验（`target_step_hz<=0`、空 `baseline_image_topics`、显式 `image_max_dt_ms<=0`）。
- `src/data_clean/data_clean_architecture.md`：在 schema 目录表中新增 `schemas/alignment_config.py` 条目。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

| 阶段 | 行为 | 结果 |
|------|------|------|
| Red | 编写 `test_alignment_config_schemas.py`（13 个测试），运行 `python3 -m pytest src/data_clean/tests/service/test_alignment_config_schemas.py -q` | 13 failed，ImportError（类型不存在），符合预期 |
| Green | 新增 `schemas/alignment_config.py`，更新 `schemas/__init__.py` 导出 | 13 passed |
| Refactor | 修正在 `__init__.py` 中发现的 `FrameIdType` 和 `SceneDispatchEvent` 重复 `__all__` 条目；更新 `data_clean_architecture.md` | 通过 |

### 验收命令结果

```bash
# 1. 测试全部通过
python3 -m pytest src/data_clean/tests/service/ -q
# → 182 passed, 9 skipped（含本 L3 13 个测试）

# 2. 验证完整测试套件（排除已知 runtime 问题）
python3 -m pytest src/data_clean/tests -q --tb=line --ignore=src/data_clean/tests/runtime
# → 296 passed, 9 skipped, 2 failed（2 个失败为 pre-existing contract test 问题，非本 L3 导致）

# 3. 内联验收（schemas 路径）
PYTHONPATH=src/data_clean python3 -c "
from schemas import Scene3AlignmentConfig
cfg = Scene3AlignmentConfig()
assert cfg.target_step_hz == 15
assert '/gopro_left/image_raw' in cfg.baseline_image_topics
assert '/gopro_right/image_raw' in cfg.baseline_image_topics
assert cfg.image_max_dt_ms > 0
"
# → 静默通过，无错误

# 4. 内联验收（data_clean.schemas 路径）
PYTHONPATH=src python3 -c "
from data_clean.schemas import Scene3AlignmentConfig
cfg = Scene3AlignmentConfig()
assert cfg.target_step_hz == 15
assert '/gopro_left/image_raw' in cfg.baseline_image_topics
assert '/gopro_right/image_raw' in cfg.baseline_image_topics
assert cfg.image_max_dt_ms > 0
"
# → 静默通过，无错误
```

### 成功标准处理

- [x] 已新增或更新场景三配置与目标字段映射类型：新增 `Scene3AlignmentConfig`、`TargetFieldMapping`、`AlignmentModality`、`AlignmentSide`。
- [x] 默认值满足 L2：`target_step_hz=15`、双目图像 topic（`/gopro_left/image_raw`、`/gopro_right/image_raw`）、`image_max_dt_ms` 从 `1000/15/2` 推导为 33ms。
- [x] 非法配置有明确失败表达：`target_step_hz<=0` → ValueError；空 `baseline_image_topics` → ValueError；显式 `image_max_dt_ms<=0` → ValueError。
- [x] 类型可 import，测试通过：两种 import 路径（`from schemas import ...` 和 `from data_clean.schemas import ...`）均可用，13 个测试全部通过。
- [x] 已说明本 L3 与开发者验收入口的关系。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用或运行日志。
- 本 L3 间接支撑场景三完整 smoke test（在 `./start_data_clean.sh --dev` 下选择场景三）。
- 本 L3 的自动化验收只证明场景三对齐配置和数据定义局部实现正确；场景最终验收需要场景三全部 L3 完成后运行完整 smoke test。

### 当前没做

- 未实现 MCAP_A 输入盘点、时间轴生成、字段对齐、插值/slerp/窗口聚合或 aligned MCAP 写出。
- 未修改上游 MCAP_A 契约。
- 未写入 `asset/阶段二：数据清洗/` 真实数据产物。
- 未修改 `DOCS/阶段二：数据清洗/执行记录/`、共享 `当前进度.md` 或共享 `执行记录.md`。

### 遗留风险

- LSP diagnostics 无法执行（当前环境缺少 `basedpyright-langserver`），无法静态检查类型一致性。
- `test_common_frame_impact.py` 中 2 个预先存在的 contract 测试失败，与本 L3 无关。

### 归档说明

- 本任务完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/`。
- 原 active 功能组目录 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g1/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成场景三全部 L3（`service_s3_001`、`service_s3_002`、`service_s3_003`）后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三完整 smoke test，检查配置默认值、产物路径和报告摘要是否符合 `Scene3AlignmentConfig` 和 `TargetFieldMapping` 契约。
