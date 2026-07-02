# L3 微元任务：接入 MCAP_A 开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：MCAP_A 生成器
L3 编号：service_s2_020
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_020_接入MCAP_A开发者功能检验项.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_020
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_020_接入MCAP_A开发者功能检验项.md
  group: service-s2-g5
  branch: service-s2
  wave: 4
  parallel_group: service-s2-g5-p4
  depends_on: [service_s2_018]
  must_run_after: [service_s2_019]
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [start_data_clean.sh, src/data_clean/runtime/, src/data_clean/ui/, src/data_clean/tests/]
    modules: [data_clean.runtime, data_clean.ui]
    config_keys: [dev_menu.scene2.mcap_a_writer]
  dispatch_status: ready
```

## 3. 本次目标

```text
把 MCAP_A 生成器接入 `./start_data_clean.sh --dev` 场景二功能检验项，生成隔离调试产物和运行日志。
```

## 4. 本次不做

- 不修改 MCAP_A 写出器核心逻辑。
- 不接入 IK、MCAP_B、Parquet 标注或场景三完整流程。
- 不默认保存临时覆盖到正式配置。

## 5. 执行对象

- 开发者入口场景二功能检验项 `scene2_mcap_a_writer`
- [[McapA]]
- [[McapAWriteSummary]]

## 6. 执行依赖

- 执行前 `service_s2_018` 必须已完成并归档，MCAP_A 写出器可用。
- 建议 `service_s2_019` 已完成并归档，使入口接入前已有契约测试保障。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：MCAP_A 写出器
上游接口定义位置：MCAP_A生成器 L2、service_s2_018
当前 L3 期望消费的字段 / 文件 / 返回值：cleaned MCAP、signal_repair_result.json、pose_filter_result.json、tactile_filter_result.json、McapAWriteConfig
是否存在接口冲突：无
如果有冲突，本次处理策略：入口只做参数收集、调用和日志；缺少上游 artifact 时清晰失败，不自行生成假数据
```

## 8. 预期改动形态

- 开发者入口中出现或可选择 `scene2_mcap_a_writer` 功能检验项。
- 功能检验运行后写出 `artifacts/mcap_a/<stem>_mcap_a.mcap`、`artifacts/mcap_a_write_summary.json` 和运行日志。
- 临时输出目录和覆盖策略只对本次运行生效。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景二：硬件数据可靠性验证
↓
选择 scene2_mcap_a_writer
↓
选择 cleaned MCAP、signal_repair_result.json、pose_filter_result.json、tactile_filter_result.json 和调试输出目录
↓
可选临时覆盖输出目录 / 覆盖策略
↓
执行 MCAP_A 写出器
↓
写出 MCAP_A、mcap_a_write_summary.json 和运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| 上游结果加载 | 执行前 | 三类 result JSON 或等价 artifact | result refs | 写清缺失项并停止 |
| MCAP_A 写出器 | 输入校验后 | cleaned MCAP、三类 result、[[McapAWriteConfig]] | [[McapA]]、[[McapAWriteSummary]] | 写错误日志并停止 |
| 调试产物写出 | 写出成功后 | [[McapA]]、[[McapAWriteSummary]] | artifacts 和运行日志 | 写出失败原因和已生成文件 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `ready` | 输入选择完成 | 运行日志 | 显示输入和配置摘要 |
| `failed` | 输入缺失、校验失败或写出失败 | 运行日志 | 显示 reason 和缺失项 |
| `completed` | MCAP_A 和 summary 写出完成 | 运行日志和终端摘要 | 显示输出目录 |

## 10. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 11. 现有程序盘点

- 先读取 `service_s2_004`、`service_s2_008`、`service_s2_012`、`service_s2_016` 的入口接入方式，保持场景二功能检验菜单风格一致。
- 先检查 `start_data_clean.sh`、`src/data_clean/runtime/`、`src/data_clean/ui/` 中已有开发者入口结构。
- 复用已有 run 目录、运行日志和调试产物写出模式。

## 12. 本 L3 的真实改造边界

- 允许新增 `scene2_mcap_a_writer` 菜单项、runner/CLI glue 和 smoke 测试。
- 允许写开发者调试产物到独立 run 目录。
- 禁止修改 MCAP_A 写出器核心语义。
- 禁止把临时覆盖默认写回正式配置。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteConfig.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`
5. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md`

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

1. `start_data_clean.sh`
2. `src/data_clean/runtime/`
3. `src/data_clean/ui/`
4. `src/data_clean/tests/`

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
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；`artifacts/mcap_a/<stem>_mcap_a.mcap`、`artifacts/mcap_a_write_summary.json` |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景二和 `scene2_mcap_a_writer` |

## 16. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改 MCAP_A 写出器核心语义。
- 禁止修改上游补全和滤波结果语义。
- 禁止把开发者调试产物写入正式生产输出目录。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] `scene2_mcap_a_writer` 可从开发者入口触发或被 CLI/smoke 测试覆盖。
- [x] 功能检验写出 MCAP_A、sidecar summary 和运行日志。
- [x] 缺少上游 result 时入口清晰失败，不生成误导性 MCAP_A。
- [x] 临时覆盖配置只对本次运行生效，默认不写回正式配置。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_020_接入MCAP_A开发者功能检验项.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_020_接入MCAP_A开发者功能检验项.md
文件名编号：service_s2_020
正文 L3 编号：service_s2_020
dispatch.task_id：service_s2_020
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`must_run_after`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md` 与 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md`，确认 `MCAP_A_Writer`、契约测试和场景三最小兼容验收可用。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `start_data_clean.sh`：在开发者入口启动前加入 bundled MCAP Python 包路径，保证 `./start_data_clean.sh --dev` 能导入 MCAP_A 写出器依赖。
- `src/data_clean/runtime/scene2_mcap_a_writer.py`：新增 `run_scene2_mcap_a_writer`，按 detection、repair、pose filter、tactile filter、MCAP_A writer 顺序编排场景二链路，写出独立 run log、`artifacts/mcap_a/<stem>_mcap_a.mcap` 和 `artifacts/mcap_a_write_summary.json`。
- `src/data_clean/ui/dev_menu.py`：新增 `scene2_mcap_a_writer` 开发者功能检验项和对应终端入口输出。
- `src/data_clean/tests/runtime/test_scene2_mcap_a_writer_runtime.py`：新增 runtime 覆盖，验证完整链路、MCAP_A 产物、sidecar summary、运行日志和开发者菜单暴露。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/runtime/test_scene2_mcap_a_writer_runtime.py`，运行 `python3 -m pytest src/data_clean/tests/runtime/test_scene2_mcap_a_writer_runtime.py -q`，按预期因 `ModuleNotFoundError: No module named 'runtime.scene2_mcap_a_writer'` 失败。
- Green：新增 `src/data_clean/runtime/scene2_mcap_a_writer.py` 并接入 `src/data_clean/ui/dev_menu.py` 后，目标测试通过，`3 passed`。
- Refactor：对齐既有场景二 run log / outputs 结构，修正 writer 运行时压缩配置为当前环境可用的 `none`，补充缺失 cleaned MCAP 的失败用例，并重新运行目标测试和相关测试。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_mcap_a_writer_runtime.py -q`：通过，`3 passed`。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_mcap_a_writer_runtime.py src/data_clean/tests/runtime/test_scene2_tactile_filter_runtime.py src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py src/data_clean/tests/runtime/test_scene2_signal_repair_runtime.py src/data_clean/tests/service/test_mcap_a_writer.py src/data_clean/tests/contract/test_mcap_a_scene3_compat.py -q`：通过，`19 passed`。
- `python3 -m pytest src/data_clean/tests -q`：未通过，收集阶段命中既有环境 / 历史测试问题 `ImportError: cannot import name 'ExtrinsicConfig' from 'repo.config.mcap_process_config'`，错误路径显示为 `src/data_clean/tests/config_tests/test_frame_alignment_config.py`，未修改该无关问题。
- `DATA_CLEAN_PYTHON=/usr/bin/python3 ./start_data_clean.sh --dev --config config/data_clean/data_clean_calibrated.yaml --run-root /tmp/scene2_mcap_menu_qa --cleaned-mcap-dir /tmp/nonexistent`：通过开发者菜单人工检查，场景二显示 `scene2_mcap_a_writer - MCAP_A 写出：完整场景二验证链路`；选择该项并输入缺失 MCAP 路径时写出 failed run log 且未生成误导性 MCAP_A。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`。

### 成功标准处理

- 已勾选全部成功标准：开发者入口和 runtime 测试可触发 `scene2_mcap_a_writer`；功能检验写出 MCAP_A、sidecar summary 和 run log；上游步骤或 writer 失败时返回 failed 且不宣称成功产物；配置覆盖只在本次 run 的输出路径中生效且不写回正式配置；开发者入口关系已记录。

### 开发者验收入口关系

- 本 L3 直接修改 `./start_data_clean.sh --dev` 后进入的 `ui.dev_menu` 场景二功能检验菜单，新增功能检验项 `scene2_mcap_a_writer`，并影响场景二完整 smoke test。
- 建议用户后续运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_mcap_a_writer` 做最终人工验收。

### 当前没做

- 未修改 MCAP_A 写出器核心语义。
- 未修改异常检测、数据补全、位姿滤波或触觉滤波算法。
- 未修改 `task/dispatch/<功能组>.yaml`、共享执行记录、阶段进度或 `DOCS/总执行日志.md`。

### 归档说明

- 本任务完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。
- 原 active 功能组目录 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/` 在本最终 L3 移动后为空，已删除。
