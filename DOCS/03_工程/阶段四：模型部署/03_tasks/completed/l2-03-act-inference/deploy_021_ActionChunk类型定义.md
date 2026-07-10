# L3 微元改造任务：ActionChunk 类型定义

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-03-act-inference` ObservationSnapshot 到 ACT ActionChunk 推理闭环
L3 编号：`deploy_021`
改造类型：`source-adaptation`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_021_ActionChunk类型定义.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_021_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/`
验收模式：`direct-local`
辅助验收模式：[]
本地验收是否必须：`true`
真机风险等级：`none`
L2 分支：`feat/model_deploy/l2-03-act-inference`
集成分支：`model_deploy`

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_021
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_021_ActionChunk类型定义.md
  group: l2-03-act-inference
  branch: feat/model_deploy/l2-03-act-inference
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference
  acceptance_scenarios: [S1]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_021_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/logs
  wave: 1
  parallel_group: l2-03-act-inference-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_022, deploy_023]
  conflict_scope:
    files:
      - src/model_deploy/act/types/action_chunk.py
      - src/model_deploy/act/tests/types/test_action_chunk.py
    modules:
      - model_deploy.act.types.action_chunk
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 执行 sub-agent 可以阅读验收卡片理解通过标准，但不得替验收 sub-agent 修改验收结论。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- 验收 sub-agent 不得改源码、测试、dispatch、任务状态或 Git。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。

## 3. 本次唯一目标

```text
定义 ActionChunk frozen dataclass：只含 actions 字段的跨模块值对象，构造时严格校验 shape/dtype/有限值，不含任何运行元数据。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 从 snapshot 取得 16D state 与图像，同步计算为 `ActionChunk`。
- `ActionChunk` 只包含 `(chunk_size, 16)` float32 physical actions。

### L2 不负责

- 不携带 request_id、时间、latency、queue state、cursor、error 或 metrics 等运行元数据。
- 不做 safety 检查、ROS publish、硬件交互。

### 本 L3 在 L2 中的位置

```text
ActionChunk 是 L2-03 到 L2-06 的唯一跨模块输出类型。deploy_022（阶段一 batch 准备）和 deploy_023（阶段三后处理）都依赖本类型完成各自的输入输出契约；deploy_024 的 ActInferenceService 总编排入口最终返回 ActionChunk。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/02_pi05源码3.5层微元拆解.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/03_ACT微元设计与协作.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/04_L2验收机制.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/05_人类验收机制.md`
9. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/06_types层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| Pi0.5 ActionChunk | `pi05/deploy/src/pi05/deploy/runtime/inference_worker.py` `ActionChunk` | 数据 | 持有 actions tensor + obs_time/infer_start_time/ready_time/action_dt/request_id/cursor/aligned_index() | 必须剥离全部运行元数据字段和方法 | 结构复用 |

### 必须保留的源码启发

- Pi0.5 `ActionChunk` 证明 L2-03 需要把 chunk 作为跨模块值对象传递，而非裸 tensor。
- `actions` 字段的 shape `(chunk_size, action_dim)` 语义正确，保留。

### 禁止照搬的源码行为

- `obs_time`、`infer_start_time`、`ready_time`、`action_dt` —— 属于 L2-06 运行记录。
- `request_id`、`cursor` —— 属于 L2-06 chunk 生命周期管理。
- `aligned_index(now)` —— 属于 L2-06 cursor 消费逻辑。

### 已知风险

- 不得把 `ActionChunk` 设计成可变对象；L2-06 接收后应只读消费。
- types 层不得反向 import config（不能用 `DeployConfig.runtime.chunk_size` 做构造校验），chunk_size 精确相等由 service 阶段三验证。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 在 `src/model_deploy/act/types/action_chunk.py` 新增 `ActionChunk` frozen dataclass。
- 字段只包含 `actions: np.ndarray`。
- 在 `__post_init__` 中校验 `ndim == 2`、`shape[1] == 16`、`dtype == float32`、全部有限值、行数 > 0。
- 可复用 `types/action_spec.py` 的 `ACTION_DIM` 常量。

### 本次不做

- 不校验 `chunk_size` 精确等于 `DeployConfig.runtime.chunk_size`（属于 service 阶段三）。
- 不添加任何运行元数据字段或方法。
- 不添加 `aligned_index`、`is_expired`、`remaining_steps` 等消费逻辑。

### 明确禁止修改

- `src/model_deploy/act/types/action_spec.py`（除非为了导入 `ACTION_DIM` 常量）。
- `src/model_deploy/act/types/` 下其他已有文件。
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件。

### 函数 / class 策略

```text
ActionChunk 是 frozen dataclass。选 class 原因：需要 __post_init__ 做构造时契约校验，且 frozen=True 保证 L2-06 消费后不能篡改字段。无状态、无方法、无生命周期管理。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 是 | `src/model_deploy/act/types/action_chunk.py` | ActionChunk frozen dataclass 定义与构造校验 |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 否 | — | — |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/types/test_action_chunk.py` | ActionChunk 构造校验与字段契约测试 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/06_types层设计.md` | ActionChunk frozen dataclass：`actions` 字段、`__post_init__` 五项校验、16D 固定语义、明确不存在字段 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `types/action_chunk.py` | ActionChunk 数据定义 | 数据 | 合法 `(N,16)` float32 finite array | frozen dataclass 实例 | 无 | types.action_chunk_contract |
| `types/action_chunk.py` | 构造时维度校验 | 计算函数 | actions ndarray | 通过或 `ValueError` | 无 | test_action_chunk.py::test_valid_construction |
| `types/action_chunk.py` | 构造时 dtype 校验 | 计算函数 | actions ndarray | 通过或 `TypeError` | 无 | test_action_chunk.py::test_invalid_dtype |
| `types/action_chunk.py` | 构造时有限值校验 | 计算函数 | actions ndarray | 通过或 `ValueError` | 无 | test_action_chunk.py::test_nan_inf_rejected |
| `types/action_chunk.py` | 构造时空 chunk 校验 | 计算函数 | actions ndarray | 通过或 `ValueError` | 无 | test_action_chunk.py::test_empty_chunk_rejected |

## 9. 实施步骤

1. 阅读 `agent_context/06_types层设计.md`，确认 ActionChunk 字段与构造约束。
2. 在 `src/model_deploy/act/types/action_chunk.py` 新建文件，定义 `@dataclass(frozen=True) class ActionChunk`。
3. 实现 `__post_init__` 五项校验：`ndim==2`、`shape[1]==16`、`dtype==np.float32`、全部有限、行数 > 0。
4. 编写 `tests/types/test_action_chunk.py`：合法构造、rank 错误、dim 错误、dtype 错误、NaN/Inf、空 chunk、frozen 不可变、无运行元数据字段，共 8+ 测试用例。
5. 运行 `python3 -m pytest src/model_deploy/act/tests/types/test_action_chunk.py -v`，全部 PASS。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/types/action_chunk.py`（新建）
- `src/model_deploy/act/tests/types/test_action_chunk.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| ActionChunk 类型 | `src/model_deploy/act/types/action_chunk.py` | types |
| ActionChunk 单测 | `src/model_deploy/act/tests/types/test_action_chunk.py` | tests/types |

## 11. 禁止修改

- `src/model_deploy/act/types/action_spec.py`（除非仅添加 `ACTION_DIM` import，不做语义修改）
- `src/model_deploy/act/types/` 下其他已有文件
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件
- `src/model_deploy/act/config/`、`repo/`、`service/`、`runtime/`、`ui/` 下任何文件
- dispatch、cards 或 acceptance 目录下其他 L2 的文件

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_action_chunk.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | ActionChunk 构造、字段校验、frozen 不可变 | pytest 全部 PASS |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| shadow-run | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/logs/
对应运行验收场景：S1
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1（类型契约） |
| 本 L3 提供的运行能力 | ActionChunk 跨模块值对象，保证 L2-06 只通过 `actions` 字段消费 physical actions |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/types/test_action_chunk.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | service 层三阶段闭环、集成 Gate 测试、verify 脚本 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/runtime/inference_worker.py`（Pi0.5 ActionChunk 参考）
2. `src/model_deploy/act/types/action_spec.py`（复用 `ACTION_DIM` 常量）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游 L3
2. 无同组已完成 L3

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：deploy_021
正文 L3 编号：deploy_021
dispatch.task_id：deploy_021
是否一致：
所属 L2 ID：l2-03-act-inference
是否属于新版 L2 白名单：是
是否命中旧 L2 ID：否
是否位于 legacy/archive 目录：否
```

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [x] 已完成 Pi0.5 源码盘点中列出的相关代码确认。
- [x] 改动没有越过当前 L2 的责任边界。
- [x] 产物路径符合六层落点约束。
- [x] 已完成本 L3 的自动化验收或说明无法自动化的原因。
- [x] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [x] 如涉及真机发送链路，已完成真机风险控制说明。（不适用，本 L3 不触发真机动作）
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
关闭参数 / 配置：无
切回旧入口：删除 action_chunk.py 和 test_action_chunk.py
移除 adapter：无
回退文件：git checkout -- src/model_deploy/act/types/action_chunk.py src/model_deploy/act/tests/types/test_action_chunk.py
不可自动回滚的人工步骤：无
```

## 17. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 所属 L2 的 `05_acceptance/l2-03-act-inference/验收结果.md`：登记本 L3 贡献。
- 对应 L3 验收卡片：供验收 agent 独立评估。
- 不得擅自更新阶段级 `当前进度.md` 或共享 `执行记录.md`。
- 执行 sub-agent 完成单个 L3 后不得自行提交或推送。

交接摘要必须包含：

1. 读取了哪些 L2 设计文档、Pi0.5 源码、ACT 源码和历史任务。
2. 任务文件身份校验结论。
3. 修改了哪些文件。
4. 新增或修改了哪些函数、class、配置、测试或脚本。
5. 如何验证，实际命令是什么。
6. 哪些成功标准已勾选，哪些未验证。
7. 是否影响 dry-run、fake-policy、real-policy、shadow-run 或 real-robot。
8. 回滚方式。
9. 本次明确没有做什么。
10. 后续建议生成或执行的 L3。

---

## 18. 执行摘要

### 1. 读取的文档

- `DOCS/02_约束/上下文加载/04_L3微元任务执行加载规则.md` -- L3 执行加载规则
- `DOCS/02_约束/编程执行/Agent编程执行原则.md` -- Agent 编程原则
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md` -- 架构边界约束
- `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md` -- 阶段四工作流
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md` -- 产物落点约束
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md` -- L3 任务模板
- `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md` -- L1 功能模块边界
- `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md` -- L1 协作架构
- `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/06_types层设计.md` -- types 层设计
- `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_021_验收卡片.md` -- 验收卡片
- `DOCS/03_工程/阶段四：模型部署/03_tasks/task/dispatch/l2-03-act-inference.yaml` -- dispatch 调度索引
- `src/model_deploy/act/types/action_spec.py` -- ACTION_DIM 常量来源

### 2. 任务文件身份校验结论

全部通过。用户指定路径、实际读取路径、文件名编号 deploy_021、正文 L3 编号 deploy_021、dispatch.task_id deploy_021 一致。所属 L2 ID l2-03-act-inference 属于新版 L2 白名单，不位于 legacy/archive 目录，当前分支 feat/model_deploy/l2-03-act-inference 符合要求。

### 3. 修改的文件

- `src/model_deploy/act/types/action_chunk.py`（新建）
- `src/model_deploy/act/tests/types/test_action_chunk.py`（新建）

### 4. 新增的 class/函数/测试

- `action_chunk.py`: 新增 `@dataclass(frozen=True) class ActionChunk`，字段 `actions: np.ndarray`，`__post_init__` 包含五项构造校验（ndim==2、shape[1]==16、dtype==float32、全部有限、行数>0）。
- `test_action_chunk.py`: 新增 15 个测试用例，覆盖合法构造、rank 错误、dim 错误、dtype 错误、NaN/Inf、空 chunk、frozen 不可变、无运行元数据字段。

### 5. 验证方式与命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_action_chunk.py -v
```

结果：15 passed in 0.10s，全部通过，无 skip。

### 6. 成功标准勾选情况

全部 12 项成功标准已勾选，其中"真机风险控制说明"标记为不适用（本 L3 不触发真机动作）。

### 7. 对运行模式的影响

不涉及 dry-run、fake-policy、real-policy、shadow-run 或 real-robot。纯类型定义，无运行时依赖。

### 8. 回滚方式

```bash
rm src/model_deploy/act/types/action_chunk.py
rm src/model_deploy/act/tests/types/test_action_chunk.py
# 或：git checkout -- src/model_deploy/act/types/action_chunk.py src/model_deploy/act/tests/types/test_action_chunk.py
```

无配置、无 adapter、无不可自动回滚的人工步骤。

### 9. 本次明确没有做什么

- 未校验 `chunk_size` 精确等于 `DeployConfig.runtime.chunk_size`（属于 service 阶段三）。
- 未添加任何运行元数据字段（obs_time、infer_start_time、request_id、cursor 等）。
- 未添加 `aligned_index`、`is_expired`、`remaining_steps` 等消费逻辑。
- 未修改 `action_spec.py` 语义（仅 import ACTION_DIM 常量，属允许范围）。
- 未修改 `pi05/`、`pi05_old/` 下任何文件。
- 未修改 config/、repo/、service/、runtime/、ui/ 层文件。
- 未修改 dispatch、cards 或 acceptance 目录下其他 L2 的文件。

### 10. 后续建议执行的 L3

- deploy_022（Observation 批次准备）-- wave 2，依赖 deploy_021。
- deploy_023（ActionChunk 后处理）-- wave 2，依赖 deploy_021。
- deploy_022 和 deploy_023 可并行执行（can_run_parallel_with 互指）。
