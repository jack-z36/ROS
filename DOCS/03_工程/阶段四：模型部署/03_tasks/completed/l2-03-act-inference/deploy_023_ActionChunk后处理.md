# L3 微元改造任务：ActionChunk 后处理（一级阶段三）

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-03-act-inference` ObservationSnapshot 到 ACT ActionChunk 推理闭环
L3 编号：`deploy_023`
改造类型：`source-adaptation`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_023_ActionChunk后处理.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_023_验收卡片.md`
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
  task_id: deploy_023
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_023_ActionChunk后处理.md
  group: l2-03-act-inference
  branch: feat/model_deploy/l2-03-act-inference
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference
  acceptance_scenarios: [S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_023_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/logs
  wave: 2
  parallel_group: l2-03-act-inference-p2
  depends_on: [deploy_021]
  must_run_after: [deploy_021]
  can_run_parallel_with: [deploy_022]
  blocks: [deploy_024]
  conflict_scope:
    files:
      - src/model_deploy/act/service/action_chunk_postprocess.py
      - src/model_deploy/act/tests/service/test_action_chunk_postprocess.py
    modules:
      - model_deploy.act.service.action_chunk_postprocess
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。

## 3. 本次唯一目标

```text
实现一级阶段三 ActionChunk 后处理：把 policy 返回的 raw normalized action tensor 经 6 个顺序计算微元（raw 结构检查、unbatch、action unnormalize、CPU float32 转换、最终契约检查、ActionChunk 构造）转换为只含 physical actions 的 ActionChunk。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 严格验证 raw policy 输出的 rank、batch、chunk 和 action 维度。
- 只调用一次 `action_normalizer.unnormalize()` 恢复物理尺度。
- 转成 CPU contiguous `np.ndarray float32`，最终构造 `ActionChunk`。

### L2 不负责

- 不 clamp、crop、pad、repeat、reorder 模型输出。
- 不做 quaternion 归一化、gripper clamp 或 TCP delta 限制（属于 L2-04）。
- 不记录运行元数据。

### 本 L3 在 L2 中的位置

```text
一级阶段三是 L2-03 内部三阶段流水线的最后阶段。deploy_024 的阶段二 policy 前向产出 raw tensor → 本 L3 的 6 个微元顺序执行 → ActionChunk 产出，供 L2-06 消费。deploy_022（阶段一）与本 L3 可并行开发。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/02_pi05源码3.5层微元拆解.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/03_ACT微元设计与协作.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/06_types层设计.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/09_service层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| unbatch + unnormalize + array | `pi05/deploy/src/pi05/deploy/models/policy_loader.py` `Pi05PolicyRuntime.predict_action_chunk` | 计算函数 | detach/CPU/float32、取 batch[0]、action unnormalize、shape 检查、np.ndarray | 包含 normalized action clamp 和 `[:output_chunk_size]` 截断，必须剥离 | 结构复用 |
| ActionChunk 构造 | `pi05/deploy/src/pi05/deploy/runtime/inference_worker.py` `ActionChunk` | 数据构造 | 构造含时间字段的 chunk | 必须去掉时间字段 | 结构复用 |

### 必须保留的源码启发

- raw tensor 先检查结构（B=1、N=chunk_size、D=16），再 unbatch，再 unnormalize。
- 最终输出固定为 numpy float32。
- 全部步骤成功后才构造 chunk。

### 禁止照搬的源码行为

- `torch.clamp(normalized_action, -1, 1)` —— 不修补模型输出。
- `action_chunk[:output_chunk_size]` —— 不对过长输出截断、不对过短输出补齐。
- Pi0.5 的 `obs_time`、`infer_start_time`、`ready_time` 等运行元数据字段。

### 已知风险

- raw 输出 shape 不匹配时必须拒绝，不得 squeeze 任意维或假设维度顺序。
- action unnormalize 失败时不得把 normalized action 当作 physical action 返回。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新增 `src/model_deploy/act/service/action_chunk_postprocess.py`。
- 实现一级阶段三函数 `postprocess_action_chunk(raw_chunk, action_normalizer, expected_chunk_size) -> ActionChunk`。
- 内部实现 6 个计算微元，每个微元独立可测。
- 导入 deploy_021 定义的 `ActionChunk`。
- 从 `DeployConfig` 读取 `runtime.chunk_size` 做严格相等校验。

### 本次不做

- 不构造 `ActInferenceService` class（属于 deploy_024）。
- 不做 state normalize 或 batch 准备（属于 deploy_022）。
- 不调用 policy 前向（属于 deploy_024 阶段二）。

### 明确禁止修改

- `src/model_deploy/act/service/` 下其他已有文件。
- `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物，只允许 import）。
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件。

### 函数 / class 策略

```text
一级阶段三使用纯函数，不建 class。6 个微元没有独立生命周期或可变状态。raw 结构检查、unbatch、unnormalize、CPU 转换、最终契约检查和 ActionChunk 构造都是纯计算/数据构造，每条可独立单测。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只 import） | — | — |
| config | 否（只读引用） | — | — |
| repo | 否 | — | — |
| service | 是 | `src/model_deploy/act/service/action_chunk_postprocess.py` | 一级阶段三 + 6 个输出微元 |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py` | 6 个微元独立单测 + 阶段三集成测试 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/09_service层设计.md` | `action_chunk_postprocess.py`：`postprocess_action_chunk` 及 6 个计算微元的完整实现 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `service/action_chunk_postprocess.py` | Raw 输出结构检查 | 计算函数 | policy return value | 合法 `(1,N,16)` Tensor 或异常 | 无 | service.output.raw_shape |
| `service/action_chunk_postprocess.py` | Batch 维移除 | 计算函数 | `(1,N,16)` Tensor | `(N,16)` Tensor | 无 | service.output.unbatch |
| `service/action_chunk_postprocess.py` | Action 反归一化 | 计算函数 | normalized `(N,16)` + action_normalizer | physical `(N,16)` Tensor | 无 | service.output.unnormalize |
| `service/action_chunk_postprocess.py` | CPU float32 array 转换 | 计算函数 | physical Tensor | contiguous CPU `np.ndarray float32` | 无 | service.output.float32_cpu |
| `service/action_chunk_postprocess.py` | 最终输出契约检查 | 计算函数 | physical array + expected N | 合法 array 或异常 | 无 | service.output.final_contract |
| `service/action_chunk_postprocess.py` | ActionChunk 构造 | 数据构造 | validated physical array | `ActionChunk` | 无 | service.output.no_repair |
| `service/action_chunk_postprocess.py` | 一级阶段三编排 | 编排函数 | raw_chunk + 依赖 | ActionChunk | 无 | test_action_chunk_postprocess.py |

## 9. 实施步骤

1. 阅读 `agent_context/09_service层设计.md` §5，确认 `action_chunk_postprocess.py` 的完整微元列表和边界。
2. 确认 deploy_021 的 `ActionChunk` 已可用（`from model_deploy.act.types.action_chunk import ActionChunk`）。
3. 新建 `src/model_deploy/act/service/action_chunk_postprocess.py`。
4. 实现 `check_raw_output_structure(raw_output, expected_chunk_size) -> torch.Tensor` —— 类型为 Tensor、rank=3、B=1、N=chunk_size、D=16、有限值。
5. 实现 `remove_batch_dim(tensor_1_N_16: torch.Tensor) -> torch.Tensor` —— 只移除已验证 B=1 维。
6. 实现 `unnormalize_actions(normalized: torch.Tensor, action_normalizer) -> torch.Tensor` —— 只调用一次 `unnormalize()`。
7. 实现 `to_cpu_float32_array(tensor: torch.Tensor) -> np.ndarray` —— contiguous CPU float32。
8. 实现 `check_final_output_contract(array: np.ndarray, expected_chunk_size: int) -> None` —— 严格 shape/dtype/有限值。
9. 实现一级阶段三编排函数 `postprocess_action_chunk(raw_chunk, action_normalizer, expected_chunk_size) -> ActionChunk`。
10. 编写 `tests/service/test_action_chunk_postprocess.py`：6 个微元独立测试 + 阶段三集成测试，使用 recording action normalizer 和 sentinel raw tensor。
11. 运行 `python3 -m pytest src/model_deploy/act/tests/service/test_action_chunk_postprocess.py -v`，全部 PASS。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/service/action_chunk_postprocess.py`（新建）
- `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| ActionChunk 后处理 | `src/model_deploy/act/service/action_chunk_postprocess.py` | service |
| 阶段三单测 | `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py` | tests/service |

## 11. 禁止修改

- `src/model_deploy/act/service/` 下其他已有文件
- `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物，只允许 import）
- `src/model_deploy/act/types/` 下其他已有文件
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件
- `src/model_deploy/act/config/`、`repo/`、`runtime/`、`ui/` 下任何文件

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_action_chunk_postprocess.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | 6 个微元独立测试 + 阶段三集成 | pytest 全部 PASS |
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
对应运行验收场景：S4
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S4（阶段三：ActionChunk 后处理） |
| 本 L3 提供的运行能力 | raw normalized tensor 到 physical ActionChunk 的完整转换 |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/service/test_action_chunk_postprocess.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | 总编排入口、集成 Gate 测试、verify 脚本 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py`（unbatch/unnormalize/array 段）
2. `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：`deploy_021`（ActionChunk 类型）
2. 无同组已完成 L3

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：deploy_023
正文 L3 编号：deploy_023
dispatch.task_id：deploy_023
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
- [x] 如涉及真机发送链路，已完成真机风险控制说明。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
关闭参数 / 配置：无
切回旧入口：删除 action_chunk_postprocess.py 和 test_action_chunk_postprocess.py
移除 adapter：无
回退文件：git checkout -- src/model_deploy/act/service/action_chunk_postprocess.py src/model_deploy/act/tests/service/test_action_chunk_postprocess.py
不可自动回滚的人工步骤：无
```

## 17. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 所属 L2 的 `05_acceptance/l2-03-act-inference/验收结果.md`：登记本 L3 贡献。
- 对应 L3 验收卡片：供验收 agent 独立评估。
- 不得擅自更新阶段级 `当前进度.md` 或共享 `执行记录.md`。
- 执行 sub-agent 完成单个 L3 后不得自行提交或推送。

## 18. 执行摘要

**执行时间**: 2026-07-10

**执行结果**: PASS

**改动清单**:

| 文件 | 操作 | 行数 |
|---|---|---|
| `src/model_deploy/act/service/action_chunk_postprocess.py` | 新建 | ~155 |
| `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py` | 新建 | ~250 |

**实现内容**:

一级阶段三 `postprocess_action_chunk(raw_chunk, action_normalizer, expected_chunk_size) -> ActionChunk` 及其 6 个计算微元:

1. `check_raw_output_structure` -- 验证 raw tensor 为 finite `(1, N, 16)` tensor，rank/B/N/D/finiteness 逐项检查
2. `remove_batch_dim` -- 移除已验证 B=1 维，`(1, N, 16) -> (N, 16)`
3. `unnormalize_actions` -- 调用 `action_normalizer.unnormalize()` 精确一次，恢复物理尺度
4. `to_cpu_float32_array` -- 转换为 contiguous C-order numpy float32
5. `check_final_output_contract` -- 严格 shape/dtype/finite 输出契约检查
6. `ActionChunk` 构造 -- 将 validated array 包装为 `ActionChunk`

明确禁止的行为已全部落实: 无 clamp/crop/pad/repeat/reorder，无 quaternion/gripper 修正，不截断过长输出、不补齐过短输出，无运行元数据字段。

**测试覆盖**:

39 个测试全部 PASS (6 个微元独立测试 class + 1 个集成测试 class):

- `TestCheckRawOutputStructure`: 8 tests (pass + 7 failure modes)
- `TestRemoveBatchDim`: 3 tests (correct shape/values/dtype)
- `TestUnnormalizeActions`: 5 tests (single call, shape, float32, identity, no-clamp)
- `TestToCpuFloat32Array`: 5 tests (tensor/numpy/type conv/contiguous)
- `TestCheckFinalOutputContract`: 7 tests (pass + 6 failure modes)
- `TestPostprocessActionChunk`: 11 tests (happy path, normalizer call count, 4 error propagation, no-clamp, no-truncate, no-fill, no-runtime-fields, finiteness, shape variants)

**验收命令**:

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_action_chunk_postprocess.py -v
```

**未验收项**: 无 (本 L3 不涉及真机硬件、dry-run、fake-policy、real-policy、shadow-run、real-robot)

**依赖**: deploy_021 (ActionChunk 类型) -- 已验证可用

**回滚**: 删除两个新建文件或 `git checkout --` 两个文件路径即可。
