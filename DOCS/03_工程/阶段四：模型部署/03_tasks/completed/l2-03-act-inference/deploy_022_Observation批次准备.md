# L3 微元改造任务：Observation 批次准备（一级阶段一）

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-03-act-inference` ObservationSnapshot 到 ACT ActionChunk 推理闭环
L3 编号：`deploy_022`
改造类型：`source-adaptation`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_022_Observation批次准备.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_022_验收卡片.md`
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
  task_id: deploy_022
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_022_Observation批次准备.md
  group: l2-03-act-inference
  branch: feat/model_deploy/l2-03-act-inference
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference
  acceptance_scenarios: [S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_022_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/logs
  wave: 2
  parallel_group: l2-03-act-inference-p2
  depends_on: [deploy_021]
  must_run_after: [deploy_021]
  can_run_parallel_with: [deploy_023]
  blocks: [deploy_024]
  conflict_scope:
    files:
      - src/model_deploy/act/service/observation_batch.py
      - src/model_deploy/act/tests/service/test_observation_batch.py
    modules:
      - model_deploy.act.service.observation_batch
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
实现一级阶段一 Observation 批次准备：把 ObservationSnapshot 转换为 policy device 上的 ACT batch dict，包含 7 个顺序计算微元（兼容性检查、state tensor 化、state normalize、图像绑定、batch 维、batch 组装、device 对齐）。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 从 snapshot 取得 `encoded_state` 与图像，整理为 ACT policy 所需的 batch。
- 只调用一次 `state_normalizer.normalize()`。

### L2 不负责

- 不做图像像素级预处理（resize、颜色转换、数值归一化），这些由 L2-02 保证。
- 不检查 snapshot freshness。
- 不写 `task`、`action` 或运行元数据到 batch。

### 本 L3 在 L2 中的位置

```text
一级阶段一是 L2-03 内部三阶段流水线的第一阶段。ObservationSnapshot 进入 → 7 个微元顺序执行 → ACT batch dict 产出，供 deploy_024 的阶段二 policy 前向消费。deploy_023（阶段三）与本 L3 可并行开发。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/02_pi05源码3.5层微元拆解.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/03_ACT微元设计与协作.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/07_config层设计.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/09_service层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `_build_batch` | `pi05/deploy/src/pi05/deploy/models/policy_loader.py` `Pi05PolicyRuntime._build_batch` | 计算函数 | state tensor 化、state normalize、图像绑定、batch 组装 | 写了 `task` 字段；调用完整 preprocessor；不检查输入兼容性 | 结构复用 |
| `_move_tensors_to_device` | 同上 `Pi05PolicyRuntime._move_tensors_to_device` | 计算函数 | CPU tensor 到 policy device | 无输入兼容性检查、无 camera key 验证 | 结构复用 |
| LeRobot ACT image features | `src/model_deploy/third_party/lerobot/src/lerobot/policies/act/modeling_act.py` `image_features` | 数据 | policy 声明的必需图像 key 和 shape | 无 | 参考理解 |

### 必须保留的源码启发

- Pi0.5 证明 state tensor 化应在 normalize 之前、batch 维在 device 搬运之前。
- 必须从 policy RAM 元数据派生图像 feature key，按完整 policy key（`observation.images.<camera>`）精确绑定。

### 禁止照搬的源码行为

- Pi0.5 `_build_batch` 写 `task` 字段 —— 当前 ACT 无 task 输入。
- 调用完整 LeRobot ACT preprocessor（含 NormalizerProcessorStep）—— state/action 归一化所有权应显式、独立。
- 按 dict 顺序猜测相机 —— 必须按 policy feature key 精确映射。

### 已知风险

- 若 `ObservationSnapshot.images` 的 key 命名与 policy `image_features` 不完全匹配，绑定将失败；这是正确的契约失败，不应静默回退。
- tensor 化和 normalize 必须是两个独立函数，便于独立区分"输入不能 tensor 化"和"normalizer 计算失败"。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新增 `src/model_deploy/act/service/observation_batch.py`。
- 实现一级阶段一函数 `prepare_observation_batch(snapshot, state_normalizer, input_spec, device) -> dict[str, Tensor]`。
- 内部实现 7 个计算微元，其中 state tensor 表达转换与 state 数值归一化是两个独立可测函数。
- 从 policy RAM 元数据派生 input_spec（image feature keys、shapes、state_dim、device）。
- 使用 `torch.no_grad()` 保护推理上下文。

### 本次不做

- 不构造 `ActInferenceService` class（属于 deploy_024）。
- 不调用 `policy.predict_action_chunk`（属于 deploy_024 阶段二）。
- 不做 action unnormalize 或 ActionChunk 构造（属于 deploy_023）。

### 明确禁止修改

- `src/model_deploy/act/service/` 下其他已有文件。
- `src/model_deploy/act/types/` 下已有文件（除 import `ObservationSnapshot` 和 `ActionChunk` 外）。
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件。

### 函数 / class 策略

```text
一级阶段一使用纯函数，不建 class。7 个微元没有独立生命周期、可变状态或资源所有权；使用函数保持输入输出显式、可独立单测。state tensor 化与 state normalize 拆成两个独立函数以区分不同失败模式。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只 import） | — | — |
| config | 否（只读引用） | — | — |
| repo | 否 | — | — |
| service | 是 | `src/model_deploy/act/service/observation_batch.py` | 一级阶段一 + 7 个输入计算微元 |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/service/test_observation_batch.py` | 7 个微元独立单测 + 阶段一集成测试 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/09_service层设计.md` | `observation_batch.py`：`prepare_observation_batch` 及 7 个计算微元的完整实现 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `service/observation_batch.py` | 模型输入兼容性检查 | 计算函数 | snapshot + input_spec | 通过或异常 | 无 | service.batch.compatibility |
| `service/observation_batch.py` | State tensor 表达转换 | 计算函数 | physical ndarray `(16,)` | CPU float32 Tensor `(16,)` | 无 | service.batch.tensorize_state |
| `service/observation_batch.py` | State 数值归一化 | 计算函数 | state Tensor + state_normalizer | normalized Tensor `(16,)` | 无 | service.batch.normalize_state |
| `service/observation_batch.py` | Image tensor 绑定 | 计算函数 | snapshot images + expected feature keys | `{full_policy_key: Tensor(C,H,W)}` | 无 | service.batch.bind_images |
| `service/observation_batch.py` | Batch 维度添加 | 计算函数 | state/image single-sample tensors | `(1,16)` / `(1,C,H,W)` | 无 | service.batch.add_dimension |
| `service/observation_batch.py` | ACT batch 组装 | 计算函数 | batched state/images | batch dict | 无 | service.batch.assemble |
| `service/observation_batch.py` | Device 对齐 | 计算函数 | CPU batch + policy device | device-aligned batch | 无（产生新 tensor） | service.batch.device |
| `service/observation_batch.py` | 一级阶段一编排 | 编排函数 | snapshot + 依赖 | ACT batch dict | 无 | test_observation_batch.py |

## 9. 实施步骤

1. 阅读 `agent_context/09_service层设计.md` §4，确认 `observation_batch.py` 的完整微元列表和边界。
2. 新建 `src/model_deploy/act/service/observation_batch.py`。
3. 实现 `check_model_input_compatibility(snapshot, input_spec)` —— 检查 state 16D/有限值、必需相机、图像 shape/dtype/数值契约。
4. 实现 `tensorize_state(encoded_state: np.ndarray) -> torch.Tensor` —— physical ndarray 到 CPU float32 tensor。
5. 实现 `normalize_state(state_tensor, state_normalizer) -> torch.Tensor` —— 只调用一次 `normalize()`，检查 shape 和有限值。
6. 实现 `bind_images(snapshot_images, input_spec) -> dict[str, torch.Tensor]` —— 按 policy feature key 精确绑定。
7. 实现 `add_batch_dim(*tensors) -> tuple[torch.Tensor, ...]` —— 为 state 和每张 image 添加 batch 维。
8. 实现 `assemble_act_batch(state_tensor, image_tensors, input_spec) -> dict[str, torch.Tensor]`。
9. 实现 `align_to_device(batch, device) -> dict[str, torch.Tensor]`。
10. 实现一级阶段一编排函数 `prepare_observation_batch(snapshot, state_normalizer, input_spec, device) -> dict[str, torch.Tensor]`。
11. 编写 `tests/service/test_observation_batch.py`：7 个微元独立测试 + 阶段一集成测试，使用 stub normalizer 和 sentinel snapshot。
12. 运行 `python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v`，全部 PASS。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/service/observation_batch.py`（新建）
- `src/model_deploy/act/tests/service/test_observation_batch.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| Observation 批次准备 | `src/model_deploy/act/service/observation_batch.py` | service |
| 阶段一单测 | `src/model_deploy/act/tests/service/test_observation_batch.py` | tests/service |

## 11. 禁止修改

- `src/model_deploy/act/service/` 下其他已有文件
- `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物，只允许 import）
- `src/model_deploy/act/types/` 下其他已有文件
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件
- `src/model_deploy/act/config/`、`repo/`、`runtime/`、`ui/` 下任何文件

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | 7 个微元独立测试 + 阶段一集成 | pytest 全部 PASS |
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
对应运行验收场景：S2
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S2（阶段一：Observation 批次准备） |
| 本 L3 提供的运行能力 | snapshot 到 policy device batch 的完整转换 |
| 本 L3 的局部命令 | `python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v` |
| L2 Gate 仍需后续 L3 补齐的内容 | 阶段二 policy 前向、阶段三后处理、总编排入口、集成 Gate |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/`

### 必读代码

1. `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py`（`_build_batch`、`_move_tensors_to_device`）
2. `src/model_deploy/third_party/lerobot/src/lerobot/policies/act/modeling_act.py`（`image_features`）

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
文件名编号：deploy_022
正文 L3 编号：deploy_022
dispatch.task_id：deploy_022
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
切回旧入口：删除 observation_batch.py 和 test_observation_batch.py
移除 adapter：无
回退文件：git checkout -- src/model_deploy/act/service/observation_batch.py src/model_deploy/act/tests/service/test_observation_batch.py
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

- 执行人: execution sub-agent (l2-03-act-inference)
- 执行时间: 2026-07-10
- 执行分支: `feat/model_deploy/l2-03-act-inference`

### 任务身份校验

| 校验项 | 结果 |
|---|---|
| 用户指定路径 = 实际读取路径 | 一致 |
| 文件名编号 = 正文 L3 编号 = dispatch.task_id | 一致 (deploy_022) |
| 新版 L2 白名单 (l2-03-act-inference) | 是 |
| 旧 L2 ID / legacy / archive | 否 |
| 当前分支 = 所属 L2 分支 | 一致 |

### 产物

| 产物 | 路径 | 层 |
|---|---|---|
| Observation 批次准备 (7 个微元 + 编排) | `src/model_deploy/act/service/observation_batch.py` | service |
| 阶段一单测 (29 个用例) | `src/model_deploy/act/tests/service/test_observation_batch.py` | tests/service |

### 7 个微元实现

1. `check_model_input_compatibility` - state 16D/有限值, 必需相机, 图像 shape/dtype/数值契约
2. `tensorize_state` - physical ndarray 到 CPU float32 tensor
3. `normalize_state` - 调用一次 state_normalizer.normalize(), 检查 shape 和有限值
4. `bind_images` - 按 camera_keys + image_prefix 精确绑定为 policy feature key
5. `add_batch_dim` - state/image 添加 B=1 leading dim
6. `assemble_act_batch` - 组装 observation.state + observation.images.* batch dict
7. `align_to_device` - 全部 tensor 移动到 policy device

### 编排

`prepare_observation_batch(snapshot, state_normalizer, input_spec, device)` 在 `torch.no_grad()` 保护下串行执行 7 个微元。

### 测试结果

```text
python3 -m pytest src/model_deploy/act/tests/service/test_observation_batch.py -v
29 passed in 0.94s
```

覆盖: 7 个微元独立测试 (正路径 + 负路径) + 阶段一集成测试 (正路径 + 异常传播)

### 边界确认

- 未修改 `src/model_deploy/act/service/` 下其他文件
- 未修改 `src/model_deploy/act/types/` 下文件 (仅 import ObservationSnapshot, ActionChunk, ACTION_DIM)
- 未修改 `src/model_deploy/pi05/`、`pi05_old/` 下任何文件
- 未修改 config/、repo/、runtime/、ui/ 下任何文件
- batch dict 不含 task、action 或 runtime metadata keys
- state tensor 化与 normalize 为两个独立可测函数

### 未验证项

- 无（本 L3 自动化验收全部通过, 无 dry-run/fake-policy/real-policy/shadow-run/real-robot 需求）

### 后续 L3

- `deploy_024` (ACT 前向推理 + 总入口 ActInferenceService) 依赖本 L3 产物
- `deploy_023` (ActionChunk 后处理) 可与本 L3 并行, 已有 deploy_021 类型基础
