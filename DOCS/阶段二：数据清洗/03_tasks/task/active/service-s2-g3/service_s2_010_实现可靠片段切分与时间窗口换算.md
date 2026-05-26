# L3 微元任务：实现可靠片段切分与时间窗口换算

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：位姿滤波器
L3 编号：service_s2_010
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_010
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md
  group: service-s2-g3
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g3-p2
  depends_on: [service_s2_007, service_s2_009]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_011, service_s2_012]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [pose_filter.window_duration_ms, pose_filter.polyorder]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现位姿滤波器的可靠片段切分、时间窗口到奇数样本窗口换算和短片段处理。
```

## 4. 本次不做

- 不实现 Savitzky-Golay 数值滤波。
- 不实现四元数姿态滤波。
- 不接入开发者入口。

## 5. 执行对象

- [[PoseFilterInputSequence]]
- [[PoseFilterConfig]]
- [[PoseFilterSegmentSummary]]

## 6. 执行依赖

- `service_s2_007` 已完成并归档，补全后 pose 序列和 [[SignalRepairResult]] 可用。
- `service_s2_009` 已完成并归档，位姿滤波器类型已落地。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器、位姿滤波器类型定义
上游接口定义位置：SignalRepairResult.md、PoseFilterInputSequence.md、PoseFilterConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：output_sequence_refs 映射后的 pose samples、MissingIntervalIssue、pose unrepaired/skipped refs
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报，不自行兼容多个猜测格式
```

## 8. 预期改动形态

- `src/data_clean/service/` 中出现可测试的 pose 分段与窗口换算逻辑。
- 测试覆盖缺失区间、未修复样本、短片段和 200ms 时间窗口换算。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法连续 pose 片段 | 按时间戳中位 `dt` 将 200ms 换算为最近奇数样本窗口 | `PoseFilterSegmentSummary.status=filtered` | 无 |
| 含 [[MissingIntervalIssue]] | 缺失区间两侧切为独立片段 | 多个片段摘要 | `split_by_missing_interval` |
| 含 pose `unrepaired` / `skipped` 样本 | 该样本作为边界，不进入滤波窗口 | 左右片段分别输出 | `split_by_unrepaired_pose` |
| 片段过短 | 缩小到可用最大奇数窗口；仍不满足则原样保留 | `kept_original_short_segment` | `short_segment_kept_original` |
| 时间戳重复或倒退 | 当前片段原样保留 | `skipped_invalid_time` | `invalid_segment_time_order` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `segment_id` | string | 片段 id | 同一次运行内唯一 |
| `actual_window_size_samples` | integer/null | 实际窗口 | 奇数且大于 `polyorder` |
| `median_dt_sec` | number/null | 时间戳中位间隔 | 合法片段必须非负 |
| `status` | enum string | 片段状态 | 与 reason 一致 |

## 10. 数据计算验收重点

- 缺失区间阻断跨段滤波。
- pose `unrepaired` / `skipped` 样本阻断跨段滤波。
- 200ms 窗口按中位 `dt` 换算为奇数样本窗口。
- 短片段自适应缩窗或原样保留。

## 11. 现有程序盘点

- `src/data_clean/service/` 尚未发现位姿滤波器实现。
- 现有 `tcp_transform.py` 只负责场景一位姿变换，不负责可靠性滤波。
- 本 L3 应新增独立 service 逻辑，复用现有分层，不改场景一清洗路径。

## 12. 本 L3 的真实改造边界

- 允许新增位姿分段和窗口换算函数。
- 允许新增对应单元测试。
- 禁止实现数值滤波和 MCAP 写出。
- 禁止修改上游数据补全器输出语义。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterInputSequence.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterSegmentSummary.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/MissingIntervalIssue.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_007_实现三模态补全计算规则.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md`

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
| 对应功能检验项 | `scene2_pose_filter` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 不直接接入开发者入口，但由 `scene2_pose_filter` 间接覆盖 |

## 16. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止实现数值滤波。
- 禁止写 MCAP_A。
- 禁止修改开发者入口。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [ ] 缺失区间会切断片段。
- [ ] pose `unrepaired` / `skipped` 样本会切断片段。
- [ ] 200ms 时间窗口按中位 `dt` 换算为奇数样本窗口。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。
