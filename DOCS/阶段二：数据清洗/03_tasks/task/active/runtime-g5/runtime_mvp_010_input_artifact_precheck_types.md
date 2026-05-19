# L3 微元任务：定义输入产物预检查 Types

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[05_输入产物预检查模块]]  
L3 编号：`runtime_mvp_010`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`

## 2. 本次目标

```text
定义输入产物预检查所需的需求、单项结果和汇总结果 Types，使后续检查逻辑和调度模块能消费同一套接口。
```

## 3. 本次不做

- 不实现文件系统存在性、可读性或类型检查。
- 不实现配置预检查。
- 不解析 [[EffectiveRuntimeConfig]] 中的具体路径键。
- 不调用 fake service 或真实 service。
- 不写 `run_log.json`、`processing_manifest.json` 或 `error_summary.json`。

## 4. 执行对象

本次主要处理 [[InputArtifactRequirement]]、[[InputArtifactCheckResult]] 和 [[InputArtifactPrecheckSummary]] 的代码级表达，并复用已有 [[SceneName]]、[[RunMode]]、[[RunStatus]] 和 [[RuntimeErrorRef]]。

## 5. 执行依赖

- `runtime_mvp_001` 到 `runtime_mvp_003` 已定义 Runtime 上下文、状态、模式、结果和错误引用相关 Types。
- `runtime_mvp_007` 已定义配置加载相关 Types。
- 功能5 L2 已定义输入产物预检查的数据语义。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_002、runtime_mvp_003、runtime_mvp_007
上游接口定义位置：DOCS/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md；runtime_mvp_002_定义Runtime状态与模式枚举.md；runtime_mvp_003_定义Runtime结果与错误引用Types.md；DOCS/阶段二：数据清洗/03_tasks/task/runtime-g3/runtime_mvp_007_runtime_config_types.md
当前 L3 期望消费的字段 / 文件 / 返回值：SceneName、RunMode、RunStatus、RuntimeErrorRef；如代码中尚未实现，按上游 L3 约束先执行上游任务
是否存在接口冲突：功能4配置预检查接口尚未定义，但本 L3 不直接消费功能4接口
如果有冲突，本次处理策略：暂停说明；不得为绕过冲突重新定义同名状态或错误对象
```

## 7. 预期改动形态

- 在 Runtime MVP 现有 Types 位置新增或扩展输入产物预检查相关对象。
- 新增最小测试，能构造合法需求、成功结果、失败结果和汇总结果。
- 失败结果必须能携带 [[RuntimeErrorRef]]，不得用裸字符串替代结构化错误。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[InputArtifactRequirement]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 场景输入需求解析、输入产物检查 |
| [[InputArtifactCheckResult]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | 输入产物检查、日志、错误摘要 |
| [[InputArtifactPrecheckSummary]] | dataclass / TypedDict / Pydantic model | `src/data_clean/schemas/` 或当前 Runtime Types 约定位置 | Service 调度、日志、错误摘要 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `scene_name` | [[SceneName]] | 目标场景 | 无 | 必须为受控场景 |
| `artifact_role` | string | 输入产物角色 | 无 | 非空 |
| `path_config_key` | string | 配置中的路径语义键 | 无 | 非空 |
| `required_kind` | string / enum | 期望路径类型 | 无 | `file` 或 `directory` |
| `candidate_path` | path string 或空 | 实际待检查路径 | 空 | 成功结果中必须非空 |
| `status` | [[RunStatus]] 或受控字符串 | 检查状态 | 无 | 成功/失败语义明确 |
| `error` | [[RuntimeErrorRef]] 或空 | 失败错误引用 | 空 | 失败结果必须存在 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactRequirement.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactCheckResult.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactPrecheckSummary.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g3/runtime_mvp_007_runtime_config_types.md`
5. `DOCS/阶段二：数据清洗/执行记录/051809_runtime_mvp_l2_docs.md`

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

- `src/data_clean/schemas/`
- `src/data_clean/runtime/`，仅当现有 Runtime Types 已放在该层
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/`

## 13. 禁止修改

- 禁止实现输入产物文件系统检查。
- 禁止实现配置预检查或 Service 调度。
- 禁止修改真实配置文件和真实数据产物。
- 禁止重新定义与上游 [[SceneName]]、[[RunMode]]、[[RunStatus]] 或 [[RuntimeErrorRef]] 冲突的对象。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 已定义 [[InputArtifactRequirement]]。
- [ ] 已定义 [[InputArtifactCheckResult]]。
- [ ] 已定义 [[InputArtifactPrecheckSummary]]。
- [ ] 失败检查结果能携带 [[RuntimeErrorRef]]。
- [ ] 未实现文件系统检查、配置预检查或 Service 调度。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_010_input_artifact_precheck_types>.md`
- 执行过程、当前状态、未完成事项和下一步建议写在同一个记录文件中
- 完成并更新任务文件后，将当前 L3 从 `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g5/` 移到 `DOCS/阶段二：数据清洗/03_tasks/completed/runtime-g5/`

交接摘要必须包含：

1. 读取了哪些相关 L3 任务文件或执行记录
2. 修改了哪些文件
3. 新增或修改了哪些函数 / 测试
4. TDD red / green / refactor 如何执行
5. 如何运行验收，命令必须使用 `python3`
6. 成功标准勾选情况
7. 当前没做什么
8. 下一步建议
