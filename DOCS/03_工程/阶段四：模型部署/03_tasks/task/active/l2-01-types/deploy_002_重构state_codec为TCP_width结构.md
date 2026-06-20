# L3 微元改造任务：重构 state_codec 为 TCP+width 结构

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 Types 层重构
来源 Delta：D8（臂状态语义：关节角 → TCP pose）、D9（encoded_state 26D → 16D/32D）
L3 编号：deploy_002
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_002_重构state_codec为TCP_width结构.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-01-types
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
对应 L2 运行验收场景：[S1, S2]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_002_验收卡片.md
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_002
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_002_重构state_codec为TCP_width结构.md
  group: l2-01-types
  branch: model_deploy-l2-01-types
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
  acceptance_scenarios: [S1, S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_002_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs
  wave: 2
  parallel_group: l2-01-types-p2
  depends_on: [deploy_001]
  must_run_after: []
  can_run_parallel_with: [deploy_003]
  blocks: [deploy_004]
  conflict_scope:
    files:
      - src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py
    modules:
      - pi05.common.data.state_codec
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 state_codec.py 的 BimanualState 从关节角+EE 结构改为 TCP+width 结构，encode_bimanual_state 从 26D 改为 16D（第一版，不含触觉），并预留触觉段落开关（include_tactile，True 时追加触觉段输出 32D），删除 picotele 专有的 decode_picotele_proprioception。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D8 + D9 |
| 变更对象 | Input Contract · 臂状态语义 + encoded_state |
| AS-IS 契约 | `BimanualState` = left_arm_q/right_arm_q/left_hand_q/right_hand_q/left_ee_pos/left_ee_rpy/right_ee_pos/right_ee_rpy；`encode_bimanual_state` 拼 26D `[left_arm_q6, right_arm_q6, left_hand1, right_hand1, left_ee_pos3, left_ee_rpy3, right_ee_pos3, right_ee_rpy3]`。源码：`state_codec.py:13-43`。 |
| TO-BE 契约 | `BimanualState` = left_tcp_pose[7]/right_tcp_pose[7]/left_gripper_width/right_gripper_width；`encode_bimanual_state` 拼 **16D**（第一版），**state 段序为「全左→全右」**（left_tcp7+right_tcp7+left_width1+right_width1），与 action 的交替段序不同；预留触觉段（include_tactile=True 时输出 32D，触觉段 [16,32)）。依据：阶段二 `数据清洗交付说明.md:11-18,35-36`。 |
| 兼容性要求 | 破坏性修改。回滚靠 git + 旧 bundle。 |
| 回滚要求 | git 回退 state_codec.py + 切回旧 bundle。 |

### 所属 L2 改造工作包

- L2 名称：L2-01 Types 层重构
- 本 L3 在该 L2 中的位置：第二个。依赖 deploy_001 改好的 `STATE_DIM`/`TCP_POSE_DOF`/`GRIPPER_WIDTH_DOF` 常量。
- 本 L3 完成后解锁的后续任务：deploy_004（单测覆盖 encode）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `BimanualState` | `state_codec.py:13-24` | frozen dataclass，关节角+EE 字段 | 应改为 TCP+width 字段 | 是 |
| `encode_bimanual_state` | `state_codec.py:27-43` | 拼 26D，校验 `STATE_DIM` | 应拼 16D（全左→全右段序）+ 预留触觉 | 是 |
| `decode_picotele_proprioception` | `state_codec.py:46-53` | 解 picotele [right6,left6] 顺序 | picotele 专有，不再需要 | 是（删除） |
| `_vector` | `state_codec.py:56-60` | 维度校验辅助 | 复用，改调用处的 dim 参数 | 否（保留辅助） |
| import | `state_codec.py:10` `from pi05.common.robot.action_spec import ARM_DOF, STATE_DIM` | 引用旧常量 | deploy_001 已改 STATE_DIM=16；ARM_DOF 不再用（改用 TCP_POSE_DOF）；需调整 import | 是（改 import） |

### 必须保留的现有行为

- frozen dataclass 不可变性。
- `encode_bimanual_state` 的严格维度校验 + 报错（不静默截断）。
- `_vector` 维度校验辅助函数。
- encode 输出 float32。

### 已知风险

- 改 BimanualState 字段后，**引用它的上层会立即失配**：`observation_collector.snapshot`（构造 BimanualState）、`safety_guard._delta_anchor`（读 state.left_arm_q）、`shared_buffer.ObservationSnapshot`（持有 BimanualState）。这些上层在 L2-03/L2-04 修复，本 L3 不改它们。
- **本 L3 完成后，observation_collector / safety_guard 暂时无法 import 通过**，这是预期中间状态。
- state 段序（全左→全右）与 action 段序（交替）**必须不同**——这是数据清洗交付说明 L36 的明确 warning，写错会导致 train/deploy 语义错位。

## 6. 真实改造边界

### 本次允许做

- 重构 `BimanualState` 字段为：`left_tcp_pose: np.ndarray`（[x,y,z,qx,qy,qz,qw]，7D）、`right_tcp_pose: np.ndarray`（7D）、`left_gripper_width: float`（[0,1]）、`right_gripper_width: float`（[0,1]）。
- 改 `encode_bimanual_state`：
  - 段序「全左→全右」：left_tcp_pose7 + right_tcp_pose7 + left_gripper_width1 + right_gripper_width1 = 16D。
  - 新增 `include_tactile: bool = False` 参数（默认 False，第一版）。
  - `include_tactile=True` 时：在 16D 后追加触觉段，输出 32D（触觉数据由调用方传入，本函数只负责拼装位置；触觉段的具体语义在后续版本定义，本 L3 预留接口位即可）。
  - 维度校验跟随 STATE_DIM（16 或 32）。
- 删除 `decode_picotele_proprioception`。
- 调整 import：移除 `ARM_DOF`（不再用），保留 `STATE_DIM`，新增引用 `TCP_POSE_DOF`/`GRIPPER_WIDTH_DOF`（来自 deploy_001 改好的 action_spec）。

### 本次不做

- 不改 observation_collector / safety_guard / shared_buffer（L2-03/L2-04 做）。
- 不实现触觉的具体聚合算法（6×15→4D），只预留位置和开关（后续版本）。
- 不补单测（deploy_004 做）。
- 不改 action_spec（deploy_001 已改）。

### 明确禁止修改

- 禁止改 state_codec.py 以外的文件。
- 禁止把 state 段序写成和 action 一样的交替排列（**这是关键错误**，会导致 train/deploy 错位）。
- 禁止在本 L3 实现 6×15 触觉聚合（超出范围）。

### Adapter / 直接修改策略

```text
直接修改。state_codec 是 Types 层，与 action_spec 同层。BimanualState 字段整体替换。触觉段落用参数开关预留（include_tactile），不破坏第一版 16D 主路径。
```

## 7. 实施步骤

1. **改 import**（L10）：移除 `ARM_DOF`，保留 `STATE_DIM`，新增 `TCP_POSE_DOF, GRIPPER_WIDTH_DOF`（从 action_spec import）。
2. **重构 BimanualState 字段**（L13-24）：删除 left_arm_q/right_arm_q/left_hand_q/right_hand_q/left_ee_pos/left_ee_rpy/right_ee_pos/right_ee_rpy；新增 left_tcp_pose[7]/right_tcp_pose[7]/left_gripper_width/right_gripper_width。更新 docstring（quaternion xyzw + m，width [0,1]）。
3. **改 encode_bimanual_state**（L27-43）：
   - 签名加 `include_tactile: bool = False, tactile_segments: tuple[np.ndarray, ...] | None = None`（触觉数据可选传入，None 时触觉段填零或报错——本 L3 选「include_tactile=True 但 tactile_segments=None 时报错」）。
   - 段序拼装：left_tcp_pose(TCP_POSE_DOF) + right_tcp_pose(TCP_POSE_DOF) + [left_gripper_width] + [right_gripper_width]。
   - include_tactile=True 时：校验 tactile_segments 非空，追加触觉段，总维度 32。
   - 维度校验：include_tactile=False 校验 == STATE_DIM(16)；True 校验 == 32。
4. **删除 decode_picotele_proprioception**（L46-53）。
5. **更新模块 docstring**：说明 state 现在是 TCP+width 语义，段序全左→全右（与 action 交替不同），触觉预留，引用数据清洗交付说明。

## 8. 验证方式

### 自动化验收命令

本 L3 完成后上层仍无法 import，验收用单文件 AST + 逻辑断言。

```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py'
src = open(path, encoding='utf-8').read()
tree = ast.parse(src)
# 检查 decode_picotele_proprioception 已删
assert 'decode_picotele_proprioception' not in src, 'decode_picotele_proprioception should be removed'
# 检查 BimanualState 新字段
assert 'left_tcp_pose' in src and 'right_tcp_pose' in src and 'left_gripper_width' in src and 'right_gripper_width' in src
# 检查 include_tactile 参数存在
assert 'include_tactile' in src, 'include_tactile param should exist'
# 检查不再引用 ARM_DOF（state_codec 不再用关节自由度）
assert 'ARM_DOF' not in src, 'ARM_DOF should not be referenced in state_codec anymore'
print('deploy_002 验收通过: BimanualState→TCP+width, include_tactile预留, picotele解码已删')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | state_codec.py AST 解析 + 字段/参数断言 | 上述命令 assert 通过 |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

> [!note] 段序正确性的完整验证
> encode 的「全左→全右」段序与 action 的「交替」段序差异，在 deploy_004 单测中用 round-trip + 段序断言覆盖。本 L3 只保证结构和参数正确。

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py`

## 10. 禁止修改

- 除上述文件外的任何文件。
- state_codec.py 中 `_vector` 辅助函数（保留）。
- 禁止把 state 段序写成交替排列。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/AS-IS Contract.md`
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`
3. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D8/D9/Q6 触觉分两版）
4. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-Types层重构.md`
5. `DOCS/01_知识/阶段二：数据清洗/数据清洗交付说明.md`（state 段序 L11-18，段序差异 warning L35-36）

### 必读代码

1. `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py`（本 L3 直接修改）
2. `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`（deploy_001 改后，确认新常量 TCP_POSE_DOF/GRIPPER_WIDTH_DOF/STATE_DIM）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游 L3：deploy_001（action_spec 重构，提供新常量）。
2. 同组已完成 L3：deploy_001。

## 12. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：
正文 L3 编号：
是否一致：
```

执行前必须读取 `dispatch` YAML，确认：

- `task_id` 与正文 L3 编号一致。
- `task_file` 与当前文件路径一致。
- `branch` 是当前 L2 分支 `model_deploy-l2-01-types`。
- `integration_branch` 是 `model_deploy`。
- `acceptance_dir` 指向 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types`。
- `depends_on: [deploy_001]` 已完成（deploy_001 已归档或确认 action_spec 新常量就位）。
- `dispatch_status` 不是 `blocked` 或 `waiting_user`。
- `robot_risk` 与验收方式一致（none）。
```text
最小复现 / 测试（AST 断言脚本）
→ 最小实现（改 state_codec.py）
→ 验证通过
→ 必要整理（更新 docstring + 段序注释）
```

不得为了通过验收而擅自改上层代码让整包 import。

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] 已读取 AS-IS、TO-BE、Contract Delta 和所属 L2。
- [ ] 已确认 deploy_001 的新常量（TCP_POSE_DOF/GRIPPER_WIDTH_DOF/STATE_DIM）已就位。
- [ ] 改动没有破坏必须保留的原始行为（frozen dataclass / 维度校验 / float32 / _vector）。
- [ ] state 段序为全左→全右（非交替）。
- [ ] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [ ] 已完成本 L3 的自动化验收（AST 断言通过）。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：include_tactile 默认 False（第一版不触觉）
切回旧入口：不适用
移除 adapter：不适用（直接修改）
回退文件：git checkout -- src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py
不可自动回滚的人工步骤：无
```

完整回滚需配合 deploy_001 回退（action_spec）+ 切回旧 bundle。

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 不擅自归档，按用户或主 Agent 指示处理。

交接摘要必须包含：

1. 读取了哪些 Contract、L2、代码和历史任务。
2. 任务文件身份校验结论。
3. 修改了哪些文件。
4. 新增或修改了哪些函数、类。
5. 如何验证，实际命令是什么。
6. 哪些成功标准已勾选，哪些未验证。
7. 是否影响 dry-run/fake-policy/real-policy/real-robot（Types 层，影响上层但本身不触发真机）。
8. 回滚方式。
9. 本次明确没有做什么（没改上层、没实现触觉聚合算法、没补单测）。
10. 后续建议生成或执行的 L3（deploy_004 单测）。
