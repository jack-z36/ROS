# L3 微元任务：定义关节限制检查数据契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：关节限制检查器
L3 编号：service_s2_027
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_027_定义关节限制检查数据契约.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_027
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_027_定义关节限制检查数据契约.md
  group: service-s2-g7
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g7-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [service_s2_026]
  blocks: [service_s2_028, service_s2_029, service_s2_030, service_s2_031]
  conflict_scope:
    files: [src/data_clean/schemas/, src/data_clean/tests/]
    modules: [data_clean.schemas]
    config_keys: [joint_constraint]
  dispatch_status: ready
```

## 3. 本次目标

```text
在代码层定义关节限制检查器需要的配置、样本证据、问题区间和检查结果类型，并与 L2 原子数据定义对齐。
```

## 4. 本次不做

- 不实现 MCAP_B 读取。
- 不实现任何检查算法。
- 不接入开发者入口。

## 5. 执行对象

- [[JointConstraintConfig]]
- [[JointConstraintSampleEvidence]]
- [[JointConstraintIssueInterval]]
- [[JointConstraintCheckResult]]

## 6. 执行依赖

- 场景二 L2 数据定义已存在。
- 上游 [[McapB]]、[[IkSolveSummary]]、[[RobotBaseTcpPose]]、[[Rm65IkSampleResult]] 语义已定义。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：IK 求解与 MCAP_B 生成器。
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapB.md
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/IkSolveSummary.md
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/Rm65IkSampleResult.md
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/RobotBaseTcpPose.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- MCAP_B JointState 成功帧
- IkSolveSummary.sample_records
- IkSolveSummary.failure_intervals
- RobotBaseTcpPose 引用
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：只调整当前类型以复用上游语义，不重定义相似对象。
```

## 8. 预期改动形态

- `src/data_clean/schemas/` 或项目既有 schema/types 位置新增关节限制检查相关类型。
- 新增序列化 / 反序列化 / 默认阈值测试。
- 类型字段引用 L2 数据定义中的官网核实阈值，不要求 L3 再联网查询。

## 9. 数据定义输出

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `JointConstraintConfig` | dataclass / schema | `src/data_clean/schemas/` 或既有类型位置 | service_s2_029 / 030 / 031 |
| `JointConstraintSampleEvidence` | dataclass / schema | 同上 | 问题区间聚合、开发者入口 |
| `JointConstraintIssueInterval` | dataclass / schema | 同上 | Parquet 标注与报告 |
| `JointConstraintCheckResult` | dataclass / schema | 同上 | 开发者入口、报告生成器 |

## 10. 数据定义验收重点

- 能 import、实例化、序列化。
- 默认角度、速度、工作半径来自 [[JointConstraintConfig]] 文档。
- `joint_max_acceleration_deg_s2` 可配置，不写死不可覆盖值。
- 所有关节数组长度必须校验为 6。
- MCAP_B rad 输入与配置 deg 单位边界必须在字段说明中明确。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintSampleEvidence.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintIssueInterval.md`
5. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintCheckResult.md`

### 必读相关微元任务记录

1. 如果存在，读取 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/` 下 MCAP_B 数据契约相关任务。

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
| 对应功能检验项 | 不直接接入开发者入口，但由 `scene2_joint_constraint_check` 间接覆盖 |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 场景最终验收仍需用户运行 `./start_data_clean.sh --dev` |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 15. 禁止修改

- 不修改 MCAP_B 写出逻辑。
- 不实现检查算法。
- 不改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "joint_constraint and (schema or config or serialization)"
```

## 17. 成功标准

- [ ] 四个关节限制检查类型已实现并可 import。
- [ ] 默认角度、速度、工作半径与 L2 数据定义一致。
- [ ] 加速度阈值可配置，未被写死为不可覆盖常量。
- [ ] 非 6 长度关节数组会被拒绝。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后勾选成功标准，追加执行摘要，并将本文件归档到：

```text
DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/
```

