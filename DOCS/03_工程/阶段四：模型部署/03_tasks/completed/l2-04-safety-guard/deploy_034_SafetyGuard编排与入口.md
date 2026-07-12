# L3 微元改造任务：SafetyGuard 编排与入口

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-04-safety-guard` 单步 Action 安全检查闭环
L3 编号：deploy_034
改造类型：`source-adaptation`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_034_SafetyGuard编排与入口.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_034_验收卡片.md`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/`
验收模式：`direct-local`
辅助验收模式：[]
本地验收是否必须：`true`
真机风险等级：`none`
L2 分支：`feat/model_deploy/l2-04-safety-guard`
集成分支：`model_deploy`

> [!warning] 产物落点约束
> 本 L3 产出的源码、测试、配置、launch 和验收脚本必须落到 `ACT代码树分层与产物落点约束.md` 规定的位置。实际产物与本任务声明不一致时，验收判失败。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_034
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_034_SafetyGuard编排与入口.md
  group: l2-04-safety-guard
  branch: feat/model_deploy/l2-04-safety-guard
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard
  acceptance_scenarios: [S4]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_034_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs
  wave: 3
  parallel_group: l2-04-safety-guard-p3
  depends_on: [deploy_031, deploy_032, deploy_033]
  must_run_after: [deploy_033]
  can_run_parallel_with: []
  blocks: [deploy_035]
  conflict_scope:
    files:
      - src/model_deploy/act/service/safety_guard.py
      - src/model_deploy/act/service/__init__.py
      - src/model_deploy/act/tests/service/test_safety_guard.py
    modules:
      - model_deploy.act.service.safety_guard
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
实现 A1 SafetyGuard 与 B1-B5 编排：对外唯一入口 filter_action 在 mock RAM 中返回正确的 PASS / ADJUSTED / REJECTED SafetyResult，且 Guard 无跨 tick 可变业务状态。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- A1 持有 immutable SafetyConfig，每 tick 同步调用 B1。
- B1：候选校验 → 选基准 → 双臂投影 → 组装 C5。
- 契约失败 → REJECTED；可投影越界 → ADJUSTED；无 finding → PASS。

### L2 不负责

- 不更新 previous_safe_action（L2-06）。
- 不选择 hold/safe-stop/fallback。
- 不发布 topic、不硬件 gate。

### 本 L3 在 L2 中的位置

```text
完整 service 行为闭环入口。deploy_035 在此之上叠加集成 Gate 与 verify 脚本。L2-06 将只依赖 A1.filter_action 的 SafetyResult.status。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03_ACT微元设计与协作.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03a_功能微元总览与组织结构.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/04_L2验收机制.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/09_service层设计.md`
9. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/10_runtime层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `SafetyGuard` | `pi05/.../runtime/safety_guard.py` | 3.25 class | config 驱动、同步调用 | Pi0.5 放 runtime，ACT 必须放 service | 结构复用 |
| `filter_action` | 同上 | 编排 | 单入口结果 | ACT 需拆 B2-B5，不能继续大函数 | 结构复用 |
| `ControlLoop._fallback` | `control_loop.py` | 编排 | reject 后策略 | 不迁入 L2-04 | 不复用 |

### 必须保留的源码启发

- 单一同步入口返回结果对象。
- Guard 只缓存 config，不缓存业务状态。

### 禁止照搬的源码行为

- 把 Guard 放进 runtime 目录。
- 在 Guard 内实现 fallback/hold。
- 在 Guard 内更新 last_command。

### 已知风险

- B1 必须捕获 C 层契约失败并转为 REJECTED，不得把未处理异常泄漏为“未定义行为”。
- ADJUSTED 不得被误标为 REJECTED 或 PASS。
- 不得对 previous 与 observation 做双重裁剪。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 在 `service/safety_guard.py` 实现：
  - A1 `class SafetyGuard`：构造注入 immutable SafetyConfig（可含防御性断言），暴露 `filter_action(...)`
  - B1 `filter_action(candidate, previous_safe_action=None, latest_observation=None) -> SafetyResult`
  - B2 `_validate_candidate_action`：组织 C6-C8 + split
  - B3 `_project_arm_pose`：组织 C10-C11
  - B4 `_project_gripper`：组织 C12-C13
  - B5 `_project_bimanual_action`：B3×2、B4×2、C14、C15
- 结果聚合规则：
  - 无 finding 且成功 → PASS + 原样/规范后 ActionSpec
  - 有投影 finding → ADJUSTED + 投影后 ActionSpec
  - 契约/无基准/最终不变量失败 → REJECTED + action=None + 对应 code
- 新建 `tests/service/test_safety_guard.py`：PASS/ADJUSTED/REJECTED 主路径、无状态性（连续调用不隐式记忆 previous）、reference 顺序、左右臂独立调整。

### 本次不做

- 不写 L2 Gate 集成测试与 `l2_04_verify.sh`（deploy_035）。
- 不实现 L2-06 ControlLoop。
- 不实现 L2-05 发布/硬件适配。

### 明确禁止修改

- deploy_031/032 产物语义（types/config 仅 import）。
- deploy_033 已测纯函数算法语义（可重构位置/可见性，不得改正确行为）。
- `src/model_deploy/pi05/`、`pi05_old/`。
- runtime/ui。

### 函数 / class 策略

```text
A1 必须是 class：多次调用共享同一 immutable policy。B1-B5 是方法或内部函数编排。C 微元继续纯函数。A1 不得保存 previous_safe_action 或 metrics。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只读） | — | — |
| config | 否（只读） | — | — |
| repo | 否 | — | — |
| service | 是 | `src/model_deploy/act/service/safety_guard.py` | A1 + B1-B5 |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/service/test_safety_guard.py` | RESULT-STATUS 与编排 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/09_service层设计.md` | A1、B1-B5、结果聚合 |
| `agent_context/10_runtime层设计.md` | 确认无 runtime 产物、无状态更新 |
| `agent_context/03_ACT微元设计与协作.md` | status 语义与失败传播 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `service/safety_guard.py` | A1 SafetyGuard | 3.25 class | config | 可调用 guard | 无业务状态 | test_safety_guard |
| `service/safety_guard.py` | B1 filter_action | 编排函数 | candidate/refs | SafetyResult | 无 | RESULT-STATUS |
| `service/safety_guard.py` | B2 _validate_candidate_action | 编排函数 | 16D | ActionSpec | 无 | INPUT-* |
| `service/safety_guard.py` | B3 _project_arm_pose | 编排函数 | pose pair | safe pose+findings | 无 | POSE-* |
| `service/safety_guard.py` | B4 _project_gripper | 编排函数 | scalar pair | safe scalar+findings | 无 | GRIPPER-* |
| `service/safety_guard.py` | B5 _project_bimanual_action | 编排函数 | cand/ref | ActionSpec+findings | 无 | BIMANUAL-ASSEMBLY |

## 9. 实施步骤

1. 阅读 `03a` 调用树与 `09` B 层表。
2. 用 deploy_033 纯函数组装 B2-B5。
3. 实现 A1 + B1 结果聚合。
4. 编写编排单测：三种 status、NO_REFERENCE、previous 优先、连续调用无状态、ADJUSTED findings 非空。
5. 运行 `test_safety_guard.py` 与既有 `test_safety_primitives.py`。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/service/safety_guard.py`
- `src/model_deploy/act/service/__init__.py`（导出 SafetyGuard）
- `src/model_deploy/act/tests/service/test_safety_guard.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| SafetyGuard 编排 | `src/model_deploy/act/service/safety_guard.py` | service |
| 编排单测 | `src/model_deploy/act/tests/service/test_safety_guard.py` | tests/service |

## 11. 禁止修改

- `src/model_deploy/act/types/safety_result.py` 契约字段
- `src/model_deploy/act/config/schema.py` 字段名/单位
- `src/model_deploy/act/runtime/`、`ui/`、`repo/`
- `src/model_deploy/pi05/`、`pi05_old/`

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_safety_guard.py src/model_deploy/act/tests/service/test_safety_primitives.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | A1/B1-B5 与三种 status | 全部 PASS |
| dry-run | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs/
对应运行验收场景：S4
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S4 service orchestration |
| 本 L3 提供的运行能力 | L2-06 可调用的 A1.filter_action 完整入口 |
| 本 L3 的局部命令 | `pytest .../test_safety_guard.py` |
| L2 Gate 仍需后续 L3 补齐的内容 | 统一标签输出、boundary 扫描、l2_04_verify.sh |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03a_功能微元总览与组织结构.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/09_service层设计.md`
3. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

### 必读代码

1. `src/model_deploy/act/service/safety_guard.py`（deploy_033 产物）
2. `src/model_deploy/act/types/safety_result.py`
3. `src/model_deploy/act/types/observation.py`
4. `pi05/deploy/src/pi05/deploy/runtime/safety_guard.py`（只读）

### 相关历史任务或执行记录

1. 直接上游：`deploy_031`、`deploy_032`、`deploy_033`
2. 无同组已完成 L3（以执行时 active/completed 状态为准）

## 14. 执行要求

- 身份校验三处一致。
- 依赖三项上游完成后才能开工。
- 测试优先；禁止在 A1 内保存 previous 或实现 fallback。

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] A1/B1-B5 均已实现。
- [x] PASS/ADJUSTED/REJECTED 路径正确。
- [x] A1 无可变业务状态（连续调用不记忆 previous）。
- [x] 无 runtime/ui/ROS/hardware import。
- [x] pytest 全部 PASS。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
回退文件：还原 service/safety_guard.py 中 A1/B 层改动与 test_safety_guard.py；还原 service/__init__.py 导出
不可自动回滚的人工步骤：若 deploy_035 已依赖，需先回退 035
```

## 17. 完成后交接

- 勾选成功标准，写执行摘要（公开 API 签名、status 语义示例）。
- 登记验收结果。
- 不得自行提交或推送。

## 18. 执行摘要

### 身份与分支

| 项 | 值 |
|---|---|
| L3 编号 | `deploy_034`（路径 / 文件名 / 正文一致） |
| 所属 L2 | `l2-04-safety-guard`（白名单） |
| 当前分支 | `feat/model_deploy/l2-04-safety-guard` |
| 依赖 | `deploy_031`、`deploy_032`、`deploy_033` 已 PASS_LOCAL 归档 |

### 公开 API

```text
class SafetyGuard:
    def __init__(self, config: SafetyConfig) -> None
    @property
    def config(self) -> SafetyConfig
    def filter_action(
        self,
        candidate,                              # (16,) ndarray 或 ActionSpec
        previous_safe_action: ActionSpec | None = None,
        latest_observation: ObservationSnapshot | None = None,
    ) -> SafetyResult
```

### 实现清单（A1 + B1-B5，复用 deploy_033 C 层）

| 编号 | 符号 | 职责 |
|---|---|---|
| A1 | `SafetyGuard` | 持有 immutable `SafetyConfig`；无跨 tick 业务状态 |
| B1 | `filter_action` | 入口：B2 → C9 → B5；契约失败 → REJECTED |
| B2 | `_validate_candidate_action` | C6 → C7 → split → C8×2 |
| B3 | `_project_arm_pose` | C10 + C11（单侧） |
| B4 | `_project_gripper` | C12 → C13（单侧） |
| B5 | `_project_bimanual_action` | B3×2、B4×2、C14、C15 |

### status 语义（聚合规则）

| status | 条件 | action | findings |
|---|---|---|---|
| `PASS` | 投影无 finding 且契约通过 | 规范后 ActionSpec | `()` |
| `ADJUSTED` | C10-C13 产生 finding | 投影后 ActionSpec | 非空 tuple |
| `REJECTED` | 契约/无基准/不变量失败 | `None` | 含对应 `SafetyCode` 的 finding |

### 无状态性

- A1 仅缓存 `_config`；不保存 `previous_safe_action` / metrics。
- 连续两次调用：第二次若不传 reference 参数 → `REJECTED(NO_REFERENCE)`，证明无隐式记忆。

### 测试清单

文件：`src/model_deploy/act/tests/service/test_safety_guard.py`（17 cases）

| 组 | 覆盖 |
|---|---|
| Construction | config 类型、导出 |
| PASS | previous / observation 小步 |
| ADJUSTED | 平移超限、夹爪、左右独立 |
| REJECTED | shape / non-finite / NO_REFERENCE / quat |
| Reference+Stateless | previous 优先、连续调用无状态 |
| Purity | 无 runtime/ui/ROS import；无 previous/metrics 字段 |

### 验证命令与结果

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/service/test_safety_guard.py \
  src/model_deploy/act/tests/service/test_safety_primitives.py -v
# → 57 passed（17 orchestration + 40 primitives）
```

### 明确未做

- deploy_035：L2 Gate 集成测试与 `l2_04_verify.sh`
- L2-06 ControlLoop / fallback / previous 更新
- L2-05 发布 / 硬件适配

### 产物文件

| 文件 | 变更 |
|---|---|
| `src/model_deploy/act/service/safety_guard.py` | 追加 A1/B1-B5；保留 C4/C6-C15 |
| `src/model_deploy/act/service/__init__.py` | 导出 `SafetyGuard` |
| `src/model_deploy/act/tests/service/test_safety_guard.py` | 新建编排单测 |
