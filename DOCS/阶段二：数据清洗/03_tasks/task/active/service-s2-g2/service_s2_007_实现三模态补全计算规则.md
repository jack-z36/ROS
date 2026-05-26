# L3 微元任务：实现三模态补全计算规则

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：数据补全器
L3 编号：service_s2_007
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_007_实现三模态补全计算规则.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_007
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_007_实现三模态补全计算规则.md
  group: service-s2-g2
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g2-p3
  depends_on: [service_s2_006]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_008]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [repair.pose, repair.tactile, repair.gripper]
  dispatch_status: ready
```

## 3. 本次目标

```text
基于 repair run 和合法邻居实现 pose、tactile、gripper 三模态补全计算，并输出 SignalRepairResult。
```

## 4. 本次不做

- 不重新发现异常。
- 不接入开发者入口。
- 不写 MCAP_A。

## 5. 执行对象

- position 线性插值。
- orientation SLERP。
- gripper 线性插值与 clamp。
- tactile 整帧矩阵逐元素线性插值。
- hold/copy nearest。
- [[SignalRepairResult]] 聚合输出。

## 6. 执行依赖

- `service_s2_006` 已完成并归档。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：repair run 聚合与合法邻居查找
上游接口定义位置：service_s2_006 完成记录、SignalRepairRun.md
当前 L3 期望消费的字段 / 文件 / 返回值：repair run、previous_neighbor_ref、next_neighbor_ref、SignalRepairPolicyConfig
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报
```

## 8. 预期改动形态

- service 层出现三模态补全计算函数。
- 输出保持原始时间戳、排序和样本数不变。
- 测试覆盖 pose/gripper/tactile 和拒绝策略。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| pose.position 可插值 | 按 timestamp 比例线性插值 | repaired sample record | `linear_interpolate` |
| pose.orientation 可插值 | 使用 SLERP 并归一化 | repaired sample record | `slerp_interpolate` |
| gripper 可插值 | 线性插值并 clamp `[0,1]` | repaired sample record | `linear_interpolate` |
| tactile 可插值 | shape 一致时整帧逐元素线性插值 | repaired sample record 摘要 | `linear_interpolate` |
| repairable_hold | 复制最近合法邻居 | repaired sample record | `copy_nearest` |
| 插值缺邻居 | fallback 关闭则拒绝 | unrepaired run | `missing_neighbor` |

## 10. 数据计算验收重点

- `repairable_hold` 不得升级为插值。
- orientation 不得用四元数分量线性插值。
- tactile 不做单 cell 修复。
- `sample_count_before == sample_count_after`。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/RepairMethod.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_006_实现repair_run聚合与合法邻居查找.md`

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

- 禁止重新做异常检测。
- 禁止新增/删除/重采样消息。
- 禁止写 MCAP_A。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [ ] pose.position 使用线性插值。
- [ ] pose.orientation 使用 SLERP。
- [ ] gripper 修复后 clamp 到 `[0,1]`。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/`。

