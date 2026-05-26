# L3 微元任务：实现位姿和夹爪样本级异常检测规则骨架

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：异常值检测器
L3 编号：service_s2_002
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_002_实现位姿和夹爪样本级异常检测规则骨架.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_002
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_002_实现位姿和夹爪样本级异常检测规则骨架.md
  group: service-s2-g1
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g1-p2
  depends_on: [service_s2_001]
  must_run_after: []
  can_run_parallel_with: [service_s2_003]
  blocks: [service_s2_004]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [reliability.pose, reliability.gripper]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现位姿和夹爪的样本级异常检测规则骨架，输出 SampleReliabilityIssue 与 MissingIntervalIssue。
```

## 4. 本次不做

- 不实现触觉规则。
- 不做数据补全。
- 不接入开发者入口。

## 5. 执行对象

- 位姿 topic 的时间、非法值、跳变、四元数异常规则。
- 夹爪 topic 的值域、跳变、卡死规则。

## 6. 执行依赖

- `service_s2_001` 已完成并归档。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景一 cleaned MCAP 契约、service_s2_001 数据结构
上游接口定义位置：CleanedMcap.md、CommonFrameTcpPose.md、GripperWidthSample.md、SignalReliabilityDetectionResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：pose 样本、gripper 样本、检测配置、检测结果类型
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报，不自行改上游契约
```

## 8. 预期改动形态

- service 层出现可测试的位姿/夹爪异常检测函数或类。
- 测试能构造合成序列并断言样本级问题。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法 pose/gripper | 无非法值、无跳变、时间连续 | 空 `sample_issues` | 无 |
| 缺失间隔 | 相邻 timestamp 间隔超过阈值 | [[MissingIntervalIssue]] | `missing_segment` |
| pose 四元数异常 | 非有限或范数偏离阈值 | [[SampleReliabilityIssue]] | `invalid_orientation` |
| gripper 越界 | value 超出 `[0,1]` | [[SampleReliabilityIssue]] | `gripper_out_of_range` |

## 10. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入生成正确 issue。
- 输出结构可被补全器直接消费。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SampleReliabilityIssue.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/MissingIntervalIssue.md`

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
| 对应功能检验项 | `scene2_signal_reliability_detect` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由后续入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 由 `scene2_signal_reliability_detect` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现触觉检测。
- 禁止实现补全。
- 禁止修改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [ ] 位姿合法样本不产生 issue。
- [ ] 位姿四元数异常产生 sample issue。
- [ ] 夹爪越界产生 sample issue。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/`。

