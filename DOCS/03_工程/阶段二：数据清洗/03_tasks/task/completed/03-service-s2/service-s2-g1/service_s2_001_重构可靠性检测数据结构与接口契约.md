# L3 微元任务：重构可靠性检测数据结构与接口契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：异常值检测器
L3 编号：service_s2_001
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_001_重构可靠性检测数据结构与接口契约.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_001
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_001_重构可靠性检测数据结构与接口契约.md
  group: service-s2-g1
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g1-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_002, service_s2_003, service_s2_004, service_s2_005]
  conflict_scope:
    files:
      - src/data_clean/schemas/
      - src/data_clean/tests/
      - DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/
    modules: [data_clean.schemas]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
定义并落地异常检测器点级主接口，使下游数据补全器可以消费 SignalReliabilityDetectionResult.sample_issues。
```

## 4. 本次不做

- 不实现异常检测算法。
- 不实现数据补全器。
- 不接入开发者入口。

## 5. 执行对象

- [[SignalSampleRef]]
- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[ReliabilityIssueGroup]]
- [[SignalReliabilityDetectionResult]]
- 旧 [[IssueTimeSegment]] 迁移说明

## 6. 执行依赖

- 场景二 L2 数据定义已存在。
- 异常值检测器 L2 已改为样本级主接口。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：场景一 cleaned MCAP 契约
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CleanedMcap.md
当前 L3 期望消费的字段 / 文件 / 返回值：topic、时间戳、message_index、三模态样本语义
是否存在接口冲突：无；本 L3 只定义场景二内部检测结果接口
如果有冲突，本次处理策略：停止并回报，不修改场景一契约
```

## 8. 预期改动形态

- 源码中出现可 import 的检测结果类型或 schema。
- 文档中的样本级接口与代码类型字段一致。
- 旧时间段主接口不再作为新代码主输入。

## 9. 数据定义输出

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `SignalSampleRef` | dataclass / TypedDict / schema | `src/data_clean/schemas/` 或同等 schema 层 | 异常检测器、数据补全器 |
| `SampleReliabilityIssue` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 数据补全器 |
| `MissingIntervalIssue` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 数据补全器、报告生成器 |
| `ReliabilityIssueGroup` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 开发者入口、报告生成器 |
| `SignalReliabilityDetectionResult` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 数据补全器、开发者入口 |

## 10. 数据定义验收重点

- 能被 `python3` import。
- 能实例化并序列化包含 sample issue、missing interval 和 issue group 的结果。
- 字段名与 L2 数据定义一致。
- `SignalReliabilityIssue` 不再作为混合式主结构出现在新类型中。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalReliabilityDetectionResult.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/SampleReliabilityIssue.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/MissingIntervalIssue.md`

### 必读相关微元任务记录

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

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

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/schemas/`
3. `src/data_clean/tests/`

## 12. TDD 执行要求

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd`。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_signal_reliability_detect` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否；由后续入口 L3 写 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 由 `scene2_signal_reliability_detect` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现异常检测算法。
- 禁止实现数据补全器。
- 禁止修改场景一接口契约。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [x] 检测结果相关类型可 import。
- [x] 类型能表达 sample issue、missing interval、issue group 和 detection result。
- [x] 测试覆盖旧 `IssueTimeSegment` 不作为新主接口。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后将当前 L3 移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/`。如果 active 功能组为空，删除空目录。不写共享执行记录。

## 19. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_001_重构可靠性检测数据结构与接口契约.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_001_重构可靠性检测数据结构与接口契约.md
文件名编号：service_s2_001
正文 L3 编号：service_s2_001
dispatch.task_id：service_s2_001
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。
- 相关 L3 历史记录：未找到相关 L3 历史记录；同功能组当前仍有 `service_s2_002`、`service_s2_003`、`service_s2_004` 待后续执行。

### 本次修改文件

- `src/data_clean/schemas/reliability.py`：新增场景二可靠性检测结果 dataclass 与枚举契约。
- `src/data_clean/schemas/__init__.py`：导出新增可靠性检测类型。
- `src/data_clean/tests/service/test_reliability_schemas.py`：新增导入、实例化、序列化和旧 `IssueTimeSegment` 非主接口测试。
- `src/data_clean/data_clean_architecture.md`：登记新增 `schemas/reliability.py`。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/service/test_reliability_schemas.py`，运行 `python3 -m pytest src/data_clean/tests/service/test_reliability_schemas.py -q`，按预期因 `ModuleNotFoundError: No module named 'schemas.reliability'` 失败。
- Green：新增 `SignalSampleRef`、`IssueSeverity`、`IssueType`、`AnomalySource`、`SampleReliabilityIssue`、`MissingIntervalIssue`、`ReliabilityIssueGroup`、`SignalReliabilityDetectionResult`，并导出公共类型后，目标测试通过。
- Refactor：补充架构文档目录表，使用 `python3 -m py_compile` 检查新增/改动 Python 文件。

### 验证结果

- `python3 -m pytest src/data_clean/tests/service/test_reliability_schemas.py -q`：通过，`3 passed`。
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest src/data_clean/tests/service/test_reliability_schemas.py -q`：通过，`3 passed`。
- `python3 -m py_compile src/data_clean/schemas/reliability.py src/data_clean/schemas/__init__.py src/data_clean/tests/service/test_reliability_schemas.py`：通过。
- 手动接口验证：通过 `schemas.reliability.SignalReliabilityDetectionResult` 实例化并 `dataclasses.asdict` 输出嵌套字典。
- `python3 -m pytest src/data_clean/tests -q`：未通过，失败发生在测试收集期的既有非本 L3 接口缺口，包括 `repo.config.mcap_process_config.ExtrinsicConfig`、`service.gripper_width.build_gripper_samples`、`runtime.run_context_directory`、`config.runtime_config_loader`、`ui.dev_menu` 等缺失；本 L3 不允许修改场景一接口、开发者菜单或无关 Runtime 文件，故未在本任务内修复。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准核对

- 已验证检测结果相关类型可通过 `from schemas.reliability import ...` 导入。
- 已验证类型能表达 sample issue、missing interval、issue group 和 detection result。
- 已验证测试覆盖旧 `IssueTimeSegment` 不作为新主接口。
- 已说明本 L3 不直接修改 `./start_data_clean.sh --dev`；后续由场景二 `scene2_signal_reliability_detect` 功能检验项间接覆盖，最终人工验收仍建议用户运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_signal_reliability_detect`。

### 本次明确未做

- 未实现异常检测算法。
- 未实现数据补全器或数据修复。
- 未修改开发者入口、菜单、脚本调用或场景一契约。
- 未修改调度索引、共享执行记录、阶段进度或总执行日志。

### 风险与后续建议

- 全量 `src/data_clean/tests` 当前存在多处与本 L3 无关的收集期失败，需要后续对应 L3 或维护任务修复。
- 枚举值覆盖了当前 L2 文档列出的异常类型；后续规则 L3 如新增异常类型，应同步扩展 `IssueType` 并补测试。
- 建议后续完成场景二全链路后，由用户通过 `./start_data_clean.sh --dev` 选择场景二 `scene2_signal_reliability_detect` 做最终人工验收。
