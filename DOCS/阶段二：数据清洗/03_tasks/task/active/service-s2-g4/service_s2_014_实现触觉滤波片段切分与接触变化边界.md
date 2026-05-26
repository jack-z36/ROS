# L3 微元任务：实现触觉滤波片段切分与接触变化边界

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：触觉滤波器
L3 编号：service_s2_014
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_014_实现触觉滤波片段切分与接触变化边界.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_014
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_014_实现触觉滤波片段切分与接触变化边界.md
  group: service-s2-g4
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g4-p2
  depends_on: [service_s2_007, service_s2_013]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_015, service_s2_016]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [tactile_filter.contact_reset_threshold]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现触觉滤波前的连续可靠片段切分与真实接触变化 EMA reset 点识别。
```

## 4. 本次不做

- 不实现中值 + EMA 滤波。
- 不写滤波后触觉序列。
- 不接入开发者入口。

## 5. 执行对象

- [[TactileFilterInputSequence]]
- [[TactileFilterConfig]]
- [[MissingIntervalIssue]]
- [[SignalRepairRun]]
- [[TactileFilterSegmentSummary]]

## 6. 执行依赖

- `service_s2_007` 已完成并归档，补全器能输出 [[SignalRepairResult]] 和修复后序列引用。
- `service_s2_013` 已完成并归档，触觉滤波类型已经落地。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器、触觉滤波器类型定义
上游接口定义位置：SignalRepairResult.md、SignalRepairRun.md、SignalRepairSampleRecord.md、TactileFilterInputSequence.md、TactileFilterConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：output_sequence_refs、timestamp_policy、repair_runs、unhandled_missing_interval_records、tactile frames rows/cols/data
是否存在接口冲突：无；如果 output_sequence_refs 尚未有物理格式，只在既有测试 fixture 上实现语义适配
如果有冲突，本次处理策略：暂停并说明缺少的上游字段，不自行发明新字段
```

## 8. 预期改动形态

- `src/data_clean/service/` 中出现触觉滤波片段切分或边界识别函数。
- 测试覆盖缺失区间、未修复样本、shape 不一致和 contact reset。
- 输出可被后续 `service_s2_015` 直接用于滤波计算。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | 同 topic、shape 一致、无缺失和未修复样本 | 连续 [[TactileFilterSegmentSummary]] | `segment_ready` |
| 缺失输入 | 缺少 [[SignalRepairResult]] 或触觉序列引用 | 失败并指出缺失项 | `missing_signal_repair_result` / `missing_tactile_sequence` |
| 边界输入 | 出现 [[MissingIntervalIssue]] 或 tactile `unrepaired/skipped` 样本 | 左右分段，不跨边界 | `missing_interval_boundary` / `unrepaired_sample_boundary` |
| 接触变化 | 相邻帧变化超过 `contact_reset_threshold` | 记录 reset point，不切断样本数量 | `contact_reset` |
| shape 不一致 | 同一序列中 rows/cols/data_len 不一致 | 当前片段停止或序列失败 | `tactile_shape_mismatch` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `segments` | list[[TactileFilterSegmentSummary]] | 可滤波片段摘要 | 不跨缺失区间或未修复样本 |
| `reset_points` | list[[SignalSampleRef]] | EMA reset 点 | 来源必须是同 topic 样本 |
| `boundary_records` | list[object] | 分段边界记录 | 必须有 reason |
| `invalid_sequence_records` | list[object] | 不可滤波序列记录 | 必须指出 topic 和 shape 问题 |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 11. 现有程序盘点

- 先检查是否已有场景二滤波或可靠片段切分工具；如已有，应优先复用。
- 不得复用位姿滤波器的 Savitzky-Golay 窗口逻辑作为触觉滤波算法，但可以参考其分段边界风格。

## 12. 本 L3 的真实改造边界

- 允许新增触觉滤波分段、shape 校验和 contact reset 识别代码。
- 允许新增对应单元测试。
- 禁止实现实际中值 + EMA 生成滤波矩阵。
- 禁止改动数据补全器输出语义。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterSegmentSummary.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_007_实现三模态补全计算规则.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md`

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
10. `DOCS/阶段二：数据清洗/02_service/场景二/执行约束.md`

### 必读代码

1. `src/data_clean/service/`
2. `src/data_clean/schemas/`
3. `src/data_clean/tests/`

## 14. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_tactile_filter` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 不直接接入开发者入口，但由 `scene2_tactile_filter` 间接覆盖 |

## 16. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止实现滤波矩阵输出。
- 禁止修改补全器接口。
- 禁止接入开发者入口。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [ ] 缺失区间和 tactile 未修复样本会形成分段边界。
- [ ] 接触变化超过阈值会生成 EMA reset 点。
- [ ] shape 不一致不会被静默滤波。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/`。
