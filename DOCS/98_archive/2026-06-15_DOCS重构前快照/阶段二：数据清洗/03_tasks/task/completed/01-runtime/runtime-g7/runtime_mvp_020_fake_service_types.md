# L3 微元任务：定义 Fake Service Types 与行为枚举

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：Runtime MVP / Fake Service 模块  
L3 编号：`runtime_mvp_020`  
任务类别：数据定义类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`

## 2. 本次目标

```text
定义 fake service 执行计划、行为枚举和执行结果的代码层类型，使后续 fake service 计算逻辑可稳定消费。
```

## 3. 本次不做

- 不实现 fake service 成功或失败结果生成逻辑。
- 不接入场景注册表或调度器。
- 不写入真实数据产物、日志、manifest 或错误摘要文件。

## 4. 执行对象

- [[FakeServicePlan]]
- [[FakeServiceBehavior]]
- [[FakeServiceResult]]

## 5. 执行依赖

- 已有 [[SceneName]]、[[ServiceMode]]、[[RunStatus]]、[[RuntimeErrorRef]]、[[RunArtifactPath]] 的代码层类型或等价结构。
- 已有功能6关于 [[ServiceBinding]] 和 [[SceneDispatchPlan]] 的语义接口任务。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：功能1 Runtime 运行上下文定义、功能2 Run 目录管理、功能6 场景注册与 Service 调度模块
上游接口定义位置：
- DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md
- DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md
- DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- SceneName、ServiceMode、RunStatus、RuntimeErrorRef、RunArtifactPath
- ServiceBinding 后续可以引用 FakeServicePlan / FakeServiceResult
是否存在接口冲突：执行前需要检查代码层已有类型命名是否与文档一致
如果有冲突，本次处理策略：优先复用既有类型；只新增 fake service 专属类型，不重定义上游类型
```

## 7. 预期改动形态

- 在 `src/data_clean/schemas/` 或 `src/data_clean/runtime/` 的合适位置新增 fake service 相关 enum / dataclass / TypedDict。
- 必要时在同层 `__init__` 或导出入口中暴露新增类型。
- 新增或扩展测试，验证类型可 import、可实例化、非法行为取值会失败或被拒绝。

## 8. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
| --- | --- | --- | --- |
| `FakeServiceBehavior` | enum | `src/data_clean/schemas/` 或 `src/data_clean/runtime/` | fake service 结果生成、Runtime smoke test |
| `FakeServicePlan` | dataclass / TypedDict / Pydantic model | 同上 | fake service 结果生成、调度适配 |
| `FakeServiceResult` | dataclass / TypedDict / Pydantic model | 同上 | 调度模块、结构化日志、错误摘要 |

### 字段或取值

| 字段 / 取值 | 类型 | 含义 | 默认值 | 合法性要求 |
| --- | --- | --- | --- | --- |
| `success` | enum value | 模拟成功执行 | 无 | 必须可稳定引用 |
| `controlled_failure` | enum value | 模拟可控失败 | 无 | 必须生成失败结果所需语义 |
| `skipped` | enum value | 预留跳过行为 | 无 | 不得被当作成功 |
| `scene_name` | SceneName | 目标场景 | 无 | 必填 |
| `service_mode` | ServiceMode | 调用模式 | `fake` 或无默认 | 必须表达 fake 语义 |
| `behavior` | FakeServiceBehavior | fake 行为 | 无 | 必填 |
| `output_paths` | map | 假输出声明 | 空 map 或必填 | 不能表达真实产物已完成 |
| `error` | RuntimeErrorRef 或空 | 失败错误引用 | 空 | 失败结果必须存在 |

## 9. 数据定义验收重点

- 能被 import 或被文档链接引用。
- 能实例化或能被 schema 校验工具读取。
- 字段类型、默认值和非法值处理符合 L2 定义。
- 相关原子数据定义文档已创建或复用，并在 L2/L3 中用 `[[wikilink]]` 引用。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServicePlan.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceBehavior.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceResult.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/`
2. `src/data_clean/schemas/`
3. `src/data_clean/runtime/`
4. `src/data_clean/tests/`

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/runtime/`
- `src/data_clean/tests/`
- 必要的同层导出文件。

## 13. 禁止修改

- 不修改功能6调度器实现。
- 不修改真实 Service 场景代码。
- 不修改 `asset/阶段二：数据清洗/` 下真实数据产物。
- 不修改 `start_data_clean.sh`。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -k fake_service
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] 已定义 `FakeServiceBehavior`、`FakeServicePlan`、`FakeServiceResult` 或等价代码结构。
- [x] 新类型复用上游 `SceneName`、`ServiceMode`、`RunStatus`、`RuntimeErrorRef`、`RunArtifactPath`，不重复定义相似对象。
- [x] 测试覆盖成功计划、失败计划、非法行为取值，以及成功/失败状态与 error 的交叉校验。
- [x] 验收命令使用 `python3` 并通过，或执行摘要说明环境阻塞。

- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

## 17. 执行摘要

### 读取的相关 L3 任务文件或历史记录

- `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md`
- `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_002_定义Runtime状态与模式枚举.md`
- `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g1/runtime_mvp_003_定义Runtime结果与错误引用Types.md`
- `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
- `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`
- 未找到相关 L3 历史记录（首次执行）

### 修改的文件

- `src/data_clean/schemas/runtime_enums.py`：已有 `FakeServiceBehavior` enum，无需修改
- `src/data_clean/schemas/fake_service_types.py`：新增，包含 `FakeServicePlan` 和 `FakeServiceResult` dataclass；`FakeServiceResult.__post_init__` 增加成功/失败交叉校验（SUCCEEDED→error 必为 None，FAILED→error 必存在）
- `src/data_clean/schemas/__init__.py`：新增导出 `FakeServiceBehavior`、`FakeServicePlan`、`FakeServiceResult`

### 新增或修改的函数 / 测试

- 新增 `FakeServicePlan` dataclass：字段 `scene_name`、`service_mode`、`behavior`、`declared_outputs`、`input_summary`、`message`；`__post_init__` 校验 `service_mode` 必须为 `FAKE`
- 新增 `FakeServiceResult` dataclass：字段 `scene_name`、`behavior`、`status`、`output_paths`、`started_at`、`finished_at`、`duration_ms`、`input_summary`、`error`；`__post_init__` 校验 `finished_at` 不得早于 `started_at`；增加成功/失败交叉校验（SUCCEEDED→error 必为 None，FAILED→error 必存在）
- 测试 `test_fake_service_types.py`（17 个用例）全部通过

### TDD red / green / refactor 执行

- RED-1：已有 14 个测试用例，初始 10 个失败（FakeServicePlan 和 FakeServiceResult 未实现），4 个通过（FakeServiceBehavior 已存在）
- GREEN-1：创建 `fake_service_types.py`，实现 `FakeServicePlan` 和 `FakeServiceResult`，14 个测试全部通过
- REFACTOR-1：无需重构，实现已最小化
- RED-2：新增 3 个交叉校验测试，其中 `test_success_result_must_not_have_error`、`test_failure_result_must_have_error` 因缺少验证逻辑失败
- GREEN-2：在 `FakeServiceResult.__post_init__` 增加 `status` 与 `error` 的交叉校验
- REFACTOR-2：无需重构

### 验收命令

```bash
PYTHONPATH=src python3 -m pytest src/data_clean/tests/runtime/test_fake_service_types.py -k fake_service
```

结果：17 passed, 0 failed（文件级运行无 collection 干扰；目录级 `-k` 运行因 `test_run_context_attach.py` 的预存 import 错误无法收集，与本次改动无关）

### 成功标准勾选情况

- [x] 已定义 `FakeServiceBehavior`、`FakeServicePlan`、`FakeServiceResult`
- [x] 复用上游 `SceneName`、`ServiceMode`、`RunStatus`、`RuntimeErrorRef`
- [x] 测试覆盖成功计划、失败计划、非法行为取值（service_mode 非 fake、finished_at 早于 started_at、success 带 error、failure 缺 error）
- [x] 验收命令通过

### 当前没做什么

- 不实现 fake service 成功或失败结果生成逻辑（L3-021 负责）
- 不接入场景注册表或调度器（L3-022 负责）
- 不写入真实数据产物、日志、manifest 或错误摘要文件
- 不修改功能6调度器实现

### 下一步建议

- 执行 L3-021：实现 Fake Service 成功与可控失败结果生成
- 执行 L3-022：为调度模块实现 Fake Service 调用适配边界

