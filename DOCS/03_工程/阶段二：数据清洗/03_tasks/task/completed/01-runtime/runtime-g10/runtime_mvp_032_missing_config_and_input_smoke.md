# L3 微元任务：实现缺配置与缺输入失败 smoke test

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[10_Runtime smoke test模块]]  
L3 编号：`runtime_mvp_032`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`

## 2. 本次目标

```text
实现缺配置和缺输入两个失败路径 smoke test，验证 Runtime 能在正确预检查阶段停止、给出稳定错误码，并且不会调用 fake service。
```

## 3. 本次不做

- 不实现单场景成功、全流程成功或 fake service 可控失败 smoke test。
- 不定义新的 smoke test Types；只消费 `runtime_mvp_030` 已落地的类型。
- 不修改配置加载、配置预检查或输入产物预检查的语义。
- 不自动补齐缺失配置或创建缺失输入。
- 不修改 `./start_data_clean.sh --dev`。

## 4. 执行对象

本次主要处理两个失败路径 [[RuntimeSmokeTestCase]] 的判断：缺配置必须停在 [[ConfigPrecheckResult]] 阶段，缺输入必须停在 [[InputArtifactPrecheckSummary]] 阶段。两个 case 都必须证明 fake service 未被调用，并把实际错误表达为 [[RuntimeSmokeTestResult]] 中的 [[RuntimeErrorRef]] 或等价测试层错误引用。

## 5. 执行依赖

- `runtime_mvp_030_runtime_smoke_test_types.md` 已完成，或已有等价 smoke test Types。
- 功能3 配置加载与配置快照相关类型可用。
- 功能4 配置预检查能力可用。
- 功能5 输入产物预检查能力可用。
- 功能6/7 的调度与 fake service 能提供可观察的“未调用”断言方式，或测试可通过 stub/mock 记录调用次数。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_007、runtime_mvp_008、runtime_mvp_017、runtime_mvp_018、runtime_mvp_019、runtime_mvp_010、runtime_mvp_011、runtime_mvp_012、runtime_mvp_015、runtime_mvp_020、runtime_mvp_030
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g3/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g4/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g5/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_015_single_scene_dispatcher.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_020_fake_service_types.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_030_runtime_smoke_test_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- EffectiveRuntimeConfig 或等价生效配置对象
- ConfigPrecheckResult 的 passed/issues/error code 表达
- InputArtifactPrecheckSummary 的 passed/results/missing artifact 表达
- RuntimeSmokeTestCase.expected_error_code、RuntimeSmokeTestResult.assertions
- fake service 调用次数或 dispatch event，能证明 service 未被调用
是否存在接口冲突：无已知冲突；执行前必须确认上游错误码实际命名
如果有冲突，本次处理策略：优先保持上游错误码语义，调整 smoke case 期望；不得在本任务中修改预检查规则语义
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/tests/runtime/` 下的失败路径 smoke test。
- 必要时在 `src/data_clean/runtime/` 中新增最小 smoke 断言辅助函数，但不得改变配置预检查或输入预检查生产语义。
- 测试能够证明缺配置、缺输入都在 service 调用前失败，且错误信息稳定可追溯。

## 8. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
| --- | --- | --- | --- |
| 合法输入 | 配置预检查通过、输入预检查通过，本任务不执行成功调度，只证明失败 case 的前置构造可控 | case 可进入后续调度前阶段 | 无 |
| 缺失输入 | 目标场景输入产物不存在或不可读 | 输入预检查失败，service 调用次数为 0，[[RuntimeSmokeTestResult]] 记录失败符合预期 | `missing_input_artifact` 或上游稳定错误码 |
| 边界输入 | Runtime 级必需配置缺失、空值或类型不合法 | 配置预检查失败，输入预检查和 service 不应继续执行，[[RuntimeSmokeTestResult]] 记录失败符合预期 | `missing_required_config` 或上游稳定错误码 |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
| --- | --- | --- | --- |
| `case_id` | string | 当前失败路径 case | 必须来自 [[RuntimeSmokeTestCase]] |
| `status` | [[RunStatus]] / 测试层状态 | case 断言结果 | 预期失败发生时，case 自身应为 passed |
| `precheck_result` | [[ConfigPrecheckResult]] / [[InputArtifactPrecheckSummary]] | 触发失败的预检查结果 | 必须指明失败阶段 |
| `observed_error` | [[RuntimeErrorRef]] / 测试层错误 | 实际错误引用 | 错误码必须稳定 |
| `service_call_count` | int | fake service 调用次数 | 缺配置/缺输入必须为 0 |
| `assertions` | list | 期望与实际断言 | 必须包含阶段、错误码、调用次数 |

## 9. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestCase.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestResult.md`
6. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/EffectiveRuntimeConfig.md`
7. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckResult.md`
8. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactPrecheckSummary.md`
9. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeErrorRef.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g3/runtime_mvp_007_runtime_config_types.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g3/runtime_mvp_008_config_load_and_overrides.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g4/runtime_mvp_017_config_precheck_types.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g4/runtime_mvp_018_config_prechecker.md`
5. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md`
6. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g5/runtime_mvp_012_input_artifact_min_boundary_check.md`
7. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_030_runtime_smoke_test_types.md`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
3. `DOCS/02_约束/阶段二任务体系/功能分支接力流程.md`
4. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
5. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
6. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/schemas/`
3. `src/data_clean/runtime/`
4. `src/data_clean/tests/runtime/`

## 11. TDD 执行要求

执行前必须确认当前分支是本 L3 所属 L1 feature 分支；Runtime MVP 使用 `runtime-mvp`。如果当前分支是 `main` 或其他不匹配分支，必须停止并提示切换。

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止定义新的 smoke test Types。
- 禁止修改配置预检查或输入预检查的错误语义。
- 禁止实现成功路径或可控失败摘要 smoke test。
- 禁止自动创建缺失配置、缺失输入或真实数据产物。
- 禁止修改启动脚本或真实 Service 算法。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "smoke and (missing_config or missing_input or precheck)" -q
```

## 15. 成功标准

- [ ] 缺配置 smoke test 在配置预检查阶段失败，且不会调用 fake service。
- [ ] 缺输入 smoke test 在输入产物预检查阶段失败，且不会调用 fake service。
- [ ] 两个失败路径都有稳定错误码或 reason，并写入 [[RuntimeSmokeTestResult]] 断言。
- [ ] 如果错误码与 L2 预期不一致，执行摘要明确记录采用的上游实际错误码。
- [ ] 相关测试通过。

- [ ] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 17. 执行摘要

### 执行信息

- 执行日期：2026-05-20
- 执行分支：`runtime-mvp`
- 执行人：Ubuntu L3 Agent

### 读取记录

- 已读取 `runtime_mvp_030` 定义的 smoke test Types（`RuntimeSmokeCaseKind`、`RuntimeSmokeTestCase`、`RuntimeSmokeTestResult`、`RuntimeSmokeAssertion`）
- 已读取 `ConfigPrecheckGate` 和 `init_runtime` 编排逻辑（`runtime/runtime_init.py`）
- 已读取 `ConfigPrechecker` 预检查实现（`runtime/config_prechecker.py`）
- 已读取 `input_artifact_prechecker` 输入预检查实现（`runtime/input_artifact_prechecker.py`）
- 已读取 `scene_dispatcher` 单场景调度器（`runtime/scene_dispatcher.py`）
- 已读取 `pipeline_dispatcher` 全流程调度器（`runtime/pipeline_dispatcher.py`）
- 已读取 `fake_service_dispatch_adapter`（`runtime/fake_service_dispatch_adapter.py`）
- 已读取现有 success smoke test 实现模式（`tests/runtime/test_smoke_success.py`）
- 已读取阶段二约束文档

### 修改文件

- 新增：`src/data_clean/tests/runtime/test_smoke_failure.py`

### TDD 过程

- TDD 技能已加载，采用 tracer bullet 方式逐测试实现。
- 先实现 `test_missing_config_precheck_fails` 和 `test_missing_input_precheck_fails` 两个核心失败路径测试。
- 再补充 `test_missing_config_case_definition` 和 `test_missing_input_case_definition` 验证 case 定义合法性。
- 最后补充 `test_pipeline_stops_on_first_missing_input` 验证 pipeline 级缺输入场景。
- 每次 RED → GREEN 迭代后验证通过。

### 验收命令

```bash
PYTHONPATH="src:src/data_clean" python3 -m pytest src/data_clean/tests/runtime/test_smoke_failure.py src/data_clean/tests/runtime/test_smoke_success.py -k "smoke and (missing_config or missing_input or precheck)" -q --override-ini="confcutdir=src/data_clean"
```

结果：5 passed, 6 deselected

### 成功标准勾选

- [x] 缺配置 smoke test（`test_missing_config_precheck_fails`）在配置预检查阶段失败，且不会调用 fake service（`tracker.call_count == 0`，input precheck hook 也未调用）
- [x] 缺输入 smoke test（`test_missing_input_precheck_fails`）在输入产物预检查阶段失败，且不会调用 fake service（`tracker.call_count == 0`）
- [x] 两个失败路径都有稳定错误码（`effective_config_missing` / `scene_precheck_failed`），并写入 `RuntimeSmokeTestResult` 断言
- [x] 相关测试通过（5 passed）

### 错误码说明

L2 预期错误码为 `config_precheck_failed` 和 `input_precheck_failed`，但上游实际实现的错误码为 `effective_config_missing`（config precheck 产生）和 `scene_precheck_failed`（dispatcher 对预检查失败的场景返回）。本任务直接采用上游实际错误码，未修改预检查语义。

### 当前没做什么

- 未实现成功路径或可控失败摘要 smoke test（与 L3 范围一致）
- 未定义新的 smoke test Types
- 未修改配置预检查或输入预检查的错误语义
- 未自动补齐缺失配置或创建缺失输入
- 未修改启动脚本或真实 Service 算法

### 下一步建议

- 后续 L3 可实现 `CONTROLLED_FAILURE` 类型 smoke test（fake service 可控失败）
- 可考虑为 smoke test 增加 suite runner，自动化执行所有 case 并生成汇总报告

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g10/`
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

交接摘要必须包含读取记录、修改文件、TDD 过程、验收命令、成功标准勾选情况、当前没做什么和下一步建议。
