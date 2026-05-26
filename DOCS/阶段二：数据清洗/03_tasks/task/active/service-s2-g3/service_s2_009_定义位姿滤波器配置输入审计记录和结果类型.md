# L3 微元任务：定义位姿滤波器配置输入审计记录和结果类型

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：位姿滤波器
L3 编号：service_s2_009
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_009
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md
  group: service-s2-g3
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g3-p1
  depends_on: [service_s2_005]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_010, service_s2_011, service_s2_012]
  conflict_scope:
    files: [src/data_clean/schemas/, src/data_clean/tests/, DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/]
    modules: [data_clean.schemas]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
定义位姿滤波器的配置、输入序列、样本级审计、片段摘要和聚合结果类型。
```

## 4. 本次不做

- 不实现分段算法。
- 不实现 Savitzky-Golay 计算。
- 不接入开发者入口。

## 5. 执行对象

- [[PoseFilterConfig]]
- [[PoseFilterInputSequence]]
- [[PoseFilterSampleRecord]]
- [[PoseFilterSegmentSummary]]
- [[PoseFilterResult]]

## 6. 执行依赖

- `service_s2_005` 已完成并归档，[[SignalRepairResult]] 等补全结果类型已经落地。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器类型定义
上游接口定义位置：DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md、SignalRepairResult.md、SignalRepairRun.md、SignalRepairSampleRecord.md
当前 L3 期望消费的字段 / 文件 / 返回值：SignalRepairResult.output_sequence_refs、timestamp_policy、repair_runs、unhandled_missing_interval_records
是否存在接口冲突：无；output_sequence_refs 的具体 artifact 格式仍未固化
如果有冲突，本次处理策略：只定义 PoseFilterInputSequence 语义接口，不猜测 artifact 物理格式
```

## 8. 预期改动形态

- 源码中出现可 import 的位姿滤波配置和结果类型。
- 测试能实例化默认 `PoseFilterConfig`、样本级记录和聚合结果。
- 文档原子定义与源码类型字段保持一致。

## 9. 数据定义输出

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `PoseFilterConfig` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 位姿滤波器 |
| `PoseFilterInputSequence` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 位姿滤波器 |
| `PoseFilterSampleRecord` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 报告生成器 |
| `PoseFilterSegmentSummary` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 位姿滤波器、报告生成器 |
| `PoseFilterResult` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | MCAP_A 生成器、报告生成器 |

## 10. 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `algorithm` | enum string | 滤波算法 | `savgol` | v1 只允许 `savgol` |
| `window_duration_ms` | number | 对外时间窗口 | `200` | 有限正数 |
| `polyorder` | integer | Savitzky-Golay 阶数 | `2` | 非负整数 |
| `position_guard_max_delta_m` | number | 位置 guard | `0.02` | 有限非负数 |
| `orientation_guard_max_delta_deg` | number | 姿态 guard | `5` | 有限非负数 |
| `status` | enum string | 样本处理状态 | 无 | `filtered` / `kept_original` / `skipped_boundary` / `filter_rejected_by_guard` |
| `timestamp_policy` | enum string | 时间戳策略 | `preserve_original` | 只能保持原时间结构 |

## 11. 数据定义验收重点

- 能被 import。
- 默认配置能表达 200ms/order2、2cm/5deg guard。
- `PoseFilterResult` 能引用 [[SignalRepairResult]]，并表达 `sample_count_before == sample_count_after`。
- 样本记录能表达 guard 拒绝时的原值、候选滤波值和最终原值。

## 12. 现有程序盘点

- `src/data_clean/schemas/` 已有 Runtime 和基础 schema 类型；尚未发现位姿滤波器类型。
- `src/data_clean/service/` 目前有场景一清洗、位姿转换和校验服务；尚未发现 `pose_filter` 实现。
- 本 L3 是在现有分层上新增 schema/types，不重写既有场景一位姿转换。

## 13. 本 L3 的真实改造边界

- 允许新增位姿滤波器相关 schema/types 和对应测试。
- 允许更新 `src/data_clean/data_clean_architecture.md` 中的目录结构说明。
- 禁止实现滤波算法或开发者入口。
- 禁止修改 [[SignalRepairResult]] 的既有语义，除非发现字段名与已归档上游 L3 不一致并先暂停汇报。

## 14. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterResult.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`

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

1. `src/data_clean/schemas/`
2. `src/data_clean/tests/`
3. `src/data_clean/data_clean_architecture.md`

## 15. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 16. 开发者验收入口关联

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

## 17. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 18. 禁止修改

- 禁止实现位姿滤波算法。
- 禁止修改数据补全器算法。
- 禁止修改开发者入口。

## 19. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 20. 成功标准

- [ ] 位姿滤波相关类型可 import。
- [ ] 默认配置能表达 200ms/order2 与 2cm/5deg guard。
- [ ] `PoseFilterResult` 能引用补全结果和输出序列。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 21. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。
