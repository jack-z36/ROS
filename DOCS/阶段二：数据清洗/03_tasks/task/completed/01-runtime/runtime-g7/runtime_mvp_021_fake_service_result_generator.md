# L3 微元任务：实现 Fake Service 成功与可控失败结果生成

## 1. 任务定位

阶段：阶段二：数据清洗
场景：Runtime MVP
L1：`runtime_mvp`
L2 能力：Runtime MVP / Fake Service 模块
L3 编号：`runtime_mvp_021`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`

## 2. 本次目标

```text
实现一个只根据 FakeServicePlan 生成成功或可控失败 FakeServiceResult 的最小 fake service 计算逻辑。
```

## 3. 本次不做

- 不接入场景注册表或真实调度链路。
- 不创建真实业务产物或占位文件。
- 不写 `run_log.json`、`processing_manifest.json`、`error_summary.json`。

## 4. 执行对象

- fake service 结果生成函数、类或等价 callable。
- [[FakeServicePlan]]
- [[FakeServiceResult]]
- [[RuntimeErrorRef]]

## 5. 执行依赖

- `runtime_mvp_020_fake_service_types.md` 完成或已经存在等价 fake service 类型。
- 已有 [[RunDirectory]] / [[RunArtifactPath]] 代码层结构可用于 fake 输出路径声明。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：功能7 L3-020 Fake Service Types、功能2 Run 目录管理、功能1 Runtime 运行上下文定义
上游接口定义位置：
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_020_fake_service_types.md
- DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/02_Run目录管理模块.md
- DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/01_Runtime运行上下文定义.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- FakeServicePlan.behavior、scene_name、service_mode、declared_outputs
- RunDirectory / RunArtifactPath 或等价路径引用
- RuntimeErrorRef 或等价错误引用
是否存在接口冲突：执行前必须确认 L3-020 实际落地类型名称和字段
如果有冲突，本次处理策略：以已落地代码类型为准，必要时更新本任务执行摘要，不回头重定义上游类型
```

## 7. 预期改动形态

- 新增或扩展 `src/data_clean/runtime/` 或 `src/data_clean/service/` 中的 fake service 计算模块。
- 新增 runtime 测试，覆盖 `success`、`controlled_failure`、非 fake mode、目标场景缺失、输出路径逃逸等行为。

## 8. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则                               | 预期输出                                                               | reason / error                      |
| -------- | --------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------- |
| 合法输入 | `service_mode=fake` 且 `behavior=success` | 成功 [[FakeServiceResult]]，包含 scene、status、output_paths、duration | 无                                  |
| 缺失输入 | 缺少目标 [[SceneName]] 或计划对象为空         | 失败 [[FakeServiceResult]] 或抛出受控异常                              | `fake_service_scene_missing`      |
| 边界输入 | `behavior=controlled_failure`               | 失败 [[FakeServiceResult]]，携带 [[RuntimeErrorRef]]                   | `fake_service_controlled_failure` |
| 边界输入 | `service_mode` 不是 `fake`                | 拒绝执行并返回失败                                                     | `fake_service_mode_mismatch`      |
| 边界输入 | 输出路径逃逸本次 run 目录                     | 返回失败                                                               | `fake_output_path_escape`         |

### 输出结构

| 字段             | 类型                 | 含义           | 有效性要求                     |
| ---------------- | -------------------- | -------------- | ------------------------------ |
| `scene_name`   | SceneName            | 被模拟场景     | 必须与 plan 一致               |
| `behavior`     | FakeServiceBehavior  | 本次 fake 行为 | 必须是受控取值                 |
| `status`       | RunStatus            | fake 执行状态  | 成功时无 error，失败时有 error |
| `output_paths` | map                  | 假输出声明     | 不得写入真实产物目录           |
| `error`        | RuntimeErrorRef 或空 | 失败引用       | 失败时必填                     |
| `duration_ms`  | integer              | 执行耗时       | 不得为负                       |

## 9. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServicePlan.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceBehavior.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceResult.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_020_fake_service_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g2/runtime_mvp_004_run_directory_types.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/schemas/`
2. `src/data_clean/runtime/`
3. `src/data_clean/service/`
4. `src/data_clean/tests/runtime/`

## 11. TDD 执行要求

如果本 L3 涉及代码新增、代码修改、bug 修复或行为变更，必须先读取并使用 `$tdd` 技能：

```text
$tdd
```

执行时按垂直切片推进：一个行为测试或最小复现 -> 最少实现 -> 验证通过 -> 必要整理 -> 下一个行为。

## 12. 允许修改

- `src/data_clean/runtime/`
- `src/data_clean/service/`
- `src/data_clean/tests/runtime/`
- 必要的同层导出文件。

## 13. 禁止修改

- 不修改功能6调度器文件，除非只是为了导入已存在类型且不改变行为。
- 不修改真实 Service 业务算法。
- 不写入 `asset/阶段二：数据清洗/`。
- 不修改启动脚本和 UI。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -k fake_service
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [x] `success` 行为能返回成功 [[FakeServiceResult]]。
- [x] `controlled_failure` 行为能返回带 `fake_service_controlled_failure` 的失败结果。
- [x] 非 fake mode、缺目标场景、输出路径逃逸均失败清楚。
- [x] 不读取或写入真实 MCAP / canonical dataset / exports。
- [x] 验收命令使用 `python3` 并通过，或执行摘要说明环境阻塞。
- [x] 执行摘要已追加到当前 L3 文件末尾。
- [x] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

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

### 读取的相关 L3 任务文件或历史记录

- `DOCS/阶段二：数据清洗/03_tasks/task/completed/runtime-g7/runtime_mvp_020_fake_service_types.md` - 了解已有类型定义
- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md` - 了解能力模块定义
- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServicePlan.md` - 了解数据定义
- `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceResult.md` - 了解数据定义

### 修改的文件

- `src/data_clean/runtime/fake_service_result_generator.py` - 新增，包含 `generate_fake_service_result` 函数和 `FakeServiceExecutionError` 异常
- `src/data_clean/tests/runtime/test_fake_service_result_generator.py` - 新增测试文件

### 新增或修改的函数 / 测试

- 新增 `FakeServiceExecutionError` 异常类：用于 fake service 执行失败
- 新增 `generate_fake_service_result` 函数：根据 FakeServicePlan 生成 FakeServiceResult
  - 验证 service_mode 为 FAKE
  - 验证输出路径不逃逸 run 目录
  - 根据 behavior 返回成功或失败结果
  - controlled_failure 返回稳定错误码 `fake_service_controlled_failure`
- 新增 10 个测试用例覆盖所有行为

### TDD red / green / refactor 执行

- RED：测试文件创建后，模块不存在导致 import 错误
- GREEN：实现 `fake_service_result_generator.py` 模块，所有 10 个测试通过
- REFACTOR：无需重构，实现已最小化

### 验收命令

```bash
PYTHONPATH=src python3 -m pytest src/data_clean/tests/runtime/test_fake_service_result_generator.py -v
```

结果：10 passed, 0 failed

```bash
PYTHONPATH=src python3 -m pytest src/data_clean/tests/runtime/test_fake_service_types.py src/data_clean/tests/runtime/test_fake_service_result_generator.py -v
```

结果：27 passed, 0 failed（L3-020 + L3-021 全部测试通过）

### 成功标准勾选情况

- [x] `success` 行为能返回成功 FakeServiceResult
- [x] `controlled_failure` 行为能返回带 `fake_service_controlled_failure` 的失败结果
- [x] 非 fake mode、缺目标场景、输出路径逃逸均失败清楚
- [x] 不读取或写入真实 MCAP / canonical dataset / exports
- [x] 验收命令使用 `python3` 并通过
- [x] 执行摘要已追加到当前 L3 文件末尾

### 当前没做什么

- 不实现 fake service 调度适配边界（L3-022 负责）
- 不写入真实数据产物、日志、manifest 或错误摘要文件
- 不修改功能6调度器实现

### 下一步建议

- 执行 L3-022：为调度模块实现 Fake Service 调用适配边界
- 执行 L3-023：定义结构化日志类型（如果尚未完成）
