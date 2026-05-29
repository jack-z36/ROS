# L3 微元任务：接入场景三 Step 时间轴开发者检验项

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：统一 Step 时间轴生成器  
L3 编号：service_s3_009  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_009_接入场景三Step时间轴开发者检验项.md`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_009
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/service_s3_009_接入场景三Step时间轴开发者检验项.md
  group: service-s3-g3
  branch: service-s3
  wave: 3
  parallel_group: service-s3-g3-p3
  depends_on: [service_s3_006, service_s3_008]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - start_data_clean.sh
      - src/data_clean/runtime/scene3_step_timeline_check.py
      - src/data_clean/ui/dev_menu.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.runtime
      - data_clean.ui
    config_keys:
      - scene3_alignment
  dispatch_status: ready
```

## 3. 本次目标

```text
把统一 Step 时间轴生成服务接入 ./start_data_clean.sh --dev 的场景三功能检验项，并写出时间轴与生成摘要调试产物。
```

## 4. 本次不做

- 不修改 Step 时间轴生成服务的核心计算规则。
- 不修改 MCAP_A 输入盘点服务。
- 不实现多策略字段对齐、alignment index 生成或 aligned MCAP 写出。
- 不保存临时覆盖到正式配置文件。

## 5. 执行对象

- `scene3_step_timeline_check` 开发者功能检验项
- [[StepTimeline]]
- [[StepTimelineGenerationSummary]]
- `step_timeline.json` 或等价结构化产物
- `step_timeline_generation_summary.json`
- 场景三开发者 run 日志

## 6. 执行依赖

- `service_s3_006` 必须已完成并归档，确保场景三开发者菜单和 MCAP_A 输入检验入口已有可复用接入模式。
- `service_s3_008` 必须已完成并归档，确保统一 Step 时间轴生成服务可调用。
- 必须遵守开发者输出隔离：调试产物进入独立 run 目录，不写正式生产输出。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：统一 Step 时间轴生成服务、场景三 MCAP_A 输入检验开发者入口、Runtime run 目录和开发者菜单
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_006_接入场景三MCAP_A输入检验开发者入口.md
- src/data_clean/service/step_timeline_generator.py
- src/data_clean/ui/dev_menu.py
当前 L3 期望消费的字段 / 文件 / 返回值：
- SourceTopicCatalog JSON 或对象
- McapAInputValidationSummary JSON 或对象
- Scene3AlignmentConfig 对象 / 配置
- Step 时间轴生成服务返回的 StepTimeline 和 StepTimelineGenerationSummary
- 独立 run 目录与运行日志写入能力
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得重写底层生成服务；停止并记录服务接口缺口或菜单接入冲突
```

## 8. 预期改动形态

- 新增 `src/data_clean/runtime/scene3_step_timeline_check.py`，封装开发者功能检验项运行流程。
- 更新 `src/data_clean/ui/dev_menu.py`，在场景三菜单中注册 `scene3_step_timeline_check`。
- 开发者运行后在独立 run 目录写出 `step_timeline.json` 或等价结构化产物、`step_timeline_generation_summary.json` 和运行日志。
- 新增 CLI / smoke 测试，验证菜单项注册、运行函数调用、成功产物写出和失败摘要写出。
- 必要时更新 `src/data_clean/data_clean_architecture.md`。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景三：MCAP 多 topic 时间轴对齐
↓
选择 scene3_step_timeline_check
↓
选择或输入 source_topic_catalog.json、mcap_a_input_validation_summary.json 和调试输出位置
↓
读取场景三配置，可临时覆盖 target_step_hz 和输入文件路径
↓
调用统一 Step 时间轴生成服务
↓
写出 step_timeline.json、step_timeline_generation_summary.json、run_log
↓
终端展示 status、step_count、起止时间、失败原因和输出位置
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| `run_scene3_step_timeline_check` | 菜单选择后 | catalog、validation summary、config、run_root | 结构化 result dict | 返回失败状态并打印错误 |
| `step_timeline_generator` 服务 | runtime wrapper 内 | [[SourceTopicCatalog]]、[[McapAInputValidationSummary]]、[[Scene3AlignmentConfig]] | [[StepTimeline]]、[[StepTimelineGenerationSummary]] | 写 failure summary，返回非 0 |
| run 日志写入能力 | 服务完成或失败后 | 输入、配置、状态、输出路径 | run log JSON | 记录错误信息，不写正式产物 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `generated` | 成功生成 [[StepTimeline]] | run log、generation summary、timeline 产物 | 显示 step_count、first/last step 和输出路径 |
| `failed` | 输入不可消费、缺失 baseline、无效频率或运行异常 | run log、generation summary 或 error summary | 显示 failure reasons 和输出路径 |
| `warning` | 上游 optional field warning 存在但不影响时间轴 | run log | 显示 warning 数量，说明不阻塞时间轴生成 |

## 10. 流程编排验收重点

- 场景三菜单出现 `scene3_step_timeline_check`。
- 调用顺序只负责加载输入、调用服务、写产物、展示摘要，不包含时间轴算法细节。
- 失败时仍写出可复查的 generation summary 或 run log，不留下误导性成功状态。
- 产物写入独立 run 目录，不污染正式 `asset/阶段二：数据清洗/dev/mcap_aligned/`。

## 11. 现有程序盘点

- `src/data_clean/ui/dev_menu.py` 已有场景功能检验菜单结构，场景三的 MCAP_A 输入检验项预计由 `service_s3_006` 接入；本 L3 应沿用同一注册方式。
- `src/data_clean/runtime/scene3_mcap_a_input_check.py` 预计由 `service_s3_006` 生成，可作为场景三 runtime wrapper 风格参考。
- `src/data_clean/runtime/run_directory_creator.py`、`structured_log_writer.py`、相关 runtime 工具已经承担 run 目录和日志能力，本 L3 应复用现有风格。
- `src/data_clean/service/step_timeline_generator.py` 预计由 `service_s3_008` 生成，本 L3 只调用服务，不改变算法。

## 12. 本 L3 的真实改造边界

- 允许新增场景三 Step 时间轴 runtime wrapper 和 dev menu 注册。
- 允许新增小范围 CLI / smoke 测试来验证菜单、产物写出和失败状态。
- 禁止重写 `dev_menu.py` 的整体交互框架。
- 禁止修改 Step 时间轴生成服务计算规则。
- 禁止实现后续字段对齐、report 汇总或写出器功能。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/统一Step时间轴生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimelineGenerationSummary.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
6. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_008_实现统一Step时间轴生成服务.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_006_接入场景三MCAP_A输入检验开发者入口.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_007_定义Step时间轴生成摘要类型.md`

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

1. `src/data_clean/service/step_timeline_generator.py`
2. `src/data_clean/runtime/scene3_mcap_a_input_check.py`
3. `src/data_clean/runtime/run_directory_creator.py`
4. `src/data_clean/runtime/structured_log_writer.py`
5. `src/data_clean/ui/dev_menu.py`
6. `start_data_clean.sh`
7. `src/data_clean/tests/`

## 14. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及入口编排变更，必须使用 `$tdd` 技能。建议顺序：菜单注册测试 -> 最小菜单接入 -> runtime wrapper 成功产物写出测试 -> 失败摘要写出测试 -> CLI / smoke 验证。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_step_timeline_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是，注册场景三功能检验项 |
| 是否需要写测试产物 | 是；`step_timeline.json` 或等价结构化产物、`step_timeline_generation_summary.json` |
| 是否需要写运行日志 | 是；最低字段：catalog 路径、validation summary 路径、配置来源、target step Hz、baseline 起止时间、step_count、失败原因、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许，本 L3 不实现自动保存 |
| 最终人工验收提示 | 本 L3 完成后，用户运行 `./start_data_clean.sh --dev` 选择场景三和 `scene3_step_timeline_check` 做最终人工验收 |

## 16. 允许修改

- `src/data_clean/runtime/scene3_step_timeline_check.py`
- `src/data_clean/ui/dev_menu.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- `start_data_clean.sh`（仅当现有统一入口无法路由到新增菜单项时）
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改 Step 时间轴生成服务核心算法。
- 禁止修改 MCAP_A 输入盘点服务 hard fail / warning 规则。
- 禁止实现字段对齐、report 汇总或 aligned MCAP 写出。
- 禁止把调试产物写入正式生产输出目录。
- 禁止修改共享执行记录或当前进度文档。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.runtime.scene3_step_timeline_check import run_scene3_step_timeline_check
assert callable(run_scene3_step_timeline_check)
PY
```

## 19. 成功标准

- [ ] 场景三开发者菜单已注册 `scene3_step_timeline_check`。
- [ ] runtime wrapper 能调用时间轴生成服务并写出时间轴产物和生成摘要。
- [ ] 失败时能写出 failure summary 或 run log，不留下误导性成功状态。
- [ ] 调试产物进入独立 run 目录，不污染正式生产输出。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 20. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 从 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/` 移到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/`
- 移动后如果 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g3/` 已经为空，删除该空 active 功能组目录
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

交接摘要必须包含：

1. 读取了哪些相关 L3 任务文件或执行记录
2. 任务文件身份校验结论：用户指定路径、实际读取路径、文件名编号、正文 L3 编号是否一致
3. 修改了哪些文件
4. 新增或修改了哪些函数 / 测试
5. TDD red / green / refactor 如何执行
6. 如何运行阶段二开工自检与 L3 验收，Python 命令必须使用 `python3`
7. 成功标准勾选情况
8. 归档目标是否为 `task/completed/04-service-s3/service-s3-g3/`，以及是否已删除空 active 功能组目录
9. 本 L3 对 `./start_data_clean.sh --dev` 开发者验收入口、功能检验项或场景完整 smoke test 的影响
10. 当前没做什么
11. 建议用户后续运行 `./start_data_clean.sh --dev` 的哪个场景、哪个功能检验项或 smoke test 做最终人工验收
12. 建议 Win 端后续同步整理什么
