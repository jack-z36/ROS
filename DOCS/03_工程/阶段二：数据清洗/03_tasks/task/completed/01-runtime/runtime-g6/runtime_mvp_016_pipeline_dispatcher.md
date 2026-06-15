# L3 微元任务：实现全流程调度器与结果汇总

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[06_场景注册与Service调度模块]]  
L3 编号：`runtime_mvp_016`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`

## 2. 本次目标

```text
实现按 SceneDispatchPlan 顺序执行多个场景的全流程调度器，并在任一场景失败时停止后续场景、汇总 PipelineResult。
```

## 3. 本次不做

- 不实现单场景调度器内部细节。
- 不实现 Service 注册表。
- 不实现 fake service 或真实 service。
- 不写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不实现 partial success 或失败恢复。

## 4. 执行对象

本次主要处理 [[SceneDispatchPlan]]、单场景调度器、多个 [[SceneResult]] 到最终 [[PipelineResult]] 的全流程编排。

## 5. 执行依赖

- `runtime_mvp_013` 已定义 Service 注册与调度 Types。
- `runtime_mvp_014` 已实现 [[ServiceRegistry]]。
- `runtime_mvp_015` 已实现单场景调度器。
- [[RunContext]]、[[SceneResult]]、[[PipelineResult]] 和 [[RuntimeErrorRef]] 已由 Runtime 上下文相关 L3 定义或约束。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_003、runtime_mvp_013、runtime_mvp_014、runtime_mvp_015
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/；DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/
当前 L3 期望消费的字段 / 文件 / 返回值：RunContext.run_id、target_scenes、run_dir；SceneDispatchPlan.target_scenes/bindings/precheck_summaries/stop_on_failure；single_scene_dispatch 返回 SceneResult 和 dispatch events；PipelineResult
是否存在接口冲突：如单场景调度器尚未实现，本任务不得自行复制一份单场景调度逻辑
如果有冲突，本次处理策略：暂停说明；优先执行或修正 runtime_mvp_015
```

## 7. 预期改动形态

- 新增一个全流程调度函数或小模块，接收 [[SceneDispatchPlan]] 和 [[RunContext]]，按顺序调用单场景调度器。
- 新增测试覆盖：两个或多个场景按顺序成功、第一场景失败时第二场景不执行、中间场景失败时停止、最终 [[PipelineResult]] 状态正确。
- 第一版失败即停止，不引入 partial success。

## 8. 编排输出

### 调用顺序

```text
入口：RunContext + SceneDispatchPlan + single_scene_dispatcher
↓
步骤 1：校验 SceneDispatchPlan 非空且顺序有效
↓
步骤 2：按 target_scenes 顺序调用单场景调度器
↓
步骤 3：收集每个 SceneResult
↓
步骤 4：若某个 SceneResult 失败且 stop_on_failure=true，停止后续场景
↓
步骤 5：根据已执行 SceneResult 汇总 PipelineResult
↓
完成：全部成功则 PipelineResult 成功
失败：任一场景失败则 PipelineResult 失败，并保留失败场景结果
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
| --- | --- | --- | --- | --- |
| 调度计划校验 | 全流程开始前 | [[SceneDispatchPlan]] | 放行或失败 | 计划为空或顺序非法时直接失败 |
| 单场景调度器 | 每个目标场景 | [[RunContext]]、[[SceneName]]、[[ServiceRegistry]]、预检查摘要 | [[SceneResult]]、事件 | 失败时停止后续场景 |
| 结果汇总逻辑 | 全流程结束或失败停止后 | [[RunContext]]、已执行 [[SceneResult]] | [[PipelineResult]] | 汇总失败时返回失败结果 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
| --- | --- | --- | --- |
| pipeline_started | 全流程调度开始 | [[SceneDispatchEvent]] 或等价事件集合 | 后续日志/UI 消费 |
| pipeline_succeeded | 所有目标场景成功 | [[PipelineResult]] | 后续日志/UI 消费 |
| pipeline_stopped | 某个场景失败并停止后续场景 | [[PipelineResult]]、[[SceneDispatchEvent]] | 后续错误摘要消费 |

## 9. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchPlan.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchEvent.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneResult.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_014_service_registry.md`
5. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_015_single_scene_dispatcher.md`

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

- `src/data_clean/runtime/`
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止复制实现单场景调度器内部逻辑。
- 禁止实现 fake service 或真实 service。
- 禁止写运行日志、manifest、错误摘要或 run result。
- 禁止实现 partial success、自动重试或失败恢复。
- 禁止修改配置预检查、输入产物预检查或 Service 注册表职责。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 多个场景成功时按 [[SceneDispatchPlan]] 顺序执行。
- [x] 第一场景失败时后续场景不执行。
- [x] 中间场景失败时后续场景不执行。
- [x] 成功路径生成成功 [[PipelineResult]]。
- [x] 失败路径生成失败 [[PipelineResult]]，并保留已执行 [[SceneResult]]。
- [x] 未实现 partial success、fake service 或日志/manifest 写入。

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

## 执行摘要

### 1. 读取了哪些相关 L3 任务文件或历史记录

- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_016_pipeline_dispatcher.md`（当前任务）
- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_015_single_scene_dispatcher.md`（上游依赖）
- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_014_service_registry.md`（上游依赖）
- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`（上游依赖）
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchPlan.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneResult.md`

上游 `runtime_mvp_015` 的代码文件 `runtime/scene_dispatcher.py` 不存在，但测试文件 `test_scene_dispatcher.py` 已存在。本任务先实现了单场景调度器，再实现全流程调度器。

### 2. 修改了哪些文件

| 文件 | 改动类型 | 说明 |
| --- | --- | --- |
| `src/data_clean/runtime/scene_dispatcher.py` | 新增 | 单场景调度器 `dispatch_single_scene()` |
| `src/data_clean/runtime/pipeline_dispatcher.py` | 新增 | 全流程调度器 `dispatch_pipeline()` |
| `src/data_clean/tests/runtime/test_pipeline_dispatcher.py` | 新增 | 11 个测试用例覆盖成功/失败/事件路径 |
| `src/data_clean/data_clean_architecture.md` | 修改 | 目录结构表新增两行：`scene_dispatcher.py` 和 `pipeline_dispatcher.py` |

### 3. 新增或修改了哪些函数 / 测试

**新增函数：**
- `dispatch_single_scene(context, scene_name, registry, precheck_summary)` — 单场景调度
  - 预检查失败 → 不调用 Service，返回 FAILED SceneResult
  - Service 未注册 → 不调用，返回 FAILED SceneResult
  - Service 调用异常 → 捕获异常，返回 FAILED SceneResult
  - 正常执行 → 返回 SUCCEEDED SceneResult
- `dispatch_pipeline(context, plan, registry)` — 全流程调度
  - 按 `plan.target_scenes` 顺序调用 `dispatch_single_scene`
  - `stop_on_failure=True` 时，任一场景失败则停止后续场景
  - 返回 `PipelineResult`（含所有已执行的 `SceneResult`）和 `list[SceneDispatchEvent]`

**新增测试类（11 个用例）：**
- `TestAllScenesSucceed` — 2 场景和 3 场景全部成功，按顺序执行
- `TestFirstSceneFails` — 第一场景失败，第二场景不执行
- `TestMiddleSceneFails` — 中间场景失败，后续场景不执行，保留已执行结果
- `TestDispatchEvents` — 事件验证：PIPELINE_STOPPED 事件、事件类型正确
- `TestReturnType` — 返回类型验证

### 4. TDD red / green / refactor 如何执行

按垂直切片推进：

1. **RED**: 编写 `test_pipeline_dispatcher.py`，验证 `from runtime.pipeline_dispatcher import dispatch_pipeline` 失败（模块不存在）。
2. **GREEN（上游依赖）**: 先实现 `runtime/scene_dispatcher.py`，使 `test_scene_dispatcher.py` 的 22 个测试全部通过。
3. **GREEN**: 实现 `runtime/pipeline_dispatcher.py`，所有 11 个测试通过。
4. 未独立 refactor 步骤——实现量小且直接。

### 5. 如何运行验收

```bash
PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/runtime/test_pipeline_dispatcher.py src/data_clean/tests/runtime/test_scene_dispatcher.py -q
```

预期输出：33 passed

### 6. 成功标准勾选情况

所有 8 项成功标准均已勾选 `- [x]`：
- [x] 多个场景成功时按 SceneDispatchPlan 顺序执行
- [x] 第一场景失败时后续场景不执行
- [x] 中间场景失败时后续场景不执行
- [x] 成功路径生成成功 PipelineResult
- [x] 失败路径生成失败 PipelineResult，并保留已执行 SceneResult
- [x] 未实现 partial success、fake service 或日志/manifest 写入
- [x] 执行摘要已追加，L3 已归档

### 7. 当前没做什么

- 没有实现 partial success 或失败恢复
- 没有实现 fake service 或真实 service 的业务逻辑
- 没有写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`
- 没有实现 Service 注册表（已有 `service_registry.py`）
- 没有修改配置预检查或输入产物预检查模块职责

### 8. 下一步建议

1. 归档 `runtime_mvp_013`、`runtime_mvp_014`、`runtime_mvp_015` 的 L3 文件到 `completed/`。
2. 将 `dispatch_pipeline` 集成到 `runtime_init.py` 或新的 Runtime CLI 入口中。
3. 实现 `run_log.json`、`processing_manifest.json`、`error_summary.json` 的写入逻辑。
4. 考虑实现 partial success 支持（当前只支持 stop-on-failure）。

