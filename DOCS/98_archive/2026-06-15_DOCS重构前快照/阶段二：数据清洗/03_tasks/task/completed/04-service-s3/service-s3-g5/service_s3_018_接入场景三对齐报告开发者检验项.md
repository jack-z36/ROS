# L3 微元任务：接入场景三对齐报告开发者检验项

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：对齐索引与报告数据生成器  
L3 编号：service_s3_018  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_018_接入场景三对齐报告开发者检验项.md`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_018
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_018_接入场景三对齐报告开发者检验项.md
  group: service-s3-g5
  branch: service-s3
  wave: 4
  parallel_group: service-s3-g5-p4
  depends_on: [service_s3_016, service_s3_017]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - start_data_clean.sh
      - src/data_clean/runtime/scene3_alignment_report_check.py
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
把 AlignmentIndex 预览和 AlignmentReport draft 生成接入场景三开发者检验项 scene3_alignment_report_check。
```

## 4. 本次不做

- 不接入 aligned MCAP 写出。
- 不写正式 `alignment_index.parquet` 或 `alignment_report.json`。
- 不修改字段对齐算法。

## 5. 执行对象

- `scene3_alignment_report_check` 开发者检验项
- AlignmentIndex 预览产物
- AlignmentReport draft 调试产物

## 6. 执行依赖

- `service_s3_016` 应已实现 AlignmentIndex 规范化。
- `service_s3_017` 应已实现 AlignmentReport draft 统计生成。
- 必须复用现有开发者入口 / UI 菜单风格。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：AlignmentIndex 规范化与 AlignmentReport draft 统计生成
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- 规范化 index records
- report draft object
- 小样本 field_alignment_results 输入
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并汇报，不自行兼容多个服务入口
```

## 8. 预期改动形态

- 新增或扩展 runtime / UI 开发者检验入口。
- 检验项输出 `alignment_index_preview.json` 或等价结构化预览、`alignment_report_draft.json` 和运行日志。
- 自动化测试覆盖菜单 / runner 调用与失败路径。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景三：MCAP 多 topic 时间轴对齐
↓
选择 scene3_alignment_report_check
↓
读取小样本 field_alignment_results / timeline / catalog / config
↓
调用 AlignmentIndex 规范化服务
↓
调用 AlignmentReport draft 统计服务
↓
写调试产物和运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| AlignmentIndex 规范化服务 | 读取小样本后 | FieldAlignmentResult | index records | 写失败日志并停止 |
| AlignmentReport draft 统计服务 | index 生成后 | index、timeline、summary、config | report draft | 写失败日志并停止 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `completed` | index 预览和 report draft 都生成 | run log | 输出产物路径 |
| `failed` | 输入缺失或服务失败 | run log / error summary | 失败原因 |

## 10. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/对齐索引与报告数据生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentIndex.md`
3. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignmentReport.md`
4. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/service_s3_016_实现AlignmentIndex规范化与唯一性检查.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/service_s3_017_实现AlignmentReport草稿统计生成.md`

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

本 L3 涉及入口编排，必须使用 `$tdd` 技能。建议顺序：runner 调用顺序测试 -> 产物写入测试 -> 失败路径测试 -> 菜单接入测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_alignment_report_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；产物类型：index 预览、report draft |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景三和 `scene3_alignment_report_check` / 场景完整 smoke test |

## 14. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止实现 aligned MCAP 写出器。
- 禁止写正式生产数据产物。
- 禁止修改字段对齐算法。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [x] 已接入 `scene3_alignment_report_check`。
- [x] 检验项能生成 index 预览和 report draft 调试产物。
- [x] 运行日志包含输入、配置、执行步骤、关键状态、错误信息和输出位置。
- [x] 未写正式 alignment index Parquet、final report JSON 或 aligned MCAP。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g5/`。如果 `active/service-s3-g5/` 为空，删除该空目录。不得写共享执行记录。

## 19. 执行摘要

### 身份校验与 Dispatch 验证

| 项目 | 结果 |
|---|---|
| 用户指定路径 | `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g5/service_s3_018_接入场景三对齐报告开发者检验项.md` |
| 实际读取路径 | 匹配 |
| 文件名编号 | `service_s3_018` |
| 正文 L3 编号 | `service_s3_018` |
| task_id | service_s3_018 |
| group | service-s3-g5 |
| branch | service-s3 (当前分支确认) |
| dispatch_status | ready |
| depends_on | [service_s3_016, service_s3_017] → 均已归档 |
| 分支校验 | service-s3 ✓ |

### TDD 执行记录

| 切片 | 测试内容 | 状态 |
|---|---|---|
| VS1 RED→GREEN | `runtime.scene3_alignment_report_check` 模块可导入, `run_scene3_alignment_report_check` 可调用; 菜单 `scene3_alignment_report_check` 注册 | ✓ |
| VS2 RED→GREEN | 菜单注册测试: SCENE3_CHECKS 包含 scene3_alignment_report_check 且有非空中文标签 | ✓ |
| VS3 RED→GREEN | runtime wrapper 返回 dict 包含 run_id, status, outputs, steps, created_at, run_log_path | ✓ |
| VS4 RED→GREEN | 有效输入后创建 run 目录; 写出 alignment_index_preview.json (含 records, record_count); 写出 alignment_report_draft.json (含 status, status_counts, field_stats) | ✓ |
| VS5 RED→GREEN | 成功时 status='success'; 写出 run_log.json (含 check_id='scene3_alignment_report_check') | ✓ |
| VS6 RED→GREEN | 缺失输入文件产生 status='failed' 而不崩溃 | ✓ |
| VS7 RED→GREEN | 输出产物位于独立 run 目录, 不在 asset/ 生产路径 | ✓ |
| VS8 RED→GREEN | run_log 含 input, config, alignment, outputs, steps, created_at 等必需字段 | ✓ |

### 修改文件

| 文件 | 改动 |
|---|---|
| `src/data_clean/runtime/scene3_alignment_report_check.py` | **新增** 完整 runtime wrapper: 加载 field_alignment_results.json → `build_alignment_index_records()` → `build_alignment_report_draft()` → 写出 alignment_index_preview.json, alignment_report_draft.json, run_log.json. 含 try/except 失败处理和 `_jsonable` / `_reconstruct_dataclass` 序列化辅助. |
| `src/data_clean/ui/dev_menu.py` | 导入 `run_scene3_alignment_report_check`; **新增** `run_scene3_alignment_report_check_check()` 交互 runner; 添加到 `SCENE3_CHECKS` 列表第四项 ("检查对齐索引与报告生成"). |
| `src/data_clean/tests/runtime/test_scene3_alignment_report_check.py` | **新增** 13 个测试, 覆盖模块导入、菜单注册、runtime 调用、产物写入、成功/失败路径、输出隔离和 run log 字段完整性. |
| 本 L3 任务文件 | 成功标准标记完成, 追加执行摘要. |

### 验收命令输出

```bash
# 开工自检
bash scripts/init_data_clean_dev.sh
# → Git branch OK: service-s3, Python imports OK, start_data_clean.sh --help OK

# 全部新增测试
python3 -m pytest src/data_clean/tests/runtime/test_scene3_alignment_report_check.py -v -q
# → 13 passed in 0.48s

# 功能验证 (integration-style)
python3 - <<'PY'
# Creates valid FieldAlignmentResult inputs, runs full runtime flow
# Verifies alignment_index_preview.json (2 records, no failure_reason)
# Verifies alignment_report_draft.json (status=completed, aligned=1)
# Verifies run_log.json (check_id, input section, alignment section)
# Verifies no production artifacts (alignment_index.parquet, alignment_report.json)
# Verifies missing input → status='failed'
# → ALL ACCEPTANCE CHECKS PASSED
PY
```

### 与开发者验收入口的关系

本 L3 直接接入了 `scene3_alignment_report_check` 功能检验项到开发者菜单 `./start_data_clean.sh --dev`。用户选择场景三后可见 "[scene3_alignment_report_check] 检查对齐索引与报告生成" 检验项。该检验项加载前序字段对齐结果 (field_alignment_results.json), 调用 `build_alignment_index_records()` 生成 alignment index 预览, 调用 `build_alignment_report_draft()` 生成 report draft, 并写出调试产物和运行日志。建议用户在完成 service-s3-g5 全部 L3 后运行 `./start_data_clean.sh --dev` 选择场景三 → `scene3_alignment_report_check` 做最终人工验收。

### 遗留风险

- `runtime.scene3_alignment_report_check` 的 JSON 输入重建依赖 `_reconstruct_dataclass` 辅助函数, 该函数与 `scene3_field_alignment_check.py` 中的版本逻辑一致, 但对深度嵌套的 dataclass 可能需扩展处理。
- 本 L3 不覆盖场景三完整 smoke test 集成; 场景级别的端到端验证仍需用户人工执行 `./start_data_clean.sh --dev`。
- 使用 `from service.alignment_report import ...` (非 `from data_clean.service...`) 符合 data_clean 全库 PYTHONPATH 惯例。

