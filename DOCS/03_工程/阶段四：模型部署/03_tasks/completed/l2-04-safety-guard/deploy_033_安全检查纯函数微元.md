# L3 微元改造任务：安全检查纯函数微元

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-04-safety-guard` 单步 Action 安全检查闭环
L3 编号：deploy_033
改造类型：`source-adaptation`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_033_安全检查纯函数微元.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_033_验收卡片.md`
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
  task_id: deploy_033
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_033_安全检查纯函数微元.md
  group: l2-04-safety-guard
  branch: feat/model_deploy/l2-04-safety-guard
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard
  acceptance_scenarios: [S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_033_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs
  wave: 2
  parallel_group: l2-04-safety-guard-p2
  depends_on: [deploy_031, deploy_032]
  must_run_after: [deploy_031, deploy_032]
  can_run_parallel_with: []
  blocks: [deploy_034, deploy_035]
  conflict_scope:
    files:
      - src/model_deploy/act/service/safety_guard.py
      - src/model_deploy/act/tests/service/test_safety_primitives.py
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
在 service/safety_guard.py 实现 C4、C6-C15 纯函数/内部数据（不含 A1/B1-B5 编排），并用独立单测覆盖输入校验、基准选择、平移/旋转/夹爪投影与最终不变量。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- RAM 内纯计算：shape/finite/quat、reference 选择、几何投影、夹爪同域限步、16D 重组与不变量。

### L2 不负责

- 不编排完整 filter_action 调用链（deploy_034）。
- 不持有 previous_safe_action 状态、不 fallback、不 ROS/硬件。

### 本 L3 在 L2 中的位置

```text
提供 A1 内部可调用的原子计算。deploy_034 用 B 层把这些 C 微元串成完整 filter_action。Gate 标签 INPUT-*/REFERENCE-*/POSE-*/GRIPPER-*/OUTPUT-INVARIANT 的算法正确性由本 L3 单测先行证明。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/02_pi05源码3.5层微元拆解.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03_ACT微元设计与协作.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03a_功能微元总览与组织结构.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/04_L2验收机制.md`
9. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/06_types层设计.md`
10. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/07_config层设计.md`
11. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/09_service层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| `_clamp_delta` | `pi05/.../runtime/safety_guard.py` | 计算函数 | 相对 anchor 限步 | 逐轴关节 clip，不能限制 TCP 三维欧氏距离 | 参考理解；算法重写 |
| `_delta_anchor` | 同上 | 计算函数 | previous/observation 优先级 | ACT 两者皆缺时必须 REJECT，不能静默 | 结构复用 |
| joint limits | 同上 | 数据/计算 | 关节绝对限位 | TCP 空间无关节语义 | 不复用 |

### 必须保留的源码启发

- previous 优先、observation 兜底的 anchor 选择结构。
- 目标相对基准做限步，而不是对绝对目标做无基准裁剪。

### 禁止照搬的源码行为

- 逐轴 component clip。
- 关节绝对限位、`max_joint_delta_rad`。
- 把 previous target 称为实测 pose。

### 已知风险

- C10 必须沿位移方向整体缩放，禁止逐轴。
- C11 必须 shortest arc，并正确处理 `q` 与 `-q`。
- C12/C13 输入与阈值同 ActionDomain。
- C8/C15 只处理内部 `xyzw`，禁止 reorder 为 `wxyz`。

## 6. ACT 微元与真实实现边界

### 本次允许做

在 `src/model_deploy/act/service/safety_guard.py` 实现（可为 module-level 或 class-static 纯函数）：

| 编号 | 名称 | 行为摘要 |
|---|---|---|
| C4 | `_ComparisonReference` | 内部 frozen 基准：source + pose/gripper |
| C6 | `require_action_vector_16` | 严格 `(16,)` |
| C7 | `require_finite_action` | 拒绝 NaN/Inf |
| C8 | `canonicalize_quaternion` | `xyzw` 近单位可单位化，零模拒绝 |
| C9 | `select_comparison_reference` | previous → fresh observation → 缺失 |
| C10 | `limit_translation_step` | 三维欧氏距离投影 + finding |
| C11 | `limit_rotation_step` | 最短弧/Slerp 投影 + finding |
| C12 | `clamp_gripper_range` | 同域 min/max + finding |
| C13 | `limit_gripper_step` | 同域单步 + finding |
| C14 | `build_safe_action` | 左右字段重组 ActionSpec（16D 段序不变） |
| C15 | `validate_safe_action_invariants` | 最终 shape/finite/quat/domain |

- 新建 `tests/service/test_safety_primitives.py`，覆盖 `04_L2验收机制.md` 中除 RESULT-STATUS/PURITY-IMPORT 编排层外的算法标签。
- 可复用 `ActionSpec`/`split_action`/`SafetyConfig`/`SafetyFinding`/`SafetyCode`。

### 本次不做

- 不实现 A1 `SafetyGuard` class 与 B1-B5 编排入口（deploy_034）。
- 不实现完整 `filter_action` 端到端。
- 不写 integration Gate 或 verify.sh。

### 明确禁止修改

- `src/model_deploy/act/types/safety_result.py` 语义（仅 import）。
- `src/model_deploy/act/config/schema.py` 字段语义（仅消费）。
- `src/model_deploy/pi05/`、`pi05_old/`。
- runtime/ui/ROS/hardware 相关文件。

### 函数 / class 策略

```text
C6-C15 均为无状态纯函数。C4 是内部 frozen 数据对象，不导出为跨 L2 公共 API。本 L3 可不创建 A1 class；若为组织函数暂时放在 module 级，deploy_034 再封装进 SafetyGuard。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否（只读依赖） | — | — |
| config | 否（只读依赖） | — | — |
| repo | 否 | — | — |
| service | 是 | `src/model_deploy/act/service/safety_guard.py` | C4/C6-C15 |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/service/test_safety_primitives.py` | 算法单测 |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/06_types层设计.md` | 消费 SafetyFinding/Code |
| `agent_context/07_config层设计.md` | 消费 SafetyConfig 阈值 |
| `agent_context/09_service层设计.md` | C4、C6-C15 算法与边界 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `service/safety_guard.py` | C4 `_ComparisonReference` | 数据 | source/fields | frozen ref | 无 | REFERENCE-* |
| `service/safety_guard.py` | C6 require_action_vector_16 | 计算函数 | object | (16,) 或错误 | 无 | INPUT-SHAPE |
| `service/safety_guard.py` | C7 require_finite_action | 计算函数 | vector | vector 或错误 | 无 | INPUT-FINITE |
| `service/safety_guard.py` | C8 canonicalize_quaternion | 计算函数 | xyzw,tol | unit quat 或错误 | 无 | QUAT-CANDIDATE |
| `service/safety_guard.py` | C9 select_comparison_reference | 计算函数 | previous/snapshot | C4 或 NO_REFERENCE | 无 | REFERENCE-* |
| `service/safety_guard.py` | C10 limit_translation_step | 计算函数 | xyz/ref/limit | xyz+finding | 无 | POSE-TRANSLATION |
| `service/safety_guard.py` | C11 limit_rotation_step | 计算函数 | quat/ref/limit | quat+finding | 无 | POSE-ROTATION |
| `service/safety_guard.py` | C12 clamp_gripper_range | 计算函数 | scalar/min/max | scalar+finding | 无 | GRIPPER-RANGE |
| `service/safety_guard.py` | C13 limit_gripper_step | 计算函数 | scalar/ref/step | scalar+finding | 无 | GRIPPER-STEP |
| `service/safety_guard.py` | C14 build_safe_action | 计算函数 | left/right fields | ActionSpec | 无 | BIMANUAL-ASSEMBLY |
| `service/safety_guard.py` | C15 validate_safe_action_invariants | 计算函数 | ActionSpec/domain | ActionSpec 或错误 | 无 | OUTPUT-INVARIANT |

## 9. 实施步骤

1. 阅读 `09_service层设计.md` §4-5 与 `03a` 调用树中的 C 层职责。
2. 先写失败测试（shape/NaN/无基准/超限投影）。
3. 实现 C6-C15 与 C4。
4. 对 C10 做“方向缩放恰到阈值”断言；对 C11 做 shortest-arc 与 `q/-q` 断言。
5. 运行 primitives 单测全部 PASS。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/service/safety_guard.py`（新建或填充纯函数部分）
- `src/model_deploy/act/service/__init__.py`（可选导出）
- `src/model_deploy/act/tests/service/test_safety_primitives.py`（新建）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| 安全纯函数 | `src/model_deploy/act/service/safety_guard.py` | service |
| 纯函数单测 | `src/model_deploy/act/tests/service/test_safety_primitives.py` | tests/service |

## 11. 禁止修改

- `src/model_deploy/act/types/safety_result.py`（语义）
- `src/model_deploy/act/config/schema.py`（字段）
- `src/model_deploy/act/runtime/`、`ui/`、`repo/`
- `src/model_deploy/pi05/`、`pi05_old/`

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_safety_primitives.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | C4/C6-C15 算法 | 全部 PASS，无 skip |
| dry-run | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs/
对应运行验收场景：S3
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S3 service primitives |
| 本 L3 提供的运行能力 | 可独立验证的 C 层投影与校验 |
| 本 L3 的局部命令 | `pytest .../test_safety_primitives.py` |
| L2 Gate 仍需后续 L3 补齐的内容 | A1/B1-B5 编排与完整 mock Gate |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/09_service层设计.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03a_功能微元总览与组织结构.md`

### 必读代码

1. `pi05/deploy/src/pi05/deploy/runtime/safety_guard.py`（只读）
2. `src/model_deploy/act/types/action_spec.py`
3. `src/model_deploy/act/types/safety_result.py`
4. `src/model_deploy/act/types/observation.py`
5. `src/model_deploy/act/config/schema.py`

### 相关历史任务或执行记录

1. 直接上游：`deploy_031`、`deploy_032`
2. 无同组已完成 L3（执行时以上游验收通过为准）

## 14. 执行要求

- 身份校验：`deploy_033` 三处一致。
- 依赖：`deploy_031`、`deploy_032` 已完成。
- 测试优先；禁止为通过测试改用逐轴 clip。

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认所属 L2 白名单与分支。
- [x] C4、C6-C15 均已实现且有对应单测。
- [x] C10 欧氏方向缩放、C11 shortest-arc、C12/C13 同域投影行为正确。
- [x] 无 runtime/ui/ROS/hardware import。
- [x] pytest 全部 PASS。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
回退文件：删除或还原 service/safety_guard.py 与 tests/service/test_safety_primitives.py
不可自动回滚的人工步骤：若 deploy_034 已依赖，需先回退 034
```

## 17. 完成后交接

- 勾选成功标准，写执行摘要（函数清单、测试清单）。
- 登记验收结果。
- 不得自行提交或推送。

## 18. 执行摘要

### 身份与分支

| 项 | 值 |
|---|---|
| L3 编号 | `deploy_033`（路径 / 文件名 / 正文一致） |
| 所属 L2 | `l2-04-safety-guard`（白名单） |
| 当前分支 | `feat/model_deploy/l2-04-safety-guard` |
| 依赖 | `deploy_031`、`deploy_032` 已 PASS_LOCAL 归档 |

### 实现清单（C 层纯函数，无 A1/B1-B5 编排）

| 编号 | 符号 | 落点 |
|---|---|---|
| C4 | `_ComparisonReference` | `src/model_deploy/act/service/safety_guard.py` |
| — | `SafetyContractError` | 同上（契约失败带 `SafetyCode`） |
| C6 | `require_action_vector_16` | 同上；严格 `(16,)`，不 ravel |
| C7 | `require_finite_action` | 同上 |
| C8 | `canonicalize_quaternion` | 同上；内部 `xyzw`，近单位可单位化 |
| C9 | `select_comparison_reference` | previous → observation → `NO_REFERENCE` |
| C10 | `limit_translation_step` | 三维欧氏方向缩放（非逐轴 clip） |
| C11 | `limit_rotation_step` | shortest-arc Slerp；`q`/`-q` 同姿态 |
| C12 | `clamp_gripper_range` | 同域 min/max |
| C13 | `limit_gripper_step` | 同域单步 |
| C14 | `build_safe_action` | 16D 段序重组 `ActionSpec` |
| C15 | `validate_safe_action_invariants` | 最终 shape/finite/quat/domain |

**明确未做（deploy_034）：** A1 `SafetyGuard` class、B1-B5 编排、`filter_action` 端到端。

### 测试清单

文件：`src/model_deploy/act/tests/service/test_safety_primitives.py`（40 cases）

| 标签 | 测试类 / 要点 |
|---|---|
| INPUT-SHAPE | `TestRequireActionVector16` |
| INPUT-FINITE | `TestRequireFiniteAction` |
| QUAT-CANDIDATE | `TestCanonicalizeQuaternion`（含 xyzw 序） |
| REFERENCE-ORDER/BOOTSTRAP/MISSING | `TestSelectComparisonReference` |
| POSE-TRANSLATION | `TestLimitTranslationStep`（欧氏恰为阈值；反证非逐轴） |
| POSE-ROTATION | `TestLimitRotationStep`（角恰为阈值；`q/-q`） |
| GRIPPER-RANGE/STEP | `TestGripperProjection` |
| BIMANUAL-ASSEMBLY | `TestBuildSafeAction` |
| OUTPUT-INVARIANT | `TestValidateSafeActionInvariants` |
| PURITY-IMPORT | `TestPurityImport`（AST 扫描无 runtime/ui/ROS/hardware） |

### 本地验证

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests/service/test_safety_primitives.py -v
# 结果：40 passed in 0.13s，无 skip
```

### 变更文件

- 新建 `src/model_deploy/act/service/safety_guard.py`
- 新建 `src/model_deploy/act/tests/service/test_safety_primitives.py`
- 更新本 L3 成功标准与执行摘要

### 未验证 / 留给后续

- A1/B1-B5 完整编排与 RESULT-STATUS（deploy_034）
- L2 mock Gate / `l2_04_verify.sh`（deploy_035）
- 真机行为（本 L3 `robot_risk: none`，不适用）

### 验收交接

- 本执行 agent **未** 写验收结论；请主 Agent 启动 `deploy_033` 验收卡片（`direct-local`）。
- 未改 dispatch、未归档、未 Git 同步。
