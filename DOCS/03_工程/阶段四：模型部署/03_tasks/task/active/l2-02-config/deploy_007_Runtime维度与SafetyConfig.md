# L3 微元改造任务：RuntimeConfig 默认维度 + SafetyConfig 重构

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 Config 层重构
来源 Delta：D9（encoded_state 维度）、D11（action 维度）、D13（safety 关节→TCP/width）
L3 编号：deploy_007
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_007_Runtime维度与SafetyConfig.md`
改造类型：behavior-change
真机风险等级：none

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_007
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_007_Runtime维度与SafetyConfig.md
  group: l2-02-config
  branch: model_deploy
  wave: 3
  parallel_group: l2-02-config-p3
  depends_on: [deploy_006]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_008]
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py
    modules:
      - pi05.deploy.config.schema
    config_keys:
      - runtime.action_dim
      - runtime.state_dim
      - safety
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 RuntimeConfig 的 action_dim/state_dim 默认值从 14/26 改为 16/16（第一版），把 SafetyConfig 从关节空间检查（max_joint_delta_rad/hand_min/hand_max）改为 policy-action 层 TCP/width 检查（max_tcp_delta_m/gripper_width_min/max），保留 JointLimitsConfig 作 bridge 参数来源。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D9 + D11 + D13 |
| 变更对象 | Input Contract · encoded_state 维度 + Action 维度 + Safety 检查 |
| AS-IS 契约 | `RuntimeConfig.action_dim=14/state_dim=26`（schema.py:48-49）；`_deploy_from_mapping` 默认 14/26（L295-296）；`SafetyConfig`（L188-199）：max_joint_delta_rad=0.08/stale_observation_timeout_s/clamp_normalized_action/hand_min=300/hand_max=1000/joint_limits。`_safety_config`（L429-450）。 |
| TO-BE 契约 | action_dim=16/state_dim=16（第一版）；SafetyConfig：max_tcp_delta_m（TCP单步位移）/gripper_width_min=0.0/gripper_width_max=1.0；保留 stale_observation_timeout_s/clamp_normalized_action/JointLimitsConfig。依据：Q3（16D）+ Q6（state 16D第一版）+ D13。 |
| 兼容性要求 | 破坏性。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-02 Config 层重构
- 本 L3 在该 L2 中的位置：第三个，依赖 deploy_006（同改 schema.py）。
- 本 L3 完成后解锁：deploy_008（deploy.yaml + 单测）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `RuntimeConfig.action_dim` | schema.py:48 `= 14` | action 维度默认 | 改 16 | 是 |
| `RuntimeConfig.state_dim` | schema.py:49 `= 26` | state 维度默认 | 改 16（第一版） | 是 |
| `_deploy_from_mapping` action_dim/state_dim 默认 | schema.py:295-296 `default=14/26` | 加载默认值 | 改 16/16 | 是 |
| `SafetyConfig.max_joint_delta_rad` | schema.py:192 `= 0.08` | 关节 delta 限幅 | 改为 max_tcp_delta_m（语义变） | 是 |
| `SafetyConfig.hand_min/hand_max` | schema.py:197-198 `= 300/1000` | 手部尺度 clip | 改为 gripper_width_min/max=0.0/1.0 | 是 |
| `SafetyConfig.joint_limits` | schema.py:199 | 关节限位配置 | **保留**（下移 bridge 作参数来源） | 否（保留） |
| `_safety_config` | schema.py:429-450 | 解析 safety 字段 | 字段名跟随 | 是 |
| `JointLimitsConfig` | schema.py:177-185 | 关节限位 rad | **保留**（bridge 用） | 否（保留） |

### 必须保留的现有行为

- `RuntimeConfig` 调度参数（inference_hz/control_hz/chunk_size/execute_horizon/prefetch_steps/blend_steps/max_action_age_sec/fallback_policy 等）**全部不动**。
- `RuntimeConfig.mode` 三档（dry/shadow/safe）+ `publishes_command_topics` 属性**不动**（Q4）。
- `__post_init__` 校验逻辑不动。
- `SafetyConfig.stale_observation_timeout_s`/`clamp_normalized_action`/`hold_last_action` 保留。
- `JointLimitsConfig` 保留（D13：关节限位下移 bridge，但配置保留作参数来源）。

### 已知风险

- 改 action_dim/state_dim 默认后，policy_loader 用 `config.runtime.action_dim` 覆盖 exp_config（policy_loader.py:184）会拿到 16——正确。但 control_loop 用 action_dim 校验 chunk，需确认一致（16D）。
- SafetyConfig 字段改名后，safety_guard.py 读 `config.max_joint_delta_rad`/`hand_min` 会失配——但 safety_guard 在 L2-04 改（D13），本 L3 不改 safety_guard。预期中间状态。

## 6. 真实改造边界

### 本次允许做

**RuntimeConfig 维度（schema.py:48-49）：**
- `action_dim: int = 14` → `16`
- `state_dim: int = 26` → `16`（第一版）

**_deploy_from_mapping 默认值（schema.py:295-296）：**
- `action_dim=...default=14` → `16`
- `state_dim=...default=26` → `16`

**SafetyConfig 字段（schema.py:188-199）：**
- `max_joint_delta_rad: float = 0.08` → `max_tcp_delta_m: float`（TCP 单步位移限幅，语义从关节rad变TCP米；默认值待定，建议保守值如 0.05）
- `hand_min: float = 300.0` → `gripper_width_min: float = 0.0`
- `hand_max: float = 1000.0` → `gripper_width_max: float = 1.0`
- 保留 `stale_observation_timeout_s`/`command_timeout_s`/`clamp_normalized_action`/`hold_last_action`/`joint_limits`

**_safety_config（schema.py:429-450）：**
- 字段名跟随（max_joint_delta_rad→max_tcp_delta_m，hand_min/max→gripper_width_min/max）
- 注意 max_joint_delta_rad 原来从 runtime.max_delta_per_step 取默认（L434-435），max_tcp_delta_m 可保留类似 fallback 或独立默认

### 本次不做

- 不改 RuntimeConfig 调度参数和 mode。
- 不改 JointLimitsConfig（保留）。
- 不改 safety_guard.py（L2-04 做）。
- 不改 deploy.yaml（deploy_008 做）。
- 不补单测（deploy_008 做）。

### 明确禁止修改

- 禁止改 RuntimeConfig 的调度参数（inference_hz 等）和 mode 三档。
- 禁止删 JointLimitsConfig（保留作 bridge 参数）。
- 禁止改 ObservationTopicsConfig/CommandTopicsConfig（deploy_005/006 已改）。
- 禁止改 safety_guard.py。

### Adapter / 直接修改策略

```text
直接修改。维度默认值是单一真相源（配合 L2-01 的 ACTION_DIM/STATE_DIM）。SafetyConfig 字段语义从关节空间转 TCP 空间，字段名同步改。JointLimitsConfig 保留（不破坏 bridge 的参数来源）。回滚靠 git。
```

## 7. 实施步骤

1. **改 RuntimeConfig**（schema.py:48-49）：action_dim=16, state_dim=16。
2. **改 _deploy_from_mapping**（schema.py:295-296）：action_dim/state_dim default 改 16。
3. **改 SafetyConfig**（schema.py:188-199）：max_joint_delta_rad→max_tcp_delta_m（默认值如 0.05），hand_min/hand_max→gripper_width_min=0.0/gripper_width_max=1.0；保留其他字段和 joint_limits。
4. **改 _safety_config**（schema.py:429-450）：字段名跟随，调整默认值 fallback。
5. **AST 验收**：确认维度 16、safety 新字段。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
import ast
src = open('pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py', encoding='utf-8').read()
tree = ast.parse(src)
# RuntimeConfig action_dim/state_dim 默认 16（需从 AST 提取，或用文本检查）
# 文本检查更简单：
assert 'action_dim: int = 16' in src or 'action_dim: int=16' in src, 'action_dim default should be 16'
assert 'state_dim: int = 16' in src or 'state_dim: int=16' in src, 'state_dim default should be 16'
# SafetyConfig 新字段
assert 'max_tcp_delta_m' in src, 'max_tcp_delta_m missing'
assert 'gripper_width_min' in src and 'gripper_width_max' in src
# 旧字段删除
assert 'max_joint_delta_rad' not in src or 'max_joint_delta_rad' in src.split('_safety_config')[0][:0], 'max_joint_delta_rad in SafetyConfig should be renamed'
assert 'hand_min' not in src.split('class SafetyConfig')[1].split('class')[0], 'hand_min should be removed from SafetyConfig'
# JointLimitsConfig 保留
assert 'class JointLimitsConfig' in src, 'JointLimitsConfig should be preserved'
# _deploy_from_mapping 默认 16
assert 'default=16' in src
print('deploy_007 验收通过: 维度16/16, SafetyConfig→TCP/width, JointLimits保留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST/文本维度断言 | 上述命令通过 |
| dry-run | 否 | — | — |

### 真机风险控制

不适用。

## 9. 允许修改

- `pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（RuntimeConfig 维度 + SafetyConfig）

## 10. 禁止修改

- RuntimeConfig 调度参数和 mode。
- JointLimitsConfig（保留）。
- ObservationTopicsConfig/CommandTopicsConfig（已改）。
- safety_guard.py。
- 通用辅助函数。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D9/D11/D13 + Q3 16D + Q6 state 16D）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-Config层重构.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（RuntimeConfig/SafetyConfig/_safety_config）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_006。
2. 同组已完成：deploy_005、deploy_006。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_006]` 已完成。

```text
最小复现 / 测试（AST 维度断言）
→ 最小实现（改维度 + SafetyConfig）
→ 验证通过
→ 必要整理（docstring + max_tcp_delta_m 默认值注释）
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] action_dim/state_dim 默认 16/16。
- [ ] SafetyConfig 改为 TCP/width 检查字段。
- [ ] JointLimitsConfig 保留。
- [ ] RuntimeConfig 调度参数和 mode 未动。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- schema.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改内容、max_tcp_delta_m 默认值选择、验收结果、成功标准勾选、真机影响（无）、回滚、未做事项（没改调度参数/mode/JointLimits/safety_guard/deploy.yaml）、后续建议（deploy_008）。
