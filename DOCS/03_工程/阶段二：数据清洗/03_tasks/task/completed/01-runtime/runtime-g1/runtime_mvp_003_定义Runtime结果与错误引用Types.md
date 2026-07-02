# L3 微元任务：定义 Runtime 结果与错误引用 Types

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[01_Runtime运行上下文定义]]  
L3 编号：`runtime_mvp_003`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md`

## 2. 本次目标

```text
把 [[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]] 和 [[RuntimeErrorRef]] 四个 Runtime 结果/错误对象落成源码 Types，并用最小测试验证成功与失败摘要结构。
```

## 3. 本次不做

- 不定义 [[RunContext]] 主对象。
- 不定义 [[RunStatus]]、[[RunMode]]、[[ServiceMode]]、[[SceneName]] 枚举。
- 不实现日志写入器。
- 不实现 manifest 或 error summary 文件写入。
- 不实现 Service 调度。

## 4. 执行对象

- [[SceneResult]]
- [[PipelineResult]]
- [[RuntimeStepRecord]]
- [[RuntimeErrorRef]]
- `src/data_clean/schemas/` 下的 Runtime 结果和错误引用 Types。

## 5. 执行依赖

- 相关原子数据定义文档必须已经存在。
- [[RunStatus]] 和 [[SceneName]] 的实现可能由 `runtime_mvp_002` 提供；如果尚未完成，本任务不得重复创造冲突枚举，应使用已有定义或清楚记录依赖缺口。
- 必须遵守 Types/Schemas 层不依赖 Config、Repo、Service、Runtime、UI 的规则。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_002_定义Runtime状态与模式枚举（如果已执行）。
上游接口定义位置：`src/data_clean/schemas/` 中的 [[RunStatus]] 和 [[SceneName]] 实现；文档定义位于 `L2数据定义/RunStatus.md`、`L2数据定义/SceneName.md`。
当前 L3 期望消费的字段 / 文件 / 返回值：[[RunStatus]]、[[SceneName]] 可 import，并可用于结果对象字段。
是否存在接口冲突：如果枚举尚未实现或命名不一致，则存在接口缺口。
如果有冲突，本次处理策略：不重复定义第二套枚举；暂停说明冲突，或在同一 schemas 模块中复用/补齐已有枚举并记录原因。
```

## 7. 预期改动形态

- 新增或更新 Runtime 结果与错误引用 Types 源码文件，位置应在 `src/data_clean/schemas/` 下。
- 必要时更新 `src/data_clean/schemas/__init__.py` 暴露四个对象。
- 必要时新增或更新 Runtime/contract 方向的最小测试文件。
- 如新增源码模块，更新 `src/data_clean/data_clean_architecture.md`。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[SceneResult]] | dataclass / Pydantic model / TypedDict 中择一，优先匹配仓库现有风格 | `src/data_clean/schemas/` | [[PipelineResult]]、日志、manifest、错误摘要 |
| [[PipelineResult]] | dataclass / Pydantic model / TypedDict 中择一，优先匹配仓库现有风格 | `src/data_clean/schemas/` | UI 结束反馈、run result、manifest、错误摘要 |
| [[RuntimeStepRecord]] | dataclass / log event model | `src/data_clean/schemas/` | 结构化日志、错误定位、smoke test |
| [[RuntimeErrorRef]] | dataclass / error model | `src/data_clean/schemas/` | [[SceneResult]]、[[PipelineResult]]、错误摘要、UI 失败反馈 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 场景结果或错误所属场景。 | 无或空 | 场景内结果必需；全局错误可为空。 |
| `status` | [[RunStatus]] | 场景、pipeline 或步骤状态。 | 无 | 必须属于 [[RunStatus]]。 |
| `input_paths` | map | 实际消费输入路径。 | 空 map | key 必须表达输入语义。 |
| `output_paths` | map | 实际生成或声明输出路径。 | 空 map | key 必须表达输出语义。 |
| `run_id` | string | 对应 Runtime 运行 ID。 | 无 | [[PipelineResult]] 中必需且非空。 |
| `scene_results` | list of [[SceneResult]] | 已执行场景结果列表。 | 空 list | [[PipelineResult]] 中必需。 |
| `run_log_path` | path / string | 结构化日志路径。 | 无 | [[PipelineResult]] 中必需。 |
| `manifest_path` | path / string / 空 | 成功时 manifest 路径。 | 空 | 成功路径应能定位。 |
| `error_summary_path` | path / string / 空 | 失败时错误摘要路径。 | 空 | 失败路径应能定位。 |
| `step_name` | string | Runtime 步骤名。 | 无 | [[RuntimeStepRecord]] 和 [[RuntimeErrorRef]] 中必需。 |
| `error_code` | string | 可分类错误码。 | 无 | [[RuntimeErrorRef]] 中必需且非空。 |
| `message` | string | 一行人类可读摘要。 | 空或无 | [[RuntimeErrorRef]] 中必需且非空。 |
| `details` | map | 机器可读补充信息。 | 空 map | 不能替代必需字段。 |
| `suggested_next_action` | string / 空 | 下一步建议。 | 空 | 可选。 |

## 9. 数据定义验收重点

- 四个对象能被 import。
- 能构造成功路径的 [[SceneResult]] 和 [[PipelineResult]]。
- 能构造失败路径的 [[RuntimeErrorRef]]，并挂入 [[SceneResult]] 或 [[PipelineResult]] 相关结构。
- `error_code`、`step_name`、`message` 缺失时有测试或替代检查覆盖。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneResult.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeStepRecord.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeErrorRef.md`
6. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunStatus.md`
7. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneName.md`

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
3. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/schemas/__init__.py`
2. `src/data_clean/schemas/ros2_schemas.py`
3. `src/data_clean/data_clean_architecture.md`

## 11. 允许修改

- `src/data_clean/schemas/` 下新增或更新 Runtime 结果与错误引用 Types 文件。
- `src/data_clean/schemas/__init__.py`
- `src/data_clean/tests/` 下与本任务直接相关的最小测试。
- `src/data_clean/data_clean_architecture.md`

## 12. 禁止修改

- 不修改 `src/data_clean/runtime/`、`service/`、`repo/`、`config/`、`ui/` 中的实现。
- 不实现日志写入、manifest 写入或 error summary 写入。
- 不修改 `start_data_clean.sh`。
- 不生成任何运行目录或真实数据产物。
- 不重复定义与上游冲突的 [[RunStatus]] 或 [[SceneName]]。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime/test_runtime_result_types.py
```

如果测试目录或测试运行环境尚未就绪，必须至少执行：

```bash
python3 -m compileall src/data_clean/schemas
```

并在执行摘要中说明未运行 pytest 的具体原因。

## 14. 成功标准

- [x] [[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]]、[[RuntimeErrorRef]] 已在 Types/Schemas 层定义。
- [x] 四个对象能被 import。
- [x] 成功路径和失败路径的最小构造测试或替代检查通过。
- [x] 未实现日志、manifest、错误摘要文件写入或调度逻辑。
- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`


交接摘要必须包含：

1. 修改了哪些文件。
2. 新增了哪些函数 / 测试。
3. 如何运行验收。
4. 当前没做什么。
5. 下一步建议。

---

## 16. 执行摘要

### 执行前读取

- 当前 L3 任务文件。
- L2 能力模块：`01_Runtime运行上下文定义.md`
- L2 数据定义：`SceneResult.md`、`PipelineResult.md`、`RuntimeStepRecord.md`、`RuntimeErrorRef.md`、`RunStatus.md`、`SceneName.md`
- 约束文件：`L3编码执行原则.md`、`文件存放规范.md`、`上游依赖接口对齐约束.md`、`执行约束.md`、`双机协作写入边界.md`、`功能分支接力流程.md`
- 代码文件：`schemas/__init__.py`、`schemas/runtime_context.py`、`schemas/runtime_enums.py`、`schemas/ros2_schemas.py`、`data_clean_architecture.md`

### 修改文件

| 文件 | 操作 | 说明 |
| --- | --- | --- |
| `src/data_clean/schemas/runtime_results.py` | 新增 | 定义 RuntimeErrorRef、RuntimeStepRecord、SceneResult、PipelineResult 四个 dataclass。 |
| `src/data_clean/schemas/__init__.py` | 更新 | 新增 runtime_results 导入和四个类型到 __all__。 |
| `src/data_clean/tests/runtime/__init__.py` | 新增 | runtime 测试包标记。 |
| `src/data_clean/tests/runtime/test_runtime_result_types.py` | 新增 | 14 个测试：成功/失败路径构造、必需字段校验、import 验证。 |
| `src/data_clean/data_clean_architecture.md` | 更新 | 目录结构表新增 runtime_results.py 条目。 |
| 当前 L3 文件 | 更新 | 勾选成功标准、追加执行摘要。 |

### TDD red / green / refactor

- Red：先编写 14 个测试覆盖四个类型的成功路径、失败路径和必需字段校验。
- Green：实现 runtime_results.py 四个 dataclass，含 `__post_init__` 校验。
- Refactor：整理 `__init__.py` 导入和 `__all__`，保持与已有 run_directory_types 共存。
- 全部 14 个测试一次通过，无需额外 refactor。

### 验收命令

```bash
python3 -m compileall src/data_clean/schemas
python3 -m pytest src/data_clean/tests/runtime/test_runtime_result_types.py -v
```

结果：`compileall` 通过，pytest 14 passed in 0.02s。

### 成功标准勾选

- [x] 四个对象已在 Types/Schemas 层定义。
- [x] 四个对象能被 import（TestImports 验证）。
- [x] 成功路径和失败路径的最小构造测试通过（SceneResult/PipelineResult 各覆盖成功与失败）。
- [x] 未实现日志、manifest、错误摘要文件写入或调度逻辑。
- [x] 执行摘要已追加。
- [x] 当前 L3 将归档到 `task/completed/runtime-g1/`。

### 当前没做什么

- 不定义 RunContext、RunStatus、RunMode、ServiceMode、SceneName（由 runtime_mvp_001/002 提供）。
- 不实现日志写入器、manifest 写入、error summary 写入。
- 不实现 Service 调度。
- 不修改 runtime/、service/、repo/、config/、ui/ 中的实现。

### 下一步建议

- 执行 runtime_mvp_004（如果存在）：定义 RunContext 主对象。
- Win 端可考虑同步整理阶段文档索引和 L2/L3 任务池状态。
