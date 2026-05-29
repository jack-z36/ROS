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

- [ ] 图像最近邻命中和超时行为已测试。
- [ ] 夹爪直接按 step 最近邻行为已测试。
- [ ] 缺 topic / 空 topic 降级行为已测试。
- [ ] 输出为 [[FieldAlignmentResult]]，未生成最终 sidecar。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。
