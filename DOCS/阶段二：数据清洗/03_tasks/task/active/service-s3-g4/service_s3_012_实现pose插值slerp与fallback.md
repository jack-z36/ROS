# L3 微元任务：实现 pose 插值、slerp 与 fallback

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：多策略字段对齐器  
L3 编号：service_s3_012  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_012_实现pose插值slerp与fallback.md`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_012
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_012_实现pose插值slerp与fallback.md
  group: service-s3-g4
  branch: service-s3
  wave: 2
  parallel_group: service-s3-g4-p2
  depends_on: [service_s3_008, service_s3_010]
  must_run_after: []
  can_run_parallel_with: [service_s3_011, service_s3_013]
  blocks: [service_s3_014]
  conflict_scope:
    files:
      - src/data_clean/service/pose_field_aligner.py
      - src/data_clean/service/__init__.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.service.pose
    config_keys:
      - scene3_alignment.pose_strategy
  dispatch_status: ready
```

## 3. 本次目标

```text
实现 pose 字段 position 线性插值、orientation 四元数 slerp，以及插值不可用时的最近邻 fallback。
```

## 4. 本次不做

- 不实现图像、夹爪或触觉策略。
- 不写 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 不接入开发者菜单。

## 5. 执行对象

- pose modality source messages
- [[StepTimeline]]
- [[FieldAlignmentResult]]
- [[FieldAlignmentStatus]]

## 6. 执行依赖

- `service_s3_010` 必须已完成并归档。
- 必须复用已有 pose / quaternion 工具；如无可用工具，只新增本任务需要的最小数学函数和测试。
- 不能改变场景一 / 场景二 pose 数据契约。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：FieldAlignmentResult 类型、统一 Step 时间轴、场景一/二 pose topic 契约
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- pose source_time_ns、position、orientation quaternion
- config pose_strategy / pose_fallback_strategy / max_dt_ms
- FieldAlignmentResult.derived_value / fallback_reason
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得重定义 pose 类型；停止并记录冲突
```

## 8. 预期改动形态

- 新增或扩展 pose 字段对齐服务。
- 正常插值输出 `status=interpolated` 和轻量 pose `derived_value`。
- 邻居不足或超阈值时输出 `status=fallback_nearest` 和 `fallback_reason`。
- 新增 numeric / fallback 测试。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 前后邻居有效 | position 线性插值，orientation slerp | `status=interpolated` | 无 |
| 缺前邻居或后邻居 | fallback 到最近邻 | `status=fallback_nearest` | `missing_neighbor` |
| 邻居超阈值 | fallback 到最近邻 | `status=fallback_nearest` | `neighbor_timeout` |
| 无 pose 样本 | 输出缺失 | `status=missing_time` | `missing_time` |
| quaternion 非法 | 标记无效输入 | `status=invalid_input` | `invalid_quaternion` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `derived_value.position` | object/list | 插值或最近邻位置 | 成功时非空 |
| `derived_value.orientation` | object/list | slerp 或最近邻四元数 | 成功时归一化或符合既有 pose 工具约束 |
| `neighbor_before_time_ns` | integer/null | 插值前邻居 | 插值时必填 |
| `neighbor_after_time_ns` | integer/null | 插值后邻居 | 插值时必填 |
| `fallback_reason` | string/null | fallback 原因 | fallback 时必填 |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败或降级。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStrategy.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentStatus.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_010_定义FieldAlignmentResult类型与策略契约.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_002_定义step时间轴与对齐索引类型.md`

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

本 L3 涉及代码新增，必须使用 `$tdd` 技能。建议顺序：position 插值测试 -> slerp 测试 -> 缺邻居 fallback -> 超阈值 fallback -> 无样本 missing。

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

- `src/data_clean/service/pose_field_aligner.py`
- `src/data_clean/service/__init__.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现图像、夹爪或触觉策略。
- 禁止修改上游 pose 数据契约。
- 禁止写最终 sidecar 或 aligned MCAP。
- 禁止写入真实数据产物或共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.service.pose_field_aligner import align_pose_field
assert callable(align_pose_field)
PY
```

## 17. 成功标准

- [ ] position 插值与 orientation slerp 已测试。
- [ ] 缺邻居和超阈值 fallback 已测试。
- [ ] 无样本 missing 和非法 quaternion 边界已处理。
- [ ] 输出为 [[FieldAlignmentResult]]，未生成最终 sidecar。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。
