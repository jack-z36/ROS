# L3 微元任务：补充 MCAP_A 契约与场景三兼容验收

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：MCAP_A 生成器
L3 编号：service_s2_019
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md`
任务类别：数据读写类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_019
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md
  group: service-s2-g5
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g5-p3
  depends_on: [service_s2_018]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [src/data_clean/tests/contract/, src/data_clean/tests/]
    modules: [data_clean.tests]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
补充 MCAP_A 契约测试和最小场景三读取兼容验收，证明 MCAP_A 可作为 validated 主 MCAP 被下游读取。
```

## 4. 本次不做

- 不实现或修改场景三时间轴对齐算法。
- 不改变 MCAP_A 写出规则。
- 不接入开发者菜单。

## 5. 执行对象

- [[McapA]]
- [[McapAWriteSummary]]
- 场景三最小读取兼容检查

## 6. 执行依赖

- 执行前 `service_s2_018` 必须已完成并归档，MCAP_A 写出器可生成测试产物。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：MCAP_A 复制替换写出器
上游接口定义位置：MCAP_A生成器 L2、service_s2_018
当前 L3 期望消费的字段 / 文件 / 返回值：MCAP_A 文件、mcap_a_write_summary.json、topic/type/timestamp/sample count
是否存在接口冲突：无
如果有冲突，本次处理策略：以 MCAP_A L2 契约为准，发现写出器不满足则补测试暴露失败，不扩大修改范围
```

## 8. 预期改动形态

- 新增 MCAP_A contract 测试。
- 新增场景三读取兼容的最小 smoke / helper 测试。
- 验证输出路径和 sidecar summary 必填字段。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 生成或读取测试 MCAP_A | 写出器测试 fixture | 测试输出目录 | MCAP | 测试隔离输出 |
| 读取 summary | `mcap_a_write_summary.json` | 断言字段 | JSON | 只读 |
| 场景三最小读取 | MCAP_A | 可读 topic/time 序列 | MCAP | 只读 |

### 文件或目录结构

```text
src/data_clean/tests/contract/
└── <mcap_a_contract_test>.py

src/data_clean/tests/outputs/
└── <test_run>/
    ├── <stem>_mcap_a.mcap
    └── mcap_a_write_summary.json
```

## 10. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 11. 现有程序盘点

- 先检查 `src/data_clean/tests/contract/` 是否已有 MCAP / cleaned contract 测试。
- 先检查场景三已有读取入口或 L2 契约；只做最小兼容验证，不提前实现对齐。
- 复用 `service_s2_018` 的写出 fixture 和 helper。

## 12. 本 L3 的真实改造边界

- 允许新增或补充 contract / smoke 测试。
- 允许补充必要测试 fixture 生成逻辑。
- 禁止修改写出器核心逻辑，除非测试暴露小范围契约 bug 且修复不跨模块。
- 禁止实现完整场景三流程。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md`

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

1. `src/data_clean/tests/contract/`
2. `src/data_clean/tests/`
3. `src/data_clean/repo/`

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
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否，本 L3 补充自动化验收 |
| 是否需要写测试产物 | 是；测试隔离 MCAP_A 和 summary |
| 是否需要写运行日志 | 测试日志即可 |
| 是否允许临时覆盖配置 | 不涉及 |
| 是否允许保存覆盖到配置文件 | 否 |
| 最终人工验收提示 | 本 L3 完成后仍需用户最终运行开发者入口确认 |

## 16. 允许修改

- `src/data_clean/tests/contract/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止实现完整场景三时间轴对齐。
- 禁止修改 MCAP_A topic 策略。
- 禁止写真实数据产物到正式生产目录。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] 合同测试验证 MCAP_A 与 cleaned MCAP topic、消息类型、时间戳和样本数对齐。
- [x] 合同测试验证 sidecar summary 必填字段齐全。
- [x] 最小场景三读取兼容检查能读取 MCAP_A 的主数据 topic。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md
文件名编号：service_s2_019
正文 L3 编号：service_s2_019
dispatch.task_id：service_s2_019
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md`，确认 `MCAP_A_Writer`、写出计划、输出 contract 和 sidecar summary 可用于本 L3 契约测试。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/tests/contract/test_mcap_a_scene3_compat.py`：新增 MCAP_A 与场景三兼容契约测试，使用 `MCAP_A_Writer` 生成测试隔离 MCAP_A，再通过 `mcap.reader.make_reader` 读取输出文件并断言 topic、样本数、时间戳、schema、payload、summary 和 writer contract。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先运行 `python3 -m pytest src/data_clean/tests/contract/test_mcap_a_scene3_compat.py -v`，按预期因测试文件不存在失败。
- Green：新增 `src/data_clean/tests/contract/test_mcap_a_scene3_compat.py`，覆盖场景三需要的 pose、gripper、tactile 主数据 topic、message count、timestamp ordering / coverage、修复或滤波 topic schema、`MCAP_A_Writer` 输出 contract 和 `mcap_a_write_summary.json` 必填字段；目标测试通过。
- Refactor：复用本文件内小型 MCAP fixture、reader helper 和按 topic 分组 helper，保持测试通过且不修改写出器核心逻辑。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/contract/test_mcap_a_scene3_compat.py -v`：通过，`5 passed`。
- 手动接口验证：目标 pytest 真实创建 cleaned MCAP、执行 `MCAP_A_Writer.execute_write_plan()` 写出 MCAP_A 和 `mcap_a_write_summary.json`，再用 `mcap.reader.make_reader` 读取输出 MCAP，确认场景三主数据 topic 可读、时间戳保留、schema 保留、替换 payload 可观察。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准处理

- 已勾选全部成功标准：契约测试验证 MCAP_A 与 cleaned MCAP 的 topic、消息类型、时间戳和样本数对齐；sidecar summary 必填字段齐全；最小场景三读取兼容检查可读取 MCAP_A 主数据 topic；开发者入口关系已记录。

### 开发者验收入口关系

- 本 L3 不修改 `./start_data_clean.sh --dev`、开发者菜单或脚本调用。
- 本 L3 通过自动化契约测试间接覆盖场景二功能检验项 `scene2_mcap_a_writer`，并影响场景二完整 smoke test。
- 建议用户后续在 `service_s2_020` 完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_mcap_a_writer` 做最终人工验收。

### 当前没做

- 未修改 MCAP_A 写出规则或 `MCAP_A_Writer` 核心逻辑。
- 未实现场景三完整时间轴对齐。
- 未修改开发者入口、调度索引或集中执行记录。

### 归档说明

- 本任务完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。
- 原 active 功能组目录仍包含 `service_s2_020`，因此不删除该目录。
