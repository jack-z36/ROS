# L3 微元改造任务：SafetyConfig 契约协调

## 1. 任务定位

阶段：阶段四：模型部署
L1：ACT 部署程序开发
所属 L2：`l2-04-safety-guard` 单步 Action 安全检查闭环
L3 编号：deploy_032
改造类型：`behavior-change`
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_032_SafetyConfig契约协调.md`
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_032_验收卡片.md`
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
  task_id: deploy_032
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_032_SafetyConfig契约协调.md
  group: l2-04-safety-guard
  branch: feat/model_deploy/l2-04-safety-guard
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard
  acceptance_scenarios: [S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-safety-guard/deploy_032_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs
  wave: 1
  parallel_group: l2-04-safety-guard-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_031]
  blocks: [deploy_033, deploy_034, deploy_035]
  conflict_scope:
    files:
      - src/model_deploy/act/config/schema.py
      - src/model_deploy/act/config_files/deploy.yaml
      - src/model_deploy/act/tests/config/test_safety_config.py
      - src/model_deploy/act/tests/config/test_schema.py
    modules:
      - model_deploy.act.config.schema
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
把 SafetyConfig 迁移到与部署 ActionDomain 同域的阈值字段：平移米制、旋转弧度、夹爪范围/步长、四元数容差，并完成解析与非法值拒绝。
```

## 4. 所属 L2 边界与设计来源

### L2 负责

- 消费 immutable SafetyConfig 作为 A1 静态 policy。
- 不读取配置文件；配置加载仍属 L2-01 schema/parser。

### L2 不负责

- 不把 F100 寄存器 `0~100` 当作模型 action 域默认值。
- 不在 service 层实现配置加载。

### 本 L3 在 L2 中的位置

```text
A1 前置条件。deploy_033/034 的 C10-C13 与 A1 构造期断言依赖本契约。现有 max_tcp_delta_per_step / hand_min=300 不能无条件继承。
```

### 必读 L2 设计文档

1. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
3. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/00_INDEX.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/01_L2功能边界.md`
5. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/03_ACT微元设计与协作.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/04_L2验收机制.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/05_人类验收机制.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/07_config层设计.md`

## 5. Pi0.5 源码盘点

| Pi0.5 对象 | 路径 / 名称 | 3.5 层微元类型 | 已有能力 | 与 ACT 目标的差距 | 本次复用判断 |
|---|---|---|---|---|---|
| Pi0.5 SafetyConfig | `pi05/.../runtime/safety_guard.py` 及相关 config | 数据 | guard 持有不可变 policy | 关节限位/硬件寄存器域不可迁入 | 结构复用 |

### 必须保留的源码启发

- Guard 只持有启动期校验过的 immutable policy。

### 禁止照搬的源码行为

- 关节绝对限位、`max_joint_delta_rad`、RM 原生夹爪寄存器默认值。
- fallback policy 字段（属 L2-06）。

### 已知风险

- 现有 `hand_min=300 / hand_max=1000` 疑似硬件域污染；必须改为与 ActionSpec 夹爪同域（默认建议 `0.0~1.0` 训练动作域，除非 ActionDomain 元数据另有约定）。
- 兼容旧 YAML 键名时必须显式映射并文档化，不得静默把米制阈值解释为关节弧度。

## 6. ACT 微元与真实实现边界

### 本次允许做

- 扩展 `src/model_deploy/act/config/schema.py::SafetyConfig` 字段：
  - `max_translation_step_m: float`（`> 0`）
  - `max_rotation_step_rad: float`（`> 0`）
  - `gripper_min: float`、`gripper_max: float`（`min <= max`，同 ActionDomain）
  - `max_gripper_step: float`（`>= 0`）
  - `quaternion_norm_tolerance: float`（`> 0`）
  - 可选 ActionDomain 元数据：`pose_frame`、`quaternion_order="xyzw"`、`gripper_domain`
- 更新 `from_mapping` / 校验逻辑：非法范围/单位域抛 `DeployConfigError`。
- 更新 `src/model_deploy/act/config_files/deploy.yaml` 的 `safety:` 段为新语义。
- 更新/重写 `tests/config/test_safety_config.py`，必要时最小调整 `test_schema.py` 中依赖旧字段的断言。
- 对旧键名（`max_tcp_delta_per_step`、`hand_min/max`、`quaternion_check`）二选一并在任务执行摘要写明：
  1. **破坏性迁移**（推荐）：删除旧字段，要求新 YAML；或
  2. **兼容映射**：旧键映射到新字段并 emit 明确警告/文档，但不得把 300~1000 默认成夹爪训练域。

### 本次不做

- 不实现 SafetyGuard 或任何投影算法。
- 不新增 service/runtime/ui 文件。
- 不引入 joint limits 或 F100 寄存器映射。

### 明确禁止修改

- `src/model_deploy/act/service/`（除本任务明确不涉及外一律禁止）
- `src/model_deploy/act/types/safety_result.py`（deploy_031 产物；本任务可与 031 并行，不得假设其已存在）
- `src/model_deploy/pi05/`、`pi05_old/`

### 函数 / class 策略

```text
不在 config 层新增业务 Class。继续使用 frozen SafetyConfig dataclass + DeployConfig.from_mapping 校验。
```

## 7. 六层产物落点

| 层 | 本 L3 是否涉及 | 文件路径 | 职责 |
|---|---|---|---|
| types | 否 | — | — |
| config | 是 | `src/model_deploy/act/config/schema.py` | SafetyConfig 字段与校验 |
| config_files | 是 | `src/model_deploy/act/config_files/deploy.yaml` | 运行配置实例 |
| repo | 否 | — | — |
| service | 否 | — | — |
| runtime | 否 | — | — |
| ui | 否 | — | — |
| tests | 是 | `src/model_deploy/act/tests/config/test_safety_config.py` | 默认值与非法拒绝 |
| acceptance | 否 | — | — |

### 对应六层设计文档

| 设计文档 | 本 L3 实现或修改的内容 |
|---|---|
| `agent_context/06_types层设计.md` | 无 |
| `agent_context/07_config层设计.md` | SafetyConfig 字段、单位、校验、禁止 F100 默认 |
| `agent_context/08_repo层设计.md` | 无 |
| `agent_context/09_service层设计.md` | 无（仅作为 A1 输入契约） |
| `agent_context/10_runtime层设计.md` | 无 |
| `agent_context/11_ui层设计.md` | 无 |

## 8. 文件内 3.5 层功能微元

| 文件 | 功能微元 | 类型 | 输入 | 输出 | 是否有副作用 | 验收覆盖 |
|---|---|---|---|---|---|---|
| `config/schema.py` | SafetyConfig 字段定义 | 数据 | YAML/mapping | frozen SafetyConfig | 无 | test_safety_config |
| `config/schema.py` | safety 段解析校验 | 数据读写函数 | raw mapping | SafetyConfig 或 DeployConfigError | 无 | test_safety_config |
| `config_files/deploy.yaml` | safety 运行值 | 数据 | — | 合法默认阈值 | 无 | from_mapping 测试 |

## 9. 实施步骤

1. 阅读 `07_config层设计.md`，列出必填字段与校验规则。
2. 改写 `SafetyConfig` 与 `_deploy_from_mapping` 的 safety 分支。
3. 更新 `deploy.yaml` safety 段默认值（米制/弧度/同域夹爪）。
4. 重写 `test_safety_config.py`：正例、`<=0` 阈值拒绝、`gripper_min > max` 拒绝、默认非硬件寄存器域。
5. 修复因字段更名失败的既有 config 测试。
6. 运行相关 pytest。

## 10. 允许修改

> [!warning] 产物落点声明（必填）

- `src/model_deploy/act/config/schema.py`
- `src/model_deploy/act/config/__init__.py`（仅当导出需要）
- `src/model_deploy/act/config_files/deploy.yaml`
- `src/model_deploy/act/tests/config/test_safety_config.py`
- `src/model_deploy/act/tests/config/test_schema.py`（最小必要）
- `src/model_deploy/act/tests/integration/test_l2_01_gate.py`（仅当断言旧 safety 字段名时的最小适配）

### 本次产物落点

| 产物 | 落点路径 | 所属层 / 目录 |
|---|---|---|
| SafetyConfig schema | `src/model_deploy/act/config/schema.py` | config |
| 运行配置实例 | `src/model_deploy/act/config_files/deploy.yaml` | config_files |
| config 单测 | `src/model_deploy/act/tests/config/test_safety_config.py` | tests/config |

## 11. 禁止修改

- `src/model_deploy/act/service/`、`runtime/`、`ui/`
- `src/model_deploy/act/types/`（本任务不依赖 types 新文件）
- `src/model_deploy/pi05/`、`pi05_old/`
- L2-04 service 算法文件（尚不存在）

## 12. 验证方式

### 自动化验收命令

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_safety_config.py src/model_deploy/act/tests/config/test_schema.py -v
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | SafetyConfig 字段与非法拒绝 | 全部 PASS |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| shadow-run | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/logs/
对应运行验收场景：S2
```

### L2 Gate 贡献

| 字段 | 内容 |
|---|---|
| 对应场景 | S2 config contract |
| 本 L3 提供的运行能力 | 同域 SafetyConfig 静态 policy |
| 本 L3 的局部命令 | `pytest .../test_safety_config.py .../test_schema.py` |
| L2 Gate 仍需后续 L3 补齐的内容 | 纯函数、编排、mock Gate |

## 13. 必读上下文

### 必读任务文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
3. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
4. `DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/agent_context/07_config层设计.md`

### 必读代码

1. `src/model_deploy/act/config/schema.py`
2. `src/model_deploy/act/config_files/deploy.yaml`
3. `src/model_deploy/act/tests/config/test_safety_config.py`
4. `pi05/deploy/src/pi05/deploy/runtime/safety_guard.py`（只读结构参考）

### 必读约束文档

1. `DOCS/02_约束/Git协作/Git操作规则.md`
2. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游 L3（与 deploy_031 并行）
2. L2-01 已完成 config schema 基线（`deploy_008` 等，已 completed）

## 14. 执行要求

执行前必须完成任务文件身份校验，确认 `group=l2-04-safety-guard`、`branch=feat/model_deploy/l2-04-safety-guard`。

测试优先：

```text
最小复现 / 测试
-> 最小实现
-> 验证通过
-> 必要整理
```

不得为通过测试而把 F100 寄存器域写回默认值。

## 15. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认所属 L2 ID 属于新版 L2 白名单。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取 `07_config层设计.md` 与 L2 边界。
- [x] SafetyConfig 含平移/旋转/夹爪范围步长/四元数容差字段且单位正确。
- [x] 默认夹爪域不是 300~1000 硬件寄存器域。
- [x] 非法阈值/范围被拒绝。
- [x] pytest 相关 config 测试全部 PASS。
- [x] 产物路径符合六层落点约束。
- [x] 已写明回滚方式。

## 16. 回滚方式

```text
关闭参数 / 配置：还原 deploy.yaml safety 段
切回旧入口：不适用
移除 adapter：不适用
回退文件：git checkout -- src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml 及相关 tests
不可自动回滚的人工步骤：若已有下游依赖新字段名，需同步回退
```

## 17. 完成后交接

- 更新本任务成功标准勾选与执行摘要。
- 登记 `05_acceptance/l2-04-safety-guard/验收结果.md`。
- 明确说明旧 YAML 键兼容策略。
- 不得自行提交或推送。

## 18. 执行摘要

### 身份校验

| 项 | 结果 |
|---|---|
| 路径 | `.../active/l2-04-safety-guard/deploy_032_SafetyConfig契约协调.md` |
| 文件名 deploy_id | `deploy_032` |
| 正文 L3 编号 | `deploy_032` |
| group / L2 | `l2-04-safety-guard`（新版白名单） |
| 分支 | `feat/model_deploy/l2-04-safety-guard`（与 L2 分支一致） |

### 旧 YAML 键兼容策略：**破坏性迁移（推荐方案）**

| 旧键 | 处理 |
|---|---|
| `max_tcp_delta_per_step` | **删除**；改用 `max_translation_step_m`（米） |
| `hand_min` / `hand_max` | **删除**；改用 `gripper_min` / `gripper_max`（默认 `0.0~1.0` 训练动作域） |
| `quaternion_check` (bool) | **删除**；改用 `quaternion_norm_tolerance`（float `> 0`） |

- 若 YAML 仍含任一旧键，`from_mapping` **显式 `DeployConfigError`**，列出迁移目标字段，**不**静默映射、**不**把 `300~1000` 当作夹爪训练域默认。
- 空 `safety: {}` 使用 ActionDomain 默认值（米/弧度/`0~1` 夹爪）。

### 实现要点

- `SafetyConfig` 新字段：`max_translation_step_m`、`max_rotation_step_rad`、`gripper_min`/`gripper_max`、`max_gripper_step`、`quaternion_norm_tolerance`；可选元数据 `pose_frame`、`quaternion_order="xyzw"`、`gripper_domain`。
- 校验：`translation/rotation/quat_tol > 0`；`max_gripper_step >= 0`；`gripper_min <= gripper_max`；非法 `quaternion_order` 拒绝。
- `deploy.yaml` safety 段已切换为新字段默认值。
- 未实现 SafetyGuard/投影；未改 service/runtime/ui/types；未引入 joint limits / F100 映射。
- 未触碰 deploy_031 冲突文件 `types/safety_result*`。

### 变更文件

| 文件 | 变更 |
|---|---|
| `src/model_deploy/act/config/schema.py` | SafetyConfig 字段 + `_safety_from_mapping` + 旧键拒绝 + `_non_negative_float` |
| `src/model_deploy/act/config_files/deploy.yaml` | safety 段新语义默认值 |
| `src/model_deploy/act/tests/config/test_safety_config.py` | 重写正/反例与 legacy 拒绝 |
| `src/model_deploy/act/tests/config/test_schema.py` | 最小适配新字段 / bool 用例改 compile_model |
| `src/model_deploy/act/tests/integration/test_l2_01_gate.py` | 最小适配 safety 断言字段名 |
| `DOCS/.../05_acceptance/l2-04-safety-guard/验收结果.md` | 执行登记 |

### 验证

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_safety_config.py src/model_deploy/act/tests/config/test_schema.py -v
# 41 passed

python3 -m pytest src/model_deploy/act/tests/config/ -q
# 82 passed
```

### 未验证 / 风险

- SafetyGuard 消费侧（deploy_033/034）尚未实现，A1 构造期断言未在本 L3 验证。
- 下游若仍写旧 YAML 键会在加载期失败（有意行为）。
- 未跑完整 `tests/` 套件 / L2 Gate（属后续 L3）。

### 验收就绪

- 执行侧自检完成，**建议主 Agent 下一步跑 `deploy_032` 验收卡片**（`direct-local`）。
- 本执行 agent **不**写验收结论、**不**归档任务、**不** commit/push。
