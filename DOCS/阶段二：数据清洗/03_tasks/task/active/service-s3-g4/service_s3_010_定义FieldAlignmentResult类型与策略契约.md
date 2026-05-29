# L3 微元任务：定义 FieldAlignmentResult 类型与策略契约

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：多策略字段对齐器  
L3 编号：service_s3_010  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_010
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md
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
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
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

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_007_定义Step时间轴生成摘要类型.md`

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

- [ ] 已定义 `FieldAlignmentResult` 或等价代码类型。
- [ ] 类型能表达 `message_ref`、`derived_value`、邻居、窗口、状态和 fallback reason。
- [ ] 已补充导入、实例化、序列化或 schema 校验测试。
- [ ] 未实现任何字段对齐算法。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。
