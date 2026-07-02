# L3 微元任务：实现场景 Service 注册表

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[06_场景注册与Service调度模块]]  
L3 编号：`runtime_mvp_014`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`

## 2. 本次目标

```text
实现一个可查询的场景 Service 注册表，能按 SceneName 和 ServiceMode 返回对应 ServiceBinding，未注册时返回结构化错误。
```

## 3. 本次不做

- 不执行 service callable。
- 不生成 [[SceneDispatchPlan]]。
- 不实现单场景或全流程调度器。
- 不实现 fake service 或真实 service 业务逻辑。
- 不写 `run_log.json`、`processing_manifest.json`、`error_summary.json` 或 `run_result.json`。

## 4. 执行对象

本次主要处理 [[ServiceRegistry]] 和 [[ServiceBinding]] 的注册、查询、重复注册处理、模式一致性检查和未注册错误表达。

## 5. 执行依赖

- `runtime_mvp_013` 已定义 [[ServiceRegistry]]、[[ServiceBinding]]、[[SceneDispatchPlan]] 和 [[SceneDispatchEvent]]。
- [[SceneName]]、[[ServiceMode]] 和 [[RuntimeErrorRef]] 已由 Runtime 上下文相关 L3 定义或约束。
- [[07_Fake Service模块]] 已定义 fake service 的计划和结果语义，但本任务不实现 fake service。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_002、runtime_mvp_003、runtime_mvp_013
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/；DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：SceneName、ServiceMode、RuntimeErrorRef、ServiceRegistry、ServiceBinding
是否存在接口冲突：如 runtime_mvp_013 尚未执行，本任务不得自行另造不兼容 Types
如果有冲突，本次处理策略：暂停说明；优先执行或修正 runtime_mvp_013
```

## 7. 预期改动形态

- 新增一个小的注册表构建/查询模块或函数。
- 新增测试覆盖：注册成功、按场景查询成功、未注册场景失败、service mode 不一致失败、重复注册策略清楚。
- 失败结果必须能被后续调度器转换为 [[RuntimeErrorRef]] 或等价结构化错误。

## 8. 编排输出

### 调用顺序

```text
入口：传入 service_mode 和一组 ServiceBinding
↓
步骤 1：校验每个 binding 的 scene_name 和 service_mode
↓
步骤 2：组装 ServiceRegistry
↓
步骤 3：按 SceneName 查询 ServiceBinding
↓
完成：返回 binding
失败：返回 service_not_registered 或 service_mode_mismatch 类结构化错误
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
| --- | --- | --- | --- | --- |
| Runtime Types | 注册表构建和查询时 | [[SceneName]]、[[ServiceMode]]、[[ServiceBinding]] | [[ServiceRegistry]] | 类型或取值非法时失败 |
| 错误引用构造逻辑 | 查询失败时 | 失败原因、目标 [[SceneName]] | [[RuntimeErrorRef]] 或等价错误 | 不抛裸字符串错误 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
| --- | --- | --- | --- |
| registered | binding 成功进入注册表 | 返回的 [[ServiceRegistry]] | 无，本任务不做 UI |
| lookup_succeeded | 查询到目标场景 binding | 查询返回值 | 无，本任务不做 UI |
| lookup_failed | 目标场景未注册或模式不一致 | 结构化错误 | 后续调度器提示当前场景未接入 service |

## 9. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceRegistry.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceBinding.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`

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
- `src/data_clean/schemas/`，仅当需要补充 runtime_mvp_013 已定义 Types 的导出或细节
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止实现单场景或全流程调度器。
- 禁止调用 service callable。
- 禁止实现 fake service 或真实 service。
- 禁止写运行日志、manifest、错误摘要或 run result。
- 禁止修改配置预检查或输入产物预检查逻辑。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 可用一组 [[ServiceBinding]] 构造 [[ServiceRegistry]]。
- [x] 已注册 [[SceneName]] 可查询到对应 [[ServiceBinding]]。
- [x] 未注册 [[SceneName]] 返回结构化错误。
- [x] [[ServiceMode]] 不一致时失败清楚。
- [x] 重复注册策略明确且有测试覆盖。
- [x] 未实现 Service 调用、调度器或 fake service。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

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

**执行时间**：2026-05-19

### 1. 读取的相关文档

- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceRegistry.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceBinding.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`
- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g6/runtime_mvp_013_service_dispatch_types.md`（上游 L3 已完成）
- `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
- `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
- `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`

### 2. 修改的文件

| 文件 | 修改类型 | 说明 |
| --- | --- | --- |
| `src/data_clean/runtime/service_registry.py` | **新增** | Service 注册表构建与查询模块 |
| `src/data_clean/tests/runtime/test_service_registry.py` | **新增** | 8 个测试 |
| `src/data_clean/data_clean_architecture.md` | 修改 | 目录结构表新增条目 |

### 3. 新增的函数和测试

**新增函数**（`service_registry.py`）：
- `build_service_registry(bindings, service_mode)` — 从 ServiceBinding 列表构建 ServiceRegistry；校验重复注册、service_mode 一致性
- `lookup_service_binding(registry, scene_name)` — 按 SceneName 查找 ServiceBinding；未注册时抛出 KeyError
- 导出常量 `SERVICE_NOT_REGISTERED` 和 `SERVICE_MODE_MISMATCH`

**新增测试（8 tests）**：
- `TestBuildServiceRegistry` — 单 binding、全场景、重复注册拒绝、mode 不匹配拒绝、空 bindings 拒绝
- `TestLookupServiceBinding` — 已注册可查、未注册抛 KeyError、多场景混合查询

### 4. TDD 执行过程

1. **RED**: 写入 8 个测试，运行后因 ModuleNotFoundError 确认 RED
2. **GREEN**: 创建 `service_registry.py`，实现 builder 和 lookup 函数
3. **REFACTOR**: 确认与上游 `runtime_dispatch_types.py`（由 runtime_mvp_013 完成）接口对齐；所有测试通过

### 5. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime/test_service_registry.py -v
```

结果：8 passed in 0.03s。整体 90 个工作测试全部通过。

### 6. 成功标准勾选

- [x] 可用一组 ServiceBinding 构造 ServiceRegistry（`test_build_with_single_binding`）
- [x] 已注册 SceneName 可查询到对应 ServiceBinding（`test_lookup_registered_scene`）
- [x] 未注册 SceneName 返回结构化错误（KeyError + `SERVICE_NOT_REGISTERED`）
- [x] ServiceMode 不一致时失败清楚（ValueError + `SERVICE_MODE_MISMATCH`）
- [x] 重复注册策略明确（ValueError + `duplicate binding for scene`）
- [x] 未实现 Service 调用、调度器或 fake service（仅注册表构建和查询）

### 7. 当前没做什么

- 未执行 service callable（属于 runtime_mvp_015 范围）
- 未生成 SceneDispatchPlan（属于 runtime_mvp_015 范围）
- 未实现单场景或全流程调度器（属于 runtime_mvp_015/016 范围）
- 未实现 fake service 或真实 service 业务逻辑（属于 runtime_mvp_020/021 范围）
- 未写运行日志、manifest、错误摘要或 run result

### 8. 下一步建议

- 执行 `runtime_mvp_015`（单场景调度器），消费 `ServiceRegistry` 和 `ServiceBinding`
- 执行 `runtime_mvp_016`（全流程调度器与结果汇总）
- fake service 绑定可在 `runtime_mvp_021` 完成后注册到 registry

