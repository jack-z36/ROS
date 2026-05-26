# L3 微元任务：定义数据补全器策略与结果类型

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：数据补全器
L3 编号：service_s2_005
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_005
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md
  group: service-s2-g2
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g2-p1
  depends_on: [service_s2_001]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_006, service_s2_007, service_s2_008]
  conflict_scope:
    files: [src/data_clean/schemas/, src/data_clean/tests/, DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/]
    modules: [data_clean.schemas]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
定义数据补全器的策略配置、修复方法、决策状态、repair run、样本记录和聚合结果类型。
```

## 4. 本次不做

- 不实现 repair run 聚合算法。
- 不实现三模态补全计算。
- 不接入开发者入口。

## 5. 执行对象

- [[SignalRepairPolicyConfig]]
- [[RepairMethod]]
- [[RepairDecisionStatus]]
- [[SignalRepairRun]]
- [[SignalRepairSampleRecord]]
- [[SignalRepairResult]]

## 6. 执行依赖

- `service_s2_001` 已完成并归档，检测结果类型已落地。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：异常值检测器数据结构
上游接口定义位置：SignalReliabilityDetectionResult.md、SampleReliabilityIssue.md、MissingIntervalIssue.md
当前 L3 期望消费的字段 / 文件 / 返回值：sample_issues、missing_interval_issues、SignalSampleRef
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报，不自行改异常检测接口
```

## 8. 预期改动形态

- 源码中出现可 import 的补全策略和结果类型。
- 测试能实例化 repaired/unrepaired/skipped 三种状态。

## 9. 数据定义输出

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `SignalRepairPolicyConfig` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 数据补全器 |
| `RepairMethod` | enum | `src/data_clean/schemas/` | 数据补全器、报告生成器 |
| `RepairDecisionStatus` | enum | `src/data_clean/schemas/` | 数据补全器、报告生成器 |
| `SignalRepairRun` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 数据补全器 |
| `SignalRepairSampleRecord` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 报告生成器 |
| `SignalRepairResult` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 滤波器、报告生成器 |

## 10. 数据定义验收重点

- 能被 import。
- 能表达 run 级和 sample 级修复记录。
- `SignalRepairResult` 不承载完整三模态序列，只承载 `output_sequence_refs`。
- `timestamp_policy` 固定支持 `preserve_original`。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairRun.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairPolicyConfig.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/service_s2_001_重构可靠性检测数据结构与接口契约.md`

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

## 12. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_signal_repair` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 由 `scene2_signal_repair` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现补全算法。
- 禁止修改异常检测器算法。
- 禁止修改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [ ] 补全相关类型可 import。
- [ ] 能表达 repaired/unrepaired/skipped。
- [ ] `SignalRepairResult` 能引用检测结果和输出序列。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/`。

