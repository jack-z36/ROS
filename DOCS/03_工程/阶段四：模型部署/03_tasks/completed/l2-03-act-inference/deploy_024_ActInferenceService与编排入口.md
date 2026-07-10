# L3 微元改造任务：ActInferenceService 与编排入口

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-03-act-inference` ObservationSnapshot 到 ACT ActionChunk 推理闭环
L3 编号：`deploy_024`
改造类型：`source-adaptation`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_024_ActInferenceService与编排入口.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_024_验收卡片.md`
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
  task_id: deploy_024
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_024_ActInferenceService与编排入口.md
  group: l2-03-act-inference
  branch: feat/model_deploy/l2-03-act-inference
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference
  acceptance_scenarios: [S2, S3, S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_024_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/logs
  wave: 3
  parallel_group: l2-03-act-inference-p3
  depends_on: [deploy_021, deploy_022, deploy_023]
  must_run_after: [deploy_022, deploy_023]
  can_run_parallel_with: []
  blocks: [deploy_025]
  conflict_scope:
    files:
      - src/model_deploy/act/service/act_inference.py
      - src/model_deploy/act/tests/service/test_act_inference.py
    modules:
      - model_deploy.act.service.act_inference
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。
- 本 L3 串联 deploy_022 与 deploy_023 的产物，必须确认两个上游 L3 均已完成后再执行。

## 3. 本次唯一目标

```text
实现 ActInferenceService class 与总编排入口 predict_action_chunk()：持有四项只读依赖（config、两个 normalizer、policy），串联一级阶段一（deploy_022）、阶段二（policy 前向）、阶段三（deploy_023），对 L2-06 暴露单一同步调用接口。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 持有 L2-01 注入的四项只读依赖。
- 从 policy RAM 元数据派生输入规格。
- 串联三个一级阶段完成 ObservationSnapshot -> ActionChunk。
- 只调用 `policy.predict_action_chunk(batch)`，不调用 `select_action`。

### L2 不负责

- 不持有请求状态、queue、cursor、metrics 或 fallback。
- 不决定调用时机、线程或排队策略。

### 本 L3 在 L2 中的位置

```text
ActInferenceService 是 L2-03 对 L2-06 的唯一暴露接口。L2-06 创建并持有 service，在自有推理运行轴中同步调用 predict_action_chunk()。本 L3 是 deploy_022、deploy_023 的消费者和串联者。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/03_ACT微元设计与协作.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/09_service层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `Pi05PolicyRuntime` | `pi05/deploy/src/pi05/deploy/models/policy_loader.py` | 编排函数 + 数据 | 持有 config/model/preprocessor/normalizer/device，串联 batch→predict→postprocess | 混合 loader 职责；持有 preprocessor；含 compile/fake 分支 | 结构复用 |
| `predict_action_chunk` 总入口 | 同上 | 编排函数 | 三步串联与异常传播 | L2-03 需更薄编排、更严格阶段分界 | 结构复用 |
| LeRobot `ACTPolicy.predict_action_chunk` | `src/model_deploy/third_party/lerobot/src/lerobot/policies/act/modeling_act.py` | 计算函数 | chunk 前向 | 无 | 直接复用（由 L2-01 加载的 policy 提供） |
| LeRobot `ACTPolicy.select_action` | 同上 | 计算函数 | queue + temporal ensemble 单步消费 | 禁止调用 | 不复用 |

### 必须保留的源码启发

- Pi0.5 的串联顺序（batch → predict → postprocess）正确，保留为三阶段。
- 异常直接向上传播，不在 service 内吞没或 fallback。

### 禁止照搬的源码行为

- `select_action()` 及其内部的 `_action_queue`、`popleft()`、temporal ensemble —— 属于 L2-06 chunk 消费。
- Pi0.5 `Pi05PolicyRuntime` 的 loader/compile/fake 职责 —— 属于 L2-01。
- 任何 request ID、时间记录、metrics 或 retry 逻辑。

### 已知风险

- 必须通过 spy/stub 验证 `predict_action_chunk` 被调用而非 `select_action`。
- service 必须在构造时或首次调用前验证 policy/config/normalizer 契约一致性。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新增 `src/model_deploy/act/service/act_inference.py`。
- 实现 `ActInferenceService` class，持有 `config`、`state_normalizer`、`action_normalizer`、`policy`、派生 `input_spec`。
- 构造时从 policy RAM 元数据派生 `input_spec`（image feature keys、state_dim、action_dim、chunk_size、device）。
- 构造时验证 policy 暴露 `predict_action_chunk`，且 config/normalizer/policy 维度一致。
- 实现总编排入口 `predict_action_chunk(observation: ObservationSnapshot) -> ActionChunk`。
- 实现一级阶段二 `run_act_inference(policy, batch) -> torch.Tensor`，使用 `torch.no_grad()` 保护。
- 串联 deploy_022 的 `prepare_observation_batch` 和 deploy_023 的 `postprocess_action_chunk`。

### 本次不做

- 不重新实现阶段一或阶段三的微元（import 并调用即可）。
- 不实现 fake-policy 分支或 policy 选择逻辑。
- 不记录 request ID、时间、latency 或任何 metrics。

### 明确禁止修改

- `src/model_deploy/act/service/observation_batch.py`（deploy_022 产物，只允许 import）。
- `src/model_deploy/act/service/action_chunk_postprocess.py`（deploy_023 产物，只允许 import）。
- `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物，只允许 import）。
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件。

### 函数 / class 策略

```text
ActInferenceService 封装为 class：四项只读依赖在程序全生命周期稳定存在，被多次同步调用复用。class 只打包依赖和总入口，不拥有运行调度状态。一级阶段二是纯计算函数（不建 class）：没有独立生命周期或可变状态。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只 import） | — | — |
| config | 否（只读引用） | — | — |
| repo | 否 | — | — |
| service | 是 | `src/model_deploy/act/service/act_inference.py` | ActInferenceService + 总编排入口 + 一级阶段二 |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/service/test_act_inference.py` | service 构造、总入口端到端、阶段二 API 选择、异常传播测试 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/09_service层设计.md` | `act_inference.py`：`ActInferenceService` class、`predict_action_chunk` 总编排入口、`run_act_inference` 阶段二 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `service/act_inference.py` | ActInferenceService 数据字段 | 数据 | config + normalizers + policy | 持有只读引用的 service 实例 | 无 | test_act_inference.py::test_construction |
| `service/act_inference.py` | 构造时契约校验 | 计算函数 | 四项依赖 | 通过或异常（维度/API 不一致） | 无 | test_act_inference.py::test_contract_mismatch |
| `service/act_inference.py` | 推理执行上下文 | 计算保护 | — | `torch.no_grad()` 上下文 | 无 | service.policy.predict_chunk |
| `service/act_inference.py` | ACT chunk API 调用 | 计算函数 | loaded policy + batch | raw action tensor | 无 | service.policy.predict_chunk |
| `service/act_inference.py` | 原始结果交接 | 数据边界 | policy return | 未修改 raw tensor 传给阶段三 | 无 | service.policy.predict_chunk |
| `service/act_inference.py` | 总编排入口 | 编排函数 | ObservationSnapshot | ActionChunk 或异常 | 无 | service.full_chain |

## 9. 实施步骤

1. 确认 deploy_021、deploy_022、deploy_023 均已完成且测试通过。
2. 阅读 `agent_context/09_service层设计.md` §3，确认 `ActInferenceService` 字段、总入口和阶段二设计。
3. 新建 `src/model_deploy/act/service/act_inference.py`。
4. 实现 `ActInferenceService.__init__`：保存四项引用，从 policy RAM 元数据派生 `input_spec`，验证维度一致性。
5. 实现 `run_act_inference(policy, batch) -> torch.Tensor`：`torch.no_grad()` 下调用 `policy.predict_action_chunk(batch)`，不处理返回 tensor。
6. 实现 `predict_action_chunk(observation: ObservationSnapshot) -> ActionChunk`：串联阶段一（import deploy_022）、阶段二（本文件）、阶段三（import deploy_023），任一步失败立即向上传播。
7. 编写 `tests/service/test_act_inference.py`：构造测试、维度不一致失败、stub policy 端到端、`select_action` spy 测试、阶段一/二/三分别失败时的异常传播。
8. 运行 `python3 -m pytest src/model_deploy/act/tests/service/test_act_inference.py -v`，全部 PASS。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/service/act_inference.py`（新建）
- `src/model_deploy/act/tests/service/test_act_inference.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| ActInferenceService | `src/model_deploy/act/service/act_inference.py` | service |
| service 单测 | `src/model_deploy/act/tests/service/test_act_inference.py` | tests/service |

## 11. 禁止修改

- `src/model_deploy/act/service/observation_batch.py`（deploy_022 产物）
- `src/model_deploy/act/service/action_chunk_postprocess.py`（deploy_023 产物）
- `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物）
- `src/model_deploy/act/types/` 下其他已有文件
- `src/model_deploy/act/service/` 下其他已有文件
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件
- `src/model_deploy/act/config/`、`repo/`、`runtime/`、`ui/` 下任何文件

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_act_inference.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | service 构造、端到端 stub policy、API 选择、异常传播 | pytest 全部 PASS |
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
对应运行验收场景：S2, S3, S4
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S2（阶段一）、S3（阶段二）、S4（阶段三） |
| 本 L3 提供的运行能力 | 三阶段完整闭环：snapshot → ActionChunk |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/service/test_act_inference.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | 集成 Gate 测试、静态边界扫描、verify 脚本 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py`（`Pi05PolicyRuntime.predict_action_chunk` 串联逻辑）
2. `src/model_deploy/third_party/lerobot/src/lerobot/policies/act/modeling_act.py`（`predict_action_chunk` vs `select_action`）
3. `src/model_deploy/act/service/observation_batch.py`（deploy_022 产物）
4. `src/model_deploy/act/service/action_chunk_postprocess.py`（deploy_023 产物）
5. `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：`deploy_021`（ActionChunk 类型）、`deploy_022`（阶段一）、`deploy_023`（阶段三）
2. 无同组已完成 L3

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：deploy_024
正文 L3 编号：deploy_024
dispatch.task_id：deploy_024
是否一致：
所属 L2 ID：l2-03-act-inference
是否属于新版 L2 白名单：是
是否命中旧 L2 ID：否
是否位于 legacy/archive 目录：否
```

执行前必须确认 `depends_on` 中的 deploy_021、deploy_022、deploy_023 均已完成并通过验收。

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [x] 已完成 Pi0.5 源码盘点中列出的相关代码确认。
- [x] 改动没有越过当前 L2 的责任边界。
- [x] 产物路径符合六层落点约束。
- [x] ActInferenceService 字段只含四项只读依赖 + 派生 input_spec。
- [x] `predict_action_chunk` 被调用，`select_action` 未被调用。
- [x] 两个 normalizer 各在正确阶段调用且各调用一次。
- [x] 三阶段任一步失败时后续阶段不执行，异常原样或带上下文向上传播。
- [x] 已完成本 L3 的自动化验收。
- [x] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [x] 如涉及真机发送链路，已完成真机风险控制说明。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
关闭参数 / 配置：无
切回旧入口：删除 act_inference.py 和 test_act_inference.py
移除 adapter：无
回退文件：git checkout -- src/model_deploy/act/service/act_inference.py src/model_deploy/act/tests/service/test_act_inference.py
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

**任务身份校验**:
- 用户指定路径与读取路径一致
- 文件名编号 deploy_024 与正文、dispatch.task_id 一致
- L2 ID: l2-03-act-inference（白名单通过，非 legacy/archive）
- 分支: feat/model_deploy/l2-03-act-inference（匹配）

**上游依赖确认**:
- deploy_021、deploy_022、deploy_023 均已在 completed 目录归档
- 三个产物文件均存在且通过 import 验证

**产物文件**:
1. `src/model_deploy/act/service/act_inference.py`（新建）
   - `ActInferenceService` class: 持有 `_config/_state_normalizer/_action_normalizer/_policy/_input_spec/_device`，无禁止字段
   - `_derive_input_spec()`: 从 policy RAM 元数据提取 state_dim、camera_keys、image_shapes、action_dim、chunk_size
   - `_validate_contract()`: 验证 policy 暴露 predict_action_chunk，state/action normalizer 维度匹配
   - `_resolve_device()`: 从 policy 参数获取 device，回退到配置
   - `predict_action_chunk()`: 串联阶段一→二→三，无 try/except，异常直接传播
   - `run_act_inference()`: torch.no_grad() 下调用 policy.predict_action_chunk(batch)

2. `src/model_deploy/act/tests/service/test_act_inference.py`（新建）
   - 20 个测试用例，覆盖：
     - 构造测试（valid dependencies、input_spec 派生、metadata 缺失回退）
     - 契约校验（缺失 predict_action_chunk、state/action normalizer 维度不匹配）
     - 实例字段审计（仅允许 6 个字段、禁止字段名扫描）
     - 端到端测试（合法 snapshot → ActionChunk、select_action spy）
     - 失败传播（阶段一/二/三分别注入失败）
     - 异常处理审计（无 try/except、无 return None/zeros）
     - Normalizer 方向和次数（state: normalize x1、action: unnormalize x1）

**验证结果**:
- 自动化验收命令: `PYTHONPATH="src:src/model_deploy/third_party/lerobot/src" python3 -m pytest src/model_deploy/act/tests/service/test_act_inference.py -v`
- 结果: 20 passed, 0 failed, 0 skipped
- 全 service 目录回归: 113 passed

**未修改禁止文件**:
- 未修改 deploy_021 产物: `src/model_deploy/act/types/action_chunk.py`
- 未修改 deploy_022 产物: `src/model_deploy/act/service/observation_batch.py`
- 未修改 deploy_023 产物: `src/model_deploy/act/service/action_chunk_postprocess.py`
- 未修改 pi05/、其他层文件、dispatch 索引

**回滚方式**:
```text
git checkout -- src/model_deploy/act/service/act_inference.py src/model_deploy/act/tests/service/test_act_inference.py
```
