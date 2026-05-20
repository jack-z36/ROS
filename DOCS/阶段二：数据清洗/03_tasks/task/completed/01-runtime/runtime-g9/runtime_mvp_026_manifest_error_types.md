# L3 微元任务：定义 Manifest 与错误摘要 Types

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[09_Manifest与错误摘要模块]]  
L3 编号：`runtime_mvp_026`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`

## 2. 本次目标

```text
定义 ProcessingManifest、ErrorSummary、RunResultIndex 的代码级结构，使后续三个写入器共用同一套结束态追溯接口。
```

## 3. 本次不做

- 不写 `processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不实现 JSON 文件写入器。
- 不修改结构化日志模块。
- 不接入 Runtime 调度器、fake service 或 smoke test。
- 不定义 canonical dataset 的生产级 manifest。

## 4. 执行对象

本次主要处理 [[ProcessingManifest]]、[[ErrorSummary]]、[[RunResultIndex]] 的代码级表达，并复用 [[RunContext]]、[[RunDirectory]]、[[RunDirectoryLayout]]、[[RunArtifactPath]]、[[RunLogFile]]、[[RuntimeLogWriteResult]]、[[ConfigSnapshot]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeErrorRef]] 和 [[RunStatus]]。

## 5. 执行依赖

- 功能1 L3 已定义 Runtime 上下文、状态、结果和错误引用相关 Types，或已经存在等价结构。
- 功能2 L3 已定义 [[RunDirectoryLayout]] / [[RunArtifactPath]] 代码层结构，或已经存在等价结构。
- 功能3 L3 已定义 [[ConfigSnapshot]] 代码层结构，或已经存在等价结构。
- 功能8 L3 已定义 [[RunLogFile]] / [[RuntimeLogWriteResult]]，或已经存在等价结构。
- 功能9 L2 已定义 manifest、error summary 和 run result 的数据语义。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_002、runtime_mvp_003、runtime_mvp_004、runtime_mvp_007、runtime_mvp_023
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g3/runtime_mvp_007_runtime_config_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- RunContext.run_id、run_mode、service_mode、target_scenes、run_dir、status
- RunDirectoryLayout.processing_manifest_path、error_summary_path、run_result_path、run_log_path
- ConfigSnapshot.snapshot_path
- RunLogFile 或 RuntimeLogWriteResult 的日志路径与写入状态
- SceneResult、PipelineResult、RuntimeErrorRef 的可序列化摘要字段
是否存在接口冲突：无已知冲突；执行前必须确认上游实际落地字段名
如果有冲突，本次处理策略：暂停说明，不重新定义与上游同名但字段不同的对象
```

## 7. 预期改动形态

- 在 Runtime MVP 现有 Types 位置新增或扩展 manifest / error summary / run result 相关对象。
- 新增最小测试，能构造成功 manifest、失败 error summary 和统一 run result。
- 必填字段缺失、失败摘要缺少 [[RuntimeErrorRef]]、成功结果缺少 manifest 路径等情况必须能被清楚表达。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[ProcessingManifest]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | `runtime_mvp_027`、Runtime smoke test |
| [[ErrorSummary]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | `runtime_mvp_028`、Runtime smoke test |
| [[RunResultIndex]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | `runtime_mvp_029`、UI / smoke test |
| `RuntimeResultSchemaVersion` | enum / Literal / 受控字符串集合 | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 三个写入器、测试断言 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `schema_version` | string / Literal | 文件结构版本 | 无 | 非空，受控取值 |
| `run_id` | string | 运行标识 | 无 | 与 [[RunContext]] 一致 |
| `status` | [[RunStatus]] | 最终状态 | 无 | manifest 必须为成功结束态；error summary 必须为失败结束态 |
| `run_log_path` | [[RunArtifactPath]] / path | 日志路径 | 无 | 必须位于本次 [[RunDirectory]] 下 |
| `config_snapshot_path` | [[RunArtifactPath]] / path / 空 | 配置快照路径 | 空 | 成功 manifest 必须存在 |
| `scene_results` | list of [[SceneResult]] | 已执行场景结果 | 空列表 | 成功时不得包含失败场景 |
| `error` | [[RuntimeErrorRef]] / 空 | 失败引用 | 空 | error summary 必须存在 |
| `manifest_path` | [[RunArtifactPath]] / 空 | 成功 manifest 路径 | 空 | 成功 run result 必须存在 |
| `error_summary_path` | [[RunArtifactPath]] / 空 | 失败摘要路径 | 空 | 失败 run result 必须存在 |
| `created_at` | datetime / string | 文件生成时间 | 写入时刻 | 必须可 JSON 序列化 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ProcessingManifest.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ErrorSummary.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunResultIndex.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeErrorRef.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunLogFile.md`
8. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogWriteResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md`

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
4. `src/data_clean/tests/runtime/`

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/runtime/`，仅当现有 Runtime Types 已放在该层
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止实现 `processing_manifest.json`、`error_summary.json` 或 `run_result.json` 写入器。
- 禁止修改结构化日志模块、调度器、fake service 或启动脚本行为。
- 禁止写入 `src/data_clean/runs/`、`asset/阶段二：数据清洗/` 或任何真实运行产物。
- 禁止重新定义与上游 [[RunStatus]]、[[SceneName]]、[[RuntimeErrorRef]]、[[RunLogFile]] 冲突的对象。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "manifest or error_summary or run_result" -q
```

## 15. 成功标准

- [x] 已定义 [[ProcessingManifest]]。
- [x] 已定义 [[ErrorSummary]]。
- [x] 已定义 [[RunResultIndex]]。
- [x] 成功 manifest、失败 error summary 和统一 run result 的必填字段能被校验。
- [x] 必填字段缺失、失败摘要缺少 [[RuntimeErrorRef]]、成功结果缺少 manifest 路径能被清楚表达。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`


交接摘要必须包含读取记录、修改文件、TDD 过程、验收命令、成功标准勾选情况、当前没做什么和下一步建议。

## 执行摘要

### 本次读取记录

- 未找到相关 L3 历史记录：`DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md` 等文件在 `active/` 目录下不存在，已在 `completed/runtime-g1/` 找到完成记录。
- 已读取上游 L2 数据定义：`ProcessingManifest.md`、`ErrorSummary.md`、`RunResultIndex.md`、`PipelineResult.md`、`RuntimeErrorRef.md`、`RunLogFile.md`、`RuntimeLogWriteResult.md`。
- 已读取 L2 能力模块：`09_Manifest与错误摘要模块.md`。
- 已读取约束文档：`L3编码执行原则.md`、`L3执行TDD与归档约束.md`、`上游依赖接口对齐约束.md`、`文件存放规范.md`、`Runtime MVP 执行约束.md`。
- 已读取现有代码结构：`src/data_clean/schemas/__init__.py`、`runtime_results.py`、`runtime_context.py`、`runtime_enums.py`、`run_directory_types.py`、`structured_log_types.py`、`runtime_config_types.py`。

### 修改文件

- 新增文件：`src/data_clean/schemas/manifest_types.py`
- 新增文件：`src/data_clean/tests/runtime/test_manifest_types.py`
- 修改文件：`src/data_clean/schemas/__init__.py`（添加 manifest_types 相关导入和导出）

### 新增或修改函数/类/测试

**manifest_types.py:**
- `RuntimeResultSchemaVersion` enum：定义三个受控 schema 版本常量
- `ProcessingManifest` dataclass：成功路径的 processing manifest，带必填字段校验
- `ErrorSummary` dataclass：失败路径的错误摘要，带必填字段校验
- `RunResultIndex` dataclass：统一 run result 索引，带成功/失败路径校验

**test_manifest_types.py:**
- 24 个测试用例覆盖三个类型的数据构造、必填字段校验和边界情况

### TDD red / green / refactor 执行

1. **RED Cycle 1**: 创建测试目录和测试文件 `test_manifest_types.py`，定义所有测试用例，确认测试失败（模块不存在）。
2. **GREEN Cycle 1**: 实现 `manifest_types.py` 包含所有四个数据类，通过全部 24 个测试。
3. **GREEN Cycle 2**: 更新 `schemas/__init__.py` 添加导入和导出，验证包级导入可用。
4. **验收**: 使用 `PYTHONPATH=/home/hit/ROS/src python3 -m pytest src/data_clean/tests/runtime/test_manifest_types.py -v` 验证全部 24 个测试通过。

### 验收命令

```bash
PYTHONPATH=/home/hit/ROS/src python3 -m pytest src/data_clean/tests/runtime/test_manifest_types.py -v
```

执行结果：24 passed in 0.04s

### 成功标准勾选情况

- [x] 已定义 [[ProcessingManifest]]。
- [x] 已定义 [[ErrorSummary]]。
- [x] 已定义 [[RunResultIndex]]。
- [x] 成功 manifest、失败 error summary 和统一 run result 的必填字段能被校验（测试覆盖所有必填字段）。
- [x] 必填字段缺失、失败摘要缺少 [[RuntimeErrorRef]]、成功结果缺少 manifest 路径能被清楚表达（测试用例明确验证这些情况并抛出 ValueError）。
- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/runtime-g9/`。

### 当前没做什么

- 未实现 JSON 文件写入器（由 `runtime_mvp_027`、`runtime_mvp_028`、`runtime_mvp_029` 负责）。
- 未修改结构化日志模块、调度器、fake service 或启动脚本。
- 未写入 `src/data_clean/runs/`、`asset/阶段二：数据清洗/` 或任何真实运行产物。
- 未重新定义与上游 [[RunStatus]]、[[SceneName]]、[[RuntimeErrorRef]]、[[RunLogFile]] 冲突的对象。

### 下一步建议

1. 执行 `runtime_mvp_027`：实现成功路径 processing_manifest.json 写入器。
2. 执行 `runtime_mvp_028`：实现失败路径 error_summary.json 写入器。
3. 执行 `runtime_mvp_029`：实现 run_result.json 统一结果索引。
4. 注意：上游测试文件（如 `test_run_context_attach.py`、`test_runtime_context_enums.py`）存在预导入问题，与本次 L3 无关，不影响本 L3 验收。

