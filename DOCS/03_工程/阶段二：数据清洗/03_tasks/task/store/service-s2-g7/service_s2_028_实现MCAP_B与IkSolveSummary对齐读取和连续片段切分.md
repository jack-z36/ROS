# L3 微元任务：实现 MCAP_B 与 IkSolveSummary 对齐读取和连续片段切分

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：关节限制检查器
L3 编号：service_s2_028
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_028_实现MCAP_B与IkSolveSummary对齐读取和连续片段切分.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_028
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_028_实现MCAP_B与IkSolveSummary对齐读取和连续片段切分.md
  group: service-s2-g7
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g7-p2
  depends_on: [service_s2_026, service_s2_027]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_029, service_s2_030]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
实现关节限制检查器的上游对齐层：同时读取 MCAP_B 与 IkSolveSummary，保留 IK 失败帧，并切分连续 IK 成功片段。
```

## 4. 本次不做

- 不检查关节角、速度、加速度。
- 不检查 workspace。
- 不接入开发者入口。

## 5. 执行对象

- [[McapB]]
- [[IkSolveSummary]]
- [[Rm65IkSampleResult]]
- [[JointConstraintCheckResult]].`continuous_success_segments`

## 6. 执行依赖

- `service_s2_026` 已完成 SDK 自检或明确记录 SDK 状态。
- `service_s2_027` 已定义关节限制检查类型。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：IK 求解与 MCAP_B 生成器。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapB.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/IkSolveSummary.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/Rm65IkSampleResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- MCAP_B 左右 JointState 成功帧
- IkSolveSummary.sample_records 覆盖所有输入 pose
- IkSolveSummary.failure_intervals
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：暂停并汇报，不修改上游契约。
```

## 8. 预期改动形态

- 新增或扩展 service 层对齐函数。
- 输出连续成功片段和 IK 失败 issue interval 候选。
- 测试覆盖 sidecar 缺失、失败帧漏标防护、大 gap 切段。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法 MCAP_B + sidecar | 按 arm_side 和 timestamp 对齐成功帧与 sample_records | 连续成功片段、失败区间 | 无 |
| 缺少 sidecar | strict 失败 | 不输出片段 | `missing_ik_solve_summary` |
| 成功帧无法在 sidecar 找到 | strict 失败 | 不输出片段 | `mcap_b_ik_summary_mismatch` |
| IK 失败帧 | 不要求 MCAP_B 有消息，直接进入失败区间 | `ik_failed` interval | `ik_failed` |
| 大 gap | 切断连续成功片段 | 两个片段 | `large_gap_segment_boundary` |

## 10. 数据计算验收重点

- 不只依赖 MCAP_B 推断问题。
- 失败帧来自 IkSolveSummary，不会漏标。
- 速度 / 加速度后续只能在连续成功片段内计算。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapB.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/IkSolveSummary.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintCheckResult.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_027_定义关节限制检查数据契约.md`
2. 如果存在，读取 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/` 下 MCAP_B 写出任务执行摘要。

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
2. `src/data_clean/repo/`
3. `src/data_clean/tests/`

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
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 场景最终验收仍需用户运行 `./start_data_clean.sh --dev` |

## 14. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 15. 禁止修改

- 不修改 MCAP_B 写出器。
- 不修改 IK 求解逻辑。
- 不改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "joint_constraint and (align or segment or ik_summary)"
```

## 17. 成功标准

- [ ] 缺少 IkSolveSummary 时 strict 失败。
- [ ] IK 失败帧能进入 `ik_failed` 区间候选。
- [ ] MCAP_B 成功帧与 sidecar 对齐失败时会报错。
- [ ] 大 gap 会切断连续成功片段。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后勾选成功标准，追加执行摘要，并将本文件归档到：

```text
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/
```

