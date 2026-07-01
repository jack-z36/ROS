# L3 微元任务：实现触觉样本级异常检测规则骨架

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：异常值检测器
L3 编号：service_s2_003
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_003_实现触觉样本级异常检测规则骨架.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_003
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_003_实现触觉样本级异常检测规则骨架.md
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

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/TactilePressureFrame.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/SampleReliabilityIssue.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/service_s2_001_重构可靠性检测数据结构与接口契约.md`

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

- [x] 触觉合法帧不产生 issue。
- [x] shape mismatch 产生 sample issue。
- [x] 触觉尖峰或全零样例产生 sample issue。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/`。

## 19. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_003_实现触觉样本级异常检测规则骨架.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_003_实现触觉样本级异常检测规则骨架.md
文件名编号：service_s2_003
正文 L3 编号：service_s2_003
dispatch.task_id：service_s2_003
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`；依赖 `service_s2_001` 已在 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/` 归档。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。
- 相关 L3 记录：已读取归档的 `service_s2_001` 与同功能组归档的 `service_s2_002`；同功能组 active 目录仍保留 `service_s2_004`。

### 本次修改文件

- `src/data_clean/service/detectors.py`：新增 `TactilePressureFrame`、触觉相关 `ReliabilityDetectionConfig` 字段、`detect_tactile_reliability()`，实现 shape、相邻帧尖峰、饱和、全零可疑和 timestamp gap 检测，输出 `SignalReliabilityDetectionResult`。
- `src/data_clean/tests/service/test_tactile_detectors.py`：新增合法触觉帧、shape mismatch、尖峰、全零和 timestamp gap 行为测试。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/service/test_tactile_detectors.py` 的合法触觉帧公共接口测试，运行 `PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/service/test_tactile_detectors.py -q`，按预期因 `ImportError: cannot import name 'TactilePressureFrame' from 'service.detectors'` 失败。
- Green：在 `service.detectors` 中新增触觉帧 dataclass、触觉检测入口和最小结果汇总后，单条 tracer bullet 测试通过。
- Refactor / 扩展行为：补齐 shape mismatch、相邻帧平均绝对差尖峰、零值比例持续、饱和值比例持续、timestamp gap 检测，并将触觉 ratio-run 判断收敛到私有辅助函数；目标测试通过。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_tactile_detectors.py -v`：通过，`5 passed`。
- `python3 -m pytest src/data_clean/tests/service/test_pose_gripper_detectors.py src/data_clean/tests/service/test_tactile_detectors.py -q`：通过，`10 passed`。
- `python3 -m py_compile src/data_clean/service/detectors.py src/data_clean/tests/service/test_tactile_detectors.py`：通过。
- 手动接口验证：通过 `PYTHONPATH=src/data_clean python3` 驱动脚本构造合成 `TactilePressureFrame` 序列并调用 `detect_tactile_reliability()`，观察到返回 `SignalReliabilityDetectionResult`，尖峰进入 `sample_issues`，时间缺口进入 `missing_interval_issues`。
- LSP diagnostics：当前环境缺少 `basedpyright-langserver`，无法提供 Python LSP 诊断；已用 `py_compile`、目标 pytest、相邻 detector 回归测试和手动驱动替代验证语法与行为。

### 成功标准核对

- 已验证合法触觉帧序列不产生 `sample_issues` 或 `missing_interval_issues`。
- 已验证 `rows * cols != len(data)` 产生 `SampleReliabilityIssue`，`issue_type=tactile_shape_mismatch`，`field_path=tactile.frame`。
- 已验证相邻帧统计突变产生 `SampleReliabilityIssue`，`issue_type=tactile_spike`；已验证全零帧产生 `SampleReliabilityIssue`，`issue_type=tactile_zero_suspicious`。
- 已说明本 L3 不直接修改 `./start_data_clean.sh --dev`；后续由场景二 `scene2_signal_reliability_detect` 功能检验项间接覆盖，最终人工验收仍建议用户运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_signal_reliability_detect`。

### 本次明确未做

- 未实现位姿或夹爪规则。
- 未实现触觉补全、数据修复或 MCAP 改写。
- 未修改开发者入口、菜单、脚本调用、调度索引、共享执行记录、阶段进度或总执行日志。

### 风险与后续建议

- 触觉物理单位和真实硬件饱和值仍按 L2 文档保留为后续调参问题；本 L3 只提供可配置规则骨架和合成样本验收。
- 建议后续完成 `service_s2_004` 接入后，由用户通过 `./start_data_clean.sh --dev` 选择场景二 `scene2_signal_reliability_detect` 做最终人工验收。
