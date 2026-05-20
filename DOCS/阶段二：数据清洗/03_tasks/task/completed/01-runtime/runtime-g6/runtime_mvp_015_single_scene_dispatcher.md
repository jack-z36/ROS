# L3 微元任务：实现单场景调度器

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[06_场景注册与Service调度模块]]  
L3 编号：`runtime_mvp_015`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`

## 2. 本次目标

```text
实现单个 SceneName 的调度流程：预检查通过且 service 已注册时调用绑定，失败时不调用 service，并返回 SceneResult 与调度事件。
```

## 3. 本次不做

- 不实现全流程多场景调度。
- 不实现 Service 注册表本身。
- 不实现 fake service 或真实 service 业务逻辑。
- 不写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不修改 UI 入口或 `start_data_clean.sh`。

## 4. 执行对象

本次主要处理 [[RunContext]]、[[ServiceRegistry]]、[[ServiceBinding]]、[[InputArtifactPrecheckSummary]] 到单个 [[SceneResult]] 和 [[SceneDispatchEvent]] 的编排闭环。

## 5. 执行依赖

- `runtime_mvp_013` 已定义 Service 注册与调度 Types。
- `runtime_mvp_014` 已实现可查询的 [[ServiceRegistry]]。
- `runtime_mvp_010` 到 `runtime_mvp_012` 已定义并实现输入产物预检查结果。
- [[07_Fake Service模块]] 已定义 [[FakeServiceResult]] 语义；若功能7代码尚未实现，本任务可用测试内最小 fake callable 模拟 service 绑定，不得实现完整 fake service 模块。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_010、runtime_mvp_012、runtime_mvp_013、runtime_mvp_014
上游接口定义位置：DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g5/；DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md；runtime_mvp_014_service_registry.md
当前 L3 期望消费的字段 / 文件 / 返回值：RunContext.active_scene 或目标 SceneName、ServiceRegistry lookup、ServiceBinding.callable_ref、InputArtifactPrecheckSummary.status/blocking_errors、SceneResult、SceneDispatchEvent
是否存在接口冲突：如 fake service 代码未实现，本任务不能扩大范围实现功能7，只允许在测试中使用局部 callable
如果有冲突，本次处理策略：暂停说明；或仅实现调度器对 callable 协议的最小消费，不落地 fake service 模块
```

## 7. 预期改动形态

- 新增一个单场景调度函数或小模块。
- 新增测试覆盖：预检查通过时调用绑定并返回成功结果；预检查失败时不调用绑定；未注册场景时失败；service callable 失败时返回失败 [[SceneResult]]。
- 调度过程产生可供后续日志模块消费的 [[SceneDispatchEvent]]。

## 8. 编排输出

### 调用顺序

```text
入口：RunContext + SceneName + ServiceRegistry + InputArtifactPrecheckSummary
↓
步骤 1：确认输入产物预检查通过
↓
步骤 2：从 ServiceRegistry 查询 ServiceBinding
↓
步骤 3：更新或记录 active_scene / scene_started 事件
↓
步骤 4：调用 ServiceBinding.callable_ref
↓
步骤 5：将返回值转换或汇总为 SceneResult
↓
完成：返回 SceneResult + SceneDispatchEvent 列表
失败：不继续调用后续逻辑，返回失败 SceneResult + RuntimeErrorRef
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
| --- | --- | --- | --- | --- |
| 输入预检查结果 | 调度开始前 | [[InputArtifactPrecheckSummary]] | 放行或阻塞 | 阻塞时不查询或不调用 service |
| [[ServiceRegistry]] | 预检查通过后 | [[SceneName]]、[[ServiceMode]] | [[ServiceBinding]] | 未注册时返回失败 [[SceneResult]] |
| service callable | binding 命中后 | [[RunContext]]、[[SceneName]]、预检查摘要 | service 结果或 [[SceneResult]] | 异常或失败包装为 [[RuntimeErrorRef]] |
| 结果汇总逻辑 | callable 返回后 | service 结果 | [[SceneResult]] | 汇总失败时返回失败结果 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
| --- | --- | --- | --- |
| scene_started | 开始调用 service 前 | [[SceneDispatchEvent]] | 后续日志/UI 消费 |
| scene_succeeded | service 返回成功 | [[SceneResult]]、[[SceneDispatchEvent]] | 后续日志/UI 消费 |
| scene_failed | 预检查失败、注册缺失或 service 失败 | [[SceneResult]]、[[RuntimeErrorRef]]、[[SceneDispatchEvent]] | 后续错误摘要消费 |

## 9. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchPlan.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchEvent.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g5/runtime_mvp_012_input_artifact_min_boundary_check.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_014_service_registry.md`

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
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止实现全流程调度器。
- 禁止实现 Service 注册表 Types 或查询逻辑，除非只是修复本任务发现的上游小缺陷并在摘要说明。
- 禁止实现 fake service 或真实 service 模块。
- 禁止写运行日志、manifest、错误摘要或 run result。
- 禁止修改配置预检查或输入产物预检查实现。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 输入预检查通过且 service 已注册时，会调用绑定 callable。
- [x] 输入预检查失败时，不调用 service。
- [x] 目标场景未注册时，不调用 service，并返回结构化失败。
- [x] service callable 返回失败或抛异常时，返回失败 [[SceneResult]] 和 [[RuntimeErrorRef]]。
- [x] 调度过程产生可消费的 [[SceneDispatchEvent]]。
- [x] 未实现全流程调度、fake service 或日志/manifest 写入。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 执行摘要

### 1. 读取的相关 L3 任务文件
- `runtime_mvp_013` (service dispatch types) — `runtime_dispatch_types.py` 已实现（纳入 `__init__.py` 导出），测试文件 `test_runtime_dispatch_types.py` 存在
- `runtime_mvp_014` (service registry) — `ServiceRegistry` dataclass 已定义，但 `runtime/` 下无独立的 `service_registry.py` 模块；本任务通过 `registry.bindings.get(scene_name)` 直接消费 registry
- `runtime_mvp_012` (input artifact min boundary check) — 已归档，`InputArtifactPrecheckSummary` 可消费

### 2. 修改的文件
- **新增** `src/data_clean/runtime/scene_dispatcher.py` — 单场景调度器实现
- **新增** `src/data_clean/tests/runtime/test_scene_dispatcher.py` — 22 个测试用例
- **修改** 当前 L3 任务文件：勾选成功标准，追加本执行摘要
- **清理** `src/data_clean/schemas/__pycache__/service_dispatch_types.cpython-312.pyc` — 清理过期 pyc（`runtime_dispatch_types.py` 已替代）

### 3. 新增的函数 / 测试

**实现** (`scene_dispatcher.py`):
- `dispatch_single_scene(context, scene_name, registry, precheck_summary) -> tuple[SceneResult, list[SceneDispatchEvent]]`
  - 步骤 1：预检查放行（`RunStatus.SUCCEEDED`）
  - 步骤 2：`registry.bindings.get(scene_name)` 查询
  - 步骤 3：发送 `SCENE_STARTED` 事件
  - 步骤 4：调用 `binding.callable_ref(context, scene_name, precheck_summary)`
  - 步骤 5：异常时返回 `SceneResult(FAILED)` + `SCENE_FAILED` 事件；成功时返回 `SceneResult(SUCCEEDED)` + `SCENE_SUCCEEDED` 事件

**测试** (22 tests):
  - `TestPrecheckPassed` (4) — 调用 service、传参正确、timing 字段、input_paths 传递
  - `TestPrecheckFailed` (3) — 不调用、错误码、无 timing
  - `TestUnregisteredScene` (2) — 不调用、`service_not_registered` 错误码
  - `TestServiceCallableFails` (3) — 返回 FAILED、异常消息捕获、timing 字段
  - `TestEdgeCases` (2) — 非 target_scenes 但已注册、run_id 透传
  - `TestDispatchEvents` (6) — 数量、顺序、字段、各种失败场景的事件
  - `TestReturnType` (2) — 返回结构类型检查

### 4. TDD red / green / refactor
- Red: `ModuleNotFoundError: No module named 'runtime.scene_dispatcher'` → 确认模块不存在
- Green: 编写 `scene_dispatcher.py`，22 测试通过
- Refactor: 修正 import 路径从 `service_dispatch_types` 改为 `runtime_dispatch_types`（因 `__init__.py` 已更新导出源）；清理过期 pyc

### 5. 验收命令
```bash
python3 -m pytest src/data_clean/tests/runtime/test_scene_dispatcher.py -q
```
22 passed in 0.05s。

上下游全量回归 (126 tests)：
```bash
python3 -m pytest src/data_clean/tests/runtime/test_scene_dispatcher.py src/data_clean/tests/runtime/test_runtime_dispatch_types.py src/data_clean/tests/runtime/test_input_artifact_prechecker.py src/data_clean/tests/runtime/test_input_artifact_types.py src/data_clean/tests/runtime/test_scene_input_requirements.py src/data_clean/tests/runtime/test_config_prechecker.py src/data_clean/tests/runtime/test_config_precheck_types.py src/data_clean/tests/runtime/test_runtime_config_types.py -q
```
126 passed in 0.12s。

### 6. 成功标准勾选情况
全部 8 项已验证通过。

### 7. 当前没做什么
- 未实现全流程调度器（015 只做单场景）
- 未实现 fake service 模块（功能7）
- 未写运行日志、manifest、错误摘要或 run result
- 未创建 `runtime/service_registry.py`（014 的 `ServiceRegistry` 以 dataclass 形式存在于 `schemas/`，无独立 runtime 模块）

### 8. 下一步建议
- **实现 runtime_mvp_016**（全流程调度器）：在单场景调度器之上，遍历 `SceneDispatchPlan.target_scenes`，按 `stop_on_failure` 策略串行调用 `dispatch_single_scene`，汇总 `PipelineResult`。
- **归档 013/014**：`runtime_mvp_013` 和 `runtime_mvp_014` 的实现和测试已存在，任务文件可归档到 `completed/runtime-g6/`。
- **清理类型重复**：`service_dispatch_types.cpython-312.pyc` 已清理，但建议确认无其他引用遗留。

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

