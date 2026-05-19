# L3 微元任务：定义配置预检查 Types 与规则常量

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[04_配置预检查模块]]  
L3 编号：`runtime_mvp_017`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`

## 2. 本次目标

```text
定义配置预检查所需的最小 Types 与规则常量，让后续预检查器能稳定表达通过结果、阻塞问题和场景最小配置要求。
```

## 3. 本次不做

- 不实现配置预检查计算逻辑。
- 不接入 Runtime 初始化链路。
- 不读取配置文件或写入 `config_snapshot.yaml`。
- 不检查输入产物存在性。
- 不定义 Service 业务级参数校验。

## 4. 执行对象

本次主要处理 [[ConfigPrecheckResult]]、[[ConfigPrecheckIssue]]、[[ConfigPrecheckRule]] 和 [[SceneConfigRequirement]] 的代码层表达，可使用 dataclass、enum、TypedDict、Pydantic model 或项目现有最轻量的等价结构。

## 5. 执行依赖

- 功能四 L2 能力模块说明已经存在。
- 功能四四个 L2 原子数据定义已经存在。
- 功能一到功能三相关 Runtime Types 任务应优先检查现状，尤其是 [[RunContext]]、[[SceneName]]、[[RuntimeErrorRef]]、[[EffectiveRuntimeConfig]] 和 [[ConfigSnapshot]]。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：Runtime 运行上下文定义、配置加载与配置快照模块
上游接口定义位置：DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md；DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/03_配置加载与配置快照模块.md；DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/；DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g3/
当前 L3 期望消费的字段 / 文件 / 返回值：RunContext.target_scenes、RunContext.run_dir、SceneName、RuntimeErrorRef、EffectiveRuntimeConfig.effective_data、ConfigSnapshot.snapshot_path
是否存在接口冲突：未知，执行时必须读取现有代码和上游 L3 状态确认
如果有冲突，本次处理策略：不重写上游 Types；优先复用现有字段，无法复用时在执行记录中说明阻塞并只做最小兼容定义
```

## 7. 预期改动形态

- 在 `src/data_clean/schemas/` 或现有 Runtime 配置类型位置新增配置预检查相关 Types。
- 定义稳定 issue code / rule id 常量或等价受控取值。
- 新增或更新测试，覆盖通过结果、阻塞 issue、规则集合和场景最小配置要求的构造。
- 如新增源码模块，更新 `src/data_clean/data_clean_architecture.md` 的目录结构表。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| [[ConfigPrecheckIssue]] | dataclass / TypedDict / model | `src/data_clean/schemas/` 或现有等价位置 | `runtime_mvp_018`、日志、错误摘要 |
| [[ConfigPrecheckResult]] | dataclass / TypedDict / model | `src/data_clean/schemas/` 或现有等价位置 | 输入产物预检查、Service 调度、smoke test |
| [[ConfigPrecheckRule]] | dataclass / enum / 常量表 | `src/data_clean/schemas/` 或现有等价位置 | `runtime_mvp_018` |
| [[SceneConfigRequirement]] | dataclass / TypedDict / model | `src/data_clean/schemas/` 或现有等价位置 | `runtime_mvp_018`、场景调度 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `issue_code` | string / enum | 配置问题码 | 无 | 稳定、非空、可测试 |
| `severity` | string / enum | 问题级别 | `error` | 第一版至少支持 `error` 和 `warning` |
| `passed` | boolean | 预检查是否通过 | 无 | 有阻塞 issue 时必须为 false |
| `checked_scenes` | list of [[SceneName]] | 被检查目标场景 | 空列表 | 应与 [[RunContext]] 一致 |
| `checked_rules` | list | 已执行规则 | 空列表 | rule id 稳定可断言 |
| `required_sections` | list of string | Runtime 级必需配置块 | 空列表 | 不包含 Service 深层业务参数 |
| `required_fields` | list of string | Runtime 级必需字段路径 | 空列表 | 不包含输入产物存在性检查 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/04_配置预检查模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckResult.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckIssue.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigPrecheckRule.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneConfigRequirement.md`
6. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/RunContext.md`
7. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/EffectiveRuntimeConfig.md`
8. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ConfigSnapshot.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g3/`
3. `DOCS/阶段二：数据清洗/执行记录/` 中与 Runtime Types 或配置加载相关的记录

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

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/config/`，仅当现有配置相关 Types 已放在配置层
- `src/data_clean/tests/runtime/` 或 `src/data_clean/tests/contract/`
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/`

## 13. 禁止修改

- 禁止实现配置预检查器计算逻辑。
- 禁止修改功能三配置加载与快照写入行为。
- 禁止修改输入产物预检查、Service 调度或 fake service。
- 禁止生成真实 run 目录或真实数据产物。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 配置预检查相关 Types 可被 import。
- [ ] 能构造通过的 [[ConfigPrecheckResult]]。
- [ ] 能构造阻塞型 [[ConfigPrecheckIssue]]。
- [ ] 能构造 [[ConfigPrecheckRule]] 和 [[SceneConfigRequirement]]。
- [ ] 未实现配置预检查计算逻辑和 Runtime 接入逻辑。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_017_config_precheck_types>.md`
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
