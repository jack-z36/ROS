# L3 微元任务：为调度模块实现 Fake Service 调用适配边界

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：Runtime MVP  
L1：`runtime_mvp`  
L2 能力：Runtime MVP / Fake Service 模块  
L3 编号：`runtime_mvp_022`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`

## 2. 本次目标

```text
为功能6调度模块提供最小 fake service 调用适配，使 fake service 结果能汇总为 SceneResult。
```

## 3. 本次不做

- 不实现完整单场景调度器或全流程调度器。
- 不实现真实 Service 接入。
- 不写日志、manifest、error summary 或 run_result。

## 4. 执行对象

- [[ServiceBinding]]
- [[FakeServicePlan]]
- [[FakeServiceResult]]
- [[SceneResult]]

## 5. 执行依赖

- `runtime_mvp_020_fake_service_types.md` 已完成。
- `runtime_mvp_021_fake_service_result_generator.md` 已完成。
- 功能6的 service dispatch types 至少已经定义 [[ServiceBinding]]、[[ServiceRegistry]]、[[SceneDispatchPlan]] 或等价结构。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：功能6 场景注册与 Service 调度模块、功能7 fake service 结果生成
上游接口定义位置：
- DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_020_fake_service_types.md
- DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_021_fake_service_result_generator.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- ServiceBinding 的 callable 或等价调用入口
- FakeServiceResult
- SceneResult
是否存在接口冲突：执行前必须检查功能6代码层接口是否已落地
如果有冲突，本次处理策略：只做最小 adapter；不重写功能6调度策略，不扩大到全流程调度
```

## 7. 预期改动形态

- 新增或扩展一个 adapter，将 fake service callable 包装成 [[ServiceBinding]] 可调用形态。
- 新增最小结果转换逻辑，把 [[FakeServiceResult]] 映射为 [[SceneResult]]。
- 新增测试，验证 fake binding 被调用后能生成成功或失败 [[SceneResult]]。

## 8. 编排输出

### 调用顺序

```text
入口：收到 RunContext、ServiceBinding、FakeServicePlan
↓
步骤 1：确认 ServiceBinding 指向 fake service 或 ServiceMode 为 fake
↓
步骤 2：调用 fake service 结果生成逻辑
↓
步骤 3：将 FakeServiceResult 转换为 SceneResult
↓
完成 / 失败
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
| --- | --- | --- | --- | --- |
| fake service 结果生成逻辑 | adapter 确认 fake 绑定后 | [[FakeServicePlan]] | [[FakeServiceResult]] | 返回失败 [[SceneResult]] |
| SceneResult 转换逻辑 | fake service 返回后 | [[FakeServiceResult]] | [[SceneResult]] | 保留 [[RuntimeErrorRef]] |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
| --- | --- | --- | --- |
| fake_bound | adapter 识别到 fake service 绑定 | [[SceneResult]] 或测试断言 | 暂不直接面向用户 |
| succeeded | fake service 返回成功 | [[SceneResult]] | 后续日志模块消费 |
| failed | fake service 返回失败或 adapter 调用失败 | [[SceneResult]].`error` | 后续错误摘要模块消费 |

## 9. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/07_Fake Service模块.md`
2. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2能力模块/06_场景注册与Service调度模块.md`
3. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/FakeServiceResult.md`
4. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/ServiceBinding.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/L2数据定义/SceneDispatchPlan.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_013_service_dispatch_types.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_014_service_registry.md`
3. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g6/runtime_mvp_015_single_scene_dispatcher.md`
4. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_020_fake_service_types.md`
5. `DOCS/阶段二：数据清洗/03_tasks/task/active/runtime-g7/runtime_mvp_021_fake_service_result_generator.md`

如果没有找到相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
5. `DOCS/阶段二：数据清洗/01_runtime_mvp/执行约束.md`

### 必读代码

1. `src/data_clean/runtime/`
2. `src/data_clean/service/`
3. `src/data_clean/schemas/`
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

- 不实现完整 pipeline dispatcher。
- 不修改真实 Service 业务算法。
- 不修改配置加载、输入产物预检查、日志、manifest 或错误摘要模块。
- 不写入真实数据产物目录。

## 14. 验收命令

Python 命令必须使用 `python3`，不得写成 `python`。
仓库内文件和目录必须使用相对仓库根目录路径，不得写入开发者本机绝对路径。

```bash
python3 -m pytest src/data_clean/tests/runtime -k "fake_service and dispatch"
```

## 15. 成功标准

完成后必须在本文件中把实际验证通过的条目改为 `- [x]`；未验证条目保持 `- [ ]`，并在执行摘要说明原因。

- [ ] fake service 可通过 [[ServiceBinding]] 或等价 adapter 被调用。
- [ ] 成功 [[FakeServiceResult]] 能转换为成功 [[SceneResult]]。
- [ ] 失败 [[FakeServiceResult]] 能转换为携带 [[RuntimeErrorRef]] 的失败 [[SceneResult]]。
- [ ] 本任务没有实现完整单场景或全流程调度器。
- [ ] 验收命令使用 `python3` 并通过，或执行摘要说明环境阻塞。

- [ ] 执行摘要已追加到当前 L3 文件末尾。
- [ ] 当前 L3 已归档到对应 `task/completed/<功能组>/`。

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

