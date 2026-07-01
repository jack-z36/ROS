# L3 微元改造任务：safety_guard 改造为 policy-action 通用检查

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-04 action 处理与发布层
来源 Delta：D13（safety 职责切分：关节检查 → policy-action 通用检查）
L3 编号：deploy_013
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_013_safety_guard改造.md`
改造类型：behavior-change
真机风险等级：none（纯逻辑，真机安全门在 bridge/L2-05）

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_013
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_013_safety_guard改造.md
  group: l2-04-publish
  branch: model_deploy
  wave: 1
  parallel_group: l2-04-publish-p1
  depends_on: [deploy_001, deploy_007]
  must_run_after: []
  can_run_parallel_with: [deploy_014]
  blocks: [deploy_016]
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/src/pi05/deploy/runtime/safety_guard.py
    modules:
      - pi05.deploy.runtime.safety_guard
    config_keys:
      - safety
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 safety_guard 从关节空间检查（max_joint_delta_rad 关节限幅 + hand_min/max clip）改造为 policy-action 通用检查（shape=16D + NaN/Inf + quaternion 归一化 + TCP 单步位移限幅 + gripper_width 值域[0,1]），保留 filter_action 接口签名让 ControlLoop 不用改，保留 SafetyResult 语义。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D13 |
| 变更对象 | Safety 检查 |
| AS-IS 契约 | `SafetyGuard.filter_action`（safety_guard.py:35-73）关节 delta 限幅：取 anchor（observation 关节角或上一帧），max_joint_delta_rad 限幅，hand_min=300/hand_max=1000 clip，返回 BimanualAction(关节)。`_build_joint_limits`（L76-84）/`JointLimitSpec`（L8-11）。依赖 `SafetyConfig.max_joint_delta_rad/hand_min/hand_max/joint_limits`。 |
| TO-BE 契约 | filter_action 做 policy-action 通用检查：action shape==ACTION_DIM(16)；全部 finite；quaternion 段归一化（pose 段 [0:7]/[8:15] 模长≈1）；TCP 单步位移限幅（max_tcp_delta_m，相对 observation.tcp_pose 或上一帧）；gripper_width 段 ∈[0,1]。返回新 BimanualAction(TCP+width)。硬件检查（workspace/IK/关节限位/angle限幅）下移 bridge（L2-05）。 |
| 兼容性要求 | 接口签名保留（filter_action 不变签名，让 ControlLoop 不改）。SafetyResult 语义保留。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-04 action 处理与发布层
- 本 L3 在该 L2 中的位置：第一个，与 deploy_014（发布侧）可并行（不同文件）。safety 是 policy 层核心。
- 本 L3 完成后解锁：deploy_016（shadow-run 验证）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `JointLimitSpec` | safety_guard.py:8-11 | 关节限位规格 | 删（关节检查下移 bridge） | 是 |
| `SafetyGuard.__init__` | safety_guard.py:14-33 | 读 SafetyConfig，_build_joint_limits | 改读新 SafetyConfig（max_tcp_delta_m/gripper_width_min/max） | 是 |
| `filter_action` | safety_guard.py:35-73 | 关节 delta 限幅 + hand clip，返回 SafetyResult(action=BimanualAction 关节) | 改 policy-action 通用检查；保留签名 | 是 |
| `_build_joint_limits` | safety_guard.py:76-84 | 构造关节限位表 | 删（或保留作诊断，不下移 bridge 的逻辑） | 是 |
| `SafetyResult` | safety_guard.py:89-99 | accepted/action/reason | 保留（action 类型跟随新 BimanualAction） | 否（保留结构） |
| import | safety_guard.py:12-13 `JointLimitsConfig`/`SafetyConfig` + BimanualAction | 引用关节 config | 改（新 SafetyConfig 字段） | 是 |

### 必须保留的现有行为

- `filter_action` 的接口签名（input: action_vector + observation + previous_action → output: SafetyResult），让 ControlLoop.tick 不用改。
- `SafetyResult` 的 `accepted: bool` + `action: BimanualAction | None` + `reason: str` 语义。
- 「失败即拒绝 + 记录 reason」语义。

### 已知风险

- 改 filter_action 返回新 BimanualAction（TCP+width）后，ControlLoop.tick 消费 SafetyResult.action 的地方会拿到新结构——但 ControlLoop 用 action.as_vector() 拼 chunk（泛型），自动跟随。确认 ControlLoop 不直接读 .left_arm_q 等旧字段（读过的代码确认它用 as_vector）。
- TCP 单步位移限幅的 anchor：相对 observation 的 TCP pose（snapshot.left_tcp_pose）还是上一帧 action？policy-action 层建议用 observation（更稳定）。但 observation 现在是 ObservationSnapshot，filter_action 需要能读 snapshot.tcp_pose。

## 6. 真实改造边界

### 本次允许做

- 删 `JointLimitSpec`（L8-11）、`_build_joint_limits`（L76-84）。
- `__init__`（L14-33）：改读新 SafetyConfig 字段（max_tcp_delta_m/gripper_width_min/gripper_width_max/stale_observation_timeout_s/clamp_normalized_action）；删 joint_limits 读取。
- `filter_action`（L35-73）重写为 policy-action 通用检查：
  1. shape 校验：len == ACTION_DIM(16)
  2. finite 校验：np.isfinite 全过
  3. quaternion 归一化校验：pose 段 [0:7] 和 [8:15] 的 quaternion 分量 [3:7] 模长≈1（tol，如 1e-3）
  4. TCP 单步位移限幅：left_tcp_xyz([0:3]) 与 anchor(observation.left_tcp_pose[0:3]) 的距离 ≤ max_tcp_delta_m；右同理。超限则拒绝（或 clamp，看 config.clamp_normalized_action）
  5. gripper_width 值域：width 段 [7]/[15] ∈ [gripper_width_min, gripper_width_max]
  6. 通过则返回 SafetyResult(accepted=True, action=BimanualAction.from_vector(vector))
- import：改引用新 SafetyConfig；保留 BimanualAction/ACTION_DIM。
- anchor 来源：filter_action 接收 observation（ObservationSnapshot），从中取 left_tcp_pose/right_tcp_pose 作 TCP anchor。

### 本次不做

- 不改 ControlLoop（确认它用 as_vector，自动跟随）。
- 不改 deploy_node（deploy_014 做发布侧）。
- 不实现硬件检查（workspace/IK/angle 限幅，L2-05 bridge 做）。
- 不补单测（deploy_016 做）。

### 明确禁止修改

- 禁止改 filter_action 的签名（ControlLoop 依赖）。
- 禁止改 SafetyResult 结构。
- 禁止改 ControlLoop / deploy_node / 其他文件。
- 禁止把硬件检查（IK/workspace）塞进 safety_guard（那是 bridge 的职责，D13 明确下移）。

### Adapter / 直接修改策略

```text
直接修改。关节检查逻辑整体替换为 TCP/width 检查。filter_action 签名保留。SafetyResult 保留。硬件检查不在本层。回滚靠 git。
```

## 7. 实施步骤

1. **删 `JointLimitSpec`/`_build_joint_limits`**（L8-11, L76-84）。
2. **改 import**（L12-13）：引用新 SafetyConfig（deploy_007 改后，字段 max_tcp_delta_m/gripper_width_min/max）。
3. **改 `__init__`**（L14-33）：读新 SafetyConfig 字段；删 joint_limits。
4. **重写 `filter_action`**（L35-73）：六步检查如上；anchor 从 observation 取 TCP pose。
5. **保留 `SafetyResult`**（L89-99）。
6. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
src = open('pi05_test/pi05/deploy/src/pi05/deploy/runtime/safety_guard.py', encoding='utf-8').read()
# 关节检查删除
assert '_build_joint_limits' not in src, '_build_joint_limits should be removed'
assert 'JointLimitSpec' not in src, 'JointLimitSpec should be removed'
assert 'max_joint_delta_rad' not in src, 'max_joint_delta_rad should be removed'
# policy-action 检查新增
assert 'max_tcp_delta_m' in src
assert 'gripper_width_min' in src and 'gripper_width_max' in src
# quaternion 归一化检查
assert 'quat' in src.lower() or 'norm' in src.lower(), 'quaternion normalization check missing'
# 签名保留
assert 'def filter_action' in src
# SafetyResult 保留
assert 'class SafetyResult' in src and 'accepted' in src
print('deploy_013 验收通过: safety_guard→policy-action通用检查')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 断言 | 上述命令通过 |
| dry-run | 否（deploy_016 做） | — | — |

### 真机风险控制

不适用。policy 层安全检查，真机硬件门在 bridge（L2-05）。本 L3 不触发真机。

## 9. 允许修改

- `pi05_test/pi05/deploy/src/pi05/deploy/runtime/safety_guard.py`

## 10. 禁止修改

- safety_guard.py 的 filter_action 签名和 SafetyResult 结构。
- ControlLoop / deploy_node / 其他文件。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D13 + Q5 七步检查）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-04-action处理与发布层.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/runtime/safety_guard.py`（本 L3 修改）
2. `pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（deploy_007 改后，确认新 SafetyConfig 字段）
3. `pi05_test/pi05/common/src/pi05/common/robot/action_spec.py`（deploy_001 改后，确认 ACTION_DIM=16/BimanualAction TCP+width）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_001（ACTION_DIM=16）、deploy_007（SafetyConfig TCP/width）。
2. 同组：无已完成（本 L3 是 L2-04 第一个，deploy_014 并行中）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_001, deploy_007]` 已完成。

```text
最小复现 / 测试（AST 断言）
→ 最小实现（重写 filter_action）
→ 验证通过
→ 必要整理
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 关节检查（max_joint_delta_rad/hand_min/max/JointLimitSpec/_build_joint_limits）删除。
- [ ] policy-action 检查新增（shape/finite/quaternion归一化/TCP位移/width值域）。
- [ ] filter_action 签名保留。
- [ ] SafetyResult 保留。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- safety_guard.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改内容、新增检查项、anchor 来源选择（observation TCP）、验收结果、成功标准勾选、真机影响（无，硬件门在 bridge）、回滚、未做事项（没改 ControlLoop/deploy_node，没塞硬件检查）、后续建议（deploy_014/016）。
