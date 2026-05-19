# L3 微元任务：实现场景输入需求解析

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[05_输入产物预检查模块]]  
L3 编号：`runtime_mvp_011`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`

## 2. 本次目标

```text
根据目标 SceneName 和 RunMode 解析当前场景需要检查的直接输入产物需求列表。
```

## 3. 本次不做

- 不检查路径是否存在或可读。
- 不从配置文件读取真实路径。
- 不实现配置预检查。
- 不调用 fake service 或真实 service。
- 不写日志、manifest 或错误摘要。

## 4. 执行对象

本次主要处理 [[SceneName]] 到 [[InputArtifactRequirement]] 列表的映射，形成场景一到场景五直接上游输入产物角色的最小规则。

## 5. 执行依赖

- `runtime_mvp_010` 已定义 [[InputArtifactRequirement]]。
- [[SceneName]] 与 [[RunMode]] 已由 Runtime 上下文相关任务定义。
- 阶段二产物架构设计已定义各场景主输入。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：runtime_mvp_001、runtime_mvp_002、runtime_mvp_010
上游接口定义位置：Runtime 上下文 Types L3；输入产物预检查 Types L3；DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md
当前 L3 期望消费的字段 / 文件 / 返回值：SceneName、RunMode、InputArtifactRequirement
是否存在接口冲突：如果 runtime_mvp_010 尚未完成，不得自行定义不兼容需求对象
如果有冲突，本次处理策略：先执行或补齐上游 Types 任务；必要时暂停说明
```

## 7. 预期改动形态

- 新增一个小的场景输入需求解析函数或等价表驱动结构。
- 测试覆盖场景一到场景五各自返回的直接输入产物角色。
- 需求解析只描述“需要检查什么”，不做文件系统动作。

## 8. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
| --- | --- | --- | --- |
| 合法输入 | 目标场景为场景一到场景五之一 | 返回对应 [[InputArtifactRequirement]] 列表 | 无 |
| 缺失输入 | 场景名称为空或不在受控取值内 | 返回失败或抛出清晰错误 | `unknown_scene_input_requirement` |
| 边界输入 | full pipeline 模式 | 第一版仍按当前目标场景直接输入需求返回，不展开全流程所有中间产物 | 无或 warning |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
| --- | --- | --- | --- |
| `requirements` | list of [[InputArtifactRequirement]] | 当前场景直接输入需求 | 目标场景合法时不能为空 |
| `artifact_role` | string | 输入产物角色 | 必须符合 L2 定义的角色语义 |
| `required_kind` | string / enum | 文件或目录 | 只能为 `file` 或 `directory` |

## 9. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactRequirement.md`
3. `DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md`
4. `DOCS/阶段二：数据清洗/00_架构与路线图/数据清洗pipeline宏观蓝图.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
4. `DOCS/阶段二：数据清洗/执行记录/051809_runtime_mvp_l2_docs.md`

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

- `src/data_clean/runtime/`
- `src/data_clean/schemas/`，仅当需要补充轻量枚举或常量
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`
- `DOCS/阶段二：数据清洗/执行记录/`

## 13. 禁止修改

- 禁止实现文件系统检查。
- 禁止读取或写入真实配置文件。
- 禁止实现 Service 调度。
- 禁止创建真实数据产物。
- 禁止修改功能5 L2 中未授权的输入产物角色语义。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -q
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] 场景一能解析出 raw 输入需求。
- [ ] 场景二能解析出 cleaned 输入需求。
- [ ] 场景三能解析出 validated 输入需求。
- [ ] 场景四能解析出 aligned 输入需求。
- [ ] 场景五能解析出 canonical dataset 输入需求。
- [ ] 本任务未执行文件系统检查或 Service 调度。

## 16. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要
- `DOCS/阶段二：数据清洗/执行记录/<MMDDHH_runtime_mvp_011_scene_input_requirements>.md`
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
