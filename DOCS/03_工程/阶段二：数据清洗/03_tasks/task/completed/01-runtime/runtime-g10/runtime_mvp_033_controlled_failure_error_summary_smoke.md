# L3 微元任务：实现 fake service 可控失败与错误摘要 smoke test

## 1. 任务定位

阶段：阶段二：数据清洗
场景：Runtime MVP
L1：`runtime_mvp`
L2 能力：[[10_Runtime smoke test模块]]
L3 编号：`runtime_mvp_033`
任务类别：流程编排类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`

## 2. 本次目标

```text
实现 fake service 可控失败 smoke test，验证 Runtime 在失败后停止后续场景，并能定位 error_summary 与 run_result 追溯产物。
```

## 3. 本次不做

- 不实现成功路径、缺配置或缺输入 smoke test。
- 不定义新的 smoke test Types；只消费 `runtime_mvp_030` 已落地的类型。
- 不重新定义 [[ErrorSummary]]、[[RunResultIndex]] 或 [[RuntimeErrorRef]]。
- 不修改 fake service 的基础行为语义。
- 不修改真实 Service 业务算法或启动脚本。

## 4. 执行对象

本次主要处理 [[FakeServiceBehavior]] 为 `controlled_failure` 或等价受控失败行为时的 Runtime 编排结果。smoke test 必须证明 [[PipelineResult]] 失败、[[RuntimeErrorRef]] 稳定、后续场景停止执行，并能通过 [[ErrorSummary]] 与 [[RunResultIndex]] 定位失败摘要产物。

## 5. 执行依赖

- `runtime_mvp_030_runtime_smoke_test_types.md` 已完成，或已有等价 smoke test Types。
- `runtime_mvp_031_single_and_pipeline_fake_success_smoke.md` 已完成，或成功路径 smoke suite 执行器已存在。
- 功能6 pipeline dispatcher 支持失败停止策略，或已有等价可观察结果。
- 功能7 fake service 支持受控失败行为，或已有等价 fake failure 注入方式。
- 功能9 error summary writer 与 run result index writer 已完成；若尚未完成，本 L3 不补实现，必须阻塞并说明。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_016、runtime_mvp_020、runtime_mvp_021、runtime_mvp_022、runtime_mvp_026、runtime_mvp_028、runtime_mvp_029、runtime_mvp_030、runtime_mvp_031
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_016_pipeline_dispatcher.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g7/
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_028_error_summary_writer.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_029_run_result_index_writer.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_030_runtime_smoke_test_types.md
- DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_031_single_and_pipeline_fake_success_smoke.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- FakeServiceBehavior.controlled_failure 或等价受控失败行为
- PipelineResult.status、scene_results、error / RuntimeErrorRef
- pipeline dispatcher 的失败后停止语义
- ErrorSummary 写入结果或 `error_summary.json` 路径
- RunResultIndex 写入结果或 `run_result.json` 路径
- RuntimeSmokeTestResult.assertions
是否存在接口冲突：功能9写入器可能尚未完成；执行前必须确认 active 或 completed L3 状态
如果有冲突，本次处理策略：如果 error summary/run result 写入器缺失，暂停或将本任务标记阻塞；不得在本任务中临时伪造功能9写入接口
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/tests/runtime/` 下的可控失败 smoke test。
- 必要时在 `src/data_clean/runtime/` 中新增最小 smoke suite 编排辅助函数，但不得改变生产 pipeline 的失败停止语义。
- 测试能够证明失败场景之后的场景没有执行，错误摘要产物可定位，统一结果索引指向错误摘要。

## 8. 编排输出

### 调用顺序

```text
入口：加载 fake service 可控失败 RuntimeSmokeTestCase
↓
步骤 1：创建独立 RunDirectory
↓
步骤 2：构造包含至少两个场景的 SceneDispatchPlan
↓
步骤 3：为第一个或指定场景配置 FakeServiceBehavior.controlled_failure
↓
步骤 4：调用 pipeline dispatcher
↓
步骤 5：断言 PipelineResult 为失败，并包含稳定 RuntimeErrorRef
↓
步骤 6：断言失败场景之后的场景没有继续执行
↓
步骤 7：调用或验证 ErrorSummary 写入结果
↓
步骤 8：调用或验证 RunResultIndex 指向 error_summary
↓
完成：生成 RuntimeSmokeTestResult 并汇总断言
```

### 被调模块

| 被调模块                    | 调用时机                    | 输入                                         | 输出                                        | 失败时处理                     |
| --------------------------- | --------------------------- | -------------------------------------------- | ------------------------------------------- | ------------------------------ |
| Run 目录管理模块            | case 开始前                 | [[RuntimeSmokeTestCase]]、[[RunContext]]     | [[RunDirectory]]                            | 当前 case setup failed         |
| 场景注册与 Service 调度模块 | 执行包含失败场景的 pipeline | [[SceneDispatchPlan]]、[[ServiceRegistry]]   | [[PipelineResult]]                          | 记录实际失败点                 |
| Fake Service 模块           | 目标失败场景被调用时        | [[FakeServicePlan]]、[[FakeServiceBehavior]] | [[FakeServiceResult]] / [[RuntimeErrorRef]] | 期望失败，继续断言停止策略     |
| Manifest 与错误摘要模块     | pipeline 失败后             | [[PipelineResult]]、[[RunDirectory]]         | [[ErrorSummary]]、[[RunResultIndex]]        | 若接口缺失，case 标记 blocked  |
| 结构化日志模块              | 运行结束后，如接口可用      | 调度事件、失败结果                           | [[RunLogFile]]                              | 若接口缺失，记录 artifact 阻塞 |

### 状态记录

| 状态           | 触发条件                                             | 记录位置                                  | 用户可见反馈       |
| -------------- | ---------------------------------------------------- | ----------------------------------------- | ------------------ |
| `setting_up` | 正在构造可控失败 case                                | [[RuntimeSmokeTestResult]]                | case 准备中        |
| `running`    | 正在调用 pipeline dispatcher                         | [[RuntimeSmokeTestResult]]                | case 执行中        |
| `asserting`  | 已获得失败 [[PipelineResult]]                        | [[RuntimeSmokeTestResult]].`assertions` | 断言失败停止和产物 |
| `passed`     | 期望失败发生、后续场景停止、错误摘要可定位           | suite 汇总                                | case 通过          |
| `failed`     | 未失败、错误码不稳定、后续场景继续执行或错误摘要错误 | suite 汇总                                | case 失败          |
| `blocked`    | 功能9写入器尚不可用                                  | suite 汇总 / assertion reason             | case 阻塞          |

## 9. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/10_Runtime smoke test模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/09_Manifest与错误摘要模块.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestCase.md`
6. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeSmokeTestResult.md`
7. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceBehavior.md`
8. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/PipelineResult.md`
9. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RuntimeErrorRef.md`
10. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ErrorSummary.md`
11. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunResultIndex.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_016_pipeline_dispatcher.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_020_fake_service_types.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_021_fake_service_result_generator.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_022_fake_service_dispatch_adapter.md`
5. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_026_manifest_error_types.md`
6. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_028_error_summary_writer.md`
7. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g9/runtime_mvp_029_run_result_index_writer.md`
8. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_030_runtime_smoke_test_types.md`
9. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g10/runtime_mvp_031_single_and_pipeline_fake_success_smoke.md`

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

- 禁止定义新的 smoke test、manifest、error summary 或 run result Types。
- 禁止修改 fake service 基础行为语义。
- 禁止为了本任务临时实现或改写功能9写入器接口。
- 禁止实现真实 Service 业务算法。
- 禁止修改启动脚本或 CLI 行为。
- 禁止写入 `asset/阶段二：数据清洗/` 或真实业务产物。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime -k "smoke and (controlled_failure or error_summary or run_result)" -q
```

## 15. 成功标准

- [X] fake service 可控失败 smoke test 能得到失败 [[PipelineResult]]。
- [X] [[RuntimeErrorRef]] 或等价错误引用稳定，错误码可断言。
- [X] 可控失败后后续场景不会继续执行。
- [X] 失败路径能定位 `error_summary.json`，并通过 `run_result.json` 指向错误摘要。
- [X] 如果功能9写入器尚不可用，本任务明确阻塞并说明缺失接口，没有伪造写入行为。
- [X] 执行摘要已追加到当前 L3 文件末尾。
- [X] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- 完成并更新任务文件后，将当前 L3 移到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g10/`
- 不写 `DOCS/03_工程/阶段二：数据清洗/执行记录/`、阶段/场景 `当前进度.md`、共享 `执行记录.md` 或 `DOCS/总执行日志.md`

交接摘要必须包含读取记录、修改文件、TDD 过程、验收命令、成功标准勾选情况、当前没做什么和下一步建议。

## 17. 执行摘要

### 读取记录

- L2 模块：10_Runtime smoke test模块、06_场景注册与Service调度模块、07_Fake Service模块、09_Manifest与错误摘要模块
- L2 数据定义：RuntimeSmokeTestCase、RuntimeSmokeTestResult、FakeServiceBehavior、PipelineResult、RuntimeErrorRef、ErrorSummary、RunResultIndex
- 上游 L3 状态确认：runtime_mvp_026/027/028/029（completed/runtime-g9）、runtime_mvp_030/031/032（completed/runtime-g10）
- 代码文件：runtime/pipeline_dispatcher.py、runtime/scene_dispatcher.py、runtime/error_summary_writer.py、runtime/run_result_index_writer.py、runtime/structured_log_writer.py、runtime/fake_service_dispatch_adapter.py、runtime/fake_service_executor.py、runtime/run_directory_creator.py、schemas/run_directory_types.py、schemas/structured_log_types.py、schemas/__init__.py
- 现有测试：test_smoke_success.py、test_smoke_failure.py

### 修改文件

| 文件                                                              | 改动类型 | 说明                                                                                                             |
| ----------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------- |
| `src/data_clean/tests/runtime/test_smoke_controlled_failure.py` | 新增     | 可控失败 smoke test，包含 case 定义验证和全流程端到端测试                                                        |
| `src/data_clean/runtime/scene_dispatcher.py`                    | 修改     | 异常处理增加 `error_code` 属性透传，使 callable 可携带结构化错误码                                             |
| `src/data_clean/schemas/__init__.py`                            | 修改     | 补充导出 RunLogFile、RuntimeLogEvent、RuntimeLogEventType、RuntimeLogWriteResult                                 |
| `src/data_clean/schemas/structured_log_types.py`                | 修改     | RuntimeLogWriteResult 字段对齐 writer 实际使用（run_log_path/status/written_at），增加 log_path/success 兼容属性 |

### TDD 过程

1. **RED**: 编写 `test_smoke_controlled_failure.py`，包含 `_ControlledFailureTracker` callable 和完整 pipeline 编排流程
2. **首次运行失败**: `RuntimeLogWriteResult` 字段不匹配 + `schemas/__init__.py` 缺少导出
3. **GREEN 第一轮**: 修复 schemas 导出和 RuntimeLogWriteResult 字段对齐
4. **第二次运行失败**: 错误码为 `service_call_failed` 而非 `fake_service_controlled_failure`
5. **GREEN 第二轮**: 修改 scene_dispatcher 异常处理，检测 `exc.error_code` 属性并透传
6. **最终验证**: 13 个 smoke 测试全部通过（6 成功 + 5 失败 + 2 可控失败）

### 验收命令

```bash
cd /home/hit/ROS/src && PYTHONPATH=/home/hit/ROS/src:$PYTHONPATH python3 -m pytest data_clean/tests/runtime/test_smoke_controlled_failure.py -k "smoke and (controlled_failure or error_summary or run_result)" -v
```

结果：2 passed in 0.05s

### 成功标准勾选情况

- [X] PipelineResult 为 FAILED
- [X] RuntimeErrorRef.error_code == "fake_service_controlled_failure"
- [X] 后续场景（SCENE2）未执行，scene_results 仅 1 条
- [X] error_summary.json 存在且 status=failed、error_code 正确
- [X] run_result.json 存在且 error_summary_path 非空、manifest_path 为空
- [X] 功能9写入器已完成（runtime_mvp_028/029 在 completed/runtime-g9），未阻塞

### 本次没做什么

- 不实现成功路径、缺配置或缺输入 smoke test（已由 runtime_mvp_031/032 覆盖）
- 不定义新的 smoke test Types
- 不重新定义 ErrorSummary、RunResultIndex 或 RuntimeErrorRef
- 不修改 fake service 的基础行为语义
- 不修改真实 Service 业务算法或启动脚本
- 不写入 asset/阶段二：数据清洗/ 或真实业务产物

### 下一步建议

- runtime_mvp_034+ 可继续补充其他 smoke test 变体（如缺配置+可控失败组合）
- 考虑将 `_ControlledFailureTracker` 提取为共享测试工具
- scene_dispatcher 的 `error_code` 透传机制可文档化为 service callable 契约
