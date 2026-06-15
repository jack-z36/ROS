# L3 微元任务：定义触觉滤波器配置输入审计记录和结果类型

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：触觉滤波器
L3 编号：service_s2_013
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_013
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md
  group: service-s2-g4
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g4-p1
  depends_on: [service_s2_005]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_014, service_s2_015, service_s2_016]
  conflict_scope:
    files: [src/data_clean/schemas/, src/data_clean/tests/, DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/]
    modules: [data_clean.schemas]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
定义触觉滤波器的配置、输入序列、样本级审计、片段摘要和聚合结果类型。
```

## 4. 本次不做

- 不实现片段切分。
- 不实现中值 + EMA 滤波计算。
- 不接入开发者入口。

## 5. 执行对象

- [[TactileFilterConfig]]
- [[TactileFilterInputSequence]]
- [[TactileFilterSampleRecord]]
- [[TactileFilterSegmentSummary]]
- [[TactileFilterResult]]

## 6. 执行依赖

- `service_s2_005` 已完成并归档，[[SignalRepairResult]] 等补全结果类型已经落地。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器类型定义
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md、SignalRepairResult.md、SignalRepairRun.md、SignalRepairSampleRecord.md
当前 L3 期望消费的字段 / 文件 / 返回值：SignalRepairResult.output_sequence_refs、timestamp_policy、repair_runs、unhandled_missing_interval_records
是否存在接口冲突：无；output_sequence_refs 的具体 artifact 格式仍未固化
如果有冲突，本次处理策略：只定义 TactileFilterInputSequence 语义接口，不猜测 artifact 物理格式
```

## 8. 预期改动形态

- 源码中出现可 import 的触觉滤波配置和结果类型。
- 测试能实例化默认 `TactileFilterConfig`、样本级记录和聚合结果。
- 文档原子定义与源码类型字段保持一致。

## 9. 数据定义输出

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `TactileFilterConfig` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 触觉滤波器 |
| `TactileFilterInputSequence` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 触觉滤波器 |
| `TactileFilterSampleRecord` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 报告生成器 |
| `TactileFilterSegmentSummary` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | 触觉滤波器、报告生成器 |
| `TactileFilterResult` | dataclass / TypedDict / schema | `src/data_clean/schemas/` | MCAP_A 生成器、报告生成器 |

## 10. 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `algorithm` | enum string | 滤波算法 | `median_ema` | v1 只允许 `median_ema` |
| `median_window` | integer | 逐 cell 中值窗口 | `3` | 大于等于 3 的奇数 |
| `ema_alpha` | number | EMA 权重 | `0.35` | `(0, 1]` |
| `contact_reset_threshold` | number/null | 接触变化 reset 阈值 | null / 测试固定值 | 有限非负数或 null |
| `timestamp_policy` | enum string | 时间戳策略 | `preserve_original` | 只能保持原时间结构 |
| `status` | enum string | 样本处理状态 | 无 | `filtered` / `kept_original` / `skipped_boundary` / `ema_reset` / `invalid_shape` |

## 11. 数据定义验收重点

- 能被 import。
- 默认配置能表达 `median_window=3`、`ema_alpha=0.35` 和可覆盖 `contact_reset_threshold`。
- `TactileFilterResult` 能引用 [[SignalRepairResult]]，并表达 `sample_count_before == sample_count_after`。
- 样本记录主结构只保存摘要，完整矩阵 diff 通过 `debug_artifact_ref` 引用。

## 12. 现有程序盘点

- `src/data_clean/schemas/` 已有 Runtime 和场景二部分 schema 类型；尚未发现触觉滤波器类型。
- `src/data_clean/service/` 目前不应存在正式 `tactile_filter` 实现。
- 本 L3 是新增 schema/types，不重写异常检测或数据补全器。

## 13. 本 L3 的真实改造边界

- 允许新增触觉滤波器相关 schema/types 和对应测试。
- 允许更新 `src/data_clean/data_clean_architecture.md` 中的目录结构说明。
- 禁止实现触觉滤波算法或开发者入口。
- 禁止修改 [[SignalRepairResult]] 的既有语义，除非发现字段名与已归档上游 L3 不一致并先暂停汇报。

## 14. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterResult.md`
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
| 对应功能检验项 | `scene2_tactile_filter` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 不直接接入开发者入口，但由 `scene2_tactile_filter` 间接覆盖 |

## 17. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 18. 禁止修改

- 禁止实现触觉滤波算法。
- 禁止修改数据补全器算法。
- 禁止修改开发者入口。

## 19. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 20. 成功标准

- [x] 触觉滤波相关类型可 import。
- [x] 默认配置能表达 `median_window=3`、`ema_alpha=0.35` 和可覆盖 reset 阈值。
- [x] `TactileFilterResult` 能引用补全结果和输出序列。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 21. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/`。


## 22. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md
文件名编号：service_s2_013
正文 L3 编号：service_s2_013
dispatch.task_id：service_s2_013
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`，确认可复用 `SignalRepairResult.output_sequence_refs`、`timestamp_policy`、`sample_count_before` 和 `sample_count_after`。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/tactile_filter.py`：新增 `TactileFilterAlgorithm`、`TactileFilterSampleStatus`、`TactileFilterConfig`、`TactileFilterInputSequence`、`TactileFilterSampleRecord`、`TactileFilterSegmentSummary`、`TactileFilterResult`。
- `src/data_clean/schemas/__init__.py`：导出触觉滤波器 schema 公共类型。
- `src/data_clean/tests/service/test_tactile_filter_schemas.py`：新增默认配置、公共类型实例化、状态覆盖和结果样本数不变量测试。
- `src/data_clean/data_clean_architecture.md`：登记新增 `schemas/tactile_filter.py`。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/service/test_tactile_filter_schemas.py`，运行 `python3 -m pytest src/data_clean/tests/service/test_tactile_filter_schemas.py -q`，按预期因 `ModuleNotFoundError: No module named 'schemas.tactile_filter'` 失败。
- Green：新增触觉滤波器枚举和 dataclass，并在 `schemas.__init__` 导出后，目标测试通过。
- Refactor：补充架构文档目录表，并运行 `python3 -m py_compile` 检查新增/改动 Python 文件。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_tactile_filter_schemas.py -v`：通过，`4 passed`。
- `python3 -m py_compile src/data_clean/schemas/tactile_filter.py src/data_clean/schemas/__init__.py src/data_clean/tests/service/test_tactile_filter_schemas.py`：通过。
- 手动接口验证：通过 `PYTHONPATH=src/data_clean python3 - <<'PY' ...` 从 `schemas` 和 `schemas.tactile_filter` 导入触觉滤波类型，实例化 `TactileFilterResult` 并用 `dataclasses.asdict` 验证样本记录状态序列化。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准核对

- 已验证触觉滤波相关类型可通过 `from schemas.tactile_filter import ...` 和 `from schemas import ...` 导入。
- 已验证默认 `TactileFilterConfig` 表达 `median_window=3`、`ema_alpha=0.35`、`contact_reset_threshold=None`，并可覆盖 reset 阈值为 `0.2`。
- 已验证 `TactileFilterResult.input_repair_result_ref` 可引用 `SignalRepairResult`，并通过 `output_sequence_refs` 引用滤波后触觉序列；`sample_count_before != sample_count_after` 时会拒绝实例化。
- 本 L3 不直接修改 `./start_data_clean.sh --dev`；后续由场景二 `scene2_tactile_filter` 功能检验项和场景完整 smoke test 间接覆盖。建议用户在场景二全链路完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_tactile_filter` 做最终人工验收。

### 本次明确未做

- 未实现片段切分。
- 未实现中值 + EMA 触觉滤波计算。
- 未接入或修改开发者入口、菜单、脚本调用、调度索引、共享执行记录、阶段进度或总执行日志。

### 归档状态

- 本任务完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/`。
- 原 active 功能组目录仍包含 `service_s2_014`、`service_s2_015`、`service_s2_016`，因此不删除。

### 风险与后续建议

- 建议后续 `service_s2_014` 复用本 L3 的 `TactileFilterInputSequence`、`TactileFilterSegmentSummary` 和 `TactileFilterSampleStatus` 实现分段与 reset 边界。
- 建议后续入口接入 L3 完成后，由用户运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_tactile_filter` 做最终人工验收。
