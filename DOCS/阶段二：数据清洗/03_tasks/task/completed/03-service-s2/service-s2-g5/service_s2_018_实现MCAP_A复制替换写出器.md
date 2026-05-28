# L3 微元任务：实现 MCAP_A 复制替换写出器

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：MCAP_A 生成器
L3 编号：service_s2_018
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md`
任务类别：数据读写类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_018
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md
  group: service-s2-g5
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g5-p2
  depends_on: [service_s2_017]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_019, service_s2_020]
  conflict_scope:
    files: [src/data_clean/repo/, src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.repo, data_clean.service]
    config_keys: [mcap_a_writer]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现 MCAP_A 复制替换写出器：保留 cleaned MCAP topic/time 结构，替换 pose、tactile、gripper 主数据并写出 sidecar summary。
```

## 4. 本次不做

- 不接入 `./start_data_clean.sh --dev` 菜单。
- 不实现场景三完整对齐逻辑。
- 不新增 processed topic、audit topic 或 MCAP metadata 审计块。

## 5. 执行对象

- [[CleanedMcap]]
- [[SignalRepairResult]]
- [[PoseFilterResult]]
- [[TactileFilterResult]]
- [[McapA]]
- [[McapAWriteSummary]]

## 6. 执行依赖

- 执行前 `service_s2_017` 必须已完成并归档，MCAP_A 写出配置和摘要类型可用。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器、位姿滤波器、触觉滤波器
上游接口定义位置：MCAP_A生成器 L2、SignalRepairResult.md、PoseFilterResult.md、TactileFilterResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：output_sequence_refs、timestamp_policy、sample_count_before/after、topic 引用
是否存在接口冲突：无
如果有冲突，本次处理策略：发现上游序列引用无法映射到 cleaned topic 时失败并记录 `topic_or_sample_count_mismatch`，不猜测兼容
```

## 8. 预期改动形态

- 增加 MCAP_A 写出服务或 repo 工具。
- 对上游 result 做 strict 输入校验。
- 写出 MCAP_A 和 `mcap_a_write_summary.json`。
- 补充最小 MCAP / fake MCAP 读写契约测试。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 读取 cleaned MCAP | `asset/阶段二：数据清洗/dev/mcap_cleaned/*.mcap` 或测试 fixture | 内存消息流 | MCAP | 只读，不覆盖 |
| 读取上游结果 | 三类 result JSON 或内存对象 | 处理后序列映射 | JSON / object | 只读 |
| 写出 MCAP_A | cleaned 结构 + 替换序列 | `asset/阶段二：数据清洗/dev/mcap_validated/<stem>_mcap_a.mcap` 或 run artifacts | MCAP | 默认不覆盖 |
| 写出 sidecar | 写出统计和状态 | `mcap_a_write_summary.json` | JSON | 同一 run 内允许更新 |

### 文件或目录结构

```text
asset/阶段二：数据清洗/dev/mcap_validated/
└── <stem>_mcap_a.mcap

src/data_clean/runs/{run_id}_scene2_mcap_a_writer/
└── outputs/
    └── artifacts/
        ├── mcap_a/
        │   └── <stem>_mcap_a.mcap
        └── mcap_a_write_summary.json
```

## 10. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 11. 现有程序盘点

- 先检查 `src/data_clean/repo/` 中现有 MCAP 读取 / 写入工具，优先复用。
- 先检查场景一 cleaned MCAP 写出逻辑，保持 topic 复制和 message encode/decode 方式一致。
- 先检查场景二前四个模块的 result artifact 加载方式。

## 12. 本 L3 的真实改造边界

- 允许新增 MCAP_A 写出器、repo 辅助函数和对应测试。
- 允许读取上游 result refs 并做 strict 校验。
- 禁止修改异常检测、补全、位姿滤波和触觉滤波算法。
- 禁止修改场景三代码作为兼容捷径。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteConfig.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`
5. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/SignalRepairResult.md`
6. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterResult.md`
7. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md`

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

1. `src/data_clean/repo/`
2. `src/data_clean/service/`
3. `src/data_clean/tests/`

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
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否，本 L3 提供底层写出能力 |
| 是否需要写测试产物 | 是；MCAP_A 和 `mcap_a_write_summary.json` |
| 是否需要写运行日志 | 通过后续入口 L3 完整接入 |
| 是否允许临时覆盖配置 | 后续入口 L3 支持 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 完成后仍需 `service_s2_020` 接入开发者入口 |

## 16. 允许修改

- `src/data_clean/repo/`
- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改上游补全和滤波算法。
- 禁止新增 processed/audit topic。
- 禁止把调试产物写入正式 canonical dataset 目录。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] 缺少任一必需上游 result 时失败且不生成 MCAP_A。
- [x] 合法输入可写出 MCAP_A 和 sidecar summary。
- [x] MCAP_A 保留 cleaned MCAP 的 topic、消息类型、时间戳排序和样本数。
- [x] pose/tactile/gripper 目标 topic 使用上游处理后序列，其他 topic 原样复制。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md
文件名编号：service_s2_018
正文 L3 编号：service_s2_018
dispatch.task_id：service_s2_018
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md`，确认 `MCAP_A_WriterConfig`、`MCAP_A_WritePlan`、`MCAP_A_OutputContract`、`MCAP_A_WriterResult` 可用。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/repo/mcap_a_writer.py`：新增 `MCAP_A_Writer`，支持单 topic 原样复制、单 topic payload 替换、完整写出计划执行、压缩配置映射、输出 contract 校验、checksum 计算和 `mcap_a_write_summary.json` sidecar 写出。
- `src/data_clean/tests/service/test_mcap_a_writer.py`：新增 MCAP fixture 读写测试，覆盖复制、替换、完整计划、contract 校验失败和缺少上游 result 失败。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/service/test_mcap_a_writer.py`，运行 `python3 -m pytest src/data_clean/tests/service/test_mcap_a_writer.py -q`，按预期因 `ModuleNotFoundError: No module named 'repo.mcap_a_writer'` 失败。
- Green：新增 `src/data_clean/repo/mcap_a_writer.py` 后，目标测试通过；随后补充上游 result refs 和 sidecar summary 断言，继续保持目标测试 green。
- Refactor：整理 writer 内部 schema/channel 注册、replacement count 校验、summary 写出和 contract 构建辅助函数，重新运行目标测试与 py_compile。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_mcap_a_writer.py -v`：通过，`5 passed`。
- `python3 -m py_compile src/data_clean/repo/mcap_a_writer.py src/data_clean/tests/service/test_mcap_a_writer.py`：通过。
- 手动接口验证：目标 pytest 真实创建 source MCAP，执行 `copy_original_topic`、`replace_topic`、`execute_write_plan`，再用 `mcap.reader.make_reader` 读取输出 MCAP，确认 topic、时间戳、sequence、payload、message count、checksum 和 sidecar summary 可观察。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准处理

- 已勾选全部成功标准：缺少必需上游 result 时失败且不生成 MCAP_A；合法输入写出 MCAP_A 和 sidecar summary；输出保留 cleaned MCAP topic、消息类型、时间戳排序和样本数；目标 topic 使用替换 payload，其他 topic 原样复制；开发者入口关系已记录。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单或脚本调用。
- 本 L3 直接支撑场景二功能检验项 `scene2_mcap_a_writer`，并影响场景二完整 smoke test。
- 建议用户后续在 `service_s2_020` 完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_mcap_a_writer` 做最终人工验收。

### 当前没做

- 未修改数据补全、位姿滤波或触觉滤波算法。
- 未接入开发者入口。
- 未修改调度索引或集中执行记录。

### 归档说明

- 本任务完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。
- 原 active 功能组目录仍包含 `service_s2_019`、`service_s2_020`，因此不删除该目录。
