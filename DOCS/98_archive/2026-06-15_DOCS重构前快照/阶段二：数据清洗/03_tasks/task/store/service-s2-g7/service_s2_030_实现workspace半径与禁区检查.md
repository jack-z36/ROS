# L3 微元任务：实现 workspace 半径与禁区检查

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：关节限制检查器
L3 编号：service_s2_030
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_030_实现workspace半径与禁区检查.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_030
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_030_实现workspace半径与禁区检查.md
  group: service-s2-g7
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g7-p3
  depends_on: [service_s2_028]
  must_run_after: []
  can_run_parallel_with: [service_s2_029]
  blocks: [service_s2_031]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [joint_constraint.workspace]
  dispatch_status: ready
```

## 3. 本次目标

```text
基于 RobotBaseTcpPose 和 JointConstraintConfig 实现 workspace 工作半径与基座正上/正下禁区检查。
```

## 4. 本次不做

- 不实现关节角 / 速度 / 加速度检查。
- 不实现 MuJoCo 仿真。
- 不计算完整奇异点或 manipulability 指标。

## 5. 执行对象

- [[RobotBaseTcpPose]]
- [[JointConstraintConfig]]
- [[JointConstraintSampleEvidence]]
- [[JointConstraintIssueInterval]]

## 6. 执行依赖

- `service_s2_027` 已定义数据类型。
- `service_s2_028` 已能从 IkSolveSummary 获取 source pose 引用或可用于 workspace 的 base-frame TCP pose。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：IK 求解与 MCAP_B 生成器、关节限制检查器对齐读取层。
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/RobotBaseTcpPose.md
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/IkSolveSummary.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_028_实现MCAP_B与IkSolveSummary对齐读取和连续片段切分.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- arm_side
- timestamp_ns
- robot_base frame TCP position
- workspace_radius_mm
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：暂停并汇报，不重定义 RobotBaseTcpPose。
```

## 8. 预期改动形态

- service 层新增 workspace 检查函数。
- 测试覆盖 610 mm 半径、边界等于阈值、超过阈值、禁区命中、缺少 pose。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| TCP 距离 <= 610 mm | 合法 | 无 issue | 无 |
| TCP 距离 > 610 mm | 输出硬问题 | `workspace_radius_limit` | `workspace_radius_limit` |
| TCP 命中配置禁区 | 输出硬问题 | `workspace_no_go_zone` | `workspace_no_go_zone` |
| 缺少 RobotBaseTcpPose | 当前样本 workspace 检查失败 | evidence 或 result 错误 | `missing_robot_base_tcp_pose` |

## 10. 数据计算验收重点

- 默认工作半径为官网核实的 610 mm。
- 禁区阈值必须来自配置，不写死。
- 首版 workspace 问题全部 `severity=hard`、`suggested_mask=drop_or_mask`。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/RobotBaseTcpPose.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintSampleEvidence.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_028_实现MCAP_B与IkSolveSummary对齐读取和连续片段切分.md`

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
| 对应功能检验项 | `scene2_joint_constraint_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；workspace 阈值覆盖只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 场景最终验收仍需用户运行 `./start_data_clean.sh --dev` |

## 14. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 15. 禁止修改

- 不修改 IK 求解。
- 不修改关节角速度加速度检查。
- 不实现 MuJoCo。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "joint_constraint and workspace"
```

## 17. 成功标准

- [ ] 610 mm 半径内样本不输出 issue。
- [ ] 超 610 mm 样本输出 `workspace_radius_limit`。
- [ ] 配置禁区命中输出 `workspace_no_go_zone`。
- [ ] workspace 问题输出硬问题和 `drop_or_mask` 建议。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后勾选成功标准，追加执行摘要，并将本文件归档到：

```text
DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/
```

