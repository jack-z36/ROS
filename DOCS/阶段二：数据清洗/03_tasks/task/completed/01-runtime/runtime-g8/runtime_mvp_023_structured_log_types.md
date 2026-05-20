# L3 微元任务：定义结构化日志 Types 与事件类型

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[08_结构化日志模块]]  
L3 编号：`runtime_mvp_023`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/08_结构化日志模块.md`

## 2. 本次目标

```text
定义结构化日志所需的 RunLogFile、RuntimeLogEvent、RuntimeLogWriteResult 和受控事件类型，使后续事件转换器与写入器共用同一套接口。
```

## 3. 本次不做

- 不实现日志事件转换器。
- 不写 `run_log.json` 文件。
- 不写 `processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不接入场景调度器或 fake service。
- 不修改启动脚本或 UI。

## 4. 执行对象

本次主要处理 [[RunLogFile]]、[[RuntimeLogEvent]]、[[RuntimeLogWriteResult]] 的代码级表达，并复用已有 [[RunContext]]、[[RunDirectoryLayout]]、[[RuntimeStepRecord]]、[[SceneDispatchEvent]]、[[SceneResult]]、[[PipelineResult]]、[[RuntimeErrorRef]]、[[RunStatus]] 和 [[SceneName]]。

## 5. 执行依赖

- 功能1 L3 已定义 Runtime 上下文、状态、结果和错误引用相关 Types，或已经存在等价结构。
- 功能2 L3 已定义 [[RunDirectoryLayout]] / [[RunArtifactPath]] 代码层结构，或已经存在等价结构。
- 功能6 L3 已定义 [[SceneDispatchEvent]] 代码层结构，或已经存在等价结构。
- 功能8 L2 已定义日志文件、日志事件和写入结果的数据语义。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_002、runtime_mvp_003、runtime_mvp_004、runtime_mvp_013
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- RunContext.run_id、run_dir、target_scenes、status、config_snapshot_path
- RunDirectoryLayout.run_log_path
- RuntimeStepRecord、SceneDispatchEvent、SceneResult、PipelineResult、RuntimeErrorRef 的可序列化摘要字段
是否存在接口冲突：无已知冲突；执行前必须确认上游实际落地字段名
如果有冲突，本次处理策略：暂停说明，不重新定义与上游同名但字段不同的对象
```

## 7. 预期改动形态

- 在 Runtime MVP 现有 Types 位置新增或扩展结构化日志相关对象。
- 新增或收敛受控事件类型，例如 `runtime_step`、`dispatch_event`、`scene_result`、`pipeline_result`、`error`。
- 新增最小测试，能构造合法日志文件、日志事件和写入结果。
- 非法事件类型、缺少 `run_id`、失败写入结果缺少错误引用等情况必须能被清楚表达。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[RunLogFile]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 日志写入器、Manifest 与错误摘要模块、smoke test |
| [[RuntimeLogEvent]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 日志事件转换器、日志写入器 |
| [[RuntimeLogWriteResult]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | [[PipelineResult]] 汇总、Manifest 与错误摘要模块 |
| `RuntimeLogEventType` | enum / Literal / 受控字符串集合 | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 日志事件转换器、测试断言 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `run_id` | string | 运行标识 | 无 | 非空，必须与 [[RunContext]] 一致 |
| `run_dir` | path / string | 本次运行目录 | 无 | 必须位于 run 根目录语义下 |
| `target_scenes` | list of [[SceneName]] | 本次目标场景 | 无 | 非空 |
| `events` | list of [[RuntimeLogEvent]] | 日志事件列表 | 空列表或无 | 写出正式日志时至少 1 条 |
| `event_id` | string | 单 run 内事件标识 | 无 | 单个日志内唯一 |
| `event_type` | `RuntimeLogEventType` | 事件类型 | 无 | 受控取值 |
| `status` | [[RunStatus]] | 事件或写入状态 | 无 | 必须使用上游状态类型 |
| `error` | [[RuntimeErrorRef]] 或空 | 失败引用 | 空 | 失败事件或失败写入结果必须存在 |
| `event_count` | integer | 写入事件数量 | 0 | 成功写入时大于或等于 1 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/08_结构化日志模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunLogFile.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogEvent.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogWriteResult.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeStepRecord.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchEvent.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`

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

- 禁止实现日志事件转换器或 `run_log.json` 写入器。
- 禁止写入 `src/data_clean/runs/`、`asset/阶段二：数据清洗/` 或任何真实运行产物。
- 禁止修改调度器、fake service、manifest、错误摘要或启动脚本行为。
- 禁止重新定义与上游 [[RunStatus]]、[[SceneName]]、[[RuntimeErrorRef]]、[[SceneDispatchEvent]] 冲突的对象。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 已定义 [[RunLogFile]]。
- [x] 已定义 [[RuntimeLogEvent]]。
- [x] 已定义 [[RuntimeLogWriteResult]]。
- [x] 已定义或收敛受控日志事件类型。
- [x] 非法事件类型、缺少 `run_id`、失败写入结果缺少错误引用能被清楚表达。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

- 执行过程、当前状态、未完成事项和下一步建议写在当前 L3 任务文件末尾的执行摘要中

交接摘要必须包含：

1. 读取了哪些相关 L3 任务文件或历史记录
2. 修改了哪些文件
3. 新增或修改了哪些函数 / 测试
4. TDD red / green / refactor 如何执行
5. 如何运行验收，命令必须使用 `python3`
6. 成功标准勾选情况
7. 当前没做什么
8. 下一步建议

---

## 执行摘要

### 读取的相关 L3 任务文件或历史记录

未找到相关 L3 历史记录。已读取必读任务文档和相关约束文档。

### 修改的文件

1. `src/data_clean/schemas/structured_log_types.py`（新建）
2. `src/data_clean/tests/runtime/test_structured_log_types.py`（新建）
3. `src/data_clean/schemas/__init__.py`（修改）
4. `src/data_clean/data_clean_architecture.md`（修改）
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md`（本文件，更新成功标准）

### 新增或修改的函数 / 测试

**新增类型定义：**

1. `RuntimeLogEventType` - 枚举类型，包含 5 个事件类型：
   - `RUNTIME_STEP` - Runtime 步骤事件
   - `DISPATCH_EVENT` - 场景调度事件
   - `SCENE_RESULT` - 场景结果事件
   - `PIPELINE_RESULT` - 流水线结果事件
   - `ERROR` - 错误事件

2. `RuntimeLogEvent` - dataclass，包含：
   - `event_id: str`
   - `event_type: RuntimeLogEventType`
   - `status: RunStatus`
   - `error: Optional[RuntimeErrorRef]`
   - `__post_init__` 方法：当 status=FAILED 时要求 error 非空

3. `RunLogFile` - dataclass，包含：
   - `run_id: str`
   - `run_dir: Path`
   - `target_scenes: List[SceneName]`
   - `events: List[RuntimeLogEvent]`
   - `__post_init__` 方法：验证 run_id、run_dir、target_scenes 非空

4. `RuntimeLogWriteResult` - dataclass，包含：
   - `success: bool`
   - `event_count: int`
   - `error: Optional[RuntimeErrorRef]`
   - `__post_init__` 方法：当 success=False 时要求 error 非空

**新增测试（18 个测试用例）：**

1. `test_runtime_log_event_type_values` - 验证枚举值
2. `test_runtime_log_event_creation_success` - 验证成功事件创建
3. `test_runtime_log_event_creation_failure_with_error` - 验证失败事件带错误
4. `test_runtime_log_event_creation_failure_without_error_raises` - 验证失败事件不带错误抛异常
5. `test_runtime_log_event_optional_error_for_non_failed_status` - 验证非失败状态可选错误
6. `test_runtime_log_event_serializable` - 验证事件可序列化
7. `test_run_log_file_creation` - 验证日志文件创建
8. `test_run_log_file_post_init_validates_run_id` - 验证 run_id 非空
9. `test_run_log_file_post_init_validates_run_dir` - 验证 run_dir 非空
10. `test_run_log_file_post_init_validates_target_scenes` - 验证 target_scenes 非空
11. `test_run_log_file_with_events` - 验证带事件的日志文件
12. `test_run_log_file_serializable` - 验证日志文件可序列化
13. `test_runtime_log_write_result_success` - 验证成功写入结果
14. `test_runtime_log_write_result_failure_with_error` - 验证失败写入结果带错误
15. `test_runtime_log