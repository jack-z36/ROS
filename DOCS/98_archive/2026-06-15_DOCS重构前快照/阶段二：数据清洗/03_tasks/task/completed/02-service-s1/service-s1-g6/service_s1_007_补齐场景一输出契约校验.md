# L3 微元任务：补齐场景一输出契约校验

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
L2 能力：基础校验与输出契约检查
L3 编号：service_s1_007
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g6/service_s1_007_补齐场景一输出契约校验.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/基础校验与输出契约检查.md`

## 2. 本次目标

```text
补齐场景一输出 contract validator，并定义 scene1_output_contract_validate 与 scene1_smoke_test 的 dev 验收产物。
```

## 3. 本次不做

- 不实现 gripper 算法。
- 不实现 pose 算法。
- 不实现统一 `--dev` 一级入口。

## 4. 执行对象

- `src/data_clean/service/validator.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/runtime/`
- [[Scene1CleanReport]]
- [[Scene1DevRunLog]]

## 5. 执行依赖

- g2-g5 输出或 fixture 能提供配置、gripper 和 pose 统计。
- 现有 `FileProcessingReport`、`PoseTopicStats`、`GripperTopicStats` 可作为基础。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：g2 夹爪配置、g3 gripper 输出、g4 frame_alignment、g5 common pose 输出
上游接口定义位置：对应 L2 数据定义与 L3 任务文件
当前 L3 期望消费的字段 / 文件 / 返回值：config_path、raw_pose_count、camera_common_pose_count、tcp_common_pose_count、image_frame_count、gripper_count、failure_reason
是否存在接口冲突：若上游尚未完成，使用 fixture 或 mock 统计对象覆盖 validator 行为
如果有冲突，本次处理策略：只做校验和报告，不反向改算法
```

## 7. 预期改动形态

- 输出 contract validator 能定位 topic、schema、配置和数量错误。
- RAW_JSON 或报告摘要可表达 dev smoke test 结果。
- `scene1_smoke_test` 产物契约明确，但不实现统一 dev 入口。

## 8. 现有程序盘点

- `validator.py` 已有 input inventory 校验、gripper topic 冲突检查和数量检查。
- `mcap_io.py` 已生成 `FileProcessingReport`，包含 pose/gripper stats。
- `runtime/mcap_clean_launcher.py` 已有 dry-run、latest、all、calibrate 等生产/交互入口，但没有 `--dev`。

## 9. 本 L3 的真实改造边界

- 只补 validator/report/dev smoke 产物契约。
- 不改 gripper 或 pose 计算。
- 不实现 `start_data_clean.sh --dev` 总入口。

## 10. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | topic 存在、数量一致、配置来源明确 | contract pass | 无 |
| 缺失输入 | pose/image/config 缺失 | contract fail | missing configured ... |
| 边界输入 | gripper/topic/pose 数量不一致 | contract fail | count mismatch |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `status` | enum | 校验状态 | `success/failed/skipped` |
| `failure_reason` | string/null | 失败原因 | failed 时非空 |
| `artifacts` | list | dev 测试产物 | 可定位 |
| `run_log` | object | dev 运行日志 | 可解析 |

## 11. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 12. 开发者验收入口

`./start_data_clean.sh --dev -> 场景一 -> scene1_output_contract_validate`

`./start_data_clean.sh --dev -> 场景一 -> scene1_smoke_test`

测试产物：`artifacts/output_contract_report.json`、`artifacts/smoke_summary.json`、可选 `artifacts/debug_cleaned.mcap`、`logs/run_log.json`。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/基础校验与输出契约检查.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1CleanReport.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevRunLog.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g3/service_s1_003_实现夹爪宽度提取输出契约.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g5/service_s1_006_实现common_frame位姿转换输出.md`

如果没有找到已完成相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3任务文件身份校验约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`
5. `DOCS/阶段二：数据清洗/约束文件/L3功能组目录约束.md`
6. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
7. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
8. `DOCS/阶段二：数据清洗/约束文件/L3现有实现盘点约束.md`
9. `DOCS/阶段二：数据清洗/02_service/场景一/执行约束.md`

### 必读代码

1. `src/data_clean/service/validator.py`
2. `src/data_clean/service/mcap_io.py`
3. `src/data_clean/runtime/`

## 14. TDD 执行要求

执行前必须先完成 L3 任务文件身份校验。本 L3 涉及代码行为变更，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 15. 允许修改

- `src/data_clean/service/validator.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/runtime/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 16. 禁止修改

- 禁止修改 gripper 或 pose 计算算法。
- 禁止实现统一 `--dev` 一级入口。
- 禁止写共享执行记录。

## 17. 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

## 18. 成功标准

- [x] 合法输出 contract 通过。
- [x] pose 数量不一致会失败。
- [x] gripper 数量不一致会失败。
- [x] topic 冲突会失败。
- [x] `scene1_smoke_test` 产物和日志契约明确。

## 19. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g6/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。

## 20. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g6/service_s1_007_补齐场景一输出契约校验.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g6/service_s1_007_补齐场景一输出契约校验.md
文件名编号：service_s1_007
正文 L3 编号：service_s1_007
校验结论：通过
```

### 相关 L3 历史记录

- 读取了 `service_s1_003_实现夹爪宽度提取输出契约.md`（completed/02-service-s1/service-s1-g3/），确认 gripper validator 测试已补齐。
- 读取了 `service_s1_006_实现common_frame位姿转换输出.md`（active/service-s1-g5/），确认 pose 转换逻辑已实现。
- 读取了已完成的 `service_s1_001_稳定cleaned_MCAP接口契约.md`、`service_s1_004_落地frame_alignment配置契约.md`、`service_s1_005_改造位姿转换配置生成器.md`。

### TDD 执行过程

采用垂直切片 TDD：

1. **RED→GREEN**: 写 `Scene1ContractResult` dataclass 和 `scene1_output_contract_validate` 函数 → 合法输入返回 success
2. **RED→GREEN**: 写 pose 数量不一致测试 → 返回 failed 且 failure_reason 包含 count mismatch
3. **RED→GREEN**: 写 gripper 数量不一致测试 → 返回 failed 且 run_log 显示 gripper check fail
4. **RED→GREEN**: 写 output topic count 不一致测试 → 返回 failed
5. **RED→GREEN**: 写 processing failed 传播测试 → report.status=failed 时 contract result 也 failed
6. **RED→GREEN**: 写 `write_scene1_contract_report` 文件写出测试 → 产出合法 JSON
7. **RED→GREEN**: 写 `write_scene1_smoke_summary` 文件写出测试 → 包含 processing_report 和 contract_result
8. **RED→GREEN**: 写 contract 层输出结构测试 → status 枚举、failure_reason 类型、artifacts 列表、run_log 字典、to_dict JSON 可序列化、checks 包含所有检查项
9. **Refactor**: 无，实现简洁直接

### 实际修改文件

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `src/data_clean/service/validator.py` | 修改 | 新增 `Scene1ContractResult` dataclass、`scene1_output_contract_validate`、`write_scene1_contract_report`、`write_scene1_smoke_summary` |
| `src/data_clean/tests/service/test_scene1_contract_validator.py` | 新增 | 11 个 service 层测试：合法输入、pose 不一致、gripper 不一致、topic count 不一致、processing failed 传播、文件写出 |
| `src/data_clean/tests/contract/test_scene1_output_contract.py` | 新增 | 17 个 contract 层测试：输出结构字段、类型校验、to_dict 序列化、下游可消费性 |

### 新增/修改函数

- `Scene1ContractResult` dataclass：status、failure_reason、artifacts、run_log 字段 + to_dict
- `scene1_output_contract_validate(report, config)` → Scene1ContractResult：校验 raw pose retention、gripper frame count、output topic count、config traceability
- `write_scene1_contract_report(result, output_dir)` → Path：写出 output_contract_report.json
- `write_scene1_smoke_summary(report, contract_result, output_dir)` → Path：写出 smoke_summary.json

### 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

结果：service 63 passed，contract 34 passed，总计 97 passed。

### 成功标准勾选

- [x] 合法输出 contract 通过 → `test_valid_contract_returns_success` 验证 status=success, failure_reason=None
- [x] pose 数量不一致会失败 → `test_pose_output_mismatch_returns_failed` + contract 层 `test_checks_include_raw_pose_retention` 验证
- [x] gripper 数量不一致会失败 → `test_gripper_mismatch_returns_failed` + contract 层 `test_checks_include_gripper_frame_count` 验证
- [x] topic 冲突会失败 → 现有 `validate_input_inventory` 在 g3 中已覆盖 output topic conflict，本 L3 的 `test_output_topic_count_mismatch_returns_failed` 覆盖输出侧 topic count 不一致
- [x] `scene1_smoke_test` 产物和日志契约明确 → `write_scene1_contract_report` 产出 `output_contract_report.json`，`write_scene1_smoke_summary` 产出 `smoke_summary.json`，`run_log` 包含 check_type、input_file、output_file、checks 列表

### 对 ./start_data_clean.sh --dev 的影响

本 L3 为 `./start_data_clean.sh --dev -> 场景一` 下的两个功能检验项补齐了实现：
- `scene1_output_contract_validate`：对已有或调试生成的场景一输出执行 contract validator，产出 `output_contract_report.json`
- `scene1_smoke_test`：结合 processing report 和 contract result 产出 `smoke_summary.json`

产物契约：
- `artifacts/output_contract_report.json`：包含 status、failure_reason、artifacts、run_log（含逐检查项结果）
- `artifacts/smoke_summary.json`：包含 processing_report + contract_result
- `logs/run_log.json`：通过 run_log 字段承载，可解析

### 本次没做

- 不实现 gripper 算法（g3 范围）
- 不实现 pose 算法（g5 范围）
- 不实现统一 `--dev` 一级入口
- 不修改 gripper 或 pose 计算

### 后续建议

- 用户后续运行 `./start_data_clean.sh --dev` 选择 `scene1_output_contract_validate` 或 `scene1_smoke_test` 时，需将 `scene1_output_contract_validate`、`write_scene1_contract_report`、`write_scene1_smoke_summary` 集成到 dev run 流程中
- 建议在场景一全部 L3 完成后用真实 MCAP 做端到端 smoke test 验证
