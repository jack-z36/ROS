# L3 微元任务：定义 Runtime smoke test Types 与 suite 契约

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[10_Runtime smoke test模块]]  
L3 编号：`runtime_mvp_030`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`

## 2. 本次目标

```text
定义 RuntimeSmokeTestCase、RuntimeSmokeTestSuite 和 RuntimeSmokeTestResult 的代码级契约，使后续 smoke test 能统一描述用例、期望、实际结果和断言。
```

## 3. 本次不做

- 不执行任何 smoke test。
- 不实现单场景、全流程、缺配置、缺输入或 fake service 可控失败用例。
- 不写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。
- 不修改 Runtime 调度器、fake service、manifest/error writer 或启动脚本。
- 不定义真实 Service 业务算法的验收标准。

## 4. 执行对象

本次主要处理 [[RuntimeSmokeTestCase]]、[[RuntimeSmokeTestSuite]] 和 [[RuntimeSmokeTestResult]] 的代码级表达。它必须复用 [[RunStatus]]、[[RunContext]]、[[RunDirectory]]、[[RunArtifactPath]]、[[SceneName]]、[[PipelineResult]]、[[RuntimeErrorRef]]、[[SceneDispatchPlan]]、[[FakeServiceBehavior]]、[[ProcessingManifest]]、[[ErrorSummary]] 和 [[RunResultIndex]]，不得重新定义这些上游对象。

## 5. 执行依赖

- 功能1 已定义 Runtime 上下文、状态、结果和错误引用，或已经存在等价代码结构。
- 功能2 已定义 run 目录和运行产物路径，或已经存在等价代码结构。
- 功能6 已定义场景调度计划，或已经存在等价代码结构。
- 功能7 已定义 fake service 行为和结果，或已经存在等价代码结构。
- 功能8/9 L2 已定义日志、manifest、error summary 和 run result 的产物语义；本 L3 只引用，不要求写入器已完成。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_002、runtime_mvp_003、runtime_mvp_004、runtime_mvp_013、runtime_mvp_020、runtime_mvp_023、runtime_mvp_026
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g1/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g2/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g7/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- RunStatus 成功/失败/阻塞等可表达最终状态的取值
- SceneName、SceneDispatchPlan 或等价目标场景描述
- FakeServiceBehavior 的 success / controlled_failure 等稳定行为取值
- PipelineResult、RuntimeErrorRef、RunArtifactPath 的结果、错误和产物路径表达
- ProcessingManifest、ErrorSummary、RunResultIndex 的路径引用语义
是否存在接口冲突：无已知冲突；执行前必须确认上游实际字段名和放置模块
如果有冲突，本次处理策略：暂停说明，不在 smoke test Types 中复制一套相似但字段不同的上游对象
```

## 7. 预期改动形态

- 在 `src/data_clean/schemas/` 或当前 Runtime Types 约定位置新增 smoke test 相关类型。
- 新增或扩展 runtime 测试，覆盖合法 case/suite/result 构造和非法 case 校验。
- smoke test 类型只表达测试层契约，不触发实际 Runtime 执行。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[RuntimeSmokeTestCase]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | `runtime_mvp_031`、`runtime_mvp_032`、`runtime_mvp_033` |
| [[RuntimeSmokeTestSuite]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 全部 smoke test 执行任务 |
| [[RuntimeSmokeTestResult]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 全部 smoke test 断言与汇总 |
| `RuntimeSmokeAssertion` | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 记录期望与实际断言 |
| `RuntimeSmokeCaseKind` | enum / Literal / 受控字符串集合 | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 区分 single_scene_success、pipeline_success、missing_config、missing_input、controlled_failure |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `case_id` | string | smoke test 用例标识 | 无 | suite 内唯一、非空 |
| `case_kind` | `RuntimeSmokeCaseKind` | 用例类别 | 无 | 必须为受控取值 |
| `target_scenes` | list of [[SceneName]] | 目标场景 | 空列表 | 成功/失败调度类 case 至少一个；未知场景必须失败清楚 |
| `fake_behavior` | [[FakeServiceBehavior]] / mapping | fake service 行为 | success | 不允许真实 service 模式 |
| `expected_status` | [[RunStatus]] / 测试层状态 | 期望最终状态 | 无 | 失败类 case 不得写成功状态 |
| `expected_error_code` | string / 空 | 期望错误码 | 空 | 期望失败时必须非空 |
| `expected_artifacts` | list of [[RunArtifactPath]] 或受控 artifact key | 期望产物 | 空列表 | 不得指向 raw MCAP 覆盖路径 |
| `pipeline_result` | [[PipelineResult]] / 空 | 实际 Runtime 结果 | 空 | 主流程执行后应存在 |
| `run_directory` | [[RunDirectory]] / 空 | 本 case 独立运行目录 | 空 | 目录创建成功后应存在 |
| `observed_error` | [[RuntimeErrorRef]] / 空 | 实际错误引用 | 空 | 失败 case 应存在 |
| `assertions` | list of `RuntimeSmokeAssertion` | 每条断言结果 | 空列表 | 必须同时包含期望和实际摘要 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestCase.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestSuite.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestResult.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunStatus.md`
6. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
7. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeErrorRef.md`
8. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceBehavior.md`
9. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunArtifactPath.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g2/runtime_mvp_004_run_directory_types.md`
5. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`
6. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_020_fake_service_types.md`
7. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g8/runtime_mvp_023_structured_log_types.md`
8. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md`

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

执行前必须确认当前分支是本 L3 所属 L1 feature 分支；Runtime MVP 使用 `runtime-mvp`。如果当前分支是 `main` 或其他不匹配分支，必须停止并提示切换。

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能。

## 12. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/runtime/`，仅当现有 Runtime Types 已放在该层
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止执行或接入实际 smoke test 流程。
- 禁止写入任何运行产物、真实数据产物或 `src/data_clean/runs/`。
- 禁止修改结构化日志、manifest/error summary 写入器、调度器、fake service 或启动脚本行为。
- 禁止重新定义与上游 [[RunStatus]]、[[SceneName]]、[[PipelineResult]]、[[RuntimeErrorRef]]、[[RunArtifactPath]] 冲突的对象。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "smoke and types" -q
```

## 15. 成功标准

- [x] 已定义 [[RuntimeSmokeTestCase]]、[[RuntimeSmokeTestSuite]] 和 [[RuntimeSmokeTestResult]] 的代码级结构。
- [x] 能构造覆盖单场景成功、全流程成功、缺配置、缺输入和可控失败的 suite。
- [x] 非法 case 能失败清楚，包括空 suite、未知场景、真实 service、失败 case 缺少期望错误码。
- [x] smoke test 类型复用上游 Runtime / dispatch / fake service / manifest error 对象，不复制冲突字段。
- [x] 相关测试通过。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g10/`
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

交接摘要必须包含读取记录、修改文件、TDD 过程、验收命令、成功标准勾选情况、当前没做什么和下一步建议。

---

## 执行摘要

### 读取记录

- 当前 L3 文件：`runtime_mvp_030_runtime_smoke_test_types.md`
- L2 能力模块说明：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`
- L2 数据定义：`RuntimeSmokeTestCase.md`、`RuntimeSmokeTestSuite.md`、`RuntimeSmokeTestResult.md`
- 上游代码类型：`runtime_enums.py`、`runtime_results.py`、`runtime_context.py`、`run_directory_types.py`、`runtime_dispatch_types.py`、`fake_service_types.py`、`manifest_types.py`、`structured_log_types.py`
- 已有测试模式：`test_runtime_result_types.py`
- 约束文档：`L3编码执行原则.md`、`L3执行TDD与归档约束.md`

### TDD 过程

1. 编写 `RuntimeSmokeCaseKind` enum + `RuntimeSmokeAssertion` dataclass → 写测试 → 通过
2. 编写 `RuntimeSmokeTestCase` dataclass（含校验逻辑）→ 写测试覆盖 valid + invalid → 通过
3. 编写 `RuntimeSmokeTestSuite` dataclass → 写测试覆盖 valid + invalid → 通过
4. 编写 `RuntimeSmokeTestResult` dataclass → 写测试覆盖 success/failure + invalid → 通过
5. 更新 `__init__.py` exports → 写 import 测试 → 通过

### 修改文件

- 新增：`src/data_clean/schemas/runtime_smoke_test_types.py` — 定义 5 个类型：
  - `RuntimeSmokeCaseKind` (enum): 5 种 case kind
  - `RuntimeSmokeAssertion` (dataclass): 期望 vs 实际断言记录
  - `RuntimeSmokeTestCase` (dataclass): 单个 smoke test case 定义，含完整校验
  - `RuntimeSmokeTestSuite` (dataclass): suite 聚合和校验
  - `RuntimeSmokeTestResult` (dataclass): 用例执行结果摘要
- 新增：`src/data_clean/tests/runtime/test_runtime_smoke_test_types.py` — 34 个测试，覆盖合法构造、非法校验、suite 聚合、import
- 修改：`src/data_clean/schemas/__init__.py` — 添加新类型到 exports

### 验收命令

```bash
PYTHONPATH=src python3 -m pytest src/data_clean/tests/runtime/test_runtime_smoke_test_types.py -v
```

结果：34 passed in 0.05s。

### 成功标准勾选情况

- [x] 已定义 RuntimeSmokeTestCase、RuntimeSmokeTestSuite、RuntimeSmokeTestResult 的代码级结构
- [x] 能构造覆盖单场景成功、全流程成功、缺配置、缺输入和可控失败的 suite
- [x] 非法 case 能失败清楚：空 case_id/title、真实 service、空 suite、missing required_case、success case 误缺 scenes、failure case 缺 error_code、failure case 期望 SUCCEEDED
- [x] smoke test 类型复用上游 Runtime/dispatch/fake service/manifest error 对象，不重复定义
- [x] 相关测试通过（34/34）

### 当前没做什么

- 未执行任何实际 smoke test
- 未实现 smoke test 执行器或编排逻辑（留给后续 runtime_mvp_031/032/033）
- 未修改调度器、fake service、日志、manifest/error writer
- 未定义 `run_log.json`、`processing_manifest.json`、`error_summary.json`
- 未知场景校验（引用未知 SceneName）留给 Python 枚举天然检查

### 下一步建议

- runtime_mvp_031：实现单场景 fake 成功与 fake 全流程 smoke test
- runtime_mvp_032：实现缺配置与缺输入失败 smoke test
- runtime_mvp_033：实现 fake service 可控失败与错误摘要 smoke test
