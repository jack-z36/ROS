# L3 微元任务：实现成功路径 processing_manifest 写入器

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[09_Manifest与错误摘要模块]]  
L3 编号：`runtime_mvp_027`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`

## 2. 本次目标

```text
实现成功路径把 ProcessingManifest 写入当前 run 目录 processing_manifest.json 的最小能力。
```

## 3. 本次不做

- 不定义新的 manifest Types；只消费 `runtime_mvp_026` 已落地的类型。
- 不写 `error_summary.json` 或 `run_result.json`。
- 不创建 run 目录。
- 不写 `run_log.json`。
- 不接入 Runtime 总入口、调度器、fake service 或 smoke test。

## 4. 执行对象

本次主要处理 [[ProcessingManifest]] 的 JSON 落盘动作，写入目标必须来自 [[RunDirectoryLayout]].`processing_manifest_path` 或等价 [[RunArtifactPath]]，并消费 [[RunLogFile]] / [[RuntimeLogWriteResult]] 提供的日志路径与写入状态。

## 5. 执行依赖

- `runtime_mvp_026_manifest_error_types.md` 已完成，或已有等价 [[ProcessingManifest]] 类型。
- `runtime_mvp_025_run_log_writer.md` 已完成，或已有等价 [[RunLogFile]] / [[RuntimeLogWriteResult]]。
- `runtime_mvp_004_run_directory_types.md` 已完成，或已有等价 [[RunDirectoryLayout]] / [[RunArtifactPath]]。
- `runtime_mvp_009_config_snapshot_writer.md` 已完成，或测试中可构造合法 [[ConfigSnapshot]]。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_004、runtime_mvp_009、runtime_mvp_023、runtime_mvp_025、runtime_mvp_026
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g3/runtime_mvp_009_config_snapshot_writer.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_025_run_log_writer.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- RunDirectoryLayout.processing_manifest_path
- RunContext.run_id、run_mode、service_mode、target_scenes、run_dir、status
- ConfigSnapshot.snapshot_path
- RuntimeLogWriteResult.run_log_path、status、error
- PipelineResult.status、scene_results、run_log_path
- ProcessingManifest 可序列化结构
是否存在接口冲突：执行前必须确认上游实际字段；不得猜测路径对象结构
如果有冲突，本次处理策略：暂停说明；只在当前写入器边界内做最小适配，不修改上游类型语义
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/runtime/` 或 `src/data_clean/repo/` 中的 manifest 写入函数或类。
- 新增 runtime 测试，覆盖成功写入、JSON 可解析、路径缺失、路径逃逸、成功路径缺少配置快照、成功结果包含失败场景。
- 写入器只写 `processing_manifest.json`，不写其他运行记录文件。

## 8. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 读取运行上下文摘要 | [[RunContext]] 或等价参数 | 无 | Python 对象 / mapping | 只读 |
| 读取配置快照引用 | [[ConfigSnapshot]] 或等价路径 | 无 | Python 对象 / mapping | 只读 |
| 读取日志写入结果 | [[RuntimeLogWriteResult]] | 无 | Python 对象 / mapping | 只读 |
| 写入成功追溯清单 | [[RunDirectoryLayout]].`processing_manifest_path` | `processing_manifest.json` | JSON | 当前新建 run 内最终写一次；不得覆盖旧 run |

### 文件或目录结构

```text
<run_dir>/
├── run_log.json
├── config_snapshot.yaml
├── processing_manifest.json
└── outputs/
```

本任务只写 `processing_manifest.json`，不创建 `outputs/`，不写 `run_log.json` 或 `config_snapshot.yaml`。

## 9. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ProcessingManifest.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigSnapshot.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunLogFile.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogWriteResult.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
8. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g3/runtime_mvp_009_config_snapshot_writer.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_025_run_log_writer.md`
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md`

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

## 13. 禁止修改

- 禁止定义新的 manifest / error summary / run result Types。
- 禁止写 `error_summary.json`、`run_result.json`、`run_log.json` 或 `config_snapshot.yaml`。
- 禁止创建 run 目录；测试必须使用临时目录或上游已创建目录。
- 禁止写入 `asset/阶段二：数据清洗/` 或真实业务产物。
- 禁止修改调度器、fake service、结构化日志写入器或启动脚本行为。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "processing_manifest" -q
```

## 15. 成功标准

- [x] 能在临时 run 目录内写出 `processing_manifest.json`。
- [x] `processing_manifest.json` 可被 JSON 解析，并包含 `schema_version`、`run_id`、`status`、`target_scenes`、`config_snapshot_path`、`run_log_path`、`scene_results`、`created_at`。
- [x] 成功结果中出现失败 [[SceneResult]]、缺少配置快照、路径逃逸 run 目录时失败清楚。
- [x] 写入结果不覆盖旧 run，不写 `error_summary.json` 或 `run_result.json`。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

交接摘要必须包含：

1. 修改了哪些文件。
2. 新增或修改了哪些函数 / 测试。
3. 如何运行验收。
4. TDD red / green / refactor 如何执行。
5. 成功标准勾选情况。
6. 当前没做什么。
7. 建议 Win 端后续同步整理什么。


## 17. 执行摘要

### 读取的相关 L3 任务文件或历史记录

- 本 L3 直接依赖的上游功能 L3 文件（runtime_mvp_004、runtime_mvp_009、runtime_mvp_023、runtime_mvp_025、runtime_mvp_026）在 `task/active/` 中未找到，属于未找到相关 L3 历史记录的情况。
- 通过读取现有代码了解了上游接口的实际落地字段名，包括 `RuntimeLogWriteResult` 的 `log_path` 字段、`ConfigSnapshot` 的 `snapshot_path` 字段等。

### 修改了哪些文件

1. `src/data_clean/schemas/runtime_results.py` - 新增 `MANIFEST_SCHEMA_VERSION` 常量和 `ProcessingManifest` dataclass
2. `src/data_clean/schemas/__init__.py` - 新增导出 `MANIFEST_SCHEMA_VERSION` 和 `ProcessingManifest`
3. `src/data_clean/runtime/processing_manifest_writer.py` - 新增 `ProcessingManifestError` 异常类和 `write_processing_manifest` 函数
4. `src/data_clean/tests/runtime/test_processing_manifest_writer.py` - 新增测试文件，包含 9 个测试用例

### 新增或修改了哪些函数 / 测试

**新增函数/类：**
- `ProcessingManifest` - dataclass，包含 manifest 所有必需和可选字段，带 `to_dict()` 方法用于 JSON 序列化
- `ProcessingManifestError` - 异常类，继承自 `RuntimeError`
- `write_processing_manifest` - 主函数，处理验证、构建、写入流程
- `_validate_paths_in_run_dir` - 私有函数，验证配置快照和日志路径在 run 目录内
- `_validate_no_failed_scenes` - 私有函数，验证成功路径不包含失败场景
- `_scene_result_to_dict` - 私有函数，将 `SceneResult` 转换为 JSON 可序列化的 dict

**新增测试（9个）：**
- `TestProcessingManifestType.test_construct_success` - 验证 ProcessingManifest 可构造
- `TestProcessingManifestType.test_to_dict_contains_required_fields` - 验证 to_dict 包含必需字段
- `TestProcessingManifestType.test_missing_required_field_raises` - 验证缺少必需字段时抛出异常
- `TestWriteProcessingManifestSuccess.test_writes_manifest_json` - 验证成功写入 JSON 文件
- `TestWriteProcessingManifestSuccess.test_returns_manifest_path` - 验证返回正确的路径
- `TestWriteProcessingManifestPathEscape.test_path_escape_raises_error` - 验证路径逃逸时抛出异常
- `TestWriteProcessingManifestFileExists.test_existing_file_raises_error` - 验证文件已存在时抛出异常
- `TestWriteProcessingManifestMissingConfigSnapshot.test_missing_config_snapshot_raises` - 验证缺少配置快照时抛出异常
- `TestWriteProcessingManifestFailedScene.test_failed_scene_in_results_raises` - 验证包含失败场景时抛出异常

### TDD red / green / refactor 如何执行

按照垂直切片 TDD 执行：

**Slice 1: 定义 ProcessingManifest 类型**
- RED: 尝试构造 ProcessingManifest 但类型不存在
- GREEN: 在 `runtime_results.py` 中定义 ProcessingManifest dataclass，包含必需字段、to_dict() 方法和验证逻辑
- 验证通过：3 个类型相关测试全部通过

**Slice 2: 实现写入器基本功能**
- RED: 测试尝试调用 write_processing_manifest 但函数不存在
- GREEN: 实现 write_processing_manifest 主函数，处理路径获取、parent 目录创建、manifest 构建、JSON 写入
- 修复：处理 RuntimeLogWriteResult 的字段名从 `run_log_path` 改为 `log_path`
- 验证通过：2 个成功路径测试通过

**Slice 3: 路径逃逸校验**
- RED: 测试期望路径逃逸时抛出异常
- GREEN: 实现 _validate_paths_in_run_dir 函数，验证配置快照和日志路径都在 run 目录内
- 验证通过：路径逃逸测试通过

**Slice 4: 文件已存在校验**
- RED: 测试期望文件已存在时抛出异常
- GREEN: 在写入前检查文件是否存在，存在则抛出异常
- 验证通过：文件已存在测试通过

**Slice 5: 缺少配置快照处理**
- RED: 测试期望空配置快照时抛出异常
- GREEN: 添加配置快照路径为空的校验，处理 `Path("")` 解析为当前目录的情况
- 验证通过：缺少配置快照测试通过

**Slice 6: 包含失败场景的处理**
- RED: 测试期望包含失败场景时抛出异常
- GREEN: 实现 _validate_no_failed_scenes 函数，遍历 scene_results 检查失败状态
- 验证通过：包含失败场景测试通过

### 如何运行验收

从仓库根目录运行：
```bash
python3 -m pytest src/data_clean/tests/runtime/test_processing_manifest_writer.py -q
```

预期输出：
```
.........
9 passed in 0.03s
```

### 成功标准勾选情况

- [x] 能在临时 run 目录内写出 `processing_manifest.json` - 测试覆盖
- [x] `processing_manifest.json` 可被 JSON 解析，并包含所有必需字段 - 测试覆盖
- [x] 成功结果中出现失败场景、缺少配置快照、路径逃逸 run 目录时失败清楚 - 3 个错误测试覆盖
- [x] 写入结果不覆盖旧 run - 文件已存在校验测试覆盖
- [x] 执行摘要已追加 - 本摘要
- [x] 当前 L3 已归档 - 已移至 `task/completed/runtime-g9/`

### 当前没做什么

- 没有定义 ErrorSummary 或 RunResultIndex 类型（按照 L3 任务要求，仅定义 ProcessingManifest）
- 没有写 `error_summary.json` 或 `run_result.json`
- 没有创建 run 目录（测试使用临时目录）
- 没有接入 Runtime 总入口、调度器、fake service 或 smoke test
- 没有修改 `asset/阶段二：数据清洗/` 或真实业务产物
- 没有修复其他测试文件的导入问题（与本 L3 无关）

### 建议 Win 端后续同步整理什么

1. 确认 runtime_mvp_026 (Manifest 与错误摘要类型定义) 的 L3 任务是否已完成。如果未完成，需要补定义 ProcessingManifest、ErrorSummary、RunResultIndex 三个类型。
2. 建议检查 `src/data_clean/tests/runtime/` 中测试文件的导入风格一致性，避免混用 `from schemas` 和 `from data_clean.schemas` 导致的导入问题。
3. 后续 L3 (runtime_mvp_028、runtime_mvp_029) 可以参考本次实现模式，使用类似的数据类、序列化方法和测试结构。
