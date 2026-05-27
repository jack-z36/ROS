# L3 微元任务：接入位姿滤波开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：位姿滤波器
L3 编号：service_s2_012
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_012_接入位姿滤波开发者功能检验项.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_012
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_012_接入位姿滤波开发者功能检验项.md
  group: service-s2-g3
  branch: service-s2
  wave: 4
  parallel_group: service-s2-g3-p4
  depends_on: [service_s2_008, service_s2_011]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [start_data_clean.sh, src/data_clean/runtime/, src/data_clean/ui/, src/data_clean/tests/]
    modules: [data_clean.runtime, data_clean.ui]
    config_keys: [dev_menu.scene2.pose_filter]
  dispatch_status: ready
```

## 3. 本次目标

```text
把位姿滤波器接入 `./start_data_clean.sh --dev` 的场景二独立功能检验项 `scene2_pose_filter`。
```

## 4. 本次不做

- 不实现底层滤波算法。
- 不修改异常检测或数据补全规则。
- 不写正式生产 MCAP_A。

## 5. 执行对象

- 场景二开发者功能检验项 `scene2_pose_filter` / 检查位姿滤波。
- 位姿滤波调试产物和运行日志。

## 6. 执行依赖

- `service_s2_008` 已完成并归档，数据补全开发者入口可输出补全结果。
- `service_s2_011` 已完成并归档，位姿滤波计算能力可调用。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全开发者入口、位姿滤波计算能力
上游接口定义位置：service_s2_008 执行结果、service_s2_011 执行结果、PoseFilterResult.md
当前 L3 期望消费的字段 / 文件 / 返回值：signal_repair_result.json、补全后 pose 序列、PoseFilterResult
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报，不在入口层猜测底层接口
```

## 8. 预期改动形态

- 开发者入口中出现场景二功能检验项 `scene2_pose_filter`。
- 运行后在独立 run 目录写出 `pose_filter_result.json`、差异摘要、滤波后序列 artifact 和运行日志。
- 场景二完整 smoke test 能串联到位姿滤波检验能力。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景二：硬件数据可靠性验证
↓
选择 scene2_pose_filter / 检查位姿滤波
↓
选择 cleaned MCAP、检测结果、补全结果和调试输出目录
↓
读取临时覆盖的 PoseFilterConfig
↓
调用位姿滤波 service
↓
写出 pose_filter_result.json、差异摘要、运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| 数据补全结果读取 | 执行开始 | `signal_repair_result.json` | [[SignalRepairResult]] | 写运行日志并失败退出 |
| 位姿滤波 service | 输入准备完成后 | [[PoseFilterInputSequence]]、[[PoseFilterConfig]] | [[PoseFilterResult]] | 写错误摘要，不写正式产物 |
| 调试产物写出 | 滤波成功后 | [[PoseFilterResult]] | JSON、diff summary、序列 artifact | 写运行日志并失败退出 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `input_loaded` | 输入读取成功 | run log | 显示输入路径和样本数 |
| `filter_completed` | 滤波完成 | run log、result JSON | 显示 filtered/kept/rejected 统计 |
| `filter_failed` | 输入或计算失败 | run log、error summary | 显示失败 reason 和输出位置 |

## 10. 流程编排验收重点

- 调用顺序正确。
- 不把调试产物写入正式生产目录。
- 运行日志包含输入、配置、分段统计、guard 拒绝统计和输出位置。
- 不把底层算法细节写进入口层。

## 11. 现有程序盘点

- `start_data_clean.sh` 是阶段二统一入口。
- `src/data_clean/runtime/` 和 `src/data_clean/ui/` 已承载 Runtime / 开发者入口相关能力。
- 现有场景二功能检验项由 `service_s2_004` 和 `service_s2_008` 逐步接入；本 L3 只新增位姿滤波检验项。

## 12. 本 L3 的真实改造边界

- 允许新增场景二 `scene2_pose_filter` 菜单项、runner 或 CLI glue。
- 允许新增 smoke/CLI 测试。
- 禁止改写底层位姿滤波算法。
- 禁止把临时覆盖自动写回生产配置。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_008_接入数据补全开发者功能检验项.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_011_实现位置姿态滤波与guard审计.md`

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
4. `src/data_clean/service/`
5. `src/data_clean/tests/`

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
| 对应功能检验项 | `scene2_pose_filter` / 检查位姿滤波 |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；`pose_filter_result.json`、`pose_filter_diff_summary.json`、滤波后序列 artifact |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景二和 `scene2_pose_filter` |

## 16. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止改写底层滤波算法。
- 禁止修改异常检测或数据补全规则。
- 禁止把调试产物写入正式生产输出目录。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] 开发者入口包含 `scene2_pose_filter`。
- [x] 功能检验项能写出 `pose_filter_result.json` 和差异摘要。
- [x] 运行日志包含输入、配置、分段统计、guard 拒绝统计和输出位置。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。


## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_012_接入位姿滤波开发者功能检验项.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_012_接入位姿滤波开发者功能检验项.md
文件名编号：service_s2_012
正文 L3 编号：service_s2_012
dispatch.task_id：service_s2_012
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on` 和 `dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_008_接入数据补全开发者功能检验项.md`、`DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_011_实现位置姿态滤波与guard审计.md`，确认本 L3 复用异常检测、数据补全、位姿分段与位姿滤波接口，不改底层算法。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/runtime/scene2_pose_filter.py`：新增场景二位姿滤波开发者运行编排，在独立 run 目录内串联 cleaned MCAP 加载、异常检测、数据补全、pose 分段、pose filter，并写出 `pose_filter_result.json`、`pose_filter_diff_summary.json`、`filtered_pose_sequences/filtered_sequence_refs.json` 和 `run_log.json`。
- `src/data_clean/ui/dev_menu.py`：新增 `scene2_pose_filter` 菜单项和 `run_scene2_pose_filter_check` 入口。
- `src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py`：新增 runtime 测试，覆盖结果 JSON、差异摘要、滤波后序列 artifact、运行日志和菜单注册。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py`，运行 `python3 -m pytest src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py -q`，按预期因 `ModuleNotFoundError: No module named 'runtime.scene2_pose_filter'` 失败。
- Green：新增 `runtime.scene2_pose_filter` 与 `ui.dev_menu` 菜单入口，复用 `scene2_signal_repair` 的检测和修复编排，接入 `service.pose_segment.split_reliable_segments` 与 `service.pose_filter.filter_pose_segments`，目标测试通过。
- Refactor：将补全后 pose 序列构造、pose 未修复边界、输入序列引用、差异摘要、分段统计、guard 统计和 JSON 序列化拆为局部辅助函数；入口层只做编排和 artifact 写出，不改滤波算法。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py -q`：通过，`2 passed`。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py src/data_clean/tests/runtime/test_scene2_signal_repair_runtime.py src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py src/data_clean/tests/service/test_pose_segment.py src/data_clean/tests/service/test_pose_filter.py -q`：通过，`17 passed`。
- `python3 -m py_compile src/data_clean/runtime/scene2_pose_filter.py src/data_clean/ui/dev_menu.py src/data_clean/tests/runtime/test_scene2_pose_filter_runtime.py`：通过。
- `bash -n start_data_clean.sh`：通过。
- `printf '2\nq\n' | ./start_data_clean.sh --dev`：通过，实际展示场景二菜单，包含 `scene2_pose_filter`。
- `printf '9\n' | ./start_data_clean.sh --dev`：通过，实际展示无效选择提示 `选择超出范围: 9`。
- `PYTHONPATH=src/data_clean src/data_clean/.conda-envs/data-clean/bin/python - <<'PY' ...`：通过手动驱动 `run_scene2_pose_filter`，观察到 `status=success`，且 `pose_filter_result.json`、`pose_filter_diff_summary.json`、`filtered_sequence_refs.json` 均写出。
- `python3 -m pytest src/data_clean/tests -q`：未通过；收集阶段因既有 `src/data_clean/tests/config_tests/test_frame_alignment_config.py` 导入 `repo.config.mcap_process_config.ExtrinsicConfig` 失败中断，该类型不在本 L3 修改范围内。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`；已用目标 pytest、相邻 runtime/service pytest、`py_compile`、shell 语法检查、开发者菜单和手动 runtime 驱动替代。

### 成功标准核对

- 已验证场景二 dev 菜单包含 `scene2_pose_filter`。
- 已验证功能检验项写出 `pose_filter_result.json`、`pose_filter_diff_summary.json` 和滤波后序列 artifact。
- 已验证运行日志包含输入、配置、分段统计、guard 拒绝统计和输出位置。
- 本 L3 直接影响 `./start_data_clean.sh --dev` 的场景二菜单与 `scene2_pose_filter` 功能检验项；建议用户后续运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_pose_filter` 做最终人工验收。

### 本次明确未做

- 未修改异常检测、数据补全、pose 分段或 pose filter 底层算法。
- 未写正式生产输出，未写 MCAP_A。
- 未修改调度索引、共享执行记录、阶段进度或 `DOCS/总执行日志.md`。

### 归档状态

- 当前 L3 完成后移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。
- 原 active 功能组目录已为空并删除。

### 风险与后续建议

- 全量 `src/data_clean/tests` 当前被既有 `ExtrinsicConfig` 导入问题阻断；本 L3 新增和相邻 runtime/service 测试已通过。
- 建议用户运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_pose_filter`，用真实 cleaned MCAP 做最终人工验收。
