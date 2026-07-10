# L3 微元改造任务：L2-03 Gate 集成测试与验收脚本

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-03-act-inference` ObservationSnapshot 到 ACT ActionChunk 推理闭环
L3 编号：`deploy_025`
改造类型：`test-coverage`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_025_Gate集成测试与验收脚本.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_025_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/`
验收模式：`direct-local`
辅助验收模式：[`static-review`]
本地验收是否必须：`true`
真机风险等级：`none`
L2 分支：`feat/model_deploy/l2-03-act-inference`
集成分支：`model_deploy`

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_025
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_025_Gate集成测试与验收脚本.md
  group: l2-03-act-inference
  branch: feat/model_deploy/l2-03-act-inference
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference
  acceptance_scenarios: [S1, S2, S3, S4, S5]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_025_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [static-review]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/logs
  wave: 4
  parallel_group: l2-03-act-inference-p4
  depends_on: [deploy_021, deploy_022, deploy_023, deploy_024]
  must_run_after: [deploy_024]
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/tests/integration/test_l2_03_gate.py
      - src/model_deploy/act/scripts/l2_03_verify.sh
    modules: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

### Agent 执行 / 验收边界

- 执行 sub-agent 只负责本 L3 的实现、局部验证和执行摘要。
- 验收 sub-agent 只能读取验收卡片、L3 文件、执行摘要、允许查看的 diff / 日志，并按 `acceptance_mode` 输出结论。
- `FAIL_LOCAL` 反馈最多回到执行 sub-agent 迭代 3 轮；超过 3 轮必须由主 Agent 停止自动推进并要求人工介入。
- 本 L3 是 l2-03-act-inference 的最后一个 L3，完成后 L2 Gate 的所有 required L3 即全部到位。

## 3. 本次唯一目标

```text
实现 L2-03 Gate 集成测试与 `l2_03_verify.sh` 验收脚本：用 stub policy + recording normalizer + sentinel snapshot 证明三阶段闭环成立、边界未被污染，并提供标准化终端输出和退出码。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 三阶段闭环端到端验证。
- 静态边界扫描（无 repo loader、无 runtime worker、无 ROS import、无 safety/smoothing 代码）。

### L2 不负责

- 真实 policy/bundle/ROS/硬件验证。

### 本 L3 在 L2 中的位置

```text
deploy_025 是 l2-03-act-inference L2 Gate 的汇总验收点。deploy_021~004 提供四个独立可测产物，本 L3 把它们组合为一次完整 Gate 验证，产出标准化验收脚本供人类和自动化验收使用。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/04_L2验收机制.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/05_人类验收机制.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| 无直接对应 | — | — | Pi0.5 无独立的 inference-only Gate 测试 | 需从零建立 | 不复用 |

### 必须保留的源码启发

- Pi0.5 测试使用 recording normalizer 和 stub policy 验证推理链是正确的模式，保留。

### 禁止照搬的源码行为

- 无。

### 已知风险

- 集成测试不得依赖真实 bundle 或 GPU；必须全部使用 stub policy 和 recording normalizer。
- 静态边界扫描依赖 `rg`/`grep`，需确认环境中这些工具可用。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新增 `src/model_deploy/act/tests/integration/test_l2_03_gate.py`。
- 新增 `src/model_deploy/act/scripts/l2_03_verify.sh`。
- 集成测试覆盖：合法 snapshot 端到端、两个 normalizer 调用方向与次数、`select_action` 未被调用、阶段一/二/三分別失败时链停止、ActionChunk 无运行元数据。
- 静态边界测试覆盖：无 bundle/checkpoint/path/json/yaml loader、无 Thread/queue/timer/request/cursor/metrics/fallback、无 ROS import/publisher/subscriber、无 clamp/delta/IK/collision/safety 代码、无 blend/smooth/RTC 代码、文件只落在 types/service/tests。
- verify 脚本按 `04_L2验收机制.md §4.2` 的终端输出格式顺序运行所有测试并汇总。

### 本次不做

- 不新增任何源码产物（types/service 等）。
- 不新增 launch 或 config_files 产物。
- 不修改 deploy_021~004 的产物。

### 明确禁止修改

- `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物）。
- `src/model_deploy/act/service/observation_batch.py`（deploy_022 产物）。
- `src/model_deploy/act/service/action_chunk_postprocess.py`（deploy_023 产物）。
- `src/model_deploy/act/service/act_inference.py`（deploy_024 产物）。
- `src/model_deploy/act/tests/types/` 和 `tests/service/` 下已有测试文件。
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件。

### 函数 / class 策略

```text
集成测试使用 pytest fixture + stub policy + recording normalizer。verify 脚本是纯 bash，顺序调用 pytest 并解析退出码。不新增 class。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否 | — | — |
| config | 否 | — | — |
| repo | 否 | — | — |
| service | 否 | — | — |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| launch | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/integration/test_l2_03_gate.py` | 三阶段闭环集成测试 + 静态边界扫描 |
| scripts | 是 | `src/model_deploy/act/scripts/l2_03_verify.sh` | 标准化验收脚本 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/04_L2验收机制.md` | §3.5 三阶段闭环与边界场景、§4 verify.sh 设计需求的完整实现 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `tests/integration/test_l2_03_gate.py` | 三阶段闭环测试 | 编排函数（测试） | stub policy + recording normalizer + sentinel snapshot | PASS/FAIL | 无 | service.full_chain |
| `tests/integration/test_l2_03_gate.py` | 错误链停止测试 | 编排函数（测试） | 各阶段分别失败的 stub | PASS/FAIL | 无 | service.error_stops_chain |
| `tests/integration/test_l2_03_gate.py` | 静态边界扫描 | 编排函数（测试） | 源码文件列表 | PASS/FAIL | 无 | boundary.* |
| `scripts/l2_03_verify.sh` | 验收脚本编排 | 编排函数 | — | 标准化终端输出 + 退出码 | 无 | 全部标签 |

## 9. 实施步骤

1. 确认 deploy_021~004 均已完成且各自单测全部 PASS。
2. 阅读 `agent_context/04_L2验收机制.md` §3.5 和 §4，确认所有 Gate 场景和 verify.sh 输出格式。
3. 新建 `src/model_deploy/act/tests/integration/test_l2_03_gate.py`。
4. 实现 stub policy fixture：暴露 `predict_action_chunk`，返回可控 sentinel 值；`select_action` 设为失败。
5. 实现 recording normalizer fixture：记录 `normalize`/`unnormalize` 调用次数和参数。
6. 实现 `test_full_chain`：合法 snapshot + recording normalizer + deterministic stub policy → ActionChunk 契约验证。
7. 实现 `test_error_stops_chain`：阶段一/二/三分别注入失败，验证后续阶段不执行、无部分输出。
8. 实现 `test_select_action_not_called`：stub policy 的 `select_action` 设为 `raise`，验证总入口仍通过。
9. 实现 `test_normalizer_call_direction_and_count`：验证 state normalizer 只调 `normalize`、action normalizer 只调 `unnormalize`、各一次。
10. 实现静态边界测试类 `TestBoundary`：`test_no_resource_io`、`test_no_runtime_state`、`test_no_ros_or_hardware`、`test_no_safety_or_smoothing`、`test_only_allowed_layers`。
11. 新建 `src/model_deploy/act/scripts/l2_03_verify.sh`。
12. 脚本按 `04_L2验收机制.md §4.2` 格式输出，顺序运行类型/service/集成/边界测试，使用标签映射表输出 PASS/FAIL/BLOCKED，汇总退出码。
13. 运行 `bash src/model_deploy/act/scripts/l2_03_verify.sh`，确认全部 PASS 且退出码为 0。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/tests/integration/test_l2_03_gate.py`（新建）
- `src/model_deploy/act/scripts/l2_03_verify.sh`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| Gate 集成测试 | `src/model_deploy/act/tests/integration/test_l2_03_gate.py` | tests/integration |
| 验收脚本 | `src/model_deploy/act/scripts/l2_03_verify.sh` | scripts |

## 11. 禁止修改

- `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物）
- `src/model_deploy/act/service/observation_batch.py`（deploy_022 产物）
- `src/model_deploy/act/service/action_chunk_postprocess.py`（deploy_023 产物）
- `src/model_deploy/act/service/act_inference.py`（deploy_024 产物）
- `src/model_deploy/act/tests/types/` 和 `tests/service/` 下已有测试文件
- `src/model_deploy/pi05/`、`pi05_old/` 下任何文件
- `src/model_deploy/act/config/`、`repo/`、`runtime/`、`ui/`、`launch/` 下任何文件

## 12. 验证方式

### 自动化验收命令

```bash
bash src/model_deploy/act/scripts/l2_03_verify.sh
```

等价于运行全部类型/service/集成/边界测试并汇总。

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | 全部 pytest 通过 + 静态边界扫描通过 | verify.sh 退出码 0，无 FAIL |
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
对应运行验收场景：S1, S2, S3, S4, S5
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1（类型契约）、S2（阶段一）、S3（阶段二）、S4（阶段三）、S5（三阶段闭环与边界） |
| 本 L3 提供的运行能力 | 完整 L2-03 Gate 验收：三阶段闭环 + 静态边界扫描 + 标准化验收脚本 |
| 本 L3 的局部命令 | `bash src/model_deploy/act/scripts/l2_03_verify.sh` |
| L2 Gate 仍需后续 L3 补齐的内容 | 无。本 L3 是 l2-03-act-inference 的最后一个 L3 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/04_L2验收机制.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/05_人类验收机制.md`

### 必读代码

1. `src/model_deploy/act/types/action_chunk.py`（deploy_021 产物）
2. `src/model_deploy/act/service/observation_batch.py`（deploy_022 产物）
3. `src/model_deploy/act/service/action_chunk_postprocess.py`（deploy_023 产物）
4. `src/model_deploy/act/service/act_inference.py`（deploy_024 产物）
5. `src/model_deploy/act/tests/types/test_action_chunk.py`（deploy_021 产物）
6. `src/model_deploy/act/tests/service/test_observation_batch.py`（deploy_022 产物）
7. `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py`（deploy_023 产物）
8. `src/model_deploy/act/tests/service/test_act_inference.py`（deploy_024 产物）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：`deploy_021`、`deploy_022`、`deploy_023`、`deploy_024`
2. 无同组已完成 L3

## 14. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：deploy_025
正文 L3 编号：deploy_025
dispatch.task_id：deploy_025
是否一致：
所属 L2 ID：l2-03-act-inference
是否属于新版 L2 白名单：是
是否命中旧 L2 ID：否
是否位于 legacy/archive 目录：否
```

执行前必须确认 `depends_on` 中的 deploy_021~004 均已完成并通过验收。

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认所属 L2 ID 属于新版 L2 白名单，且任务不位于 legacy/archive 目录。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取当前 L2 功能边界、Pi0.5 源码 3.5 层微元拆解、ACT 微元设计、L2 验收机制、人类验收机制与六层设计文档。
- [x] `test_full_chain`：stub policy + recording normalizer + sentinel snapshot → 合法 ActionChunk。
- [x] `test_error_stops_chain`：各阶段失败时链停止，无部分输出。
- [x] `test_select_action_not_called`：stub policy 的 `select_action` 未被调用。
- [x] `test_normalizer_call_direction_and_count`：两个 normalizer 调用方向与次数正确。
- [x] 静态边界测试全部 PASS：无 resource I/O、无 runtime state、无 ROS/hardware、无 safety/smoothing、文件只在 types/service/tests。
- [x] `l2_03_verify.sh` 输出符合 `04_L2验收机制.md §4.2` 格式。
- [x] `l2_03_verify.sh` 退出码为 0（全部 PASS，仅真实 policy 可 BLOCKED）。
- [x] 已完成本 L3 的自动化验收。
- [x] 已确认本 L3 的验收卡片、验收模式和本地验收边界。
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [x] 如涉及真机发送链路，已完成真机风险控制说明。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
关闭参数 / 配置：无
切回旧入口：删除 test_l2_03_gate.py 和 l2_03_verify.sh
移除 adapter：无
回退文件：git checkout -- src/model_deploy/act/tests/integration/test_l2_03_gate.py src/model_deploy/act/scripts/l2_03_verify.sh
不可自动回滚的人工步骤：无
```

## 17. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 所属 L2 的 `05_acceptance/l2-03-act-inference/验收结果.md`：登记本 L3 贡献的运行验收场景、实际命令、测试输入、观察点、通过/失败现象、证据链接、未验证项和是否影响 L2 Gate。
- 对应 L3 验收卡片：供验收 agent 独立评估；执行 agent 不得自行改验收结论。
- 不得擅自更新阶段级 `当前进度.md` 或共享 `执行记录.md`。
- 执行 sub-agent 完成单个 L3 后不得自行提交或推送。

交接摘要必须包含：

1. 读取了哪些 L2 设计文档、Pi0.5 源码、ACT 源码和历史任务。
2. 任务文件身份校验结论。
3. 修改了哪些文件。
4. 新增或修改了哪些函数、class、配置、测试或脚本。
5. 如何验证，实际命令是什么（`bash src/model_deploy/act/scripts/l2_03_verify.sh`）。
6. 哪些成功标准已勾选，哪些未验证。
7. 是否影响 dry-run、fake-policy、real-policy、shadow-run 或 real-robot。
8. 回滚方式。
9. 本次明确没有做什么。
10. 本 L3 是 l2-03-act-inference 的最后一个 L3，后续应进入 L2 Gate 验收与人类验收流程。

## 18. 执行摘要

### 执行日期

2026-07-10

### 1. 读取的设计文档与源码

L2 设计文档：
- `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
- `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
- `DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/agent_context/00_INDEX.md`
- `agent_context/01_L2功能边界.md`
- `agent_context/02_pi05源码3.5层微元拆解.md`
- `agent_context/03_ACT微元设计与协作.md`
- `agent_context/04_L2验收机制.md`
- `agent_context/05_人类验收机制.md`
- `agent_context/06_types层设计.md` 至 `agent_context/11_ui层设计.md`

ACT 源码：
- `src/model_deploy/act/types/action_chunk.py`（deploy_021）
- `src/model_deploy/act/service/observation_batch.py`（deploy_022）
- `src/model_deploy/act/service/action_chunk_postprocess.py`（deploy_023）
- `src/model_deploy/act/service/act_inference.py`（deploy_024）

已有测试（了解 fixture 和 stub 模式）：
- `src/model_deploy/act/tests/types/test_action_chunk.py`
- `src/model_deploy/act/tests/service/test_observation_batch.py`
- `src/model_deploy/act/tests/service/test_action_chunk_postprocess.py`
- `src/model_deploy/act/tests/service/test_act_inference.py`

约束文档：
- `DOCS/02_约束/编程执行/Agent编程执行原则.md`
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`
- `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

### 2. 任务文件身份校验

```
用户指定任务路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_025_Gate集成测试与验收脚本.md
实际读取任务路径：DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_025_Gate集成测试与验收脚本.md
文件名编号：deploy_025
正文 L3 编号：deploy_025
dispatch.task_id：deploy_025
是否一致：是
所属 L2 ID：l2-03-act-inference
是否属于新版 L2 白名单：是
是否命中旧 L2 ID：否
是否位于 legacy/archive 目录：否
当前分支：feat/model_deploy/l2-03-act-inference -- 匹配 L2 分支规范
前置依赖 deploy_021~024 的测试全部 PASS（103/103）：是
```

### 3. 修改的文件

- `src/model_deploy/act/tests/integration/test_l2_03_gate.py`（**新建**）
- `src/model_deploy/act/scripts/l2_03_verify.sh`（**新建**）

### 4. 新增的函数、class、测试和脚本

**test_l2_03_gate.py**（19 个测试用例）：
- `TestFullChain`（5 个测试）：三阶段闭环、sentinel 值传递、normalizer 调用方向与次数、select_action 未调用、ActionChunk 无运行元数据
- `TestErrorStopsChain`（8 个测试）：stage1/2/3 分别失败时链停止、no-repair（longer/shorter/2D/NaN 输出均被拒绝）
- `TestBoundary`（6 个测试）：no_resource_io、no_runtime_state、no_ros_or_hardware、no_safety_or_smoothing、only_allowed_layers、source_files_exist

辅助函数：
- `StubPolicy` / `StubPolicyWithRaisingSelectAction` / `WrongShapePolicy` / `WrongDimPolicy`：确定性 stub policy
- `RecordingNormalizer`：记录调用方向与次数的 normalizer wrapper
- `_strip_docstrings_and_comments`：用于边界扫描的源文本清理
- `_check_forbidden_imports`：基于 AST 的 import 检查

**l2_03_verify.sh**（bash 验收脚本）：
- 顺序运行 types / config+repo / service / integration / boundary 五组测试
- 每行输出格式：`PASS|FAIL  <label>  <description>`
- FAIL 行紧随 pytest 路径和错误摘要
- 末尾汇总 `N PASS / N FAIL / N BLOCKED`
- 退出码 0（全部 PASS）或 1（有 FAIL）

### 5. 验证命令与结果

```bash
bash src/model_deploy/act/scripts/l2_03_verify.sh
```

结果：
```
28 PASS / 0 FAIL / 0 BLOCKED  (共 28 标签)
Exit code: 0
```

覆盖标签：
- types: `types.action_chunk_contract`
- config/repo: `boundary.reuse_only`
- service: `service.batch.tensorize_state`, `service.batch.normalize_state`, `service.batch.bind_images`, `service.batch.add_dimension`, `service.batch.assemble`, `service.batch.device`, `service.policy.predict_chunk`, `service.policy.error_propagation`, `service.output.raw_shape`, `service.output.unbatch`, `service.output.unnormalize`, `service.output.float32_cpu`, `service.output.final_contract`, `service.output.no_repair`, `service.full_chain`, `service.policy.no_select_action`, `service.observation_batch_full`, `service.postprocess_full`, `service.inference_full`
- integration: `service.error_stops_chain`, `gate.full_chain`
- boundary: `boundary.no_resource_io`, `boundary.no_runtime_state`, `boundary.no_ros_or_hardware`, `boundary.no_safety_or_smoothing`, `boundary.only_allowed_layers`

### 6. 成功标准（全部已勾选）

所有 16 项成功标准均已验证通过。

### 7. 是否影响 dry-run / fake-policy / real-policy / shadow-run / real-robot

否。本 L3 仅新增测试和验收脚本，不修改任何运行时代码。真机风险等级 `none`，不触发真机动作。

### 8. 回滚方式

```bash
git checkout -- src/model_deploy/act/tests/integration/test_l2_03_gate.py src/model_deploy/act/scripts/l2_03_verify.sh
```

### 9. 本次明确没有做什么

- 没有修改 deploy_021~024 的任何产物文件（types/action_chunk.py、service/observation_batch.py、service/action_chunk_postprocess.py、service/act_inference.py）
- 没有修改已有测试文件
- 没有新增任何源码产物（types/service 等）
- 没有新增 launch 或 config_files 产物
- 没有依赖真实 bundle、GPU 或 ROS
- 没有修改 `src/model_deploy/pi05/` 或 `pi05_old/` 下任何文件

### 10. 后续建议

本 L3 是 l2-03-act-inference 的最后一个 L3。deploy_021~025 全部实现完成且 Gate 测试全部 PASS。建议：
1. 运行验收卡片（`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-act-inference/deploy_025_验收卡片.md`）确认 PASS_LOCAL。
2. 进入 L2 Gate 验收（`l2-03-act-inference_整体验收卡片.md`）。
3. 进入人类验收流程，按 `agent_context/05_人类验收机制.md` 执行人工审查并签字。
