# L3 微元任务：实现 Runtime 日志事件转换器

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[08_结构化日志模块]]  
L3 编号：`runtime_mvp_024`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/08_结构化日志模块.md`

## 2. 本次目标

```text
实现把 RuntimeStepRecord、SceneDispatchEvent、SceneResult、PipelineResult 和 RuntimeErrorRef 转换为 RuntimeLogEvent 的最小转换逻辑。
```

## 3. 本次不做

- 不定义新的日志 Types；只消费 `runtime_mvp_023` 已落地的类型。
- 不写 `run_log.json` 文件。
- 不创建 run 目录。
- 不写 manifest、error summary 或 run result。
- 不改变场景调度器、fake service 或真实 service 行为。

## 4. 执行对象

- 日志事件转换函数、类或等价 callable。
- [[RuntimeStepRecord]]
- [[SceneDispatchEvent]]
- [[SceneResult]]
- [[PipelineResult]]
- [[RuntimeErrorRef]]
- [[RuntimeLogEvent]]

## 5. 执行依赖

- `runtime_mvp_023_structured_log_types.md` 已完成，或仓库中已经存在等价 [[RunLogFile]]、[[RuntimeLogEvent]]、[[RuntimeLogWriteResult]] 和事件类型。
- 功能1、功能6相关 Types 已存在，能提供步骤、调度事件、场景结果、最终结果和错误引用。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_023、runtime_mvp_001、runtime_mvp_003、runtime_mvp_013、runtime_mvp_016
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/
当前 L3 期望消费的字段 / 文件 / 返回值：
- RuntimeStepRecord.step_name、scene_name、status、message、details、started_at、finished_at
- SceneDispatchEvent.event_type、scene_name、status、message、error、created_at
- SceneResult.scene_name、status、input_paths、output_paths、duration_ms、error
- PipelineResult.run_id、status、scene_results、run_log_path、manifest_path、error_summary_path
- RuntimeErrorRef.error_code、scene_name、step_name、message、details
是否存在接口冲突：执行前必须确认上游实际字段；不得凭空兼容多个猜测版本
如果有冲突，本次处理策略：暂停说明；只在本任务范围内做明确的适配，不修改上游接口
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/runtime/` 中的日志事件转换模块。
- 新增 runtime 测试，覆盖步骤记录、调度事件、场景结果、最终结果和错误引用转换。
- 转换结果必须可 JSON 序列化，并保留 `run_id`、事件类型、状态、场景、错误引用和时间信息。

## 8. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
| --- | --- | --- | --- |
| 合法 [[RuntimeStepRecord]] | 转成 `event_type=runtime_step` 的 [[RuntimeLogEvent]] | 包含 step、status、scene、message、details | 无 |
| 合法 [[SceneDispatchEvent]] | 转成 `event_type=dispatch_event` 的 [[RuntimeLogEvent]] | 保留调度事件类型、场景、状态、错误 | 无 |
| 合法 [[SceneResult]] | 转成 `event_type=scene_result` 的 [[RuntimeLogEvent]] | 包含场景、状态、输入输出摘要、耗时、错误 | 无 |
| 合法 [[PipelineResult]] | 转成 `event_type=pipeline_result` 的 [[RuntimeLogEvent]] | 包含最终状态、场景结果数量、关键文件路径 | 无 |
| 合法 [[RuntimeErrorRef]] | 转成 `event_type=error` 的 [[RuntimeLogEvent]] | 包含错误码、失败步骤、场景和摘要 | 无 |
| 缺失 `run_id` | 无法归属日志事件 | 返回结构化失败或抛出受控异常 | `runtime_log_run_id_missing` |
| 非 JSON 可序列化 details | 转换时清理为摘要或返回结构化失败 | 不能生成不可写事件 | `runtime_log_event_not_serializable` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
| --- | --- | --- | --- |
| `event_id` | string | 单 run 内事件标识 | 非空且可排序或可稳定断言 |
| `run_id` | string | 运行标识 | 必须来自输入上下文或显式参数 |
| `event_type` | RuntimeLogEventType | 事件类型 | 受控取值 |
| `scene_name` | SceneName 或空 | 场景 | 场景相关事件应填写 |
| `status` | RunStatus | 状态 | 必须使用上游状态类型 |
| `message` | string 或空 | 摘要 | 失败时不能只写“失败” |
| `details` | map | 机器可读摘要 | 必须可 JSON 序列化 |
| `error` | RuntimeErrorRef 或空 | 错误引用 | 失败事件必须存在 |

## 9. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/08_结构化日志模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeLogEvent.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeStepRecord.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchEvent.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneResult.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeErrorRef.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_016_pipeline_dispatcher.md`
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
4. `src/data_clean/tests/runtime/`

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/tests/runtime/`
- 必要的同层导出文件
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/`

## 13. 禁止修改

- 禁止重新定义 `runtime_mvp_023` 已落地的日志 Types。
- 禁止写 `run_log.json` 或创建运行产物。
- 禁止修改 run 目录创建、配置加载、调度器或 fake service 行为。
- 禁止写 manifest、error summary 或 run result。
- 禁止读取、解析或写入真实 MCAP / canonical dataset / exports。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -k log_event -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] [[RuntimeStepRecord]] 能转换为 `runtime_step` 日志事件。
- [ ] [[SceneDispatchEvent]] 能转换为 `dispatch_event` 日志事件。
- [ ] [[SceneResult]] 能转换为 `scene_result` 日志事件。
- [ ] [[PipelineResult]] 能转换为 `pipeline_result` 日志事件。
- [ ] [[RuntimeErrorRef]] 能转换为 `error` 日志事件。
- [ ] 缺少 `run_id` 或不可序列化 details 时失败清楚。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_024_runtime_log_event_converter>.md`
- 执行过程、当前状态、未完成事项和下一步建议写在同一个记录文件中
- 完成并更新任务文件后，将当前 L3 从 `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/` 移到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/runtime-g8/`

交接摘要必须包含：

1. 读取了哪些相关 L3 任务文件或执行记录
2. 修改了哪些文件
3. 新增或修改了哪些函数 / 测试
4. TDD red / green / refactor 如何执行
5. 如何运行验收，命令必须使用 `python3`
6. 成功标准勾选情况
7. 当前没做什么
8. 下一步建议
