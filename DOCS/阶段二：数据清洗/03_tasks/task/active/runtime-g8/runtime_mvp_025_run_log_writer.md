# L3 微元任务：实现 run_log.json 写入器

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[08_结构化日志模块]]  
L3 编号：`runtime_mvp_025`  
任务类别：数据读写类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/08_结构化日志模块.md`

## 2. 本次目标

```text
实现把 RuntimeLogEvent 列表写入当前 run 目录 run_log.json，并返回 RuntimeLogWriteResult 的最小写入能力。
```

## 3. 本次不做

- 不定义新的日志 Types；只消费 `runtime_mvp_023` 已落地的类型。
- 不实现日志事件转换器；只消费 `runtime_mvp_024` 已产生或测试构造的事件。
- 不创建 run 目录。
- 不写配置快照、manifest、error summary 或 run result。
- 不接入 Runtime 总入口、调度器或 fake service。

## 4. 执行对象

本次主要处理 [[RunLogFile]] 的 JSON 落盘动作，写入目标必须来自 [[RunDirectoryLayout]].`run_log_path` 或等价 [[RunArtifactPath]]，写入后返回 [[RuntimeLogWriteResult]]。

## 5. 执行依赖

- `runtime_mvp_023_structured_log_types.md` 已完成，或已有等价日志 Types。
- `runtime_mvp_024_runtime_log_event_converter.md` 已完成，或测试中可构造合法 [[RuntimeLogEvent]]。
- `runtime_mvp_004_run_directory_types.md` 已完成，或已有等价 [[RunDirectoryLayout]] / [[RunArtifactPath]]。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_004、runtime_mvp_023、runtime_mvp_024
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_024_runtime_log_event_converter.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- RunContext.run_id、run_dir、target_scenes、status、config_snapshot_path
- RunDirectoryLayout.run_log_path 或 RunArtifactPath(path, artifact_name, artifact_kind, format)
- RuntimeLogEvent 列表
- RuntimeLogWriteResult(status, run_log_path, event_count, written_at, error)
是否存在接口冲突：执行前必须确认上游实际字段；不得猜测路径对象结构
如果有冲突，本次处理策略：暂停说明；只做当前写入器边界内的最小适配，不修改上游类型语义
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/runtime/` 或 `src/data_clean/repo/` 中的日志写入函数或类。
- 新增 runtime 测试，覆盖成功写入、文件可解析、路径缺失、路径逃逸、不可序列化事件、已有旧 run 不被污染。
- 写入器只在当前新建 run 目录内写 `run_log.json`，不写其他运行记录文件。

## 8. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
| --- | --- | --- | --- | --- |
| 读取运行上下文摘要 | [[RunContext]] 或等价参数 | 无 | Python 对象 / mapping | 只读 |
| 读取日志事件 | [[RuntimeLogEvent]] 列表 | 无 | Python 对象 / mapping | 只读 |
| 写入结构化日志 | [[RunDirectoryLayout]].`run_log_path` | `run_log.json` | JSON | 当前新建 run 内允许补全写入；不得覆盖旧 run |
| 返回写入结果 | 文件写入状态、事件数量、错误引用 | [[RuntimeLogWriteResult]] | Python 对象 | 不写其他文件 |

### 文件或目录结构

```text
<run_dir>/
├── run_log.json
└── outputs/
```

本任务只写 `run_log.json`，不创建 `outputs/`，不写其他运行记录文件。

## 9. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/08_结构化日志模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunLogFile.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogEvent.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogWriteResult.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunDirectoryLayout.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_024_runtime_log_event_converter.md`

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

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/repo/`，仅当仓库现有读写能力集中在 repo 层
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止创建 run 目录；测试必须使用临时目录或上游已创建目录。
- 禁止写除 `run_log.json` 以外的运行记录文件。
- 禁止写入 `asset/阶段二：数据清洗/` 或真实业务产物。
- 禁止修改配置快照、manifest、错误摘要、run result、调度器或 fake service 行为。
- 禁止静默覆盖旧 run 的 `run_log.json`。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -k run_log -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 能在临时 run 目录内写出 `run_log.json`。
- [ ] `run_log.json` 可被 JSON 解析，并包含 `run_id`、`run_dir`、`status`、`target_scenes`、`events`。
- [ ] 写入结果返回 [[RuntimeLogWriteResult]]，成功时包含事件数量和日志路径。
- [ ] 缺少日志路径、路径逃逸 run 目录、不可序列化事件时失败清楚。
- [ ] 不写 manifest、error summary、run result 或真实数据产物。

- [ ] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

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

