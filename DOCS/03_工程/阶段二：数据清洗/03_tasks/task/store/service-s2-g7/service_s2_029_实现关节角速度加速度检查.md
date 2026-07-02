# L3 微元任务：实现关节角速度加速度检查

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：关节限制检查器
L3 编号：service_s2_029
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_029_实现关节角速度加速度检查.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_029
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_029_实现关节角速度加速度检查.md
  group: service-s2-g7
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g7-p3
  depends_on: [service_s2_028]
  must_run_after: []
  can_run_parallel_with: [service_s2_030]
  blocks: [service_s2_031]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [joint_constraint]
  dispatch_status: ready
```

## 3. 本次目标

```text
在连续 IK 成功片段内实现关节角、速度和加速度限制检查，输出样本级证据和问题区间。
```

## 4. 本次不做

- 不实现 MCAP_B / sidecar 对齐读取。
- 不实现 workspace 检查。
- 不接入开发者入口。

## 5. 执行对象

- [[JointConstraintConfig]]
- [[JointConstraintSampleEvidence]]
- [[JointConstraintIssueInterval]]
- `continuous_success_segments`

## 6. 执行依赖

- `service_s2_026` 已完成 SDK 自检。
- `service_s2_027` 已定义类型。
- `service_s2_028` 已实现连续成功片段。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：关节限制检查器对齐读取层。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_028_实现MCAP_B与IkSolveSummary对齐读取和连续片段切分.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- 连续成功片段，片段内每个样本有 arm_side、timestamp_ns、joint positions
- JointConstraintConfig 中角度、速度、加速度阈值
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：暂停并汇报，不重写对齐层。
```

## 8. 预期改动形态

- service 层新增或扩展关节角 / 速度 / 加速度检查函数。
- 测试覆盖 SDK 返回码映射、本地阈值证据、加速度缺配置行为。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法连续片段 | 角度用 SDK position limit + 配置证据，速度用 SDK velocity limit，加速度用配置差分 | 无或若干 evidence / interval | 无 |
| 角度超限 | SDK 返回非 0 或配置比较超限 | `joint_position_limit` | `joint_position_limit` |
| 速度超限 | SDK velocity limit 返回非 0 或本地速度超限 | `joint_velocity_limit` | `joint_velocity_limit` |
| 加速度超限 | 速度差分超过配置 | `joint_acceleration_limit` | `joint_acceleration_limit` |
| 加速度阈值缺失 | 不执行加速度检查，写明跳过或失败 | result 中记录 | `missing_joint_acceleration_threshold` |
| 片段长度不足 | 跳过速度或加速度检查 | 无证据或 skipped summary | `short_segment` |

## 10. 数据计算验收重点

- 不跨越失败帧或大 gap。
- SDK 返回码必须保留到 evidence。
- 关节角输入若来自 JointState rad，必须转换为 deg 后与配置比较。
- 加速度阈值必须配置化。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintConfig.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintSampleEvidence.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintIssueInterval.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_026_睿尔曼SDK本地部署与IK限位函数自检.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/service_s2_028_实现MCAP_B与IkSolveSummary对齐读取和连续片段切分.md`

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
| 是否允许临时覆盖配置 | 是；阈值覆盖只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 场景最终验收仍需用户运行 `./start_data_clean.sh --dev` |

## 14. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 文件自身。

## 15. 禁止修改

- 不修改 SDK 自检任务。
- 不修改 workspace 检查。
- 不改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "joint_constraint and (position or velocity or acceleration)"
```

## 17. 成功标准

- [ ] 关节角超限能输出 evidence 和 interval。
- [ ] 速度超限能输出 evidence 和 interval。
- [ ] 加速度超限能输出 evidence 和 interval。
- [ ] 加速度阈值缺失时不会使用写死默认值。
- [ ] 检查不跨越失败帧或大 gap。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后勾选成功标准，追加执行摘要，并将本文件归档到：

```text
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/
```

