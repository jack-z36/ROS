# L3 微元任务：实现 repair run 聚合与合法邻居查找

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：数据补全器
L3 编号：service_s2_006
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_006_实现repair_run聚合与合法邻居查找.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_006
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_006_实现repair_run聚合与合法邻居查找.md
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

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairRun.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairPolicyConfig.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3任务文件身份校验约束.md`
3. `DOCS/02_约束/阶段二任务体系/L3调度元数据约束.md`
4. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
5. `DOCS/02_约束/阶段二任务体系/功能分支接力流程.md`
6. `DOCS/02_约束/阶段二任务体系/L3功能组目录约束.md`
7. `DOCS/02_约束/阶段二任务体系/开发者验收入口约束.md`
8. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
9. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
10. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/执行约束.md`

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

- [x] 同一样本多 issue 被聚合。
- [x] 连续异常样本形成 repair run。
- [x] run 不跨 missing interval。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/`。

## 19. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_006_实现repair_run聚合与合法邻居查找.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_006_实现repair_run聚合与合法邻居查找.md
文件名编号：service_s2_006
正文 L3 编号：service_s2_006
dispatch.task_id：service_s2_006
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`，确认可复用 `SignalRepairRun`、`SignalRepairPolicyConfig`、`RepairDecisionStatus`、`RepairMethod` 和可靠性检测结果类型。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/service/repair_run.py`：新增 `aggregate_sample_issues`、`build_repair_runs`、`find_legal_neighbors` 及轻量结果类型。
- `src/data_clean/tests/service/test_repair_run.py`：新增样本聚合、repair run、missing interval、混合可修复性和邻居查找测试。
- `src/data_clean/data_clean_architecture.md`：登记新增 service 模块。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增同一样本多 issue 聚合测试，运行 `python3 -m pytest src/data_clean/tests/service/test_repair_run.py -q`，按预期因 `ModuleNotFoundError: No module named 'service.repair_run'` 失败。
- Green：新增 `src/data_clean/service/repair_run.py` 并实现 `aggregate_sample_issues` 后，首个测试通过。
- Incremental：继续补充连续 run、跨 missing interval 拆分、混合可修复性和合法邻居查找测试；首次扩展后发现 missing interval 边界和混合可修复性兼容规则未满足，修正后目标测试全部通过。
- Refactor：补充架构目录登记，并清理新增模块中不必要的 docstring。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_repair_run.py -q`：通过，`6 passed`。
- `python3 -m pytest src/data_clean/tests/service/test_repair_run.py -v`：通过，`6 passed`。
- `python3 -m py_compile src/data_clean/service/repair_run.py src/data_clean/tests/service/test_repair_run.py`：通过。
- 手动接口验证：通过 `PYTHONPATH=src/data_clean python3 - <<'PY' ... PY` 调用 `aggregate_sample_issues`、`build_repair_runs`、`find_legal_neighbors`，观察到一个 repair run 和 clean previous/next neighbors。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准核对

- 已验证同一样本多 issue 按 `source_topic + time_domain + timestamp + message_index + modality` 聚合为一个样本问题组。
- 已验证同 topic、同模态、同 replacement unit、兼容修复建议且 message_index 连续的异常样本形成单个 `SignalRepairRun`。
- 已验证 repair run 不跨 `MissingIntervalIssue` 起始边界，跨边界时拆分为多个 run。
- 已验证任一 run 内含 `inspect_required` 等不可修建议时，整个 run 标记为 `RepairDecisionStatus.UNREPAIRABLE`，reason 为 `mixed_repairability_in_run`。
- 已验证合法邻居查找只在同 topic、同 modality 中查找，跳过 dirty sample、target sample 和刚修复 sample，并能表达无邻居情况。
- 本 L3 不直接修改 `./start_data_clean.sh --dev`；后续由场景二 `scene2_signal_repair` 功能检验项和场景完整 smoke test 间接覆盖。建议用户在场景二全链路完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_signal_repair` 做最终人工验收。

### 本次明确未做

- 未计算实际修复值，未实现插值、融合或 hold 的值写入。
- 未写 `SignalRepairResult` 完整输出。
- 未修改开发者入口、菜单、脚本调用、调度索引、共享执行记录、阶段进度或总执行日志。

### 归档状态

- 本文件完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/`。
- 原 active 功能组目录若为空则删除。

### 风险与后续建议

- `RepairDecisionStatus` 当前只有 `REPAIRED` / `UNREPAIRABLE` / `SKIPPED`，本 L3 将可自动修复的 run 表达为 `REPAIRED` 候选状态；后续 `service_s2_007` 写入实际修复结果时可继续复用该 run 结构。
- 建议后续 `service_s2_007` 在本 L3 的 `previous_neighbor_ref` / `next_neighbor_ref` 基础上执行具体补全计算，并继续避免使用 run 内刚修复值作为邻居。
