# L3 微元任务：实现触觉样本级异常检测规则骨架

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：异常值检测器
L3 编号：service_s2_003
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_003_实现触觉样本级异常检测规则骨架.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_003
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_003_实现触觉样本级异常检测规则骨架.md
  group: service-s2-g1
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g1-p2
  depends_on: [service_s2_001]
  must_run_after: []
  can_run_parallel_with: [service_s2_002]
  blocks: [service_s2_004]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [reliability.tactile]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现触觉帧的样本级异常检测规则骨架，覆盖 shape、尖峰、饱和和全零可疑样本。
```

## 4. 本次不做

- 不实现位姿和夹爪规则。
- 不实现触觉补全。
- 不接入开发者入口。

## 5. 执行对象

- [[TactilePressureFrame]]
- 触觉 `rows/cols/data` shape 检查。
- 触觉尖峰、突变、饱和、全零可疑规则。

## 6. 执行依赖

- `service_s2_001` 已完成并归档。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：阶段一触觉消息契约、service_s2_001 数据结构
上游接口定义位置：TactilePressureFrame.md、SignalReliabilityDetectionResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：rows、cols、data、timestamp、message_index
是否存在接口冲突：触觉物理单位和饱和阈值仍未知
如果有冲突，本次处理策略：实现结构、相对突变、全零和可配置阈值骨架，不写死生产阈值
```

## 8. 预期改动形态

- service 层出现可测试的触觉异常检测函数或类。
- 测试能构造触觉 shape 异常、尖峰和全零样例。

## 9. 计算输出

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法触觉帧 | shape 正常、值有限、无突变 | 空 `sample_issues` | 无 |
| shape 不一致 | `rows * cols != len(data)` | [[SampleReliabilityIssue]] | `tactile_shape_mismatch` |
| 矩阵尖峰 | 相邻帧统计差异超过阈值 | [[SampleReliabilityIssue]] | `tactile_spike` |
| 大面积全零 | 零值比例和持续时间超过阈值 | [[SampleReliabilityIssue]] 或 group | `tactile_zero_suspicious` |

## 10. 数据计算验收重点

- 合法触觉帧通过。
- shape 异常必定输出 sample issue。
- 输出 `field_path=tactile.frame`。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/TactilePressureFrame.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SampleReliabilityIssue.md`

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

- 禁止实现位姿/夹爪规则。
- 禁止实现补全。
- 禁止修改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [ ] 触觉合法帧不产生 issue。
- [ ] shape mismatch 产生 sample issue。
- [ ] 触觉尖峰或全零样例产生 sample issue。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/`。

