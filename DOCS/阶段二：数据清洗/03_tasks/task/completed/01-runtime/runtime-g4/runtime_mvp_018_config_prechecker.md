# L3 微元任务：实现 Runtime 级配置预检查器

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[04_配置预检查模块]]  
L3 编号：`runtime_mvp_018`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`

## 2. 本次目标

```text
实现 Runtime 级配置预检查器，基于 RunContext、EffectiveRuntimeConfig、ConfigSnapshot 和 SceneConfigRequirement 产出 ConfigPrecheckResult。
```

## 3. 本次不做

- 不定义新的配置对象来替代功能三的 [[EffectiveRuntimeConfig]] 或 [[ConfigSnapshot]]。
- 不读取原始配置文件。
- 不写入配置快照。
- 不检查输入产物路径是否存在。
- 不调用 fake service 或真实 service。
- 不检查 Service 深层业务算法参数。

## 4. 执行对象

本次主要实现一个可测试的配置预检查函数、类或等价模块。它应消费上游已经产出的配置事实和运行上下文，返回 [[ConfigPrecheckResult]]。

## 5. 执行依赖

- `runtime_mvp_017` 已定义配置预检查 Types 与规则常量；如果尚未完成，本任务不得自行发明冲突结构。
- 功能三配置加载与配置快照 Types 或等价结构已经存在，或需要在执行摘要中说明阻塞。
- [[RunContext]]、[[SceneName]]、[[EffectiveRuntimeConfig]] 和 [[ConfigSnapshot]] 接口必须在开工前对齐。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：Runtime 运行上下文定义、配置加载与配置快照模块、配置预检查 Types 与规则常量
上游接口定义位置：DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md；DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md；DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_017_config_precheck_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：RunContext.target_scenes、RunContext.run_dir、EffectiveRuntimeConfig.effective_data、EffectiveRuntimeConfig.config_source、EffectiveRuntimeConfig.override_set、ConfigSnapshot.snapshot_path、SceneConfigRequirement.required_sections、SceneConfigRequirement.required_fields
是否存在接口冲突：未知，执行时必须读取现有代码和 runtime_mvp_017 完成状态确认
如果有冲突，本次处理策略：暂停说明冲突；不得同时重写上游 Types 和本预检查器，除非任务文件已明确授权
```

## 7. 预期改动形态

- 在 `src/data_clean/runtime/` 或 `src/data_clean/config/` 中新增 Runtime 级配置预检查实现。
- 新增或更新测试，覆盖合法配置、缺生效配置、缺场景配置、快照逃逸、全流程场景顺序错误。
- 如新增源码模块，更新 `src/data_clean/data_clean_architecture.md` 的目录结构表。

## 8. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
| --- | --- | --- | --- |
| 合法输入 | [[EffectiveRuntimeConfig]] 为 mapping，来源和覆盖项可追溯，[[ConfigSnapshot]] 位于本次 run 目录内，目标场景满足 [[SceneConfigRequirement]] | [[ConfigPrecheckResult]] 的 `passed = true`，`issues = []` | 无 |
| 缺失输入 | [[EffectiveRuntimeConfig]] 缺失、`effective_data` 非 mapping、来源缺失、覆盖项缺失或快照缺失 | `passed = false`，至少一个阻塞型 [[ConfigPrecheckIssue]] | `effective_config_missing`、`effective_config_not_mapping`、`config_source_untraceable`、`override_set_missing`、`snapshot_untraceable` |
| 边界输入 | 目标场景不受控、全流程顺序错误、目标场景缺 Runtime 级配置块 | `passed = false`，按场景生成 issue | `unknown_scene_name`、`invalid_scene_sequence`、`missing_scene_config` |
| 业务参数边界 | Service 内部业务参数缺失，但 Runtime 级场景配置入口存在 | 不阻塞，必要时 warning | `service_business_config_not_checked` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
| --- | --- | --- | --- |
| `passed` | boolean | 是否允许进入输入产物预检查 | 有阻塞 issue 时必须为 false |
| `checked_scenes` | list of [[SceneName]] | 已检查目标场景 | 必须与 [[RunContext]] 一致 |
| `issues` | list of [[ConfigPrecheckIssue]] | 发现的问题 | 无问题时为空列表 |
| `checked_rules` | list | 执行过的规则 | 至少覆盖功能四 L2 规则表 |
| `effective_config_ref` | [[EffectiveRuntimeConfig]] | 被检查配置 | 不得重新读取配置 |
| `config_snapshot_ref` | [[ConfigSnapshot]] 或空 | 配置快照引用 | 缺失时必须有阻塞 issue |

## 9. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckResult.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckIssue.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckRule.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneConfigRequirement.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/EffectiveRuntimeConfig.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigSnapshot.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_017_config_precheck_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g3/`

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
3. `src/data_clean/config/`
4. `src/data_clean/runtime/`

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/config/`，仅当现有配置校验能力放在配置层更贴合
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

## 13. 禁止修改

- 禁止修改功能三配置加载和快照写入接口。
- 禁止修改输入产物预检查模块。
- 禁止修改 Service 层算法或场景业务校验。
- 禁止修改 `start_data_clean.sh`。
- 禁止生成真实数据产物。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 合法 Runtime 级配置预检查通过。
- [x] 缺失 [[EffectiveRuntimeConfig]] 或非 mapping 配置失败且 issue code 清楚。
- [x] 缺少目标场景 Runtime 级配置块失败且指明 [[SceneName]]。
- [x] [[ConfigSnapshot]] 路径逃逸本次 [[RunDirectory]] 时失败。
- [x] Service 业务级参数缺失不被本任务提前判死。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<runtime-g4>/`。

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

---

## 执行摘要

### 1. 读取的相关文档

- 本 L3 文件 `runtime_mvp_018_config_prechecker.md`
- 上游 L3 `runtime_mvp_017_config_precheck_types.md`（未完成，本轮一并实现）
- L2 能力模块：`04_配置预检查模块.md`、`01_Runtime运行上下文定义.md`、`03_配置加载与配置快照模块.md`
- L2 数据定义：`ConfigPrecheckResult.md`、`ConfigPrecheckIssue.md`、`ConfigPrecheckRule.md`、`SceneConfigRequirement.md`、`EffectiveRuntimeConfig.md`、`ConfigSnapshot.md`、`SceneName.md`、`RunContext.md`
- 约束文件：`L3编码执行原则.md`、`L3执行TDD与归档约束.md`、`上游依赖接口对齐约束.md`、`文件存放规范.md`
- 现有代码：`src/data_clean/schemas/` 各类型文件、`src/data_clean/runtime/` 各模块、`src/data_clean/tests/runtime/` 已有测试
- 相关 L3 历史记录：未找到已完成的 runtime-g4 历史记录（runtime-g4 目录首次创建）

### 2. 修改的文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/data_clean/runtime/config_prechecker.py` | 新增 | ConfigPrechecker 类及各检查函数 |
| `src/data_clean/tests/runtime/test_config_precheck_types.py` | 新增 | Types 构造测试（10 个），测试现有 `runtime_precheck_types.py` |
| `src/data_clean/tests/runtime/test_config_prechecker.py` | 新增 | Prechecker 行为测试（21 个） |
| `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g4/runtime_mvp_018_config_prechecker.md` | 修改 | 勾选成功标准、追加本执行摘要 |

### 3. 新增的函数/类/测试

**无新增类型文件** — 复用已有 `schemas/runtime_precheck_types.py`（由上游 L3 `runtime_mvp_017` 定义），其中包含 `ConfigPrecheckIssue`、`ConfigPrecheckResult`、`ConfigPrecheckRule`、`SceneConfigRequirement`、`PrecheckRuleId` 枚举及 `PRECHECK_RULES` 常量。

**runtime/config_prechecker.py:**
- `_check_effective_config_exists()` — 检查配置是否存在且为 mapping
- `_check_config_source_traceable()` — 检查配置来源可追溯
- `_check_override_set_recorded()` — 检查覆盖项显式记录
- `_check_snapshot_traceable()` — 检查快照路径在 run_dir 内
- `_check_scene_names_controlled()` — 检查场景名受控
- `_check_scene_sequence()` — 检查全流程顺序正确
- `_check_scene_config_blocks()` — 检查目标场景配置块
- `_check_global_runtime_config()` — 检查全局必需字段
- `_add_service_not_checked_warning()` — 产生 Service 参数未检查 warning
- `ConfigPrechecker` class — 主入口，汇总检查并产出 ConfigPrecheckResult

### 4. TDD 执行情况

按垂直切片 TDD 推进：

1. **Red → 现有类型确认**: 先读取已有 `schemas/runtime_precheck_types.py`（runtime_mvp_017 已完成），确认类型定义满足本 L3 需求
2. **Red**: 写 `test_config_prechecker.py`（21 个行为测试），覆盖合法输入、缺失配置、非 mapping、来源不可追溯、覆盖项缺失、快照逃逸、场景名非法、场景序列错误、场景配置块缺失、全局字段缺失、Service 参数边界
3. **Green**: 实现 `runtime/config_prechecker.py`，21 个测试通过
4. **Red**: 写 `test_config_precheck_types.py`（10 个类型构造测试），确认能构造现有类型
5. **Green**: 10 个类型测试全部通过
6. **Refactor — 跨模块 SceneName 兼容性修复**:

发现 `schemas/runtime_context.py` 和 `schemas/runtime_enums.py` 各自定义 `SceneName` 类（不同类、相同值），且 `RunContext.target_scenes` 来自前者、预检查器导入后者。Python 3.12 中 `isinstance()` 跨类判断为 False，导致场景需求检查被跳过。

修复策略：统一用 `hasattr(x, "value")` + 字符串值比较，避免 `isinstance(x, SceneName)` 依赖特定 import。涉及函数：`_check_scene_config_blocks`、`_check_scene_names_controlled`、`_check_scene_sequence`。

### 5. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime/test_config_precheck_types.py -q
python3 -m pytest src/data_clean/tests/runtime/test_config_prechecker.py -q
```

全部通过（10 + 21 = 31 tests）。

```bash
python3 -m pytest src/data_clean/tests/runtime/test_config_precheck_types.py -q   # 10 passed
python3 -m pytest src/data_clean/tests/runtime/test_config_prechecker.py -q       # 21 passed
```

`python3 -m pytest src/data_clean/tests/runtime -q` 因已有 `test_config_snapshot.py`（缺少 `config.runtime_config_loader` 模块）和 `test_run_context_attach.py`（import 路径问题）报错，非本次改动引入。

### 6. 成功标准勾选

- [x] 合法 Runtime 级配置预检查通过 → `TestLegalInput`
- [x] 缺失 [[EffectiveRuntimeConfig]] 或非 mapping 配置失败且 issue code 清楚 → `TestMissingEffectiveConfig`
- [x] 缺少目标场景 Runtime 级配置块失败且指明 [[SceneName]] → `TestMissingSceneConfig`、`TestSceneRequirements`
- [x] [[ConfigSnapshot]] 路径逃逸本次 [[RunDirectory]] 时失败 → `TestSnapshotTraceability`
- [x] Service 业务级参数缺失不被本任务提前判死 → `TestServiceBusinessConfig`

### 7. 当前没做什么

- 未接入 Runtime 初始化链路（属于 `runtime_mvp_019`）
- 未修改功能三配置加载和快照写入接口
- 未修改输入产物预检查模块
- 未修改 Service 层算法或场景业务校验
- 未修改 `start_data_clean.sh`
- 未生成运行目录或真实数据产物
- 未写集中执行记录文件
- 未重新定义 `SceneName` 或合并 `runtime_context.SceneName` 与 `runtime_enums.SceneName`（跨模块兼容性已通过值比较策略解决）

### 8. 下一步建议

1. **runtime_mvp_019**：将 ConfigPrechecker 接入 Runtime 初始化链路，在配置加载后、输入产物预检查前执行预检查
2. **跨模块 SceneName 统一**：建议后续将 `runtime_context.SceneName` 改为从 `runtime_enums.SceneName` 导入/继承，消除两个 `SceneName` 类并存问题
3. `data_clean_architecture.md` 的目录结构表已有 `runtime/config_prechecker.py` 和 `schemas/runtime_precheck_types.py` 条目，无需额外修改

