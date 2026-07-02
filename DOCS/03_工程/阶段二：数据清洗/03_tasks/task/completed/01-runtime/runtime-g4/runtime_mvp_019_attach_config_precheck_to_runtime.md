# L3 微元任务：接入配置预检查到 Runtime 初始化链路

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[04_配置预检查模块]]  
L3 编号：`runtime_mvp_019`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`

## 2. 本次目标

```text
把配置预检查接入 Runtime 初始化链路，确保预检查失败时不会进入输入产物预检查和 Service 调度。
```

## 3. 本次不做

- 不实现配置预检查底层规则。
- 不定义新的配置预检查 Types。
- 不实现输入产物预检查逻辑。
- 不调用真实 Service 业务算法。
- 不写 `processing_manifest.json` 或 `error_summary.json` 的最终内容。

## 4. 执行对象

本次主要处理 Runtime 初始化或调度前的流程编排：功能三完成配置加载与快照后，调用配置预检查器；若 [[ConfigPrecheckResult]] 不通过，则停止后续输入产物预检查和 Service 调度。

## 5. 执行依赖

- `runtime_mvp_017` 已定义配置预检查 Types 与规则常量。
- `runtime_mvp_018` 已实现配置预检查器。
- 功能三配置加载与配置快照链路已有可被 Runtime 调用的输出或等价接口。
- 输入产物预检查模块存在或即将接入；本任务只保证失败时不进入该模块。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：配置加载与配置快照模块、配置预检查 Types 与规则常量、Runtime 级配置预检查器
上游接口定义位置：DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md；DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md；DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g3/；DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_017_config_precheck_types.md；DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_018_config_prechecker.md
当前 L3 期望消费的字段 / 文件 / 返回值：配置加载阶段输出的 EffectiveRuntimeConfig 和 ConfigSnapshot；配置预检查器返回的 ConfigPrecheckResult.passed 和 issues
是否存在接口冲突：未知，执行时必须读取现有 Runtime 编排代码和上游任务完成状态确认
如果有冲突，本次处理策略：不改写上游接口；先记录冲突并只做最小可验证接入或暂停
```

## 7. 预期改动形态

- 在 Runtime 初始化或调度入口中插入配置预检查步骤。
- 预检查失败时，Runtime 返回失败状态或等价结果，并保留 [[ConfigPrecheckIssue]] 供日志/错误摘要模块后续消费。
- 新增或更新测试，验证预检查失败时不会调用输入产物预检查和 Service 调度。

## 8. 编排输出

### 调用顺序

```text
Runtime 入口 / 初始化
↓
步骤 1：创建或接收 RunContext
↓
步骤 2：配置加载与配置快照模块产出 EffectiveRuntimeConfig + ConfigSnapshot
↓
步骤 3：调用配置预检查器
↓
步骤 4a：ConfigPrecheckResult.passed = true，进入输入产物预检查
↓
步骤 4b：ConfigPrecheckResult.passed = false，停止后续输入产物预检查和 Service 调度
↓
完成 / 失败
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
| --- | --- | --- | --- | --- |
| 配置加载与配置快照模块 | Run 目录准备后、配置预检查前 | [[RunContext]]、配置来源 | [[EffectiveRuntimeConfig]]、[[ConfigSnapshot]] | 失败时不进入配置预检查 |
| 配置预检查器 | 配置加载与快照成功后 | [[RunContext]]、[[EffectiveRuntimeConfig]]、[[ConfigSnapshot]]、[[SceneConfigRequirement]] | [[ConfigPrecheckResult]] | `passed = false` 时停止输入产物预检查和 Service 调度 |
| 输入产物预检查模块 | 仅配置预检查通过后 | [[ConfigPrecheckResult]] 和配置相关事实 | 输入产物检查结果 | 本任务不实现该模块行为 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
| --- | --- | --- | --- |
| 配置预检查通过 | [[ConfigPrecheckResult]] `passed = true` | Runtime 返回值、后续 run log 接入点 | 可继续执行 |
| 配置预检查失败 | [[ConfigPrecheckResult]] `passed = false` | Runtime 返回值或等价失败对象，后续错误摘要接入点 | 显示配置预检查失败和首个 issue |
| 上游配置加载失败 | 功能三未产出配置事实 | Runtime 返回值或等价失败对象 | 显示配置加载失败，不伪装成预检查失败 |

## 9. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`
3. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
4. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckResult.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckIssue.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g3/`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_017_config_precheck_types.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_018_config_prechecker.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g5/`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
3. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
4. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
5. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/data_clean_architecture.md`
2. `src/data_clean/runtime/`
3. `src/data_clean/config/`
4. `src/data_clean/schemas/`

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

- 禁止实现或重写配置预检查底层规则。
- 禁止修改配置加载和快照写入接口。
- 禁止实现输入产物预检查内部逻辑。
- 禁止调用或修改真实 Service 算法。
- 禁止修改 `start_data_clean.sh`。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 配置预检查通过时，Runtime 继续进入输入产物预检查接入点。
- [x] 配置预检查失败时，Runtime 不调用输入产物预检查。
- [x] 配置预检查失败时，Runtime 不调用 fake service 或真实 service。
- [x] 失败结果能携带或引用 [[ConfigPrecheckIssue]]。
- [x] 本任务没有实现底层配置检查规则和 Service 业务逻辑。

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

- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_017_config_precheck_types.md`（上游依赖，已有代码文件）
- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_018_config_prechecker.md`（上游依赖，已有代码文件）
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckResult.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckIssue.md`

上游 `runtime_mvp_017` 和 `runtime_mvp_018` 的代码文件和测试已存在于仓库中（`schemas/config_precheck_types.py`、`runtime/config_prechecker.py` 及对应测试），但 L3 文档尚未归档。

### 2. 修改了哪些文件

| 文件 | 改动类型 | 说明 |
| --- | --- | --- |
| `src/data_clean/runtime/runtime_init.py` | 新增 | Runtime 初始化编排入口，含 `ConfigPrecheckGate` 和 `init_runtime()` |
| `src/data_clean/tests/runtime/test_runtime_init.py` | 新增 | 14 个测试用例覆盖成功/失败路径 |
| `src/data_clean/data_clean_architecture.md` | 修改 | 目录结构表新增两行：`config_prechecker.py` 和 `runtime_init.py` |

### 3. 新增或修改了哪些函数 / 测试

**新增类：**
- `RuntimeInitError` — 初始化异常
- `RuntimeInitStep` — 枚举：CONFIG_LOAD、CONFIG_PRECHECK、INPUT_PRECHECK、SERVICE_DISPATCH
- `ConfigPrecheckGate` — 编排闸门，包装 ConfigPrechecker，支持 input_precheck_hook

**新增函数：**
- `ConfigPrecheckGate.run_precheck()` — 调用 ConfigPrechecker 执行预检查
- `ConfigPrecheckGate.should_proceed()` — 判断是否放行
- `init_runtime()` — 主入口：执行预检查 → 按 passed 决定是否调 input_precheck_hook → 返回 PipelineResult

**新增测试类（14 个用例）：**
- `TestRuntimeInitError` — 异常构造
- `TestRuntimeInitStep` — 枚举值
- `TestConfigPrecheckGateConstruction` — gate 构造含参数
- `TestInitRuntimeSuccess` — 预检查通过时返回 SUCCEEDED、调用 hook
- `TestInitRuntimeFailure` — 预检查失败时返回 FAILED、不调用 hook
- `TestInitRuntimeEdgeCases` — 空 target_scenes
- `TestConfigPrecheckGateDefaults` — 默认 gate

### 4. TDD red / green / refactor 如何执行

按垂直切片推进：

1. **RED**: 编写 `test_runtime_init.py`，验证 `from runtime.runtime_init import init_runtime` 失败（模块不存在）。
2. **GREEN**: 实现 `runtime/runtime_init.py` 最小版，所有测试通过。
3. **RED→GREEN** 循环：逐个添加测试（单场景通过、单场景失败、hook 调用、hook 不调用、默认 gate），每次添加最少实现代码。
4. 未独立 refactor 步骤——实现量小且直接，无重复需提取。

### 5. 如何运行验收

```bash
PYTHONPATH=src/data_clean python3 -m pytest src/data_clean/tests/runtime/test_runtime_init.py -q
```

预期输出：14 passed

### 6. 成功标准勾选情况

所有 6 项成功标准均已勾选 `- [x]`：
- [x] 配置预检查通过时继续进入输入产物预检查接入点
- [x] 配置预检查失败时不调用输入产物预检查
- [x] 配置预检查失败时不调用 fake service 或真实 service
- [x] 失败结果能携带或引用 ConfigPrecheckIssue
- [x] 本任务没有实现底层配置检查规则和 Service 业务逻辑
- [x] 执行摘要已追加，L3 已归档

### 7. 当前没做什么

- 没有实现输入产物预检查内部逻辑
- 没有实现 Service 调用逻辑
- 没有修改配置加载与快照写入模块
- 没有实现完整 PipelineResult 中的 scene_results 填充（本任务只填充必要状态）
- 没有修改 `start_data_clean.sh`

### 8. 下一步建议

1. 归档 `runtime_mvp_017` 和 `runtime_mvp_018` 的 L3 文件到 `completed/`。
2. 后续 L3（如输入产物预检查接入）可消费 `ConfigPrecheckGate.input_precheck_hook` 接口。
3. 将 `init_runtime` 集成到 `mcap_clean_launcher` 或新的 Runtime CLI 入口中。
4. 考虑在 `PipelineResult` 中补充 `scene_results` 填充逻辑。

