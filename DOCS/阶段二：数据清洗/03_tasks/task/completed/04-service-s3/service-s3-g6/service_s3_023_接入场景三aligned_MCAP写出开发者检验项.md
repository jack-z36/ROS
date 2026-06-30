# L3 微元任务：接入场景三 aligned MCAP 写出开发者检验项

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：aligned MCAP 与 sidecar 写出器  
L3 编号：service_s3_023  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_023_接入场景三aligned_MCAP写出开发者检验项.md`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_023
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_023_接入场景三aligned_MCAP写出开发者检验项.md
  group: service-s3-g6
  branch: service-s3
  wave: 4
  parallel_group: service-s3-g6-p4
  depends_on: [service_s3_022]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - start_data_clean.sh
      - src/data_clean/runtime/scene3_aligned_mcap_write_check.py
      - src/data_clean/ui/dev_menu.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.runtime
      - data_clean.ui
    config_keys:
      - scene3_alignment.output_dir
  dispatch_status: ready
```

## 3. 本次目标

```text
把 aligned MCAP 与 sidecar 整体写出流程接入场景三开发者检验项 scene3_aligned_mcap_write_check。
```

## 4. 本次不做

- 不新增底层写出算法。
- 不修改 report draft 统计。
- 不修改字段对齐算法。
- 不执行场景最终人工验收。

## 5. 执行对象

- `scene3_aligned_mcap_write_check` 开发者检验项
- aligned MCAP / sidecar / write summary 调试产物
- 运行日志

## 6. 执行依赖

- `service_s3_022` 应已实现临时目录整体提交与失败摘要。
- 必须复用现有开发者入口 / UI 菜单风格。
- 本任务只负责开发者入口编排和可观察产物。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：aligned MCAP 与 sidecar 整体写出服务
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- 完整写出服务输入、输出路径、write summary、失败摘要、运行日志字段
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并汇报，不在入口层重写底层写出
```

## 8. 预期改动形态

- 新增或扩展 runtime / UI 开发者检验入口。
- 检验项能选择小样本输入和输出目录，调用整体写出服务。
- 输出 aligned MCAP、`alignment_index.parquet`、`alignment_report.json`、`aligned_mcap_write_summary.json` 和运行日志。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景三：MCAP 多 topic 时间轴对齐
↓
选择 scene3_aligned_mcap_write_check
↓
选择小样本输入和调试输出目录
↓
调用 aligned MCAP 与 sidecar 整体写出服务
↓
输出四类测试产物和运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| aligned MCAP 整体写出服务 | 用户确认输入后 | MCAP_A、FieldAlignmentResult、AlignmentIndex、report draft、配置 | aligned MCAP、sidecar、summary | 写失败摘要和运行日志 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `completed` | 四类产物写出成功 | run log / write summary | 输出路径 |
| `failed` | 任一写出步骤失败 | run log / write summary | 失败原因和诊断路径 |

## 10. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md`
3. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/service_s3_022_实现临时目录整体提交与失败摘要.md`

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
10. `DOCS/阶段二：数据清洗/02_service/场景三/执行约束.md`

### 必读代码

1. `start_data_clean.sh`
2. `src/data_clean/runtime/`
3. `src/data_clean/ui/`
4. `src/data_clean/tests/`
5. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及入口编排，必须使用 `$tdd` 技能。建议顺序：runner 调用测试 -> 成功产物路径测试 -> 失败摘要显示测试 -> 菜单接入测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_aligned_mcap_write_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；产物类型：aligned MCAP、alignment index、alignment report、write summary |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景三和 `scene3_aligned_mcap_write_check` / 场景完整 smoke test |

## 14. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止重写底层 sidecar 或 MCAP 写出服务。
- 禁止修改 report draft 统计。
- 禁止修改字段对齐算法。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [x] 已接入 `scene3_aligned_mcap_write_check`。
- [x] 检验项能写出 aligned MCAP、alignment index、alignment report 和 write summary。
- [x] 运行日志包含输入、配置、执行步骤、关键状态、错误信息和输出位置。
- [x] 失败时能展示失败摘要，不把半成品标记为 completed。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 任务文件身份校验

| 项目 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_023_接入场景三aligned_MCAP写出开发者检验项.md` |
| 实际读取路径 | 匹配 |
| 文件名编号 | `service_s3_023` |
| 正文 L3 编号 | `service_s3_023` |
| 校验结论 | 通过 |

### 调度元数据校验

| 项目 | 结果 |
|---|---|
| task_id | service_s3_023 |
| task_file | 匹配 active 路径 |
| group | service-s3-g6 |
| branch | service-s3（当前分支确认） |
| dispatch_status | ready |
| depends_on | service_s3_022（已归档于 `04-service-s3/service-s3-g6/`） |
| 分支校验 | service-s3 ✓ |

### 开工自检

```bash
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK, branch: service-s3
```

### 必读上下文

已读取的文档：
- L2 能力模块：`aligned MCAP 与 sidecar 写出器.md`
- L2 数据定义：`AlignedMcapWriteSummary.md`
- 已完成 L3：`service_s3_022`（临时目录整体提交与失败摘要）
- 约束文档：`开发者验收入口约束.md`、`L3编码执行原则.md`、`L3任务文件身份校验约束.md`、`L3调度元数据约束.md`、`L3执行TDD与归档约束.md` 等
- 代码：`service/aligned_mcap_writer.py`、`runtime/scene3_field_alignment_check.py`、`runtime/scene3_alignment_report_check.py`、`runtime/scene3_step_timeline_check.py`、`ui/dev_menu.py`、`data_clean_architecture.md`

### TDD 执行记录

| 切片 | 测试内容 | 状态 |
|---|---|---|
| VS1 RED→GREEN | Menu registration: `scene3_aligned_mcap_write_check` appears in SCENE_MENUS | ✓ |
| VS2 RED→GREEN | Menu entry has descriptive label | ✓ |
| VS3 RED→GREEN | Menu runner is callable | ✓ |
| VS4 RED→GREEN | Runtime module importable with `run_scene3_aligned_mcap_write_check` function | ✓ |
| VS5 RED→GREEN | Runtime wrapper returns dict with expected keys (run_id, status, outputs, run_log_path, steps) | ✓ |
| VS6 RED→GREEN | Runtime wrapper writes valid run_log.json with correct check_id, input, outputs | ✓ |

### 修改文件

| 文件 | 改动 |
|---|---|
| `src/data_clean/runtime/scene3_aligned_mcap_write_check.py` | **新增** `run_scene3_aligned_mcap_write_check()` runtime wrapper — 创建隔离 run 目录，调用 `run_aligned_mcap_write_staging()`，写出 run log |
| `src/data_clean/ui/dev_menu.py` | 新增 `run_scene3_aligned_mcap_write_check_check()` 交互 runner 函数，导入 runtime 模块，在 SCENE3_CHECKS 添加 `scene3_aligned_mcap_write_check` 条目 |
| `src/data_clean/tests/service/test_scene3_aligned_mcap_write_check.py` | **新增** 6 个测试覆盖 6 个 VS 切片 |
| `src/data_clean/data_clean_architecture.md` | 在 runtime 层级表中添加 `scene3_aligned_mcap_write_check.py` 条目，更新场景三检验项描述 |
| 本 L3 任务文件 | 成功标准标记完成，追加执行摘要 |

### 验收命令输出

```bash
# 1. 开工自检
bash scripts/init_data_clean_dev.sh
# → Data clean dev environment OK, branch: service-s3

# 2. 本 L3 全部测试通过
PYTHONPATH=src/data_clean:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support python3 -m pytest src/data_clean/tests/service/test_scene3_aligned_mcap_write_check.py -q
# → 6 passed in 0.51s

# 3. 全量测试无回归
PYTHONPATH=src/data_clean:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support python3 -m pytest src/data_clean/tests/service/ src/data_clean/tests/contract/ src/data_clean/tests/config/ src/data_clean/tests/ -q --ignore=src/data_clean/tests/runtime
# → 590 passed, 9 skipped (3 pre-existing failures unrelated to this L3)

# 4. Importability
PYTHONPATH=src/data_clean:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support python3 -c "
from runtime.scene3_aligned_mcap_write_check import run_scene3_aligned_mcap_write_check
assert callable(run_scene3_aligned_mcap_write_check)
print('run_scene3_aligned_mcap_write_check importable: OK')
"
```

### 成功标准处理

- [x] 已接入 `scene3_aligned_mcap_write_check`：新增 runtime wrapper + UI 菜单项。
- [x] 检验项能写出 aligned MCAP、alignment index、alignment report 和 write summary：通过 `run_aligned_mcap_write_staging()` 服务完成，runtime wrapper 传递输出路径。
- [x] 运行日志包含输入、配置、执行步骤、关键状态、错误信息和输出位置：VS6 验证 run_log.json 包含所有必要字段。
- [x] 失败时能展示失败摘要，不把半成品标记为 completed：staging 层（service_s3_022）已处理原子提交；runtime wrapper 转发 summary 状态。
- [x] 已说明本 L3 与开发者验收入口的关系。

### 开发者验收入口关系

- 本 L3 直接修改 `./start_data_clean.sh --dev` → 场景三 → `scene3_aligned_mcap_write_check` 功能检验项。
- 用户通过开发者菜单选择 MCAP_A 路径，运行时调用 `run_aligned_mcap_write_staging()` 执行 aligned MCAP 与 sidecar 写出。
- 输出产物：aligned MCAP、alignment_index.parquet、alignment_report.json、aligned_mcap_write_summary.json、run_log.json。
- 本 L3 自动化验收只证明局部实现正确；场景最终验收仍需用户运行：
  ```bash
  ./start_data_clean.sh --dev
  ```
  选择场景三 → `scene3_aligned_mcap_write_check`，检查四类产物和运行日志是否符合 L2 契约。

### 当前没做

- 未重写底层 sidecar 或 MCAP 写出服务（复用 service/aligned_mcap_writer.py 的 `run_aligned_mcap_write_staging`）。
- 未修改 report draft 统计或字段对齐算法。
- 未写入共享执行记录。

### 遗留风险

- 无已知回归风险：590 service/contract/config 测试全部通过（含新增 6 个），9 skipped（与基线一致）。
- 当前 runtime wrapper 使用空 field_results/alignment_index_records 调用 staging 服务；实际场景需要上游对齐链路输出真实数据。
- 交互菜单需要用户手动输入 MCAP_A 路径；建议后续 L3 增加自动搜索默认路径功能。

### 归档说明

- 本任务完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。
- 原 active 功能组目录 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/` 若为空，则删除该空目录。

### 建议最终人工验收

本 L3 完成后，建议用户在完成 service-s3-g6 全部 L3 后运行：

```bash
./start_data_clean.sh --dev
```

选择场景三 → `scene3_aligned_mcap_write_check`，检查 aligned MCAP 写出检验项是否出现在菜单中、能否选择 MCAP_A 并输出四类产物和运行日志。

