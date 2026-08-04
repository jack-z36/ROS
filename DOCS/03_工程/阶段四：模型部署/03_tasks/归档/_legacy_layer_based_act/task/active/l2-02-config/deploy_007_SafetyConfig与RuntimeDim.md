# L3 微元改造任务：新建 ACT SafetyConfig + RuntimeConfig 维度与 mode

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 ACT Config 层
来源 ACT Delta：A4（safety 配置、维度 16/16、mode 三档）
L3 编号：deploy_007
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_007_SafetyConfig与RuntimeDim.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-02-config`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/`
对应 L2 运行验收场景：S2
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_007_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_007
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_007_SafetyConfig与RuntimeDim.md
  group: l2-02-config
  branch: feat/model_deploy/l2-02-config
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
  acceptance_scenarios: [S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_007_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs
  wave: 1b
  parallel_group: l2-02-config-w1
  depends_on: [deploy_005]
  must_run_after: []
  can_run_parallel_with: [deploy_006]
  blocks: [deploy_008]
  conflict_scope:
    files:
      - src/model_deploy/act/config/schema.py
    modules:
      - act.config.schema
    config_keys: [safety, runtime]
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
在 deploy_005 骨架中填充 SafetyConfig（policy-action 层 TCP 检查项，删关节检查）；
将 RuntimeConfig 的 action_dim/state_dim 默认值从 14/26 改为 16/16；
将 SafetyConfig 接入 DeployConfig 顶层。
mode 三档枚举（dry-run/shadow-run/safe-run）已在 deploy_005 保留，本 L3 确认不改。
```

## 4. 来源契约

| 字段 | 内容 |
|---|---|
| Delta | A4 + A8（safety 配置） |
| AS-IS | 同事 `SafetyConfig`（`:188-199`）：`max_joint_delta_rad`、`hand_min=300/hand_max=1000`、`JointLimitsConfig`。`RuntimeConfig`（`:48-49`）默认 `action_dim=14/state_dim=26`。 |
| TO-BE | SafetyConfig 改为 TCP 检查：`max_tcp_step_m`、`max_quat_delta`、`gripper_width_min=0.0/gripper_width_max=1.0`、`enable_quaternion_check`、`enable_nan_inf_check`、`clamp_normalized_action`、`hold_last_action`、`stale_observation_timeout_s`。删 `max_joint_delta_rad`/`hand_min/hand_max`/`JointLimitsConfig`。RuntimeConfig 维度改 16/16。 |

所属 L2：[[L2-02-ACT Config层]]，依据 [[ACT部署契约]]、[[L2-04-ACT action处理与发布]]（safety_guard 检查项）。

## 5. 现有程序盘点

| 现有对象 | 路径 | 已有能力 | 差距 | 复用方式 |
|---|---|---|---|---|
| `SafetyConfig` | `pi05_old/.../schema.py:188-199` | frozen dataclass，关节检查项 | 检查项全换 | **结构复用**（框架保留，字段重写） |
| `JointLimitsConfig` | `:178-186` | 关节限位 | ACT TCP 模式不用 | **删除，不搬** |
| `_safety_config()` 工厂 | `:429-450` | 从 YAML 构建 safety | 字段映射重写 | **结构复用** |
| `RuntimeConfig.action_dim/state_dim` | `:48-49` | 默认 14/26 | 改 16/16 | **改默认值** |

## 6. 真实改造边界

### 本次允许做

- 编辑 `act/config/schema.py`：
  - `SafetyConfig` 重写（见 TO-BE 字段），删 `JointLimitsConfig`。
  - `_act_safety_config(raw)` 工厂：从 YAML 构建 TCP 版 safety。
  - `RuntimeConfig` 默认 `action_dim=16`/`state_dim=16`（改 deploy_005 搬来的暂留值）。
  - SafetyConfig 接入 DeployConfig 顶层和 `_deploy_from_mapping`（替换 deploy_005 占位）。
- 新建 `act/tests/config/test_safety.py`。

### 本次不做

- 不改 TopicsConfig（deploy_006）。
- 不改 mode 枚举（已是三档）。
- 不写 deploy.yaml（deploy_008）。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`、`act/types/**`
- deploy_005 的 BundleConfig/ImageConfig/辅助函数；deploy_006 的 TopicsConfig

## 7. 实施步骤

1. 编辑 `act/config/schema.py`：
   - 删除 `JointLimitsConfig`（若 deploy_005 搬了的话；大概率没搬，确认即可）。
   - 重写 `SafetyConfig`：
     ```python
     @dataclass(frozen=True)
     class SafetyConfig:
         max_tcp_step_m: float = 0.05
         max_quat_delta: float = 0.1
         gripper_width_min: float = 0.0
         gripper_width_max: float = 1.0
         enable_quaternion_check: bool = True
         enable_nan_inf_check: bool = True
         clamp_normalized_action: bool = True
         hold_last_action: bool = True
         stale_observation_timeout_s: float = 0.5
     ```
   - `_act_safety_config(raw)`：用辅助函数 `_positive_float`/`_bool`/`_float` 构建。
   - `RuntimeConfig`：`action_dim: int = 16`、`state_dim: int = 16`。
   - `_deploy_from_mapping` 中 `safety=_act_safety_config(...)` 替换占位。
2. 新建 `act/tests/config/test_safety.py`：合法 safety 加载；max_tcp_step_m 正数；gripper_width_min/max；非法 mode（非三档）报错；dim=16。
3. 运行 pytest。

## 8. 验证方式

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/test_safety.py -v
```

| 层级 | 通过标准 |
|---|---|
| unit | test_safety.py PASSED；SafetyConfig 含 TCP 检查项；runtime.action_dim==16/state_dim==16 |

L2 贡献：safety 配置与维度固化。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| schema.py 补充 SafetyConfig + 改 dim | `src/model_deploy/act/config/schema.py` | config |
| 单测 | `src/model_deploy/act/tests/config/test_safety.py` | tests/config |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`、`act/types/**`
- deploy_005 的 Bundle/Image/辅助；deploy_006 的 TopicsConfig

## 11. 必读上下文

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-ACT Config层.md`
- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-04-ACT action处理与发布.md`（safety_guard 检查项依据）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（`:178-199, 429-450`）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-02-config`。
- 依赖：deploy_005 完成。
- 并行注意：与 deploy_006 都改 schema.py，但改不同段落（safety vs topics）。若并行执行，各自只动自己的 dataclass 和工厂。
- 落点校验。

## 13. 成功标准

- [ ] `SafetyConfig` 含 max_tcp_step_m/max_quat_delta/gripper_width_min/max/enable_quaternion_check/enable_nan_inf_check。
- [ ] 无 `max_joint_delta_rad`/`hand_min`/`hand_max`/`JointLimitsConfig` 残留。
- [ ] `RuntimeConfig.action_dim==16`、`state_dim==16`。
- [ ] mode 三档枚举不变。
- [ ] `test_safety.py` PASSED。
- [ ] 未修改 pi05/types/deploy_005基础/deploy_006 topics。

## 14. 回滚方式

`git checkout -- src/model_deploy/act/config/schema.py`（回退 safety+runtime 段）。

## 15. 完成后交接

（执行 sub-agent 完成后填写）
