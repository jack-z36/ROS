# L3 微元任务：接入场景三字段对齐开发者检验项

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：多策略字段对齐器  
L3 编号：service_s3_014  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_014_接入场景三字段对齐开发者检验项.md`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_014
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g4/service_s3_014_接入场景三字段对齐开发者检验项.md
  group: service-s3-g4
  branch: service-s3
  wave: 3
  parallel_group: service-s3-g4-p3
  depends_on: [service_s3_011, service_s3_012, service_s3_013]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - start_data_clean.sh
      - src/data_clean/runtime/scene3_field_alignment_check.py
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
把多策略字段对齐服务接入 ./start_data_clean.sh --dev 的场景三功能检验项，并写出字段对齐调试产物。
```

## 4. 本次不做

- 不修改字段对齐算法。
- 不生成 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 不保存临时覆盖到正式配置文件。
- 不修改场景四或训练格式导出逻辑。

## 5. 执行对象

- `scene3_field_alignment_check` 开发者功能检验项
- [[FieldAlignmentResult]]
- `field_alignment_results.json` 或等价结构化产物
- 场景三开发者 run 日志

## 6. 执行依赖

- `service_s3_011`、`service_s3_012`、`service_s3_013` 必须已完成并归档。
- 建议 `service_s3_009` 已完成并归档，以便复用场景三时间轴检验入口和 run 目录写出风格。
- 必须遵守开发者输出隔离：调试产物进入独立 run 目录，不写正式生产输出。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：多策略字段对齐服务、场景三时间轴开发者入口、Runtime run 目录和开发者菜单
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_012_实现pose插值slerp与fallback.md
- DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- MCAP_A 小样本或 source message reader
- SourceTopicCatalog、McapAInputValidationSummary、StepTimeline、Scene3AlignmentConfig
- FieldAlignmentResult 列表或等价结果
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：不得重写底层算法；停止并记录服务接口缺口或菜单接入冲突
```

## 8. 预期改动形态

- 新增 `src/data_clean/runtime/scene3_field_alignment_check.py`，封装开发者功能检验项运行流程。
- 更新 `src/data_clean/ui/dev_menu.py`，在场景三菜单中注册 `scene3_field_alignment_check`。
- 开发者运行后在独立 run 目录写出 `field_alignment_results.json` 或等价结构化产物和运行日志。
- 新增 CLI / smoke 测试，验证菜单项注册、运行函数调用、成功产物写出和失败状态写出。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景三：MCAP 多 topic 时间轴对齐
↓
选择 scene3_field_alignment_check
↓
选择或输入 MCAP_A 小样本、source_topic_catalog、validation_summary、step_timeline 和调试输出位置
↓
读取场景三配置，可临时覆盖字段策略、阈值和输入路径
↓
调用多策略字段对齐服务
↓
写出 field_alignment_results.json 和 run_log
↓
终端展示各字段 status 计数、失败原因和输出位置
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| `run_scene3_field_alignment_check` | 菜单选择后 | MCAP_A、catalog、summary、timeline、config、run_root | 结构化 result dict | 返回失败状态并打印错误 |
| 字段对齐服务 | runtime wrapper 内 | [[StepTimeline]]、[[SourceTopicCatalog]]、[[McapAInputValidationSummary]]、配置和源消息 | [[FieldAlignmentResult]] 列表 | 写 failure summary，返回非 0 |
| run 日志写入能力 | 服务完成或失败后 | 输入、配置、状态、输出路径 | run log JSON | 记录错误信息，不写正式产物 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `completed` | 字段对齐服务完成 | run log、field alignment results | 显示字段数量、step 数和 status 计数 |
| `failed` | 输入不可消费、timeline 缺失、配置错误或运行异常 | run log 或 error summary | 显示 failure reasons 和输出路径 |
| `warning` | optional 字段不可用、timeout、fallback 或 missing | run log、result status counts | 显示 warning / 降级计数 |

## 10. 流程编排验收重点

- 场景三菜单出现 `scene3_field_alignment_check`。
- 调用顺序只负责加载输入、调用服务、写产物、展示摘要，不包含底层算法细节。
- 失败时仍写出可复查的运行日志或错误摘要，不留下误导性成功状态。
- 产物写入独立 run 目录，不污染正式 `asset/阶段二：数据清洗/dev/mcap_aligned/`。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/多策略字段对齐器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/FieldAlignmentResult.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/SourceTopicCatalog.md`
4. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/McapAInputValidationSummary.md`
5. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/StepTimeline.md`
6. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/Scene3AlignmentConfig.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_011_实现图像与夹爪最近邻对齐.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_012_实现pose插值slerp与fallback.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/service_s3_013_实现触觉半step窗口聚合.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g3/service_s3_009_接入场景三Step时间轴开发者检验项.md`

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

1. `src/data_clean/runtime/scene3_step_timeline_check.py`
2. `src/data_clean/runtime/run_directory_creator.py`
3. `src/data_clean/runtime/structured_log_writer.py`
4. `src/data_clean/ui/dev_menu.py`
5. `src/data_clean/service/field_aligner.py`
6. `start_data_clean.sh`
7. `src/data_clean/tests/`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及入口编排变更，必须使用 `$tdd` 技能。建议顺序：菜单注册测试 -> 最小菜单接入 -> runtime wrapper 成功产物写出测试 -> 失败摘要写出测试 -> CLI / smoke 验证。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_field_alignment_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是，注册场景三功能检验项 |
| 是否需要写测试产物 | 是；`field_alignment_results.json` 或等价结构化产物 |
| 是否需要写运行日志 | 是；最低字段：输入 MCAP_A、catalog 路径、validation summary 路径、timeline 路径、配置来源、target fields、status 计数、失败原因、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许，本 L3 不实现自动保存 |
| 最终人工验收提示 | 本 L3 完成后，用户运行 `./start_data_clean.sh --dev` 选择场景三和 `scene3_field_alignment_check` 做最终人工验收 |

## 14. 允许修改

- `src/data_clean/runtime/scene3_field_alignment_check.py`
- `src/data_clean/ui/dev_menu.py`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- `start_data_clean.sh`（仅当现有统一入口无法路由到新增菜单项时）
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止修改字段对齐服务核心算法。
- 禁止生成 AlignmentIndex、AlignmentReport 或 aligned MCAP。
- 禁止把调试产物写入正式生产输出目录。
- 禁止修改场景四或训练格式导出逻辑。
- 禁止修改共享执行记录或当前进度文档。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
python3 - <<'PY'
from data_clean.runtime.scene3_field_alignment_check import run_scene3_field_alignment_check
assert callable(run_scene3_field_alignment_check)
PY
```

## 17. 成功标准

- [ ] 场景三开发者菜单已注册 `scene3_field_alignment_check`。
- [ ] runtime wrapper 能调用字段对齐服务并写出字段对齐结果产物。
- [ ] 失败时能写出 failure summary 或 run log，不留下误导性成功状态。
- [ ] 调试产物进入独立 run 目录，不污染正式生产输出。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g4/`。如果 `active/service-s3-g4/` 为空，删除该空目录。不得写共享执行记录。
