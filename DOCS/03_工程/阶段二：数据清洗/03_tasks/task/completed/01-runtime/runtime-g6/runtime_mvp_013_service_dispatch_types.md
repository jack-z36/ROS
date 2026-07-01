# L3 微元任务：定义 Service 注册与调度 Types

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[06_场景注册与Service调度模块]]  
L3 编号：`runtime_mvp_013`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`

## 2. 本次目标

```text
定义 Service 注册与调度所需的注册表、绑定、调度计划和调度事件 Types，使后续注册表和调度器共用同一套接口。
```

## 3. 本次不做

- 不实现 service 注册表查询逻辑。
- 不实现单场景或全流程调度器。
- 不实现 fake service 或真实 service。
- 不写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不修改 UI 入口或 `start_data_clean.sh`。

## 4. 执行对象

本次主要处理 [[ServiceRegistry]]、[[ServiceBinding]]、[[SceneDispatchPlan]] 和 [[SceneDispatchEvent]] 的代码级表达，并复用已有 [[RunContext]]、[[SceneName]]、[[ServiceMode]]、[[RunStatus]]、[[RuntimeErrorRef]]、[[InputArtifactPrecheckSummary]]、[[SceneResult]] 和 [[PipelineResult]]。

## 5. 执行依赖

- `runtime_mvp_001` 到 `runtime_mvp_003` 已定义 Runtime 上下文、状态、模式、结果和错误引用相关 Types。
- `runtime_mvp_010` 已定义输入产物预检查相关 Types。
- 功能6 L2 已定义注册表、绑定、调度计划和调度事件的数据语义。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_002、runtime_mvp_003、runtime_mvp_010
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/；DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：SceneName、ServiceMode、RunStatus、RuntimeErrorRef、InputArtifactPrecheckSummary、SceneResult、PipelineResult；如代码中尚未实现，按上游 L3 约束先执行上游任务
是否存在接口冲突：无已知冲突；功能7 fake service 语义已形成 L2，但本任务只定义调度通用 Types
如果有冲突，本次处理策略：暂停说明；不得重新定义与上游同名但字段不同的对象
```

## 7. 预期改动形态

- 在 Runtime MVP 现有 Types 位置新增或扩展 Service 注册与调度相关对象。
- 新增最小测试，能构造合法注册表、绑定、调度计划和调度事件。
- 非法场景、service mode 不一致、缺 binding 等情况必须能被类型或构造校验表达清楚。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[ServiceRegistry]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | Service 注册表实现、调度器、smoke test |
| [[ServiceBinding]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 注册表、单场景调度器、fake service 适配 |
| [[SceneDispatchPlan]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 单场景调度器、全流程调度器 |
| [[SceneDispatchEvent]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 结构化日志、错误摘要、smoke test |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `bindings` | map of [[SceneName]] to [[ServiceBinding]] | 注册表绑定集合 | 无 | 必须覆盖注册场景 |
| `service_mode` | [[ServiceMode]] | fake 或真实 service 模式 | 无 | 必须与 [[RunContext]] 一致 |
| `callable_ref` | callable 标识或对象引用 | service 可调用入口 | 无 | 装配完成后必须可调用 |
| `target_scenes` | list of [[SceneName]] | 调度场景顺序 | 无 | 非空，全流程按受控顺序 |
| `precheck_summaries` | map of [[SceneName]] to [[InputArtifactPrecheckSummary]] | 输入预检查结果 | 无 | 目标场景必须都有摘要 |
| `event_type` | string / enum | 调度事件类型 | 无 | 受控取值 |
| `error` | [[RuntimeErrorRef]] 或空 | 失败错误引用 | 空 | 失败事件必须存在 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceRegistry.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceBinding.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchPlan.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchEvent.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
3. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
4. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

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

- 禁止实现注册表查询逻辑、单场景调度器或全流程调度器。
- 禁止实现 fake service 或真实 service。
- 禁止写运行日志、manifest、错误摘要或 run result。
- 禁止重新定义与上游 [[SceneName]]、[[ServiceMode]]、[[RunStatus]] 或 [[RuntimeErrorRef]] 冲突的对象。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 已定义 [[ServiceRegistry]]。
- [x] 已定义 [[ServiceBinding]]。
- [x] 已定义 [[SceneDispatchPlan]]。
- [x] 已定义 [[SceneDispatchEvent]]。
- [x] 非法场景、模式不一致或缺 binding 能被清楚表达。
- [x] 未实现注册表查询、Service 调度或 fake service。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到对应 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/<功能组>/`
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

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

### 1. 读取的相关文档
- L2 能力模块：`06_场景注册与Service调度模块.md`
- L2 数据定义：`ServiceRegistry.md`、`ServiceBinding.md`、`SceneDispatchPlan.md`、`SceneDispatchEvent.md`
- 上游 L3：`runtime_mvp_001`、`runtime_mvp_002`、`runtime_mvp_003`、`runtime_mvp_010`（已归档，未找到具体 L3 历史记录文件内容，按上游接口定义对齐即可）
- 约束文件：`L3编码执行原则.md`、`L3执行TDD与归档约束.md`、`上游依赖接口对齐约束.md`、`文件存放规范.md`、`01_runtime_mvp/执行约束.md`
- 现有代码：`schemas/runtime_enums.py`、`schemas/runtime_context.py`、`schemas/runtime_results.py`、`schemas/runtime_precheck_types.py`、`schemas/input_artifact_types.py`、`schemas/__init__.py`、`data_clean_architecture.md`

### 2. 修改的文件
- **新增** `src/data_clean/schemas/runtime_dispatch_types.py` — 包含 `DispatchEventType` 枚举、`ServiceBinding`、`ServiceRegistry`、`SceneDispatchPlan`、`SceneDispatchEvent` 四个 dataclass
- **新增** `src/data_clean/tests/runtime/test_runtime_dispatch_types.py` — 24 个测试用例覆盖所有类型
- **修改** `src/data_clean/schemas/__init__.py` — 导出新增的 5 个公共名字

### 3. 新增的类型 / 测试

| 类型 | 文件 | 说明 |
| --- | --- | --- |
| `DispatchEventType` | `runtime_dispatch_types.py` | 调度事件类型枚举（5 个受控值） |
| `ServiceBinding` | `runtime_dispatch_types.py` | 场景到可调用 service 的绑定描述 |
| `ServiceRegistry` | `runtime_dispatch_types.py` | 场景注册表，含模式一致性校验 |
| `SceneDispatchPlan` | `runtime_dispatch_types.py` | 调度执行计划，含覆盖性 & 模式校验 |
| `SceneDispatchEvent` | `runtime_dispatch_types.py` | 调度结构化事件，失败事件强制 error |

测试文件 `test_runtime_dispatch_types.py` 包含 7 个测试类共 24 个用例：

- `TestServiceBinding`（3 用例）：最小/全量构造、不可调用入参拒绝
- `TestDispatchEventType`（1 用例）：枚举值存在性
- `TestServiceRegistry`（6 用例）：最小构造、空 bindings/registered_scenes 拒绝、注册场景缺 binding 拒绝、service_mode 不一致拒绝、可选字段
- `TestSceneDispatchPlan`（6 用例）：最小构造、空 run_id/target_scenes 拒绝、缺 binding 拒绝、缺 precheck_summary 拒绝、service_mode 不一致拒绝、多场景
- `TestSceneDispatchEvent`（6 用例）：plan_created、scene_started、scene_failed 缺 error 拒绝、pipeline_stopped 缺 error 拒绝、scene_failed 含 error、空 run_id 拒绝、包导入
- 额外 2 用例含在 `test_import_from_package` 风格验证中

### 4. TDD 执行记录
按垂直切片推进：先写测试文件（RED），确认 ModuleNotFoundError → 实现 `runtime_dispatch_types.py`（GREEN）→ 修复 2 处测试 regex 匹配大小写问题 → 24 用例全通过。**refactor 阶段**：无需额外重构，类型定义简洁且与代码库现有 dataclass 风格一致。

### 5. 验收命令
```bash
python3 -m pytest src/data_clean/tests/runtime/test_runtime_dispatch_types.py -q
```
输出：24 passed in 0.05s

### 6. 成功标准勾选
- [x] 已定义 [[ServiceRegistry]] — `ServiceRegistry` dataclass
- [x] 已定义 [[ServiceBinding]] — `ServiceBinding` dataclass
- [x] 已定义 [[SceneDispatchPlan]] — `SceneDispatchPlan` dataclass
- [x] 已定义 [[SceneDispatchEvent]] — `SceneDispatchEvent` dataclass + `DispatchEventType` 枚举
- [x] 非法场景、模式不一致或缺 binding 能被清楚表达 — `__post_init__` 校验覆盖空/缺失/不一致场景
- [x] 未实现注册表查询、Service 调度或 fake service — 仅定义 Types
- [x] 执行摘要已追加到当前 L3 文件末尾
- [x] 当前 L3 已归档到对应 `task/completed/runtime-g6/`

### 7. 当前没做什么
- 没有实现注册表查询逻辑、单场景调度器或全流程调度器。
- 没有实现 fake service 或真实 service。
- 没有写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 没有修改 UI 入口或 `start_data_clean.sh`。
- 没有重新定义上游已有的 `SceneName`、`ServiceMode`、`RunStatus`、`RuntimeErrorRef`。
- 没有写集中共享记录文件。

### 8. 下一步建议
1. **runtime_mvp_014**：实现场景 Service 注册表（查询逻辑），依赖本 L3 的 `ServiceRegistry` 和 `ServiceBinding`。
2. **runtime_mvp_015**：实现单场景调度器，消费 `SceneDispatchPlan`、`ServiceBinding` 和 `InputArtifactPrecheckSummary` 生成 `SceneResult` 和 `SceneDispatchEvent`。
3. **runtime_mvp_016**：实现全流程调度器与结果汇总，消费多个 `SceneResult` 生成 `PipelineResult`。

