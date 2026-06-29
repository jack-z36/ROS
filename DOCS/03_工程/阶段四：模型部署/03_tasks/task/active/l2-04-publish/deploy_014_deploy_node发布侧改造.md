# L3 微元改造任务：deploy_node 发布侧改造

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-04 action 处理与发布层
来源 Delta：D12（发布出口收敛单路）、D18（runtime mode + gate）
L3 编号：deploy_014
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_014_deploy_node发布侧改造.md`
改造类型：behavior-change
真机风险等级：none（dry-run/shadow 不触发真机，真机由 bridge/L2-05）

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_014
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-publish/deploy_014_deploy_node发布侧改造.md
  group: l2-04-publish
  branch: model_deploy
  wave: 1
  parallel_group: l2-04-publish-p1
  depends_on: [deploy_001, deploy_010]
  must_run_after: [deploy_010]
  can_run_parallel_with: [deploy_013]
  blocks: [deploy_015, deploy_016]
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py
    modules:
      - pi05.deploy.ros_nodes.pi05_vla_deploy_node
    config_keys:
      - topics.command
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 deploy_node 发布侧从四路 JointState/Float64 publisher 收敛为单路 /pi05/policy_action（Float32MultiArray 16D），改 _control_tick 发新格式，删 _joint_msg 辅助，保留 mode 三档对发布的控制。只改发布侧，不改订阅侧（deploy_010 已改）。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D12 + D18 |
| 变更对象 | Action 发布出口 + Runtime mode |
| AS-IS 契约 | `_create_publishers`（pi05_vla_deploy_node.py:145-152）四路：left_arm_pub/right_arm_pub(JointState) + left_hand_pub/right_hand_pub(Float64)；`_control_tick`（L196-211）发四路；`_joint_msg`（L242-248）辅助；status/metrics topic /pi05_vla/*。 |
| TO-BE 契约 | 单路 policy_action_pub（Float32MultiArray 16D，topic=/pi05/policy_action）；_control_tick 在 mode shadow/safe 时发 16D（BimanualAction.as_vector）；dry-run 只日志打印；status/metrics 改 /pi05/*。保留 mode 三档（Q4）+ publishes_command_topics。 |
| 兼容性要求 | 破坏性（四路→单路）。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-04 action 处理与发布层
- 本 L3 在该 L2 中的位置：与 deploy_013（safety_guard）可并行（不同文件）。但与 deploy_010（订阅侧）同文件，must_run_after deploy_010。
- 本 L3 完成后解锁：deploy_015（metrics）、deploy_016（shadow-run）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `_create_publishers` | pi05_vla_deploy_node.py:145-152 | 四路 publisher + status/metrics | 删四路，加 policy_action_pub | 是 |
| `_control_tick` | pi05_vla_deploy_node.py:196-211 | command is None 不发；mode 判断；发四路；publish_metrics | 改发单路 16D | 是 |
| `_joint_msg` | pi05_vla_deploy_node.py:242-248 | 构造 JointState | 删 | 是 |
| status/metrics publisher | L147-152 | /pi05_vla/status, /pi05_vla/metrics | topic 名改 /pi05/*（跟随 deploy_006 CommandTopics） | 是（topic 来源跟随 config） |
| mode 三档 | RuntimeConfig.mode + publishes_command_topics | dry/shadow/safe | 保留（Q4） | 否（保留机制） |

### 必须保留的现有行为

- `_control_tick` 的「command is None 不发」+ mode 判断框架。
- `publishes_command_topics` 属性（mode dry-run=False，shadow/safe=True）。
- ControlLoop.tick 的调度调用（返回 ControlCommand）。
- timer 驱动的 _control_tick。

### 已知风险

- **与 deploy_010 同文件**：deploy_010 改订阅侧（已 must_run_after），本 L3 改发布侧。必须 deploy_010 先完成，本 L3 在其基础上改发布侧。或同 Agent 顺序完成两半。
- _control_tick 消费 ControlCommand.action（现在是新 BimanualAction TCP+width，deploy_001 改后），用 .as_vector() 拼 16D——自动跟随。
- mode 三档语义：dry-run 不发 policy_action；shadow/safe 发。但 shadow 的 gate 关闭在 bridge（L2-05），本 L3 的 _control_tick 在 shadow/safe 都发 policy_action。

## 6. 真实改造边界

### 本次允许做

**`_create_publishers`（L145-152）重构：**
- 删 left_arm_pub/right_arm_pub/left_hand_pub/right_hand_pub。
- 加 `policy_action_pub`（Float32MultiArray，topic 来自 config.topics.command.policy_action）。
- status/metrics publisher topic 名跟随 config（deploy_006 改 /pi05/*）。

**`_control_tick`（L196-211）重构：**
- command is None → 不发（保留）。
- mode dry-run → 日志打印 action（16D）（保留框架，改打印内容）。
- mode shadow/safe → `policy_action_pub.publish(Float32MultiArray(data=BimanualAction.as_vector()))`。
- 调 publish_metrics（保留）。

**删 `_joint_msg`（L242-248）。**

**import：**
- 加 `from std_msgs.msg import Float32MultiArray`。
- 评估 JointState 是否还需（订阅侧 deploy_010 可能已不订阅 JointState；如全不用则删 import）。

### 本次不做

- 不改订阅侧（deploy_010 已改）。
- 不改 safety_guard（deploy_013 做）。
- 不改 _publish_metrics 内容（deploy_015 做字段增强；本 L3 只保留调用点）。
- 不改 ControlLoop（调度核心不动）。

### 明确禁止修改

- 禁止改 deploy_node.py 的订阅侧（_create_subscriptions/_image_topic_map/callback）——deploy_010 范围。
- 禁止改 ControlLoop。
- 禁止改 mode 三档机制。

### Adapter / 直接修改策略

```text
直接修改。四路 publisher 整体替换为单路 policy_action。_control_tick 发布逻辑跟随。mode 三档保留。回滚靠 git。
```

## 7. 实施步骤

1. **改 import**：加 Float32MultiArray；评估删 JointState（如订阅侧不再用）。
2. **改 `_create_publishers`**（L145-152）：删四路，加 policy_action_pub；status/metrics topic 跟 config。
3. **改 `_control_tick`**（L196-211）：shadow/safe 发 Float32MultiArray(data=action.as_vector())；dry-run 日志。
4. **删 `_joint_msg`**（L242-248）。
5. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
src = open('pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py', encoding='utf-8').read()
# policy_action_pub 新增
assert 'policy_action_pub' in src and 'Float32MultiArray' in src
# 四路 publisher 删除
for p in ['left_arm_pub','right_arm_pub','left_hand_pub','right_hand_pub']:
    assert p not in src, f'{p} should be removed'
# _joint_msg 删除
assert '_joint_msg' not in src, '_joint_msg should be removed'
# mode 三档保留
assert 'publishes_command_topics' in src and 'dry' in src.lower() and ('shadow' in src.lower() or 'safe' in src.lower())
# 订阅侧未动（deploy_010 产物保留）
assert '_tcp_pose_cb' in src and '_gripper_cb' in src
print('deploy_014 验收通过: 发布侧→单路policy_action 16D, 订阅侧保留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 断言 | 上述命令通过 |
| dry-run | 否（deploy_016 做） | — | — |

### 真机风险控制

不触发真机。shadow-run 的 gate 关闭在 bridge（L2-05），本 L3 在 shadow/safe 都发 policy_action。

## 9. 允许修改

- `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（仅发布侧：import + _create_publishers + _control_tick + _joint_msg）

## 10. 禁止修改

- deploy_node.py 订阅侧（deploy_010 产物）。
- ControlLoop / safety_guard / 其他文件。
- mode 三档机制。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（policy_action 解析契约 + mode 三档）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D12/D18 + Q4 三档）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-04-action处理与发布层.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（本 L3 改发布侧；deploy_010 改后看订阅侧现状）
2. `pi05_test/pi05/common/src/pi05/common/robot/action_spec.py`（deploy_001 改后，确认 BimanualAction.as_vector 16D）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_001（BimanualAction 16D）、deploy_010（订阅侧，同文件先完成）。
2. 同组：deploy_013（并行）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_001, deploy_010]` 已完成。**deploy_010 必须先归档**（同文件订阅侧改完，本 L3 在其基础上改发布侧）。

```text
最小复现 / 测试（AST 断言）
→ 最小实现（改发布侧）
→ 验证通过
→ 必要整理
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] policy_action_pub 新增（Float32MultiArray 16D）。
- [ ] 四路 publisher 删除。
- [ ] _joint_msg 删除。
- [ ] _control_tick 发新格式。
- [ ] mode 三档保留（publishes_command_topics）。
- [ ] 订阅侧未动（deploy_010 产物保留）。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- pi05_vla_deploy_node.py
注意：回退会同时回退 deploy_010 订阅侧改动（同文件）。如需只回退发布侧，需手动 cherry-pick。
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改发布侧内容、新增 publisher、验收结果、成功标准勾选、真机影响（无，shadow gate 在 bridge）、回滚（注意同文件回退影响 deploy_010）、未做事项（没改订阅侧/safety/ControlLoop/metrics内容）、后续建议（deploy_015 metrics + deploy_016 shadow-run）。
