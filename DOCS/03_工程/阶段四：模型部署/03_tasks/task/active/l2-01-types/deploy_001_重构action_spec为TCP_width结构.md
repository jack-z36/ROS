# L3 微元改造任务：重构 action_spec 为 TCP+width 结构

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-01 Types 层重构
来源 Delta：D11（action 语义：关节空间 → TCP 绝对目标 16D）
L3 编号：deploy_001
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_001_重构action_spec为TCP_width结构.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-01-types
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
对应 L2 运行验收场景：[S1, S2]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_001_验收卡片.md
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_001
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_001_重构action_spec为TCP_width结构.md
  group: l2-01-types
  branch: model_deploy-l2-01-types
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types
  acceptance_scenarios: [S1, S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_001_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs
  wave: 1
  parallel_group: l2-01-types-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_002, deploy_003]
  conflict_scope:
    files:
      - src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py
    modules:
      - pi05.common.robot.action_spec
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 action_spec.py 的 BimanualAction 从关节空间（left_arm/right_arm/left_hand/right_hand，14D）改为 TCP 绝对目标结构（left_tcp_pose[7]/left_gripper_width/right_tcp_pose[7]/right_gripper_width，16D），并同步更新 ACTION_DIM/STATE_DIM 常量和 split_bimanual_action 段序，删除不再需要的 hand_command_to_trigger。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D11 |
| 变更对象 | Action Contract · action 语义 |
| AS-IS 契约 | 14D = `[left_arm_joint6, right_arm_joint6, left_hand1, right_hand1]`，关节空间绝对命令。源码：`action_spec.py:17,22-52`。 |
| TO-BE 契约 | 16D = `[left_tcp(x,y,z,qx,qy,qz,qw), left_gripper_width, right_tcp(x,y,z,qx,qy,qz,qw), right_gripper_width]`，绝对 TCP 目标，段序交替排列。依据：阶段二 `数据清洗交付说明.md:25-28`。 |
| 兼容性要求 | 破坏性修改（旧 bundle/旧 config 无法配合，回滚靠 git + 旧 bundle）。 |
| 回滚要求 | git 回退 action_spec.py + 切回旧 bundle。 |

### 所属 L2 改造工作包

- L2 名称：L2-01 Types 层重构
- 本 L3 在该 L2 中的位置：**地基第一个**。action_spec 定义 ACTION_DIM/STATE_DIM 常量，被 state_codec / action_codec / config / collector / safety_guard 等几乎所有上层引用。必须最先改。
- 本 L3 完成后解锁的后续任务：deploy_002（state_codec 用新 STATE_DIM）、deploy_003（action_codec 跟随）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `ACTION_DIM` | `action_spec.py:17`，值 `14` | action 向量维度单一真相源 | 应为 16 | 是 |
| `STATE_DIM` | `action_spec.py:18`，值 `26` | state 向量维度单一真相源（第一版不含触觉） | 应为 16（第一版） | 是 |
| `ARM_DOF` | `action_spec.py:15`，值 `6` | 关节自由度 | 改造后 action 不再以关节为主语义，但保留供 IK 兜底 | 否（保留，标注非主路径） |
| `ARM_JOINT_NAMES` | `action_spec.py:19` | 关节名元组 | 保留供 IK 兜底 | 否（保留） |
| `BimanualAction` | `action_spec.py:22-39` | frozen dataclass，字段 left_arm/right_arm/left_hand/right_hand + as_vector() 拼 14D | 字段应改为 TCP+width；as_vector 段序改交替 16D | 是 |
| `split_bimanual_action` | `action_spec.py:42-52` | 14D 向量 → BimanualAction，段序 left_arm6+right_arm6+hand2 | 应按 16D 交替段序拆 | 是 |
| `hand_command_to_trigger` | `action_spec.py:55-59` | 手部尺度→trigger 转换 | TO-BE 不再用 trigger，转换移到 bridge（width→angle） | 是（删除） |

### 必须保留的现有行为

- frozen dataclass 不可变性 + as_vector/split 双向转换模式。
- 维度常量（ACTION_DIM/STATE_DIM）作为单一真相源的模式。
- 严格维度校验 + 报错语义（不静默截断/补零）。
- `ARM_DOF`/`ARM_JOINT_NAMES` 保留（IK 兜底、关节限位可能用）。

### 已知风险

- 改 ACTION_DIM/STATE_DIM 后，**所有引用这两个常量的上层代码会立即失配**（state_codec、action_codec、config schema、control_loop、observation_collector 等）。本 L3 只改 action_spec，不改上层——上层会在 deploy_002/003 及后续 L2 修复。**本 L3 完成后，整个 deploy 包暂时无法 import 通过，这是预期的中间状态**，直到 L2-01 全部 L3 完成。
- 因此本 L3 的验收**不要求整个包 import 通过**，只要求 action_spec.py 自身语法正确 + 常量值正确（见验收）。

## 6. 真实改造边界

### 本次允许做

- 改 `ACTION_DIM` 14→16、`STATE_DIM` 26→16。
- 新增常量 `TCP_POSE_DOF = 7`、`GRIPPER_WIDTH_DOF = 1`（供 split/encode 引用，避免魔法数字）。
- 重构 `BimanualAction` 字段为 TCP+width 结构。
- 改 `as_vector` 段序为交替排列（left_tcp[7]+left_width+right_tcp[7]+right_width）。
- 改 `split_bimanual_action` 段序为交替拆分。
- 删除 `hand_command_to_trigger`。

### 本次不做

- 不改 state_codec.py（deploy_002 做）。
- 不改 action_codec.py（deploy_003 做）。
- 不改 config schema / collector / safety_guard 等上层（后续 L2 做）。
- 不补单测（deploy_004 做）。
- 不改 ARM_DOF / ARM_JOINT_NAMES（保留）。

### 明确禁止修改

- 禁止改 `pi05_test/` 以外的任何文件（本 L3 只动 action_spec.py）。
- 禁止为了「让整个包能 import」而顺手改上层代码——那会扩大改动范围，违反微元任务原则。
- 禁止删除 ARM_DOF / ARM_JOINT_NAMES（IK 兜底需要）。

### Adapter / 直接修改策略

```text
直接修改。action_spec.py 是 Types 层地基，用 adapter 包裹旧结构会导致上层全部适配两层语义，得不偿失。维度常量作为单一真相源，改一处即生效。回滚靠 git。
```

## 7. 实施步骤

1. **改常量**：`ACTION_DIM = 14` → `16`；`STATE_DIM = 26` → `16`（第一版，不含触觉）。新增 `TCP_POSE_DOF = 7`、`GRIPPER_WIDTH_DOF = 1`。
2. **重构 BimanualAction 字段**：删除 `left_arm/right_arm/left_hand/right_hand`；新增 `left_tcp_pose: np.ndarray`、`left_gripper_width: float`、`right_tcp_pose: np.ndarray`、`right_gripper_width: float`。更新 docstring 说明「TCP 绝对目标，quaternion xyzw，width 归一化 [0,1]」。
3. **改 as_vector 段序**：交替排列 `left_tcp_pose(7) + [left_gripper_width] + right_tcp_pose(7) + [right_gripper_width]`，用 TCP_POSE_DOF/GRIPPER_WIDTH_DOF 常量，输出 16D。
4. **改 split_bimanual_action 段序**：按交替段序拆 16D（`[0:7]`左tcp、`[7:8]`左width、`[8:15]`右tcp、`[15:16]`右width），用常量表达 offset。
5. **删除 hand_command_to_trigger** 函数整体（L55-59）。
6. **更新模块 docstring**：说明 action 现在是 TCP 绝对目标语义，段序交替，引用数据清洗交付说明。

## 8. 验证方式

### 自动化验收命令

本 L3 完成后整个 deploy 包暂时无法 import（上层未跟进），因此验收用**单文件语法检查 + 常量断言**，不要求整包 import。

```bash
python3 -c "
import ast, sys
path = 'src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py'
tree = ast.parse(open(path, encoding='utf-8').read())
# 提取模块级赋值，检查常量值
assigns = {t.targets[0].id: t.value.value for t in tree.body if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name) and isinstance(t.value, ast.Constant)}
assert assigns.get('ACTION_DIM') == 16, f'ACTION_DIM should be 16, got {assigns.get(\"ACTION_DIM\")}'
assert assigns.get('STATE_DIM') == 16, f'STATE_DIM should be 16, got {assigns.get(\"STATE_DIM\")}'
assert assigns.get('TCP_POSE_DOF') == 7
assert assigns.get('GRIPPER_WIDTH_DOF') == 1
# 检查 hand_command_to_trigger 已删除
src = open(path, encoding='utf-8').read()
assert 'hand_command_to_trigger' not in src, 'hand_command_to_trigger should be removed'
# 检查 BimanualAction 字段名
assert 'left_tcp_pose' in src and 'left_gripper_width' in src and 'right_tcp_pose' in src and 'right_gripper_width' in src
print('deploy_001 验收通过: ACTION_DIM=16, STATE_DIM=16, TCP+width结构, trigger已删')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | action_spec.py AST 解析 + 常量断言 + 字段名检查 | 上述命令全部 assert 通过 |
| dry-run | 否 | — | — |
| fake-policy | 否 | — | — |
| real-policy | 否 | — | — |
| real-robot | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作（纯 Types 层数据结构定义）。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-types/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`

## 10. 禁止修改

- 除上述文件外的任何文件。
- action_spec.py 内的 `ARM_DOF`、`ARM_JOINT_NAMES`（保留）。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/AS-IS Contract.md`
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`
3. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D11）
4. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-01-Types层重构.md`
5. `DOCS/01_知识/阶段二：数据清洗/数据清洗交付说明.md`（action 段序权威定义，L21-36）

### 必读代码

1. `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`（本 L3 直接修改）
2. `src/model_deploy/pi05/common/src/pi05/common/data/state_codec.py`（下游，确认它 import 了哪些常量，但本 L3 不改它）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游 L3（本 L3 是 L2-01 的第一个）。
2. 无同组已完成 L3。

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
- `depends_on` 已完成或明确无需等待。
- `dispatch_status` 不是 `blocked` 或 `waiting_user`。
- `robot_risk` 与验收方式一致。
如果本 L3 涉及代码修改，必须采用测试优先或最小复现优先：

```text
最小复现 / 测试（AST 断言脚本）
→ 最小实现（改 action_spec.py）
→ 验证通过（AST 断言通过）
→ 必要整理（更新 docstring）
```

不得为了通过当前 L3 验收而擅自扩大修改范围（如顺手改 state_codec 让整包能 import）。

## 13. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取 AS-IS、TO-BE、Contract Delta 和所属 L2。
- [x] 已完成现有程序盘点中列出的相关代码确认。
- [x] 改动没有破坏必须保留的原始行为（frozen dataclass / 维度校验 / ARM_DOF 保留）。
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录。
- [x] 已完成本 L3 的自动化验收（AST 断言通过）。
- [x] 如涉及真机发送链路，已完成真机风险控制说明。（不适用）
- [x] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：不适用
切回旧入口：不适用
移除 adapter：不适用（本 L3 直接修改）
回退文件：git checkout -- src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py
不可自动回滚的人工步骤：无
```

注意：本 L3 回滚后，依赖 ACTION_DIM/STATE_DIM 的上层代码会回到旧 14/26 语义。完整回滚需配合切回旧 bundle（26D state / 14D action）。

## 15. 完成后交接

必须更新：

- 当前 L3 任务文件本身：勾选已验证成功标准，并在末尾追加执行摘要。
- 不擅自创建 completed 目录或归档规则，按用户或主 Agent 指示处理。
- 不得擅自更新阶段级进度文档、共享执行记录或 Git 状态。

交接摘要必须包含：

1. 读取了哪些 Contract、L2、代码和历史任务。
2. 任务文件身份校验结论。
3. 修改了哪些文件。
4. 新增或修改了哪些函数、类、配置、测试或脚本。
5. 如何验证，实际命令是什么。
6. 哪些成功标准已勾选，哪些未验证。
7. 是否影响 dry-run、fake-policy、real-policy 或 real-robot（本 L3 是 Types 层，影响所有上层但本身不触发真机）。
8. 回滚方式。
9. 本次明确没有做什么（没改 state_codec/action_codec/上层，没补单测）。
10. 后续建议生成或执行的 L3（deploy_002 state_codec、deploy_003 action_codec）。

---

## 16. 执行摘要（deploy_001）

### 读取的上下文

- AS-IS Contract.md（阶段四）
- TO-BE Contract.md（阶段四）
- Contract Delta.md（D11 action 语义变更）
- L2-01-Types层重构.md
- 数据清洗交付说明.md（阶段二，action 段序权威定义）
- state_codec.py（确认 import 了哪些常量）
- action_spec.py（本 L3 直接修改的文件）

### 身份校验结论

| 检查项 | 结果 |
|---|---|
| 用户指定任务路径 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-types/deploy_001_重构action_spec为TCP_width结构.md` |
| 实际读取任务路径 | 同上 |
| 文件名 deploy ID | `deploy_001` |
| 正文 L3 编号 | `deploy_001` |
| 一致性 | ✅ 完全一致 |
| 当前分支 | `model_deploy-l2-01-types` ✅ 匹配 dispatch YAML |
| dispatch `task_id` | `deploy_001` ✅ |
| dispatch `status` | `ready` ✅ |
| dispatch `depends_on` | `[]` ✅ 无依赖（第一个 L3） |
| dispatch `robot_risk` | `none` ✅ |

### 修改的文件

1. `src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`

### 修改详情

| 变更项 | AS-IS | TO-BE |
|---|---|---|
| `ACTION_DIM` | 14 | **16** |
| `STATE_DIM` | 26 | **16**（第一版，不含触觉） |
| `TCP_POSE_DOF` | 不存在 | **新增 = 7** |
| `GRIPPER_WIDTH_DOF` | 不存在 | **新增 = 1** |
| `HAND_DOF` | 1 | **删除**（不再需要） |
| `BimanualAction` 字段 | `left_arm`/`right_arm`/`left_hand`/`right_hand` | **left_tcp_pose**/left_gripper_width/**right_tcp_pose**/right_gripper_width |
| `as_vector` 段序 | `left_arm6+right_arm6+hand2` (14D) | **left_tcp7+left_width1+right_tcp7+right_width1** (16D 交替) |
| `split_bimanual_action` 段序 | 按关节拆分 (14D) | **按交替 16D 拆分**（左 TCP→左 width→右 TCP→右 width） |
| `hand_command_to_trigger` | 存在 | **已删除** |
| 模块 docstring | 关节空间语义 | **TCP 绝对目标 + quaternion + width 语义** |
| `ARM_DOF` (6) | 保留不变 | 保留不变 |
| `ARM_JOINT_NAMES` | 保留不变 | 保留不变 |

### 验证方式

1. **AST 断言验收**（来自 L3 任务文件）：
   ```bash
   python3 -c "
   import ast
   path = 'src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py'
   tree = ast.parse(open(path).read())
   assigns = {t.targets[0].id: t.value.value
              for t in tree.body if isinstance(t, ast.Assign)
              and isinstance(t.targets[0], ast.Name)
              and isinstance(t.value, ast.Constant)}
   assert assigns.get('ACTION_DIM') == 16
   assert assigns.get('STATE_DIM') == 16
   assert assigns.get('TCP_POSE_DOF') == 7
   assert assigns.get('GRIPPER_WIDTH_DOF') == 1
   src = open(path).read()
   assert 'hand_command_to_trigger' not in src
   assert all(kw in src for kw in ('left_tcp_pose','left_gripper_width','right_tcp_pose','right_gripper_width'))
   print('deploy_001 验收通过')
   "
   ```

2. **完整 round-trip 测试**（额外验证）：
   - Construct `BimanualAction` → `as_vector()` produces 16D interleaved vector
   - `split_bimanual_action(vector)` recovers original fields exactly
   - Frozen dataclass immutability preserved
   - Wrong-dimension input raises `ValueError`
   - `ARM_DOF` (6) and `ARM_JOINT_NAMES` still accessible
   - `hand_command_to_trigger` attribute absent

### 结果

**所有验收标准通过** ✅

### 成功标准状态

- [x] 已完成任务文件身份校验
- [x] 已确认当前分支符合所属 L2 分支规范
- [x] 已读取 AS-IS、TO-BE、Contract Delta 和所属 L2
- [x] 已完成现有程序盘点中列出的相关代码确认
- [x] 改动没有破坏必须保留的原始行为（frozen dataclass / 维度校验 / ARM_DOF 保留）
- [x] 已将验收结果、脚本或日志登记到所属 L2 的 `05_acceptance` 目录
- [x] 已完成本 L3 的自动化验收（AST 断言通过）
- [x] 如涉及真机发送链路，已完成真机风险控制说明（不适用）
- [x] 已写明回滚方式

### 未验证项

- 整个 deploy 包 import（预期失败——上层 state_codec/action_codec 尚未跟进，这是 L3 边界内接受的中间状态）
- dry-run / fake-policy / real-policy / real-robot（不适用，纯 Types 层）

### 影响评估

- **dry-run**: 间接影响（ACTION_DIM/STATE_DIM 变更会传播到所有上层，需 deploy_002/003 修复后才可运行）
- **fake-policy**: 同上
- **real-policy**: 同上
- **real-robot**: 无直接触发（真机风险 = none）
- **回滚方式**: `git checkout -- src/model_deploy/pi05/common/src/pi05/common/robot/action_spec.py`

### 本次明确没有做

- 没有改 `state_codec.py`（deploy_002 做）
- 没有改 `action_codec.py`（deploy_003 做）
- 没有改任何 config / collector / safety_guard / ControlLoop / ROS 节点
- 没有补单测（deploy_004 做）
- 没有创建或修改任务索引文件
- 没有执行 Git 提交、推送或分支切换
- 没有修改 `DOCS/98_archive/`、`DOCS/99_learning/` 或 `pi05_old/`

### 后续建议

- **deploy_002**: 重构 `state_codec.py`，`BimanualState` 改为 TCP+width 结构，`encode_bimanual_state` 输出 16D
- **deploy_003**: 跟随改 `action_codec.py` 维度校验 14→16
- **deploy_004**: 补充 Types 层单测（维度/段序/round-trip/触觉预留）
- **验收卡片**: 建议运行 `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-types/deploy_001_验收卡片.md`
