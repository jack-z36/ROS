# L3 微元任务：定义位姿滤波器配置输入审计记录和结果类型

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：位姿滤波器
L3 编号：service_s2_009
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_009
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md
  group: service-s2-g3
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g3-p1
  depends_on: [service_s2_005]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_010, service_s2_011, service_s2_012]
  conflict_scope:
    files: [src/data_clean/schemas/, src/data_clean/tests/, DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/]
    modules: [data_clean.schemas]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
定义位姿滤波器的配置、输入序列、样本级审计、片段摘要和聚合结果类型。
```

## 4. 本次不做

- 不实现分段算法。
- 不实现 Savitzky-Golay 计算。
- 不接入开发者入口。

## 5. 执行对象

- [[PoseFilterConfig]]
- [[PoseFilterInputSequence]]
- [[PoseFilterSampleRecord]]
- [[PoseFilterSegmentSummary]]
- [[PoseFilterResult]]

## 6. 执行依赖

- `service_s2_005` 已完成并归档，[[SignalRepairResult]] 等补全结果类型已经落地。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器类型定义
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md、SignalRepairResult.md、SignalRepairRun.md、SignalRepairSampleRecord.md
当前 L3 期望消费的字段 / 文件 / 返回值：SignalRepairResult.output_sequence_refs、timestamp_policy、repair_runs、unhandled_missing_interval_records
是否存在接口冲突：无；output_sequence_refs 的具体 artifact 格式仍未固化
如果有冲突，本次处理策略：只定义 PoseFilterInputSequence 语义接口，不猜测 artifact 物理格式
```

## 8. 预期改动形态

- 源码中出现可 import 的位姿滤波配置和结果类型。
- 测试能实例化默认 `PoseFilterConfig`、样本级记录和聚合结果。
- 文档原子定义与源码类型字段保持一致。

## 9. 数据定义输出

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `PoseFilterConfig` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 位姿滤波器 |
| `PoseFilterInputSequence` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 位姿滤波器 |
| `PoseFilterSampleRecord` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 报告生成器 |
| `PoseFilterSegmentSummary` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 位姿滤波器、报告生成器 |
| `PoseFilterResult` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | MCAP_A 生成器、报告生成器 |

## 10. 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `algorithm` | enum string | 滤波算法 | `savgol` | v1 只允许 `savgol` |
| `window_duration_ms` | number | 对外时间窗口 | `200` | 有限正数 |
| `polyorder` | integer | Savitzky-Golay 阶数 | `2` | 非负整数 |
| `position_guard_max_delta_m` | number | 位置 guard | `0.02` | 有限非负数 |
| `orientation_guard_max_delta_deg` | number | 姿态 guard | `5` | 有限非负数 |
| `status` | enum string | 样本处理状态 | 无 | `filtered` / `kept_original` / `skipped_boundary` / `filter_rejected_by_guard` |
| `timestamp_policy` | enum string | 时间戳策略 | `preserve_original` | 只能保持原时间结构 |

## 11. 数据定义验收重点

- 能被 import。
- 默认配置能表达 200ms/order2、2cm/5deg guard。
- `PoseFilterResult` 能引用 [[SignalRepairResult]]，并表达 `sample_count_before == sample_count_after`。
- 样本记录能表达 guard 拒绝时的原值、候选滤波值和最终原值。

## 12. 现有程序盘点

- `src/data_clean/schemas/` 已有 Runtime 和基础 schema 类型；尚未发现位姿滤波器类型。
- `src/data_clean/service/` 目前有场景一清洗、位姿转换和校验服务；尚未发现 `pose_filter` 实现。
- 本 L3 是在现有分层上新增 schema/types，不重写既有场景一位姿转换。

## 13. 本 L3 的真实改造边界

- 允许新增位姿滤波器相关 schema/types 和对应测试。
- 允许更新 `src/data_clean/data_clean_architecture.md` 中的目录结构说明。
- 禁止实现滤波算法或开发者入口。
- 禁止修改 [[SignalRepairResult]] 的既有语义，除非发现字段名与已归档上游 L3 不一致并先暂停汇报。

## 14. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterResult.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairResult.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`

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

1. `src/data_clean/schemas/`
2. `src/data_clean/tests/`
3. `src/data_clean/data_clean_architecture.md`

## 15. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 16. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_pose_filter` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 不直接接入开发者入口，但由 `scene2_pose_filter` 间接覆盖 |

## 17. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 18. 禁止修改

- 禁止实现位姿滤波算法。
- 禁止修改数据补全器算法。
- 禁止修改开发者入口。

## 19. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 20. 成功标准

- [x] 位姿滤波相关类型可 import。
- [x] 默认配置能表达 200ms/order2 与 2cm/5deg guard。
- [x] `PoseFilterResult` 能引用补全结果和输出序列。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 21. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。

## 22. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md
文件名编号：service_s2_009
正文 L3 编号：service_s2_009
dispatch.task_id：service_s2_009
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`，确认可复用 `SignalRepairResult`、`SignalRepairRun`、`SignalRepairSampleRecord` 和 `output_sequence_refs` / `timestamp_policy` / sample count 语义。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/pose_filter.py`：新增 `PoseFilterAlgorithm`、`PoseFilterSampleStatus`、`PoseFilterConfig`、`PoseFilterInputSequence`、`PoseFilterSampleRecord`、`PoseFilterSegmentSummary`、`PoseFilterResult`。
- `src/data_clean/schemas/__init__.py`：导出位姿滤波 schema 公共类型。
- `src/data_clean/tests/service/test_pose_filter_schemas.py`：新增默认配置、全类型实例化、guard 拒绝样本记录、sample count 不变测试。
- `src/data_clean/data_clean_architecture.md`：登记新增 `schemas/pose_filter.py`。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/service/test_pose_filter_schemas.py`，运行 `python3 -m pytest src/data_clean/tests/service/test_pose_filter_schemas.py -q`，按预期因 `ModuleNotFoundError: No module named 'schemas.pose_filter'` 失败。
- Green：新增位姿滤波枚举和 dataclass，并在 `schemas.__init__` 导出后，目标测试通过。
- Refactor：补充架构文档目录表，并运行 `python3 -m py_compile` 与手动导入检查确认新增公共接口可用。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_pose_filter_schemas.py -q`：通过，`4 passed`。
- `python3 -m pytest src/data_clean/tests/service/test_pose_filter_schemas.py -v`：通过，4 个测试全部 PASSED。
- `python3 -m py_compile src/data_clean/schemas/pose_filter.py src/data_clean/schemas/__init__.py src/data_clean/tests/service/test_pose_filter_schemas.py`：通过。
- 手动接口验证：通过 `PYTHONPATH=src/data_clean python3 -c ...` 从 `schemas` 导入 `PoseFilterConfig`、`PoseFilterResult`、`PoseFilterAlgorithm`，实例化 `PoseFilterResult` 并验证 `sample_count_before == sample_count_after`。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准核对

- 已验证位姿滤波相关类型可通过 `from schemas.pose_filter import ...` 和 `from schemas import ...` 导入。
- 已验证默认 `PoseFilterConfig` 表达 `window_duration_ms=200`、`polyorder=2`、`position_guard_max_delta_m=0.02`、`orientation_guard_max_delta_deg=5`、`timestamp_policy=preserve_original`。
- 已验证 `PoseFilterResult.input_repair_result_ref` 可引用 `SignalRepairResult`，并通过 `output_sequence_refs` 保存滤波后序列引用，不承载完整 MCAP。
- 本 L3 不直接修改 `./start_data_clean.sh --dev`；后续由场景二 `scene2_pose_filter` 功能检验项和场景完整 smoke test 间接覆盖。建议用户在场景二位姿滤波链路完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_pose_filter` 做最终人工验收。

### 本次明确未做

- 未实现分段算法。
- 未实现 Savitzky-Golay 计算、位置滤波、姿态滤波或 guard 判定算法。
- 未修改开发者入口、菜单、脚本调用、调度索引、共享执行记录、阶段进度或总执行日志。

### 风险与后续建议

- 当前环境缺少 `basedpyright-langserver`，无法取得 LSP diagnostics；已用目标 pytest、`py_compile` 和手动导入覆盖本 L3 的可观察接口。
- 建议后续 `service_s2_010` 基于 `PoseFilterInputSequence`、`PoseFilterSegmentSummary` 和 `SignalRepairResult.unhandled_missing_interval_records` 实现可靠片段切分与窗口换算。
