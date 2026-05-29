# L3 微元任务：实现触觉半 step 窗口聚合

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：多策略字段对齐器  
L3 编号：service_s3_013  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_013
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md
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
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
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

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`

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

- [ ] 半 step 窗口范围和边界规则已测试。
- [ ] 多样本聚合、空窗口和字段不可用已测试。
- [ ] 样本数和覆盖率统计已输出。
- [ ] 输出为 [[FieldAlignmentResult]]，未生成最终 sidecar。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。
