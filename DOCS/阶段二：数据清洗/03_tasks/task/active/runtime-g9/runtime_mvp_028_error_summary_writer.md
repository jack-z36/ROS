# L3 微元任务：实现失败路径 error_summary 写入器

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[09_Manifest与错误摘要模块]]  
L3 编号：`runtime_mvp_028`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`

## 2. 本次目标

```text
实现失败路径把 ErrorSummary 写入当前 run 目录 error_summary.json 的最小能力。
```

## 3. 本次不做

- 不定义新的错误摘要 Types；只消费 `runtime_mvp_026` 已落地的类型。
- 不写 `processing_manifest.json` 或 `run_result.json`。
- 不创建 run 目录。
- 不写 `run_log.json`。
- 不接入 Runtime 总入口、调度器、fake service 或 smoke test。

## 4. 执行对象

本次主要处理 [[ErrorSummary]] 的 JSON 落盘动作，写入目标必须来自 [[RunDirectoryLayout]].`error_summary_path` 或等价 [[RunArtifactPath]]，并消费 [[RuntimeErrorRef]]、[[RunLogFile]] / [[RuntimeLogWriteResult]] 和 [[PipelineResult]]。

## 5. 执行依赖

- `runtime_mvp_026_manifest_error_types.md` 已完成，或已有等价 [[ErrorSummary]] 类型。
- `runtime_mvp_025_run_log_writer.md` 已完成，或已有等价 [[RunLogFile]] / [[RuntimeLogWriteResult]]。
- `runtime_mvp_004_run_directory_types.md` 已完成，或已有等价 [[RunDirectoryLayout]] / [[RunArtifactPath]]。
- 上游调度或 fake service 已能提供 [[RuntimeErrorRef]]，或测试中可构造合法错误引用。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_003、runtime_mvp_004、runtime_mvp_023、runtime_mvp_025、runtime_mvp_026
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_025_run_log_writer.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- RunDirectoryLayout.error_summary_path
- RunContext.run_id、target_scenes、run_dir、status
- RuntimeErrorRef.error_code、scene_name、step_name、message、details、suggested_next_action
- RuntimeLogWriteResult.run_log_path、status、error
- PipelineResult.status、scene_results、run_log_path
- ErrorSummary 可序列化结构
是否存在接口冲突：执行前必须确认上游实际字段；不得猜测路径对象结构
如果有冲突，本次处理策略：暂停说明；只在当前写入器边界内做最小适配，不修改上游类型语义
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/runtime/` 或 `src/data_clean/repo/` 中的错误摘要写入函数或类。
- 新增 runtime 测试，覆盖失败摘要写入、JSON 可解析、缺少 [[RuntimeErrorRef]]、日志写入失败兜底、路径缺失、路径逃逸。
- 写入器只写 `error_summary.json`，不写其他运行记录文件。

## 8. 读写输出

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 读取失败错误引用 | [[RuntimeErrorRef]] | 无 | Python 对象 / mapping | 只读 |
| 读取日志写入结果 | [[RuntimeLogWriteResult]] | 无 | Python 对象 / mapping | 只读 |
| 读取运行结果摘要 | [[PipelineResult]] 或等价参数 | 无 | Python 对象 / mapping | 只读 |
| 写入失败摘要 | [[RunDirectoryLayout]].`error_summary_path` | `error_summary.json` | JSON | 当前新建 run 内最终写一次；不得覆盖旧 run |

```text
<run_dir>/
├── run_log.json
├── error_summary.json
└── outputs/
```

## 9. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ErrorSummary.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeErrorRef.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunLogFile.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogWriteResult.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
8. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_025_run_log_writer.md`
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md`
6. `DOCS/阶段二：数据清洗/执行记录/`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/schemas/`
3. `src/data_clean/runtime/`
4. `src/data_clean/repo/`
5. `src/data_clean/tests/runtime/`

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/repo/`，仅当仓库现有读写能力集中在 repo 层
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/`

## 13. 禁止修改

- 禁止定义新的 manifest / error summary / run result Types。
- 禁止写 `processing_manifest.json`、`run_result.json`、`run_log.json` 或 `config_snapshot.yaml`。
- 禁止创建 run 目录；测试必须使用临时目录或上游已创建目录。
- 禁止写入 `asset/阶段二：数据清洗/` 或真实业务产物。
- 禁止修改调度器、fake service、结构化日志写入器或启动脚本行为。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "error_summary" -q
```

## 15. 成功标准

- [ ] 能在临时 run 目录内写出 `error_summary.json`。
- [ ] `error_summary.json` 可被 JSON 解析，并包含 `schema_version`、`run_id`、`status`、`failed_step`、`error`、`run_log_path`、`message`、`created_at`。
- [ ] 缺少 [[RuntimeErrorRef]]、路径逃逸 run 目录、日志写入失败兜底场景能失败清楚或写出最小错误摘要。
- [ ] 写入结果不覆盖旧 run，不写 `processing_manifest.json` 或 `run_result.json`。

## 16. 完成后交接

必须更新当前 L3 任务文件、写入 `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_028_error_summary_writer>.md`，并将当前 L3 移到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/runtime-g9/`。
