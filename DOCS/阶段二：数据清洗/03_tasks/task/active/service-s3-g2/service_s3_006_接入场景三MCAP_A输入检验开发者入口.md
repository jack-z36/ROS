# L3 微元任务：接入场景三 MCAP_A 输入检验开发者入口

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：MCAP_A 输入盘点与校验器  
L3 编号：service_s3_006  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_006_接入场景三MCAP_A输入检验开发者入口.md`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/MCAP_A输入盘点与校验器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_006
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/service_s3_006_接入场景三MCAP_A输入检验开发者入口.md
  group: service-s3-g2
  branch: service-s3
  wave: 3
  parallel_group: service-s3-g2-p3
  depends_on: [service_s3_005]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - start_data_clean.sh
      - src/data_clean/runtime/scene3_mcap_a_input_check.py
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
把 MCAP_A 输入盘点服务接入 ./start_data_clean.sh --dev 的场景三功能检验项，并写出 catalog / summary 调试产物和运行日志。
```

## 4. 本次不做

- 不修改输入盘点服务的核心计算规则。
- 不生成 [[StepTimeline]]。
- 不实现多策略字段对齐或 aligned MCAP 写出。
- 不保存临时覆盖到正式配置文件。

## 5. 执行对象

- `scene3_mcap_a_input_check` 开发者功能检验项
- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]
- `source_topic_catalog.json`
- `mcap_a_input_validation_summary.json`
- 场景三开发者 run 日志

## 6. 执行依赖

- `service_s3_005` 必须已完成并归档，确保 MCAP_A 输入盘点服务可调用。
- 必须复用现有 `src/data_clean/ui/dev_menu.py` 的场景菜单结构。
- 必须遵守开发者输出隔离：调试产物进入独立 run 目录，不写正式生产输出。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：MCAP_A 输入盘点与校验服务、Runtime run 目录和开发者菜单
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/MCAP_A输入盘点与校验器.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_005_实现MCAP_A输入盘点与校验服务.md
- src/data_clean/service/mcap_a_input_validator.py
- src/data_clean/ui/dev_menu.py
当前 L3 期望消费的字段 / 文件 / 返回值：
- 输入盘点服务返回 SourceTopicCatalog 与 McapAInputValidationSummary
- 开发者 CLI 参数中的 config/run_root，以及用户选择的 MCAP_A 和 summary 路径
- 独立 run 目录与运行日志写入能力
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得重写输入盘点服务；停止并记录服务接口缺口或菜单接入冲突
```

## 8. 预期改动形态

- 新增 `src/data_clean/runtime/scene3_mcap_a_input_check.py`，封装开发者功能检验项的运行流程。
- 更新 `src/data_clean/ui/dev_menu.py`，在场景三菜单中注册 `scene3_mcap_a_input_check`。
- 开发者运行后在独立 run 目录写出 `source_topic_catalog.json`、`mcap_a_input_validation_summary.json` 和运行日志。
- 新增 CLI / smoke 测试，验证菜单项注册、运行函数调用和调试产物写出。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景三：MCAP 多 topic 时间轴对齐
↓
选择 scene3_mcap_a_input_check
↓
选择或输入 MCAP_A 路径、mcap_a_write_summary.json 路径和调试输出位置
↓
读取场景三配置，可临时覆盖输入路径和输出目录
↓
调用 MCAP_A 输入盘点与校验服务
↓
写出 source_topic_catalog.json、mcap_a_input_validation_summary.json、run_log
↓
终端展示 status、hard fail、warning、输出位置
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| `run_scene3_mcap_a_input_check` | 菜单选择后 | MCAP_A、summary、config、run_root | 结构化 result dict | 返回失败状态并打印错误 |
| `mcap_a_input_validator` 服务 | runtime wrapper 内 | [[Scene3AlignmentConfig]]、MCAP_A、summary | [[SourceTopicCatalog]]、[[McapAInputValidationSummary]] | 写 summary，返回非 0 |
| run 日志写入能力 | 服务完成或失败后 | 输入、配置、状态、输出路径 | run log JSON | 记录错误信息，不写正式产物 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `success` | summary `status=consumable` | run log、validation summary | 显示 MCAP_A 可消费和输出路径 |
| `failed` | hard fail 或运行异常 | run log、validation summary 或 error summary | 显示 hard fail reasons 和输出路径 |
| `warning` | 非基准字段 warning | run log、catalog、validation summary | 显示 warning 数量和 catalog 路径 |

## 10. 流程编排验收重点

- 场景三菜单出现 `scene3_mcap_a_input_check`。
- 调用顺序只负责选择输入、调用服务、写产物、展示摘要，不包含底层盘点算法。
- 失败时仍写出可复查的 validation summary 或 run log，不留下误导性成功状态。
- 产物写入独立 run 目录，不污染正式 `asset/阶段二：数据清洗/dev/mcap_aligned/`。

## 11. 现有程序盘点

- `src/data_clean/ui/dev_menu.py` 已注册场景一和场景二功能检验项，`SCENE_MENUS` 中场景三当前是空列表；本 L3 需要按现有 `SCENE2_CHECKS` 方式新增场景三 checks。
- `src/data_clean/runtime/scene2_mcap_a_writer.py` 已提供场景二开发者入口 runtime wrapper，可作为 run 目录、输出 dict 和日志字段风格参考。
- `src/data_clean/runtime/run_directory_creator.py`、`structured_log_writer.py`、相关 runtime 工具已经承担 run 目录和日志能力，本 L3 应复用现有风格。
- `start_data_clean.sh` 已作为统一入口调用 dev menu；除非现有参数缺失，否则不应大改入口脚本。

## 12. 本 L3 的真实改造边界

- 允许新增场景三 runtime wrapper 和 dev menu 注册。
- 允许新增小范围 CLI / smoke 测试来验证菜单和产物写出。
- 禁止重写 `dev_menu.py` 的整体交互框架。
- 禁止修改输入盘点服务 hard fail / warning 规则。
- 禁止实现后续时间轴、字段对齐或写出器功能。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/MCAP_A输入盘点与校验器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/TargetFieldMapping.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_005_实现MCAP_A输入盘点与校验服务.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/service_s3_004_定义MCAP_A输入盘点与校验类型.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g1/service_s3_001_定义场景三配置与schema.md`

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

1. `src/data_clean/service/mcap_a_input_validator.py`
2. `src/data_clean/runtime/scene2_mcap_a_writer.py`
3. `src/data_clean/runtime/run_directory_creator.py`
4. `src/data_clean/runtime/structured_log_writer.py`
5. `src/data_clean/ui/dev_menu.py`
6. `start_data_clean.sh`

## 14. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及入口编排变更，必须使用 `$tdd` 技能。建议顺序：菜单注册测试 -> 最小菜单接入 -> runtime wrapper 产物写出测试 -> 失败状态测试 -> CLI / smoke 验证。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_mcap_a_input_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是，注册场景三功能检验项 |
| 是否需要写测试产物 | 是；`source_topic_catalog.json`、`mcap_a_input_validation_summary.json` |
| 是否需要写运行日志 | 是；最低字段：输入 MCAP_A、summary、配置来源、hard fail、warning、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许，本 L3 不实现自动保存 |
| 最终人工验收提示 | 本 L3 完成后，用户运行 `./start_data_clean.sh --dev` 选择场景三和 `scene3_mcap_a_input_check` 做最终人工验收 |

## 16. 允许修改

- `src/data_clean/runtime/scene3_mcap_a_input_check.py`
- `src/data_clean/ui/dev_menu.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 必要时小范围修改 `start_data_clean.sh`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止重写 `dev_menu.py` 的整体菜单框架。
- 禁止修改输入盘点服务的核心 hard fail / warning 规则。
- 禁止实现 [[StepTimeline]]、字段对齐或 aligned MCAP 写出。
- 禁止把调试产物写入正式生产目录。
- 禁止写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.ui.dev_menu import SCENE_MENUS

scene3 = next(checks for scene_id, _label, checks in SCENE_MENUS if scene_id == "scene3")
ids = [check_id for check_id, _label, _runner in scene3]
assert "scene3_mcap_a_input_check" in ids
PY
```

## 19. 成功标准

- [ ] `./start_data_clean.sh --dev` 的场景三菜单包含 `scene3_mcap_a_input_check`。
- [ ] 功能检验项能调用 MCAP_A 输入盘点服务并返回结构化状态。
- [ ] 成功或失败时都写出 `source_topic_catalog.json`、`mcap_a_input_validation_summary.json` 或可复查 run log。
- [ ] 运行日志包含输入、配置来源、hard fail、warning 和输出位置。
- [ ] 调试产物写入独立 run 目录，不污染正式生产输出。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 20. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 完成并更新任务文件后，将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g2/`。
- 移动后如果 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g2/` 已经为空，删除该空 active 功能组目录。
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`。

交接摘要必须包含模板要求的 12 项内容，尤其说明已读取 `service_s3_005` 完成记录、TDD red / green / refactor、验收命令结果和建议用户运行 `./start_data_clean.sh --dev` 的场景三 `scene3_mcap_a_input_check`。
