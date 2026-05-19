# L3 微元任务：实现 run_result 统一结果索引

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[09_Manifest与错误摘要模块]]  
L3 编号：`runtime_mvp_029`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`

## 2. 本次目标

```text
实现把成功 manifest 或失败 error summary 汇总为 run_result.json 的统一结果索引写入能力。
```

## 3. 本次不做

- 不定义新的 run result Types；只消费 `runtime_mvp_026` 已落地的类型。
- 不写 `processing_manifest.json` 或 `error_summary.json`。
- 不创建 run 目录。
- 不写 `run_log.json`。
- 不接入 Runtime 总入口、调度器、fake service 或 smoke test。

## 4. 执行对象

本次主要处理 [[RunResultIndex]] 的 JSON 落盘动作。成功运行时索引必须指向 [[ProcessingManifest]]，失败运行时索引必须指向 [[ErrorSummary]]，写入目标必须来自 [[RunDirectoryLayout]].`run_result_path` 或等价 [[RunArtifactPath]]。

## 5. 执行依赖

- `runtime_mvp_026_manifest_error_types.md` 已完成，或已有等价 [[RunResultIndex]] 类型。
- `runtime_mvp_027_processing_manifest_writer.md` 已完成，或测试中可构造合法 manifest 路径。
- `runtime_mvp_028_error_summary_writer.md` 已完成，或测试中可构造合法 error summary 路径。
- `runtime_mvp_004_run_directory_types.md` 已完成，或已有等价 [[RunDirectoryLayout]] / [[RunArtifactPath]]。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_004、runtime_mvp_026、runtime_mvp_027、runtime_mvp_028
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_027_processing_manifest_writer.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_028_error_summary_writer.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- RunDirectoryLayout.run_result_path
- PipelineResult.run_id、status、scene_results、run_dir、run_log_path
- ProcessingManifest 文件路径或 ErrorSummary 文件路径
- RunResultIndex 可序列化结构
是否存在接口冲突：执行前必须确认上游实际字段；不得猜测路径对象结构
如果有冲突，本次处理策略：暂停说明；只在当前写入器边界内做最小适配，不修改上游类型语义
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/runtime/` 或 `src/data_clean/repo/` 中的 run result 写入函数或类。
- 新增 runtime 测试，覆盖成功索引指向 manifest、失败索引指向 error summary、路径缺失、路径逃逸、成功/失败互斥规则。
- 写入器只写 `run_result.json`，不写其他运行记录文件。

## 8. 读写输出

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 读取最终运行结果 | [[PipelineResult]] | 无 | Python 对象 / mapping | 只读 |
| 读取成功 manifest 路径 | [[ProcessingManifest]] 写入结果或路径 | 无 | Python 对象 / path | 成功路径必需 |
| 读取失败摘要路径 | [[ErrorSummary]] 写入结果或路径 | 无 | Python 对象 / path | 失败路径必需 |
| 写入统一结果索引 | [[RunDirectoryLayout]].`run_result_path` | `run_result.json` | JSON | 当前新建 run 内最终写一次；不得覆盖旧 run |

```text
<run_dir>/
├── run_log.json
├── processing_manifest.json      # 成功路径
├── error_summary.json            # 失败路径
├── run_result.json
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
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunResultIndex.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ProcessingManifest.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ErrorSummary.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_027_processing_manifest_writer.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_028_error_summary_writer.md`
5. `DOCS/阶段二：数据清洗/执行记录/`

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
- 禁止写 `processing_manifest.json`、`error_summary.json`、`run_log.json` 或 `config_snapshot.yaml`。
- 禁止创建 run 目录；测试必须使用临时目录或上游已创建目录。
- 禁止写入 `asset/阶段二：数据清洗/` 或真实业务产物。
- 禁止修改调度器、fake service、结构化日志写入器或启动脚本行为。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "run_result" -q
```

## 15. 成功标准

- [ ] 能在临时 run 目录内写出 `run_result.json`。
- [ ] 成功路径 `run_result.json` 指向 `processing_manifest.json`，且不要求 `error_summary_path`。
- [ ] 失败路径 `run_result.json` 指向 `error_summary.json`，且不要求 `manifest_path`。
- [ ] `run_result.json` 可被 JSON 解析，并包含 `schema_version`、`run_id`、`status`、`run_dir`、`run_log_path`、`scene_results`、`created_at`。
- [ ] 路径逃逸、成功缺 manifest、失败缺 error summary 时失败清楚。

## 16. 完成后交接

必须更新当前 L3 任务文件、写入 `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_029_run_result_index_writer>.md`，并将当前 L3 移到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/runtime-g9/`。
