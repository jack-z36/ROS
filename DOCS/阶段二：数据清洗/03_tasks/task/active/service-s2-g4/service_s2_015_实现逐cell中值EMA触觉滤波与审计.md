# L3 微元任务：实现逐 cell 中值 EMA 触觉滤波与审计

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：触觉滤波器
L3 编号：service_s2_015
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_015_实现逐cell中值EMA触觉滤波与审计.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_015
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_015_实现逐cell中值EMA触觉滤波与审计.md
  group: service-s2-g4
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g4-p3
  depends_on: [service_s2_014]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_016]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [tactile_filter.median_window, tactile_filter.ema_alpha]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现逐 cell 短窗口中值 + EMA 触觉滤波，生成滤波后序列引用、样本级摘要审计和可选完整 diff artifact。
```

## 4. 本次不做

- 不重新做片段切分策略设计。
- 不写 MCAP_A。
- 不接入开发者入口。

## 5. 执行对象

- [[TactileFilterSegmentSummary]]
- [[TactileFilterSampleRecord]]
- [[TactileFilterResult]]
- [[TactileFilterConfig]]

## 6. 执行依赖

- `service_s2_014` 已完成并归档，触觉可靠片段和 contact reset 点可用。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：触觉滤波片段切分
上游接口定义位置：TactileFilterSegmentSummary.md、service_s2_014 执行结果
当前 L3 期望消费的字段 / 文件 / 返回值：连续触觉片段、reset_points、median_window、ema_alpha、触觉矩阵 rows/cols/data
是否存在接口冲突：无
如果有冲突，本次处理策略：暂停并说明缺失的片段字段，不自行改写上游语义
```

## 8. 预期改动形态

- `src/data_clean/service/` 中出现逐 cell 中值 + EMA 触觉滤波计算。
- 输出 [[TactileFilterResult]]，保持样本数、时间戳、topic、shape 不变。
- 测试覆盖尖峰抑制、EMA reset、审计摘要和可选完整 diff。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | 逐 cell 先做 `median_window=3` 中值，再做 `ema_alpha=0.35` EMA | [[TactileFilterResult]] | `filtered` |
| 缺失输入 | 缺少片段、配置或触觉帧 | 失败并指出缺失项 | `missing_tactile_filter_segment` |
| 边界输入 | reset 点出现 | 重置 EMA 状态，不跨 reset 平滑 | `ema_reset` |
| 短片段 | 样本少于窗口 | 使用可用窗口或原样保留并记录 | `short_segment_kept_original` |
| 调试模式 | `emit_full_diff_in_dev=true` | 输出完整矩阵 diff artifact 引用 | `debug_artifact_ref` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `output_sequence_refs` | object/list | 滤波后触觉序列引用 | 不嵌入完整 MCAP |
| `sample_records` | list[[TactileFilterSampleRecord]] | 样本级审计 | 主记录只保存摘要 |
| `segment_summaries` | list[[TactileFilterSegmentSummary]] | 片段摘要 | 保留 reset 统计 |
| `sample_count_before/after` | object | 样本数统计 | 每 topic 必须相等 |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 11. 现有程序盘点

- 先检查 `src/data_clean/service/` 中是否已有滤波工具；可复用通用统计或序列工具。
- 不得把位姿滤波器的 Savitzky-Golay 算法复制为触觉默认算法。

## 12. 本 L3 的真实改造边界

- 允许新增触觉滤波计算和审计代码。
- 允许新增单元测试和 fixture。
- 禁止写 MCAP_A。
- 禁止修改开发者入口。
- 禁止改变数据补全器输出。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterSampleRecord.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterConfig.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/service_s2_014_实现触觉滤波片段切分与接触变化边界.md`

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
| 是否需要写测试产物 | 是；由入口 L3 统一写出 |
| 是否需要写运行日志 | 是；由入口 L3 统一写出 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 不直接接入开发者入口，但由 `scene2_tactile_filter` 间接覆盖 |

## 16. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止写 MCAP_A。
- 禁止修改补全器接口。
- 禁止接入开发者入口。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [ ] 逐 cell 中值 + EMA 能滤波触觉矩阵。
- [ ] reset 点不会被跨越平滑。
- [ ] 输出保持 topic、时间戳、shape 和样本数量不变。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/`。
