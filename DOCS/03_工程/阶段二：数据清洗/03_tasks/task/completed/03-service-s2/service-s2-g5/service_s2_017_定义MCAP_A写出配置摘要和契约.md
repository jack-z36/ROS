# L3 微元任务：定义 MCAP_A 写出配置摘要和契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：MCAP_A 生成器
L3 编号：service_s2_017
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_017
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md
  group: service-s2-g5
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g5-p1
  depends_on: [service_s2_005, service_s2_009, service_s2_013]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_018]
  conflict_scope:
    files: [src/data_clean/schemas/, src/data_clean/tests/, DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/]
    modules: [data_clean.schemas]
    config_keys: [mcap_a_writer]
  dispatch_status: ready
```

## 3. 本次目标

```text
定义 MCAP_A 写出配置、写出摘要和 MCAP_A 契约代码形态，使后续写出器能稳定消费。
```

## 4. 本次不做

- 不实现 MCAP 复制替换写出。
- 不接入开发者菜单。
- 不修改上游补全、位姿滤波或触觉滤波接口。

## 5. 执行对象

- [[McapA]]
- [[McapAWriteConfig]]
- [[McapAWriteSummary]]

## 6. 执行依赖

- 执行前 `service_s2_005` 必须已完成并归档，[[SignalRepairResult]] 类型可用。
- 执行前 `service_s2_009` 必须已完成并归档，[[PoseFilterResult]] 类型可用。
- 执行前 `service_s2_013` 必须已完成并归档，[[TactileFilterResult]] 类型可用。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器、位姿滤波器、触觉滤波器
上游接口定义位置：SignalRepairResult.md、PoseFilterResult.md、TactileFilterResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：三类 result ref、output_sequence_refs、timestamp_policy、sample_count_before/after
是否存在接口冲突：无
如果有冲突，本次处理策略：只定义 MCAP_A 侧引用和校验字段，不改上游 result 语义
```

## 8. 预期改动形态

- 在 schema / type 层增加 MCAP_A 写出配置和摘要对象。
- 确认默认输出目录、命名策略、strict 必需输入策略和 sidecar summary 结构。
- 补充最小序列化 / 校验测试。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `McapAWriteConfig` | dataclass / TypedDict / schema | `src/data_clean/schemas/` 或既有 schema 位置 | MCAP_A 写出器、开发者入口 |
| `McapAWriteSummary` | dataclass / TypedDict / schema | `src/data_clean/schemas/` 或既有 schema 位置 | 写出器、报告生成器、场景三兼容测试 |
| `McapA` 契约常量 | schema 常量 / 文档引用 | `src/data_clean/schemas/` 或既有契约位置 | 写出器和契约测试 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
|---|---|---|---|---|
| `output_dir` | string | MCAP_A 输出目录 | `asset/阶段二：数据清洗/dev/mcap_validated/` | 开发者 run 可临时覆盖 |
| `filename_policy` | enum string | 命名策略 | `derive_from_cleaned_stem` | 首版只支持该策略 |
| `topic_policy` | enum string | topic 策略 | `preserve_cleaned_topics` | 不允许 processed/audit topic |
| `strict_required_inputs` | bool | 缺少上游结果是否失败 | `true` | 首版必须为 true |
| `status` | enum string | 写出状态 | 无 | `completed` / `failed` |
| `failure_reason` | string/null | 失败原因 | null | 失败时必填 |

## 10. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 11. 现有程序盘点

- 先检查 `src/data_clean/schemas/` 中场景二前四个功能模块已落地的 result/config 类型命名方式。
- 先检查 `src/data_clean/tests/` 中已有 schema / serialization 测试组织方式。
- 不把已有补全、滤波结果类型重命名或迁移。

## 12. 本 L3 的真实改造边界

- 允许新增 MCAP_A 写出相关 schema/type 和测试。
- 允许补充契约常量或枚举。
- 禁止修改 [[SignalRepairResult]]、[[PoseFilterResult]]、[[TactileFilterResult]] 字段语义。
- 禁止实现实际 MCAP 写出逻辑。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteConfig.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`
5. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairResult.md`
6. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterResult.md`
7. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterResult.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md`

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

## 14. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_mcap_a_writer` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否，本 L3 间接支撑 |
| 是否需要写测试产物 | 否，本 L3 只定义契约 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 后续入口 L3 支持 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 完成后仍需后续 `service_s2_020` 接入开发者入口 |

## 16. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改上游补全和滤波结果语义。
- 禁止实现 MCAP 写出器。
- 禁止新增真实数据产物。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] MCAP_A 写出配置和摘要类型可 import / 实例化 / 序列化。
- [x] 默认输出目录、命名策略、topic 策略和 strict 输入策略有测试覆盖。
- [x] 缺少必需引用或非法 topic policy 能被校验拒绝。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md
文件名编号：service_s2_017
正文 L3 编号：service_s2_017
dispatch.task_id：service_s2_017
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_005_定义数据补全器策略与结果类型.md`、`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md`、`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/service_s2_013_定义触觉滤波器配置输入审计记录和结果类型.md`，确认三类上游结果均使用 `output_sequence_refs` 引用处理后序列并保持 `timestamp_policy=preserve_original`。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/schemas/mcap_a_writer.py`：新增 `MCAP_A_WriterConfig`、`MCAP_A_WritePlan`、`MCAP_A_OutputContract`、`MCAP_A_WriterResult`，并约束 topic 策略、timestamp 策略、strict 输入和 replace 序列引用。
- `src/data_clean/schemas/__init__.py`：导出 MCAP_A writer schema 公共类型。
- `src/data_clean/tests/service/test_mcap_a_writer_schemas.py`：新增配置、写出计划、输出契约、结果序列化、`output_sequence_refs` 兼容格式和非法值拒绝测试。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/service/test_mcap_a_writer_schemas.py`，运行 `python3 -m pytest src/data_clean/tests/service/test_mcap_a_writer_schemas.py -q`，按预期因 `ModuleNotFoundError: No module named 'schemas.mcap_a_writer'` 失败。
- Green：新增 `src/data_clean/schemas/mcap_a_writer.py` 并在 `schemas.__init__` 导出后，目标测试通过。
- Refactor：补充 topic/timestamp/strict/replace 引用校验和公共导出断言，重新运行目标测试与 py_compile。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_mcap_a_writer_schemas.py -v`：通过，`7 passed`。
- `python3 -m py_compile src/data_clean/schemas/mcap_a_writer.py src/data_clean/schemas/__init__.py src/data_clean/tests/service/test_mcap_a_writer_schemas.py`：通过。
- 手动接口验证：通过 `PYTHONPATH=src/data_clean python3 -c ...` 从 `schemas` 导入四个 MCAP_A writer 类型，实例化 config / plan / contract / result 并 `dataclasses.asdict` 序列化。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准处理

- 已勾选全部成功标准：MCAP_A writer schema 可 import / 实例化 / 序列化；默认命名、topic 和 strict 输入策略有测试覆盖；非法 topic policy 与缺失 replace 序列引用被拒绝；开发者入口关系已记录。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单、脚本调用、测试产物或运行日志。
- 本 L3 间接支撑场景二功能检验项 `scene2_mcap_a_writer`，并影响场景二完整 smoke test。
- 建议用户后续在 `service_s2_020` 完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_mcap_a_writer` 做最终人工验收。

### 当前没做

- 未实现 MCAP 复制替换写出器。
- 未执行任何 MCAP I/O。
- 未修改开发者入口或调度索引。

### 归档说明

- 本任务完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。
- 原 active 功能组目录仍包含 `service_s2_018`、`service_s2_019`、`service_s2_020`，因此不删除该目录。
