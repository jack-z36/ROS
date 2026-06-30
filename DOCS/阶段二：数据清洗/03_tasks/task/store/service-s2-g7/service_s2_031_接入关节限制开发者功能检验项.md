# L3 微元任务：接入关节限制开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：关节限制检查器
L3 编号：service_s2_031
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_031_接入关节限制开发者功能检验项.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_031
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_031_接入关节限制开发者功能检验项.md
  group: service-s2-g7
  branch: service-s2
  wave: 4
  parallel_group: service-s2-g7-p4
  depends_on: [service_s2_029, service_s2_030]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [start_data_clean.sh, src/data_clean/runtime/, src/data_clean/ui/, src/data_clean/tests/]
    modules: [data_clean.runtime, data_clean.ui]
    config_keys: [joint_constraint]
  dispatch_status: ready
```

## 3. 本次目标

```text
把关节限制检查器接入 `./start_data_clean.sh --dev` 场景二功能检验项 `scene2_joint_constraint_check`，输出检查结果、证据摘要、SDK 自检状态和运行日志。
```

## 4. 本次不做

- 不新增底层检查算法。
- 不修改 SDK 部署逻辑。
- 不宣称场景二最终验收完成。

## 5. 执行对象

- 开发者入口：`./start_data_clean.sh --dev`
- 场景二功能检验项：`scene2_joint_constraint_check`
- 输出：`joint_constraint_check_result.json`、`joint_constraint_evidence_summary.json`、运行日志。

## 6. 执行依赖

- `service_s2_029` 已完成关节角速度加速度检查。
- `service_s2_030` 已完成 workspace 检查。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：关节限制检查器计算能力。
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_029_实现关节角速度加速度检查.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_030_实现workspace半径与禁区检查.md
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintCheckResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- JointConstraintCheckResult
- sample_evidence
- issue_intervals
- SDK 自检状态
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：暂停并汇报，不改底层算法契约。
```

## 8. 预期改动形态

- 场景二开发者菜单新增或接入 `scene2_joint_constraint_check`。
- 功能检验项创建独立 run 目录。
- 输出检查结果 JSON、证据摘要和运行日志。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景二：硬件数据可靠性验证
↓
选择 scene2_joint_constraint_check
↓
选择 MCAP_B、IkSolveSummary、JointConstraintConfig 和调试输出目录
↓
检查 SDK 自检状态
↓
读取并对齐上游输入
↓
运行关节角 / 速度 / 加速度 / workspace 检查
↓
写 joint_constraint_check_result.json、evidence summary 和运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| SDK 自检状态读取 | 检查前 | SDK 缓存或自检记录 | 可用 / 不可用 | 不可用则失败并写日志 |
| 上游对齐读取层 | 检查前 | MCAP_B、IkSolveSummary | 连续成功片段和失败区间 | strict 失败 |
| 关节检查 | 对齐后 | 片段、配置、SDK Algo | 关节类 evidence / interval | 写错误摘要 |
| workspace 检查 | 对齐后 | RobotBaseTcpPose、配置 | workspace evidence / interval | 写错误摘要 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `completed` | 检查完成 | result JSON / run log | 输出问题统计和路径 |
| `failed` | 输入缺失、SDK 不可用、对齐失败 | run log / error summary | 显示 reason |
| `partial` | 加速度阈值缺失但其他检查完成 | result JSON / run log | 显示跳过加速度检查原因 |

## 10. 流程编排验收重点

- 功能检验项可从开发者入口选择。
- 调试产物写入独立 run 目录。
- 不把调试产物写入正式生产输出。
- 运行日志包含输入、配置、SDK 状态、阈值来源、问题统计、输出位置和错误信息。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintCheckResult.md`
3. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_029_实现关节角速度加速度检查.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_030_实现workspace半径与禁区检查.md`

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

1. `start_data_clean.sh`
2. `src/data_clean/runtime/`
3. `src/data_clean/ui/`
4. `src/data_clean/tests/`

## 12. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 必须使用 `$tdd`。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_joint_constraint_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；result JSON、evidence summary |
| 是否需要写运行日志 | 是；输入、配置、SDK 状态、阈值来源、问题统计、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景二和本功能检验项 |

## 14. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 15. 禁止修改

- 不重写底层检查算法。
- 不修改 MCAP_B 写出。
- 不写正式生产数据目录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "joint_constraint and (dev or cli or smoke)"
```

## 17. 成功标准

- [ ] 开发者入口可选择 `scene2_joint_constraint_check`。
- [ ] 功能检验项能读取 MCAP_B、IkSolveSummary 和配置。
- [ ] 输出 `joint_constraint_check_result.json`。
- [ ] 输出证据摘要和运行日志。
- [ ] 调试产物写入独立 run 目录，不污染正式生产输出。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后勾选成功标准，追加执行摘要，并将本文件归档到：

```text
DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/
```

