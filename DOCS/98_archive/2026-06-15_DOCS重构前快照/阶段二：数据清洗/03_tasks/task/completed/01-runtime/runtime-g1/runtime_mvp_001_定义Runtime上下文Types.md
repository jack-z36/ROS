# L3 微元任务：定义 Runtime 上下文 Types

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[01_Runtime运行上下文定义]]  
L3 编号：`runtime_mvp_001`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md`

## 2. 本次目标

```text
把 [[RunContext]] 原子数据定义落成源码中的 Runtime 上下文类型，并用最小测试验证必需字段和基础构造语义。
```

## 3. 本次不做

- 不创建 run 目录。
- 不读取配置文件。
- 不检查输入产物是否存在。
- 不实现 Runtime 调度、日志、manifest 或错误摘要。
- 不实现 [[SceneResult]]、[[PipelineResult]]、[[RuntimeStepRecord]]、[[RuntimeErrorRef]]；这些由后续 L3 处理。

## 4. 执行对象

- [[RunContext]]
- `src/data_clean/schemas/` 下的 Runtime 上下文类型定义。
- 对应的最小构造/字段校验测试。

## 5. 执行依赖

- [[RunContext]] 原子数据定义必须已经存在。
- [[RunMode]]、[[ServiceMode]]、[[SceneName]]、[[RunStatus]] 的实现可能尚未完成；本任务可以引用它们的既有实现，或在缺失时通过类型占位/字符串注解保持边界清晰，并在执行摘要中说明依赖未完成。
- 必须遵守 `Types -> Config -> Repo -> Service -> Runtime -> UI` 单向依赖；本任务只能落在 Types/Schemas 层。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：无直接上游接口；本任务属于 Runtime MVP 的数据语义基座。
上游接口定义位置：无。
当前 L3 期望消费的字段 / 文件 / 返回值：不消费上游运行时接口，只读取 L2 与原子数据定义文档。
是否存在接口冲突：无。
如果有冲突，本次处理策略：如发现现有 schemas 中已有同名对象，先复用或兼容现有对象，不得另起冲突定义；在执行摘要中说明。
```

## 7. 预期改动形态

- 新增或更新一个 Runtime 上下文 Types 源码文件，位置应在 `src/data_clean/schemas/` 下。
- 必要时更新 `src/data_clean/schemas/__init__.py` 暴露 [[RunContext]]。
- 必要时新增或更新 Runtime/contract 方向的最小测试文件。
- 如新增源码模块，更新 `src/data_clean/data_clean_architecture.md` 的目录结构说明。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[RunContext]] | dataclass / Pydantic model / TypedDict 中择一，优先匹配仓库现有风格 | `src/data_clean/schemas/` | Run 目录、配置快照、预检查、调度、日志、manifest、错误摘要模块 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `run_id` | string | 本次 Runtime 运行的唯一身份。 | 无 | 必须非空，运行期间稳定。 |
| `run_mode` | [[RunMode]] | 本次运行处于哪种入口和范围。 | 无 | 必须属于 [[RunMode]]。 |
| `service_mode` | [[ServiceMode]] | 本次调用 fake service 还是真实 service。 | Runtime MVP 可默认 fake | 必须属于 [[ServiceMode]]。 |
| `target_scenes` | list of [[SceneName]] | 本次计划执行的阶段二场景。 | 无 | 必须非空，只能包含 [[SceneName]]。 |
| `active_scene` | [[SceneName]] 或空 | 当前正在执行的场景。 | 空 | 如果存在，必须属于 [[SceneName]]。 |
| `input_paths` | map | 本次运行依赖的输入产物路径映射。 | 空 map 或由入口提供 | key 必须表达输入语义。 |
| `output_root` | path / string | 本次运行输出根位置。 | 无 | 必须非空，真实路径存在性可由后续模块检查。 |
| `run_dir` | path / string / 空 | 本次运行的独立记录目录。 | 空 | 由 Run 目录管理模块回填。 |
| `config_path` | path / string / 空 | 用户指定或默认读取的配置文件。 | 空 | 存在性由配置加载模块检查。 |
| `config_snapshot_path` | path / string / 空 | 本次实际生效配置快照路径。 | 空 | 由配置快照模块回填。 |
| `status` | [[RunStatus]] | 本次运行当前或最终状态。 | `created` | 必须属于 [[RunStatus]]。 |
| `started_at` | datetime / 空 | Runtime 开始执行时间。 | 空 | 后续 Runtime 状态流转回填。 |
| `finished_at` | datetime / 空 | Runtime 结束执行时间。 | 空 | 后续 Runtime 状态流转回填。 |
| `duration_ms` | integer / 空 | 本次运行耗时。 | 空 | 如果存在，必须非负。 |
| `metadata` | map | 额外运行元信息。 | 空 map | 不得承载必需字段。 |

## 9. 数据定义验收重点

- [[RunContext]] 能被 import 或被文档链接引用。
- 能实例化最小有效 Runtime 上下文。
- 缺少 `run_id`、`run_mode`、`service_mode`、`target_scenes`、`output_root` 或 `status` 时有明确失败或测试覆盖。
- `target_scenes` 为空时有测试覆盖。
- 相关原子数据定义文档已存在，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunContext.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunMode.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceMode.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneName.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunStatus.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
3. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/schemas/__init__.py`
2. `src/data_clean/schemas/ros2_schemas.py`
3. `src/data_clean/data_clean_architecture.md`

## 11. 允许修改

- `src/data_clean/schemas/` 下新增或更新 Runtime 上下文 Types 文件。
- `src/data_clean/schemas/__init__.py`
- `src/data_clean/tests/` 下与本任务直接相关的最小测试。
- `src/data_clean/data_clean_architecture.md`

## 12. 禁止修改

- 不修改 `src/data_clean/runtime/`、`service/`、`repo/`、`config/`、`ui/` 中的实现。
- 不修改 `start_data_clean.sh`。
- 不生成任何 `src/data_clean/runs/` 运行目录。
- 不修改真实数据产物目录 `asset/阶段二：数据清洗/`。

## 13. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime/test_runtime_context_types.py
```

如果测试目录或测试运行环境尚未就绪，必须至少执行：

```bash
python3 -m compileall src/data_clean/schemas
```

并在执行摘要中说明未运行 pytest 的具体原因。

## 14. 成功标准

- [ ] [[RunContext]] 类型已定义在 Types/Schemas 层。
- [ ] [[RunContext]] 可以被 import 和最小实例化。
- [ ] 必需字段和空 `target_scenes` 的失败行为有测试或替代检查。
- [ ] 未实现 run 目录、配置加载、调度或日志。
- [ ] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`


交接摘要必须包含：

1. 修改了哪些文件。
2. 新增了哪些函数 / 测试。
3. 如何运行验收。
4. 当前没做什么。
5. 下一步建议。

## 16. 执行摘要

### 成功标准验证

- [x] [[RunContext]] 类型已定义在 Types/Schemas 层。
- [x] [[RunContext]] 可以被 import 和最小实例化。
- [x] 必需字段和空 `target_scenes` 的失败行为有测试或替代检查。
- [x] 未实现 run 目录、配置加载、调度或日志。
- [x] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。（待移动文件）

### 交接内容

1. **修改的文件**：
   - `src/data_clean/schemas/runtime_context.py`（新增）
   - `src/data_clean/schemas/__init__.py`（更新，导出 Runtime 上下文类型）
   - `src/data_clean/data_clean_architecture.md`（更新目录结构表）
   - `src/data_clean/tests/runtime/test_runtime_context_types.py`（新增）

2. **新增的函数/测试**：
   - `schemas/runtime_context.py`：`RunMode`、`ServiceMode`、`SceneName`、`RunStatus` 枚举；`RunContext` dataclass（含 `__post_init__` 校验）
   - `tests/runtime/test_runtime_context_types.py`：10 个测试用例，覆盖枚举值、最小实例化、完整实例化、必需字段缺失校验、包导入验证

3. **验收命令**：
   ```bash
   cd src/data_clean && python3 -m pytest tests/runtime/test_runtime_context_types.py -v
   ```
   结果：10 passed in 0.02s

4. **当前没做什么**：
   - 不创建 run 目录
   - 不读取配置文件
   - 不检查输入产物是否存在
   - 不实现 Runtime 调度、日志、manifest 或错误摘要
   - 不实现 SceneResult、PipelineResult、RuntimeStepRecord、RuntimeErrorRef

5. **下一步建议**：
   - 执行 `runtime_mvp_002`：定义 Runtime 状态与模式枚举（如本任务中枚举已实现，可确认或跳过）
   - 执行 `runtime_mvp_003`：定义 Runtime 结果与错误引用 Types
   - 后续 L3 可实现 Run 目录管理、配置加载、预检查等模块
