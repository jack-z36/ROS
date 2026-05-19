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
3. `DOCS/阶段二：数据清洗/执行记录/` 中与配置加载、快照或配置预检查相关的记录

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
- `DOCS/阶段二：数据清洗/执行记录/`

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

- [ ] 合法 Runtime 级配置预检查通过。
- [ ] 缺失 [[EffectiveRuntimeConfig]] 或非 mapping 配置失败且 issue code 清楚。
- [ ] 缺少目标场景 Runtime 级配置块失败且指明 [[SceneName]]。
- [ ] [[ConfigSnapshot]] 路径逃逸本次 [[RunDirectory]] 时失败。
- [ ] Service 业务级参数缺失不被本任务提前判死。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_018_config_prechecker>.md`
- 执行过程、当前状态、未完成事项和下一步建议写在同一个记录文件中
- 完成并更新任务文件后，将当前 L3 从 `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g4/` 移到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/runtime-g4/`

交接摘要必须包含：

1. 读取了哪些相关 L3 任务文件或执行记录
2. 修改了哪些文件
3. 新增或修改了哪些函数 / 测试
4. TDD red / green / refactor 如何执行
5. 如何运行验收，命令必须使用 `python3`
6. 成功标准勾选情况
7. 当前没做什么
8. 下一步建议
