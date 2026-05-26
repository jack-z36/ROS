# L3 微元任务：实现 repair run 聚合与合法邻居查找

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：数据补全器
L3 编号：service_s2_006
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_006_实现repair_run聚合与合法邻居查找.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_006
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_006_实现repair_run聚合与合法邻居查找.md
  group: service-s2-g2
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g2-p2
  depends_on: [service_s2_005]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_007]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [repair.run_grouping]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现数据补全器的样本问题聚合、repair run 聚合和同 topic 合法邻居查找。
```

## 4. 本次不做

- 不计算修复后的值。
- 不写 `SignalRepairResult` 完整输出。
- 不接入开发者入口。

## 5. 执行对象

- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[SignalRepairRun]]
- 合法邻居查找规则。

## 6. 执行依赖

- `service_s2_005` 已完成并归档。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：异常值检测器输出和补全器类型定义
上游接口定义位置：SignalReliabilityDetectionResult.md、SignalRepairRun.md
当前 L3 期望消费的字段 / 文件 / 返回值：sample_issues、missing_interval_issues、SignalSampleRef、RepairDecisionStatus
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报
```

## 8. 预期改动形态

- service 层出现 repair run 构建和合法邻居查找函数。
- 测试覆盖同样本多 issue、连续 run、跨 missing interval 拆分、混合可修复性拒绝。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 同一样本多 issue | 按 `source_topic + time_domain + timestamp + message_index + modality` 聚合 | 一个样本问题组 | 无 |
| 连续可修样本 | 同 topic、同模态、同替换单位、建议兼容 | 一个 [[SignalRepairRun]] | 无 |
| 跨缺失区间 | run 不得跨越 [[MissingIntervalIssue]] | 拆成两个 run 或拒绝 | `cross_missing_interval` |
| 含不可修建议 | run 内任一 issue 为 `mark_only`/`inspect_required` 等 | run unrepaired | `mixed_repairability_in_run` |
| 邻居不干净 | 邻居有 sample issue 或基本有效性失败 | 继续查找或返回缺失邻居 | `missing_clean_neighbor` |

## 10. 数据计算验收重点

- 不使用刚修复值作为邻居。
- 不跨 topic、跨左右臂、跨模态查找邻居。
- 不跨未处理缺失区间。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairRun.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairPolicyConfig.md`

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

1. `src/data_clean/service/`
2. `src/data_clean/schemas/`
3. `src/data_clean/tests/`

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

- `src/data_clean/service/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止计算修复值。
- 禁止实现开发者入口。
- 禁止修改异常检测器规则。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [ ] 同一样本多 issue 被聚合。
- [ ] 连续异常样本形成 repair run。
- [ ] run 不跨 missing interval。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/`。

