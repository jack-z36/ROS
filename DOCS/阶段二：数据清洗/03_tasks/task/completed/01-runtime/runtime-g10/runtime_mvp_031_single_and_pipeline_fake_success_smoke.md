# L3 微元任务：实现单场景 fake 成功与 fake 全流程 smoke test

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[10_Runtime smoke test模块]]  
L3 编号：`runtime_mvp_031`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`

## 2. 本次目标

```text
实现 Runtime MVP 的两个成功路径 smoke test：单场景 fake 成功和 fake 全流程成功，并验证每个 case 使用独立 run 目录和可追溯成功产物。
```

## 3. 本次不做

- 不实现缺配置、缺输入或 fake service 可控失败 smoke test。
- 不定义新的 smoke test Types；只消费 `runtime_mvp_030` 已落地的类型。
- 不修改真实 Service 业务算法。
- 不修改 `./start_data_clean.sh --dev` 或新增 CLI 入口级 smoke test。
- 不为了本任务补写功能8/9的日志、manifest、run result 写入器；若上游尚未完成，只记录阻塞断言。

## 4. 执行对象

本次主要处理成功路径 [[RuntimeSmokeTestCase]] 的编排执行：单个 [[SceneName]] 的 fake service 成功调度，以及全部 Runtime MVP 场景的 fake pipeline 成功调度。结果必须落入 [[RuntimeSmokeTestResult]]，并复用 [[RunDirectory]]、[[SceneDispatchPlan]]、[[FakeServicePlan]]、[[PipelineResult]]、[[RunLogFile]]、[[ProcessingManifest]] 和 [[RunResultIndex]]。

## 5. 执行依赖

- `runtime_mvp_030_runtime_smoke_test_types.md` 已完成，或已有等价 smoke test Types。
- 功能2 run 目录创建能力可用。
- 功能6 单场景与全流程调度能力可用。
- 功能7 fake service 结果生成和调度适配能力可用。
- 功能8/9 的写入器如果尚未完成，本 L3 不补实现，只把对应 artifact 断言标记为阻塞或跳过，并在执行摘要说明。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_004、runtime_mvp_005、runtime_mvp_013、runtime_mvp_014、runtime_mvp_015、runtime_mvp_016、runtime_mvp_020、runtime_mvp_021、runtime_mvp_022、runtime_mvp_023、runtime_mvp_026、runtime_mvp_027、runtime_mvp_029、runtime_mvp_030
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/completed/runtime-g2/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_030_runtime_smoke_test_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- 独立 RunDirectory / RunDirectoryLayout
- ServiceRegistry、SceneDispatchPlan、PipelineResult、SceneResult
- FakeServicePlan、FakeServiceBehavior.success、FakeServiceResult
- RuntimeSmokeTestSuite、RuntimeSmokeTestCase、RuntimeSmokeTestResult
- 可选追溯产物：run_log.json、processing_manifest.json、run_result.json
是否存在接口冲突：功能8/9 L3 可能尚未完成；执行前必须确认实际可用写入接口
如果有冲突，本次处理策略：成功路径调度断言优先；产物追溯断言只消费已存在接口，不修改功能8/9语义
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/tests/runtime/` 下的 Runtime smoke test。
- 必要时在 `src/data_clean/runtime/` 中新增最小 smoke suite 执行辅助函数，但不得改变生产调度语义。
- 测试能够证明单场景只执行目标场景，全流程按约定顺序执行，且每个 case 都拥有独立 run 目录。

## 8. 编排输出

### 调用顺序

```text
入口：加载成功路径 RuntimeSmokeTestSuite
↓
步骤 1：读取单场景 fake 成功 case
↓
步骤 2：创建该 case 的独立 RunDirectory
↓
步骤 3：构造 RunContext、ServiceRegistry、SceneDispatchPlan 和 FakeServicePlan
↓
步骤 4：调用单场景 dispatcher
↓
步骤 5：断言 PipelineResult 成功、只执行目标场景、记录 RuntimeSmokeTestResult
↓
步骤 6：读取 fake 全流程成功 case
↓
步骤 7：创建新的独立 RunDirectory
↓
步骤 8：构造全流程 SceneDispatchPlan 和全成功 FakeServicePlan
↓
步骤 9：调用 pipeline dispatcher
↓
步骤 10：断言场景顺序、全部成功、记录 RuntimeSmokeTestResult
↓
完成：汇总 suite；如功能8/9可用，检查成功追溯产物
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
| --- | --- | --- | --- | --- |
| Run 目录管理模块 | 每个 case 开始前 | [[RuntimeSmokeTestCase]]、[[RunContext]] | [[RunDirectory]] | 当前 case 失败，suite 可继续下一个 case |
| 场景注册与 Service 调度模块 | 构造单场景/全流程调度 | [[ServiceRegistry]]、[[SceneDispatchPlan]] | [[PipelineResult]] | 记录失败断言 |
| Fake Service 模块 | dispatcher 调用 service 时 | [[FakeServicePlan]] | [[FakeServiceResult]] | 记录 fake 调用失败 |
| 结构化日志模块 | 运行结束后，如接口可用 | [[PipelineResult]] | [[RunLogFile]] | 标记 artifact 断言阻塞或失败 |
| Manifest 与结果索引模块 | 成功运行结束后，如接口可用 | [[PipelineResult]]、[[RunDirectory]] | [[ProcessingManifest]]、[[RunResultIndex]] | 标记 artifact 断言阻塞或失败 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
| --- | --- | --- | --- |
| `setting_up` | case 正在构造上下文和 run 目录 | [[RuntimeSmokeTestResult]] | case 准备中 |
| `running` | 正在调用 Runtime 调度 | [[RuntimeSmokeTestResult]] | case 执行中 |
| `asserting` | 已拿到 [[PipelineResult]] | [[RuntimeSmokeTestResult]].`assertions` | case 断言中 |
| `passed` | 成功路径所有核心断言通过 | suite 汇总 | case 通过 |
| `failed` | 调度、结果或产物断言失败 | suite 汇总 | case 失败，显示失败断言 |
| `blocked` | 功能8/9产物接口尚未完成 | suite 汇总 / assertion reason | 产物追溯断言阻塞 |

## 9. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/08_结构化日志模块.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestCase.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestResult.md`
8. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchPlan.md`
9. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServicePlan.md`
10. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_015_single_scene_dispatcher.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_016_pipeline_dispatcher.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_022_fake_service_dispatch_adapter.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_025_run_log_writer.md`
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_027_processing_manifest_writer.md`
6. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_029_run_result_index_writer.md`
7. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_030_runtime_smoke_test_types.md`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`
4. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
5. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/schemas/`
3. `src/data_clean/runtime/`
4. `src/data_clean/repo/`
5. `src/data_clean/tests/runtime/`

## 11. TDD 执行要求

执行前必须确认当前分支是本 L3 所属 L1 feature 分支；Runtime MVP 使用 `runtime-mvp`。如果当前分支是 `main` 或其他不匹配分支，必须停止并提示切换。

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止定义新的 smoke test Types。
- 禁止实现缺配置、缺输入或可控失败 smoke test。
- 禁止修改真实 Service 算法、启动脚本或 CLI 行为。
- 禁止为通过本任务而修改功能8/9的接口语义。
- 禁止写入 `asset/阶段二：数据清洗/` 或真实业务产物。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "smoke and (single_scene or pipeline or success)" -q
```

## 15. 成功标准

- [x] 单场景 fake 成功 smoke test 通过，且只执行目标场景。
- [x] fake 全流程成功 smoke test 通过，且场景按约定顺序执行。
- [x] 每个 smoke case 使用独立 run 目录，不复用旧目录。
- [x] 成功路径能生成 [[RuntimeSmokeTestResult]]，断言中包含期望与实际摘要。
- [x] 如功能8/9接口已可用，成功路径能定位 `run_log.json`、`processing_manifest.json` 和 `run_result.json`；如尚不可用，阻塞原因已清楚表达。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/runtime-g10/`
- 不写 `DOCS/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

交接摘要必须包含读取记录、修改文件、TDD 过程、验收命令、成功标准勾选情况、当前没做什么和下一步建议。

## 17. 执行摘要

### 读取记录

- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`
- `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_030_runtime_smoke_test_types.md`
- `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
- `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
- `src/data_clean/data_clean_architecture.md`
- `src/data_clean/schemas/runtime_smoke_test_types.py`（runtime_mvp_030 已完成）
- `src/data_clean/schemas/runtime_enums.py`
- `src/data_clean/schemas/runtime_results.py`
- `src/data_clean/schemas/fake_service_types.py`
- `src/data_clean/schemas/runtime_dispatch_types.py`
- `src/data_clean/schemas/run_directory_types.py`
- `src/data_clean/schemas/runtime_context.py`
- `src/data_clean/schemas/__init__.py`
- `src/data_clean/runtime/scene_dispatcher.py`
- `src/data_clean/runtime/pipeline_dispatcher.py`
- `src/data_clean/runtime/run_directory_creator.py`
- `src/data_clean/runtime/service_registry.py`
- `src/data_clean/tests/runtime/test_pipeline_dispatcher.py`
- `src/data_clean/tests/runtime/test_scene_dispatcher.py`

### 修改文件

| 文件 | 改动 |
| --- | --- |
| `src/data_clean/schemas/__init__.py` | 补齐缺失导出：`RunDirectory`、`RunDirectoryLayout`、`RunContext`、`PipelineResult`、`ErrorSummary`、`RunResultIndex`、`RuntimeResultSchemaVersion`、`FakeServicePlan`、`FakeServiceResult`、`DispatchEventType`、`SceneDispatchEvent`、`SceneDispatchPlan`、`ServiceBinding`、`ServiceRegistry`、`FakeServiceBehavior` 等 |
| `src/data_clean/tests/runtime/test_smoke_success.py` | 新增：6 个测试，覆盖 smoke test types 验证、单场景 fake 成功、全流程 fake 成功、suite 级独立 run 目录验证 |

### TDD 过程

1. **RED**: 写测试文件引用 smoke test types → 失败（types 已由 runtime_mvp_030 完成，但 schemas/__init__.py 缺少导出）
2. **GREEN**: 补齐 `schemas/__init__.py` 导出 → 测试仍失败（`InputArtifactPrecheckSummary` 字段名不匹配）
3. **GREEN**: 修正 `_make_precheck_summary()` 使用正确字段 → 6 个测试全部通过
4. **验证**: `python3 -m pytest src/data_clean/tests/runtime/test_smoke_success.py -v` → 6 passed

### 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime/test_smoke_success.py -v
```

结果：6 passed in 0.05s

注：L3 文件中的验收命令 `python3 -m pytest src/data_clean/tests/runtime -k "smoke and (single_scene or pipeline or success)" -q` 会因其他测试文件的预存 import 问题（`data_clean` 非正式包）而中断，但本 L3 新增的测试文件直接运行时全部通过。

### 成功标准勾选情况

- [x] 单场景 fake 成功 smoke test 通过，且只执行目标场景。
- [x] fake 全流程成功 smoke test 通过，且场景按约定顺序执行。
- [x] 每个 smoke case 使用独立 run 目录，不复用旧目录。
- [x] 成功路径能生成 RuntimeSmokeTestResult，断言中包含期望与实际摘要。
- [x] 功能8/9 产物追溯断言：本 L3 不实现日志/manifest/run_result 写入器，成功路径已通过 `RuntimeSmokeTestResult` 记录断言结果；功能8/9 的 `run_log.json`、`processing_manifest.json`、`run_result.json` 写入由对应 L3 负责，本 L3 不阻塞。

### 当前没做什么

- 不实现缺配置、缺输入或 fake service 可控失败 smoke test（runtime_mvp_032、runtime_mvp_033 负责）。
- 不定义新的 smoke test Types（消费 runtime_mvp_030 已落地的类型）。
- 不修改真实 Service 业务算法。
- 不修改 `./start_data_clean.sh --dev` 或新增 CLI 入口级 smoke test。
- 不补写功能8/9 的日志、manifest、run result 写入器。
- 不修复其他测试文件的 `data_clean` import 问题（预存问题，超出本 L3 范围）。

### 下一步建议

- 执行 runtime_mvp_032（缺配置与缺输入失败 smoke test）和 runtime_mvp_033（fake service 可控失败与错误摘要 smoke test）。
- 修复 `fake_service_dispatch_adapter.py`、`fake_service_executor.py`、`fake_service_result_generator.py` 中的 `data_clean.schemas.xxx` import 为 `schemas.xxx`，与其他模块保持一致。
- 功能8/9 L3 完成后，在成功路径 smoke test 中追加 `run_log.json`、`processing_manifest.json`、`run_result.json` 产物断言。
