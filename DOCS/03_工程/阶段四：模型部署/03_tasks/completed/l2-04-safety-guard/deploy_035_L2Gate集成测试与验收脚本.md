# L3 微元改造任务：L2-04 Gate 集成测试与验收脚本

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-04-safety-guard` 单步 Action 安全检查闭环
L3 编号：deploy_035
改造类型：`test-coverage`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_035_L2Gate集成测试与验收脚本.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_035_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/`
验收模式：`direct-local`
辅助验收模式：[`static-review`]
本地验收是否必须：`true`
真机风险等级：`none`
L2 分支：`feat/model_deploy/l2-04-safety-guard`
集成分支：`model_deploy`

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_035
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_035_L2Gate集成测试与验收脚本.md
  group: l2-04-safety-guard
  branch: feat/model_deploy/l2-04-safety-guard
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard
  acceptance_scenarios: [S1, S2, S3, S4, S5]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_035_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: [static-review]
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs
  wave: 4
  parallel_group: l2-04-safety-guard-p4
  depends_on: [deploy_031, deploy_032, deploy_033, deploy_034]
  must_run_after: [deploy_034]
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - src/model_deploy/act/tests/integration/test_l2_04_gate.py
      - DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh
    modules: []
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
- 本 L3 是 l2-04-safety-guard 的最后一个 L3，完成后 L2 Gate 的所有 required L3 即全部到位。

## 3. 本次唯一目标

```text
实现 L2-04 mock Gate 集成测试与 l2_04_verify.sh：用 mock RAM 覆盖全部验证标签，证明 PASS/ADJUSTED/REJECTED 与边界纯度，输出标准化分层结果。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 在无 ROS、无硬件环境下用 mock 证明完整 safety service 闭环。
- 静态确认 service 不 import runtime/ui/ROS/hardware/repo loader。

### L2 不负责

- 真机可达、IK、碰撞、急停、F100 寄存器（属 L2-05 / real-robot）。

### 本 L3 在 L2 中的位置

```text
L2 Gate 汇总点。deploy_031~034 提供 types/config/primitives/orchestration；本 L3 组合为一次完整 Gate 验证，并产出人类与自动化共用的 verify 脚本。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/04_L2验收机制.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/05_人类验收机制.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/09_service层设计.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/10_runtime层设计.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/11_ui层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| 无直接对应 Gate | — | — | Pi0.5 无独立 L2-04 mock Gate 脚本 | 需从零建立标签化输出 | 不复用 |

### 必须保留的源码启发

- 无。

### 禁止照搬的源码行为

- 不得依赖真机或 ROS 才能跑核心 Gate。

### 已知风险

- 核心 C/B 标签不得因缺环境标 BLOCKED；缺环境只能出现在明确可选补验项。
- verify 输出格式必须可被人类与 Agent 解析。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 新建 `src/model_deploy/act/tests/integration/test_l2_04_gate.py`，覆盖 `04_L2验收机制.md` §3 全部标签：
  - TYPES-RESULT、INPUT-SHAPE、INPUT-FINITE、QUAT-CANDIDATE
  - REFERENCE-ORDER、REFERENCE-BOOTSTRAP、REFERENCE-MISSING
  - POSE-TRANSLATION、POSE-ROTATION
  - GRIPPER-RANGE、GRIPPER-STEP
  - BIMANUAL-ASSEMBLY、OUTPUT-INVARIANT、RESULT-STATUS
  - PURITY-IMPORT
- 新建验收脚本：
  ```text
  DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh
  ```
  按 `types / config / repo / service / runtime / ui / boundary` 分组输出：
  ```text
  PASS|FAIL|BLOCKED  LABEL  简短说明
    file: ... / class: ... / micro-unit: B? or C? / pytest: ... / error: ...
  SUMMARY: N PASS / N FAIL / N BLOCKED
  ```
- 任一 FAIL 退出非零。
- 可选：初始化 `05_acceptance/l2-04-safety-guard/验收结果.md` 骨架。

### 本次不做

- 不修改 deploy_031~034 的实现语义（测试失败应修测试或回退到对应 L3，不得在 Gate 任务中“顺手改算法”扩大范围，除非最小修复且在摘要中声明）。
- 不新增 launch、不接 ROS、不接硬件。

### 明确禁止修改

- `src/model_deploy/pi05/`、`pi05_old/`
- 其他 L2 的 task/dispatch/cards
- 把 verify 脚本放到与声明不符的路径

### 函数 / class 策略

```text
集成测试使用 pytest + mock ActionSpec/ObservationSnapshot/SafetyConfig。verify 为 bash，顺序调用 pytest 并汇总。不新增生产 Class。
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
| tests | 是 | `src/model_deploy/act/tests/integration/test_l2_04_gate.py` | Gate 集成 |
| acceptance | 是 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh` | 统一验收脚本 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/04_L2验收机制.md` | 全部标签的可执行 Gate |
| `agent_context/08_repo层设计.md` | PURITY：不 import repo loader |
| `agent_context/10_runtime层设计.md` | 无 runtime 产物 |
| `agent_context/11_ui层设计.md` | 无 ROS/hardware import |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `tests/integration/test_l2_04_gate.py` | Gate 场景用例 | 编排（测试） | mock RAM 输入 | PASS/FAIL | 写测试过程变量 | 全部标签 |
| `l2_04_verify.sh` | 分层汇总脚本 | 编排（脚本） | pytest 退出码 | 标准化终端输出 | 进程退出码 | 人类验收 |

## 9. 实施步骤

1. 对照 `04_L2验收机制.md` §3 建立标签→测试函数映射表。
2. 编写 integration 测试，复用 deploy_034 的 A1 入口。
3. 实现 `l2_04_verify.sh` 分层输出与 SUMMARY。
4. 本地运行 verify，确认退出码 0 且无 FAIL。
5. 登记验收结果骨架。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/tests/integration/test_l2_04_gate.py`（新建）
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh`（新建）
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md`（新建或更新骨架）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| Gate 集成测试 | `src/model_deploy/act/tests/integration/test_l2_04_gate.py` | tests/integration |
| 验收脚本 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh` | acceptance/scripts |

## 11. 禁止修改

- 无正当理由不得改 deploy_031~034 生产语义
- `src/model_deploy/pi05/`、`pi05_old/`
- 其他 L2 目录

## 12. 验证方式

### 自动化验收命令

```bash
bash "DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | 通过 verify 串联 types/config/service 测试 | 核心标签 PASS |
| mock gate | 是 | 全标签 | 无 FAIL；核心项无 BLOCKED |
| dry-run | 可选 | L2-06 mock 调 B1 | 非本 L3 必过 |
| shadow-run | 否 | 下游 L2-05 | hardware-blocked / 下游 |
| real-robot | 否 | — | hardware-blocked |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs/
对应运行验收场景：S1, S2, S3, S4, S5
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S1-S5 全量 |
| 本 L3 提供的运行能力 | 可一键执行的 L2-04 mock Gate |
| 本 L3 的局部命令 | `bash .../l2_04_verify.sh` |
| L2 Gate 仍需后续 L3 补齐的内容 | 无（本 L2 required L3 完成）；下游 shadow/real-robot 属 L2-05/人类验收 |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/04_L2验收机制.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/05_人类验收机制.md`
3. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

### 必读代码

1. `src/model_deploy/act/service/safety_guard.py`
2. `src/model_deploy/act/types/safety_result.py`
3. `src/model_deploy/act/tests/service/test_safety_guard.py`
4. （参考格式）`src/model_deploy/act/scripts/l2_03_verify.sh` 或 L2-01/02 同类脚本

### 相关历史任务或执行记录

1. 直接上游：`deploy_031`~`deploy_034`
2. 同组全部前置 L3

## 14. 执行要求

- 身份校验三处一致。
- 四个上游完成后开工。
- 不得用 BLOCKED 伪装核心标签 PASS。

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] integration 测试覆盖 `04` §3 全部核心标签。
- [x] `l2_04_verify.sh` 路径与输出格式符合设计。
- [x] verify 退出码 0，无 FAIL。
- [x] PURITY-IMPORT 通过。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
回退文件：删除 test_l2_04_gate.py 与 l2_04_verify.sh（或 git checkout）
不可自动回滚的人工步骤：清理 logs/ 下本次生成的日志
```

## 17. 完成后交接

- 勾选成功标准，附 verify 终端摘要。
- 更新 `05_acceptance/l2-04-safety-guard/验收结果.md`。
- 不得自行提交或推送；L2 Gate 与人类验收通过后由主 Agent 按 Git 规则合入。

## 18. 执行摘要

### 身份校验

| 检查项 | 结果 |
|---|---|
| L3 编号 | `deploy_035`（文件名 / 正文 / dispatch.task_id 一致） |
| 所属 L2 | `l2-04-safety-guard` |
| 当前分支 | `feat/model_deploy/l2-04-safety-guard`（与 L3 声明一致） |
| 前置依赖 | deploy_031–034 均 PASS_LOCAL 且已归档（主 Agent 确认） |
| 允许修改范围 | 仅 integration Gate 测试 + `l2_04_verify.sh` + 验收结果骨架 |

### 产物

| 产物 | 路径 |
|---|---|
| Gate 集成测试 | `src/model_deploy/act/tests/integration/test_l2_04_gate.py`（21 cases） |
| 验收脚本 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh` |
| 验收结果登记 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md`（deploy_035 行） |

### 标签 → 测试映射（04 §3）

| 标签 | 集成测试类 | micro-unit |
|---|---|---|
| TYPES-RESULT | `TestTypesResult` | C1-C3/C5 |
| INPUT-SHAPE | `TestInputShape` | C6/B2 |
| INPUT-FINITE | `TestInputFinite` | C7/B2 |
| QUAT-CANDIDATE | `TestQuatCandidate` | C8/B2 |
| REFERENCE-ORDER | `TestReferenceOrder` | C4/C9/B1 |
| REFERENCE-BOOTSTRAP | `TestReferenceBootstrap` | C4/C9/B1 |
| REFERENCE-MISSING | `TestReferenceMissing` | C9/B1 |
| POSE-TRANSLATION | `TestPoseTranslation` | C10/B3 |
| POSE-ROTATION | `TestPoseRotation` | C11/B3 |
| GRIPPER-RANGE | `TestGripperRange` | C12/B4 |
| GRIPPER-STEP | `TestGripperStep` | C13/B4 |
| BIMANUAL-ASSEMBLY | `TestBimanualAssembly` | C14/B5 |
| OUTPUT-INVARIANT | `TestOutputInvariant` | C15/B5 |
| RESULT-STATUS | `TestResultStatus` | B1/C5 |
| PURITY-IMPORT | `TestPurityImport` | A1/B/C |

### 本地验证

```bash
# 1) Gate 集成
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/integration/test_l2_04_gate.py -v
# 结果：21 passed

# 2) 统一验收脚本
bash "DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh"
# 结果：SUMMARY: 23 PASS / 0 FAIL / 0 BLOCKED ；exit code 0
```

verify 分层输出：`types / config / repo / service / runtime / ui / boundary`；核心标签无 BLOCKED、无 FAIL。

### 未做 / 未验证

- 未修改 deploy_031–034 生产语义。
- 未接 ROS / 硬件 / launch。
- 未做 dry-run（L2-06）/ shadow-run（L2-05）/ real-robot。
- 验收 agent 独立 `PASS_LOCAL` 尚未登记。
- 未 Git 提交 / 推送 / 归档（由主 Agent 在验收 PASS 后处理）。

### 回滚

删除上述两新建文件，或 `git checkout --` 对应路径；清理 `05_acceptance/l2-04-safety-guard/logs/` 下本轮日志（如有）。
