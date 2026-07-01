# L3 微元任务：实现场景输入需求解析

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：[[05_输入产物预检查模块]]  
L3 编号：`runtime_mvp_011`  
任务类别：数据计算类  
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`

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

1. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
2. `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactRequirement.md`
3. `DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md`
4. `DOCS/阶段二：数据清洗/00_架构与路线图/数据清洗pipeline宏观蓝图.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`

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
- `src/data_clean/schemas/`，仅当需要补充轻量枚举或常量
- `src/data_clean/tests/runtime/`
- `src/data_clean/data_clean_architecture.md`

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

- [x] 场景一能解析出 raw 输入需求。
- [x] 场景二能解析出 cleaned 输入需求。
- [x] 场景三能解析出 validated 输入需求。
- [x] 场景四能解析出 aligned 输入需求。
- [x] 场景五能解析出 canonical dataset 输入需求。
- [x] 本任务未执行文件系统检查或 Service 调度。

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

- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2能力模块/05_输入产物预检查模块.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactRequirement.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactCheckResult.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/L2数据定义/InputArtifactPrecheckSummary.md`
- `DOCS/阶段二：数据清洗/00_架构与路线图/阶段二产物架构设计.md`
- `DOCS/阶段二：数据清洗/00_架构与路线图/数据清洗pipeline宏观蓝图.md`
- `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
- `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
- `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
- `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
- `DOCS/03_工程/阶段二：数据清洗/01_runtime_mvp/执行约束.md`
- `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/runtime-g5/runtime_mvp_010_input_artifact_precheck_types.md`（上游 L3 已完成）

### 2. 修改的文件

| 文件 | 修改类型 | 说明 |
| --- | --- | --- |
| `src/data_clean/runtime/scene_input_requirements.py` | **新增** | 场景输入需求解析模块 |
| `src/data_clean/tests/runtime/test_scene_input_requirements.py` | **新增** | 15 个测试覆盖场景 1-5 及边界情况 |
| `src/data_clean/data_clean_architecture.md` | 修改 | 目录结构表新增 InputArtifact types 和 scene_input_requirements 条目 |

### 3. 新增的函数和测试

**新增函数**（`scene_input_requirements.py`）：
- `get_scene_input_requirements(scene_name, run_mode=None)` — 返回给定场景的 `InputArtifactRequirement` 列表
- `_build_all()` — 构建场景 1-5 的需求表
- 导出常量 `UNKNOWN_SCENE_MSG = "unknown_scene_input_requirement"`

**新增常量映射**（通过 `PRECHECK_RULES` 风格的表驱动）：
- Scene 1 → `raw_mcap` (file)
- Scene 2 → `cleaned_mcap` (file)
- Scene 3 → `validated_mcap` (file)
- Scene 4 → `aligned_mcap` (file)
- Scene 5 → `canonical_dataset` (directory)

**新增测试（15 tests）**：
- `test_scene1_returns_raw_mcap_requirement` — 场景一返回 raw_mcap 角色
- `test_scene2_returns_cleaned_mcap_requirement` — 场景二返回 cleaned_mcap 角色
- `test_scene3_returns_validated_mcap_requirement` — 场景三返回 validated_mcap 角色
- `test_scene4_returns_aligned_mcap_requirement` — 场景四返回 aligned_mcap 角色
- `test_scene5_returns_canonical_dataset_requirement` — 场景五返回 canonical_dataset 角色
- `test_each_requirement_has_valid_kind` — 所有 required_kind 为 file 或 directory
- `test_scene1_raw_mcap_is_file` / `test_scene4_aligned_mcap_is_file` / `test_scene5_canonical_dataset_is_directory` — 类型检查
- `test_all_requirements_have_path_config_key` / `test_all_requirements_have_non_empty_artifact_role` / `test_all_requirements_allow_manual_override` — 字段完整性
- `test_unknown_scene_raises_value_error` — 未知场景抛 ValueError
- `test_run_mode_is_accepted` — run_mode 参数兼容
- `test_return_type_is_list_of_requirement` — 返回值类型确认

### 4. TDD 执行过程

1. **RED**: 写入 15 个测试用例，运行后因 ModuleNotFoundError（模块不存在）确认 RED
2. **GREEN**: 创建 `scene_input_requirements.py`，实现表驱动的 `get_scene_input_requirements()` 函数 + 场景映射 + 未知场景异常
3. **REFACTOR**: 所有 15 个测试通过；确认不影响已有测试（84 个工作测试全部通过）；更新架构文档

### 5. 验收命令

```bash
python3 -m pytest src/data_clean/tests/runtime/test_scene_input_requirements.py -v
python3 -m pytest src/data_clean/tests/runtime/test_input_artifact_types.py -v
```

结果：15 passed + 9 passed = 24 passed。

### 6. 成功标准勾选

- [x] 场景一能解析出 raw 输入需求（`test_scene1_returns_raw_mcap_requirement` 通过）
- [x] 场景二能解析出 cleaned 输入需求（`test_scene2_returns_cleaned_mcap_requirement` 通过）
- [x] 场景三能解析出 validated 输入需求（`test_scene3_returns_validated_mcap_requirement` 通过）
- [x] 场景四能解析出 aligned 输入需求（`test_scene4_returns_aligned_mcap_requirement` 通过）
- [x] 场景五能解析出 canonical dataset 输入需求（`test_scene5_returns_canonical_dataset_requirement` 通过）
- [x] 本任务未执行文件系统检查或 Service 调度（仅返回需求列表，无文件操作）
- [x] 执行摘要已追加到当前 L3 文件末尾
- [ ] 当前 L3 已归档（归档前最后一个步骤）

### 7. 当前没做什么

- 未检查路径是否存在或可读（属于 runtime_mvp_012 范围）
- 未从配置文件读取真实路径（属于 runtime_mvp_012 范围）
- 未实现配置预检查（已由 runtime_mvp_008/017/018 覆盖）
- 未调用 fake service 或真实 service
- 未写日志、manifest 或错误摘要
- 对于 full pipeline 模式，第一版仍按单场景输入需求返回（按 L2 规划）
- `path_config_key` 使用语义键（如 `scene1.input_path`），尚未与实际配置键名对齐（留给 runtime_mvp_012 处理）

### 8. 一步建议

- 后续 L3 `runtime_mvp_012` 可消费本模块的 `get_scene_input_requirements()` 结果，结合 `EffectiveRuntimeConfig` 解析实际路径并执行文件系统边界检查。
- 当场景二到五的真实配置字段名稳定后，`path_config_key` 需要与 `EffectiveRuntimeConfig` 中的配置键对齐。

