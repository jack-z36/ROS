# L3 微元任务：接入触觉滤波开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：触觉滤波器
L3 编号：service_s2_016
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_016_接入触觉滤波开发者功能检验项.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_016
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_016_接入触觉滤波开发者功能检验项.md
  group: service-s2-g4
  branch: service-s2
  wave: 4
  parallel_group: service-s2-g4-p4
  depends_on: [service_s2_008, service_s2_015]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [start_data_clean.sh, src/data_clean/runtime/, src/data_clean/ui/, src/data_clean/tests/]
    modules: [data_clean.runtime, data_clean.ui]
    config_keys: [dev_menu.scene2.tactile_filter]
  dispatch_status: ready
```

## 3. 本次目标

```text
把触觉滤波器接入 `./start_data_clean.sh --dev` 场景二功能检验项，生成调试产物和运行日志。
```

## 4. 本次不做

- 不修改触觉滤波算法。
- 不写生产 MCAP_A。
- 不自动保存临时覆盖到正式配置。

## 5. 执行对象

- 开发者入口场景二功能检验项 `scene2_tactile_filter`
- [[TactileFilterResult]]
- 触觉滤波调试产物和运行日志

## 6. 执行依赖

- `service_s2_008` 已完成并归档，场景二数据补全开发者功能检验项可提供或展示上游补全产物。
- `service_s2_015` 已完成并归档，触觉滤波计算可用。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全开发者入口、触觉滤波计算
上游接口定义位置：数据补全器 L2、触觉滤波器 L2、service_s2_008、service_s2_015
当前 L3 期望消费的字段 / 文件 / 返回值：cleaned MCAP、signal_repair_result.json 或等价补全结果、TactileFilterConfig、TactileFilterResult
是否存在接口冲突：无
如果有冲突，本次处理策略：优先接入已有场景二入口模式；缺少上游 artifact 时给出清晰错误，不自行改写上游功能
```

## 8. 预期改动形态

- 开发者入口中出现或可选择 `scene2_tactile_filter` 功能检验项。
- 功能检验运行后写出 `tactile_filter_result.json`、`tactile_filter_diff_summary.json`、`filtered_tactile_sequences/` 和运行日志。
- 临时配置覆盖只对本次运行生效，默认不写回正式配置。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景二：硬件数据可靠性验证
↓
选择 scene2_tactile_filter
↓
选择 cleaned MCAP、signal_repair_result.json 和调试输出目录
↓
可选临时覆盖 median_window / ema_alpha / contact_reset_threshold / full_diff
↓
执行触觉滤波
↓
写出测试产物和运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| 补全结果加载 | 执行前 | `signal_repair_result.json` 或等价 artifact | [[SignalRepairResult]] | 写清 `missing_signal_repair_result` |
| 触觉滤波器 | 加载输入后 | cleaned MCAP、[[SignalRepairResult]]、[[TactileFilterConfig]] | [[TactileFilterResult]] | 写错误日志并停止本次功能检验 |
| 调试产物写出 | 滤波成功后 | [[TactileFilterResult]] | JSON、diff summary、filtered sequences | 写出失败原因和已生成文件 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `ready` | 输入选择完成 | 运行日志 | 显示输入和配置摘要 |
| `failed` | 输入缺失或滤波失败 | 运行日志 | 显示 reason 和缺失项 |
| `completed` | 产物写出完成 | 运行日志和终端摘要 | 显示输出目录 |

## 10. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 11. 现有程序盘点

- 先读取 `service_s2_008` 的入口接入方式，保持场景二功能检验菜单风格一致。
- 先检查 `start_data_clean.sh`、`src/data_clean/runtime/`、`src/data_clean/ui/` 中已有开发者入口结构。

## 12. 本 L3 的真实改造边界

- 允许新增 `scene2_tactile_filter` 菜单项、runner/CLI glue 和 smoke 测试。
- 允许写开发者调试产物到独立 run 目录。
- 禁止修改触觉滤波核心算法。
- 禁止把临时覆盖默认写回正式配置。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/触觉滤波器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/TactileFilterResult.md`
4. `DOCS/02_约束/阶段二任务体系/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_008_接入数据补全开发者功能检验项.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/service_s2_015_实现逐cell中值EMA触觉滤波与审计.md`

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
| 对应功能检验项 | `scene2_tactile_filter` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；`tactile_filter_result.json`、`tactile_filter_diff_summary.json`、`filtered_tactile_sequences/`、可选 `tactile_filter_full_diff/` |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景二和 `scene2_tactile_filter` |

## 16. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改触觉滤波核心算法。
- 禁止修改数据补全器输出语义。
- 禁止把开发者调试产物写入正式生产输出目录。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] `scene2_tactile_filter` 可从开发者入口触发或被 CLI/smoke 测试覆盖。
- [x] 功能检验写出触觉滤波结果、diff 摘要、滤波后序列和运行日志。
- [x] 临时覆盖配置只对本次运行生效，默认不写回正式配置。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/`。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_016_接入触觉滤波开发者功能检验项.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g4/service_s2_016_接入触觉滤波开发者功能检验项.md
文件名编号：service_s2_016
正文 L3 编号：service_s2_016
dispatch.task_id：service_s2_016
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_008_接入数据补全开发者功能检验项.md`、`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/service_s2_015_实现逐cell中值EMA触觉滤波与审计.md`，并参考 `service_s2_004`、`service_s2_012` 的场景二入口接入模式。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/runtime/scene2_tactile_filter.py`：新增场景二触觉滤波开发者运行编排，按 cleaned MCAP -> detection -> repair -> tactile_segment -> tactile_filter 顺序执行，并写出 `signal_reliability_detection_result.json`、`signal_repair_result.json`、`tactile_filter_result.json`、`tactile_filter_diff_summary.json`、`filtered_tactile_sequences/filtered_sequence_refs.json` 和 `run_log.json`。
- `src/data_clean/ui/dev_menu.py`：新增 `scene2_tactile_filter` 菜单项和 `run_scene2_tactile_filter_check` 入口。
- `src/data_clean/tests/runtime/test_scene2_tactile_filter_runtime.py`：新增 runtime 测试，覆盖触觉滤波结果、diff 摘要、滤波后序列 artifact、运行日志和菜单注册。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要后归档。

### TDD 过程

- Red：先新增 `src/data_clean/tests/runtime/test_scene2_tactile_filter_runtime.py`，运行 `python3 -m pytest src/data_clean/tests/runtime/test_scene2_tactile_filter_runtime.py -q`，按预期因 `ModuleNotFoundError: No module named 'runtime.scene2_tactile_filter'` 失败。
- Green：新增 `runtime.scene2_tactile_filter` 与 `ui.dev_menu` 菜单入口，复用场景二 detection / repair 编排，再接入 `split_tactile_segments`、`filter_tactile_segment`、`run_tactile_audit` 和 `aggregate_tactile_result`，目标测试通过。
- Refactor：将触觉修复后序列构建、输入序列引用、diff 摘要和 run stats 收敛为小函数；未修改触觉滤波核心算法和数据补全语义。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_tactile_filter_runtime.py -q`：通过，`2 passed`。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_tactile_filter_runtime.py src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py src/data_clean/tests/runtime/test_scene2_signal_repair_runtime.py src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py -q`：通过，`8 passed`。
- `python3 -m py_compile src/data_clean/runtime/scene2_tactile_filter.py src/data_clean/ui/dev_menu.py src/data_clean/tests/runtime/test_scene2_tactile_filter_runtime.py`：通过。
- `bash -n start_data_clean.sh`：通过。
- `printf '2\nq\n' | ./start_data_clean.sh --dev`：通过，实际展示场景二菜单，包含 `scene2_tactile_filter`。
- `printf '9\n' | ./start_data_clean.sh --dev`：通过，实际展示无效选择提示 `选择超出范围: 9`。
- `PYTHONPATH=src/data_clean:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap:src/data_collection/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support python3 - <<'PY' ... PY`：手动驱动 `run_scene2_tactile_filter()`，观察到 `status=success`，写出 `tactile_filter_result.json`、`tactile_filter_diff_summary.json` 和 `filtered_sequence_refs.json`。
- `python3 -m pytest src/data_clean/tests -q`：未通过；收集阶段因既有 `src/data_clean/tests/config_tests/test_frame_alignment_config.py` 导入 `repo.config.mcap_process_config.ExtrinsicConfig` 失败中断，该类型不在本 L3 修改范围内。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`；已用目标 pytest、相邻 runtime pytest、`py_compile`、shell 语法检查和开发者菜单手动验证替代。

### 成功标准核对

- 已验证 `scene2_tactile_filter` 可从 `./start_data_clean.sh --dev` 的场景二开发者入口看到，并被 runtime 测试覆盖。
- 已验证功能检验写出 `tactile_filter_result.json`、`tactile_filter_diff_summary.json`、`filtered_tactile_sequences/filtered_sequence_refs.json` 和 `run_log.json`。
- 已验证运行日志记录 `temporary_override_saved=false`，本 L3 不把临时配置覆盖写回正式配置。
- 本 L3 直接影响 `./start_data_clean.sh --dev` 的场景二菜单与 `scene2_tactile_filter` 功能检验项；建议用户后续运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_tactile_filter` 做最终人工验收。

### 本次明确未做

- 未修改触觉滤波核心算法。
- 未写 MCAP_A、生产 MCAP 或正式生产输出。
- 未修改调度索引、共享执行记录、阶段进度或 `DOCS/总执行日志.md`。

### 归档状态

- 当前 L3 完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g4/`。
- 原 active 功能组目录已为空并删除。

### 风险与后续建议

- 全量 `src/data_clean/tests` 当前被既有 `ExtrinsicConfig` 导入问题阻断；本 L3 新增测试和相邻场景二 runtime 测试已通过。
- 建议用户运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_tactile_filter`，用真实 cleaned MCAP 做最终人工验收。
