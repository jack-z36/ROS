# L3 微元改造任务：deploy_node 订阅侧改造

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-03 数据装配 Service 层
来源 Delta：D3（相机）、D7（topic）、D8（臂状态语义）
L3 编号：deploy_010
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_010_deploy_node订阅侧改造.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-03-assembly
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
对应 L2 运行验收场景：[S1, S2]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_010_验收卡片.md
验收模式：static-review
辅助验收模式：['downstream-l2']
本地验收是否必须：false
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_010
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_010_deploy_node订阅侧改造.md
  group: l2-03-assembly
  branch: model_deploy-l2-03-assembly
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
  acceptance_scenarios: [S1, S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_010_验收卡片.md
  acceptance_mode: static-review
  acceptance_secondary_modes: [downstream-l2]
  local_acceptance_required: false
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs
  wave: 2
  parallel_group: l2-03-assembly-p2
  depends_on: [deploy_009]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_012]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py
    modules:
      - pi05.deploy.ros_nodes.pi05_vla_deploy_node
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 deploy_node 的订阅侧从 AS-IS 的 realsense/proprio/hand/ee 订阅，改造为 TO-BE 的鱼眼图像 + TCP pose + gripper width 订阅（触觉第一版不订阅），新增对应 callback 调 collector 的新方法，删除旧 callback。只改订阅侧，不改发布侧（发布侧归 L2-04）。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D3 + D7 + D8 |
| 变更对象 | 相机 + topic + 臂状态 |
| AS-IS 契约 | `_create_subscriptions`（pi05_vla_deploy_node.py:100-133）订阅 realsense/proprio/hand/ee；`_image_topic_map`（L135-143）= top/left_wrist/right_wrist/left_tactile/right_tactile；callback `_image_cb`/`_proprio_cb`/`_hand_cb`/`_point_cb`/`_vec3_cb`（L154-182）。 |
| TO-BE 契约 | 订阅鱼眼双目 + TCP pose(PoseStamped) + gripper(Float32)；触觉第一版不订阅；callback 调 collector.update_tcp_pose/update_gripper_width。 |
| 兼容性要求 | 破坏性。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-03 数据装配 Service 层
- 本 L3 在该 L2 中的位置：第二个，依赖 deploy_009（collector 新方法）。
- 本 L3 完成后解锁：deploy_012（dry-run）。
- **与 L2-04 的协调**：本 L3 改 deploy_node 订阅侧，L2-04 改 deploy_node 发布侧。同一文件两半，必须串行（本 L3 先，L2-04 后），或同 Agent 顺序完成。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `_create_subscriptions` | pi05_vla_deploy_node.py:100-133 | 订阅 realsense/proprio/hand/ee | 改订阅鱼眼/tcp/gripper | 是 |
| `_image_topic_map` | pi05_vla_deploy_node.py:135-143 | top/left_wrist/right_wrist/tactile | 改 left_fisheye/right_fisheye | 是 |
| `_image_cb` | pi05_vla_deploy_node.py:154-161 | 图像解码+preprocess+update_image | 保留（鱼眼图像处理不变） | 否（保留，改 topic 来源） |
| `_proprio_cb` | pi05_vla_deploy_node.py:163-168 | 调 update_proprioception | 删（collector 方法已删） | 是 |
| `_hand_cb` | pi05_vla_deploy_node.py:170-174 | 调 update_hand | 删 | 是 |
| `_point_cb`/`_vec3_cb` | pi05_vla_deploy_node.py:176-182 | 调 update_vector（ee_pos/rpy） | 删，换 tcp_pose callback | 是 |
| `_publish_observation_if_ready` | pi05_vla_deploy_node.py:184-194 | snapshot 门控 + 写 SharedBuffer | 保留（逻辑不变） | 否（保留） |
| import | pi05_vla_deploy_node.py:12-16 | Point/Vector3/JointState/Image/CompressedImage | 改（加 PoseStamped，删 Point/Vector3 if 不再用） | 是 |

### 必须保留的现有行为

- `_image_cb` 的图像解码 + preprocess_rgb_image + update_image 流程（鱼眼图像处理与 realsense 一致）。
- `_publish_observation_if_ready` 的 snapshot 门控 + 写 SharedBuffer + missing 节流日志。
- `_create_subscriptions` 的「按 image_names 动态订阅」框架（required image keys 来自 bundle manifest）。
- image transport（compressed/raw/both）选择逻辑。

### 已知风险

- **与 L2-04 共享文件**：deploy_node.py 被本 L3（订阅侧）和 L2-04（发布侧）都改。必须串行或同 Agent 协调行范围，避免合并冲突。
- 新 callback 的 ROS msg 类型：TCP pose 是 `geometry_msgs/PoseStamped`（position xyz + orientation quaternion xyzw），gripper 是 `std_msgs/Float32`。callback 要把 PoseStamped 解成 7D `[x,y,z,qx,qy,qz,qw]`。
- 本 L3 完成后，deploy_node 订阅侧通了，但发布侧还是旧的（四路 JointState/Float64 publisher 还在，_control_tick 还发旧格式）——预期中间状态，直到 L2-04 改发布侧。

## 6. 真实改造边界

### 本次允许做

**`_create_subscriptions`（L100-133）重构：**
- 保留「按 image_names 动态订阅图像」框架。
- 订阅 `topics.observation.left_tcp_pose`/`right_tcp_pose`（PoseStamped）→ `_tcp_pose_cb(side, msg)`。
- 订阅 `topics.observation.left_gripper_state`/`right_gripper_state`（Float32）→ `_gripper_cb(side, msg)`。
- 触觉订阅受 config 开关控制（第一版不订阅；预留条件分支）。
- 删除 proprio/hand/ee 的订阅。

**`_image_topic_map`（L135-143）重构：**
- 改为 `{"left_fisheye": (...), "right_fisheye": (...)}`（从 config 读 topic 名）。

**callback 重构：**
- 保留 `_image_cb`（L154-161）。
- 删 `_proprio_cb`/`_hand_cb`/`_point_cb`/`_vec3_cb`。
- 新增 `_tcp_pose_cb(side, PoseStamped)`：解 position(x,y,z) + orientation(qx,qy,qz,qw) → 7D → `collector.update_tcp_pose(side, vec7)`。
- 新增 `_gripper_cb(side, Float32)`：`collector.update_gripper_width(side, msg.data)`。

**import（L12-16）：**
- 加 `from geometry_msgs.msg import PoseStamped`。
- 删 `Point`/`Vector3`（如不再用）；保留 Image/CompressedImage/JointState（JointState 可能 IK 兜底用，确认）。

### 本次不做

- 不改 `_create_publishers`/`_control_tick`/`_publish_metrics`（发布侧，L2-04 做）。
- 不改 `_joint_msg`（L2-04 删）。
- 不改 collector（deploy_009 已改）。
- 不改 policy_loader（deploy_011 做）。

### 明确禁止修改

- 禁止改 deploy_node.py 的发布侧（_create_publishers/_control_tick/_publish_metrics/_joint_msg）——那是 L2-04 的范围。
- 禁止改 `_publish_observation_if_ready`（保留门控）。
- 禁止改 `_image_cb` 的图像处理逻辑。
- 禁止改 collector / policy_loader / 其他文件。

### Adapter / 直接修改策略

```text
直接修改。订阅字段整体替换，callback 跟随 collector 新方法。图像处理流程保留（鱼眼与 realsense 同构）。回滚靠 git。
```

## 7. 实施步骤

1. **改 import**（L12-16）：加 PoseStamped；评估 Point/Vector3 是否还需（如发布侧 L2-04 会删 _joint_msg 则 JointState 也可能删，但本 L3 只删自己不用的 Point/Vector3，JointState 暂留）。
2. **改 `_image_topic_map`**（L135-143）：left_fisheye/right_fisheye。
3. **改 `_create_subscriptions`**（L100-133）：图像订阅框架保留；加 tcp_pose（PoseStamped×2）+ gripper（Float32×2）订阅；触觉条件分支预留；删 proprio/hand/ee 订阅。
4. **删 `_proprio_cb`/`_hand_cb`/`_point_cb`/`_vec3_cb`**（L163-182）。
5. **新增 `_tcp_pose_cb`**：解 PoseStamped → 7D → collector.update_tcp_pose。
6. **新增 `_gripper_cb`**：Float32.data → collector.update_gripper_width。
7. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
src = open('src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py', encoding='utf-8').read()
# 新 callback
for m in ['_tcp_pose_cb','_gripper_cb']:
    assert f'def {m}' in src, f'{m} missing'
# 新 topic map
assert 'left_fisheye' in src and 'right_fisheye' in src
# PoseStamped import
assert 'PoseStamped' in src
# 旧 callback 删除
for m in ['_proprio_cb','_hand_cb','_point_cb','_vec3_cb']:
    assert f'def {m}' not in src, f'{m} should be removed'
# 发布侧未动（L2-04 范围，本 L3 不碰）
assert '_create_publishers' in src and '_control_tick' in src
print('deploy_010 验收通过: 订阅侧→鱼眼/TCP/gripper, 发布侧保留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST callback/topic 断言 | 上述命令通过 |
| dry-run | 否（deploy_012 做） | — | — |

### 真机风险控制

不适用。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（仅订阅侧：import + _create_subscriptions + _image_topic_map + callback 部分）

## 10. 禁止修改

- deploy_node.py 的发布侧（_create_publishers/_control_tick/_publish_metrics/_joint_msg）。
- `_publish_observation_if_ready`（门控）。
- `_image_cb` 图像处理逻辑。
- collector / policy_loader / 其他文件。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（topic 表 + 夹爪语义约定）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D3/D7/D8）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-03-数据装配Service层.md`

### 必读代码

1. `src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（本 L3 改订阅侧）
2. `src/model_deploy/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py`（deploy_009 改后，确认 update_tcp_pose/update_gripper_width 签名）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_009（collector 新方法）。
2. 同组已完成：deploy_009（deploy_011 并行中）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_009]` 已完成。

```text
最小复现 / 测试（AST 断言）
→ 最小实现（改订阅侧）
→ 验证通过
→ 必要整理
```

**与 L2-04 协调**：本 L3 完成后，deploy_node 发布侧仍是旧的。L2-04 的 L3 会改发布侧。两者必须串行（本 L3 先归档，L2-04 后做），或主 Agent 安排同一 Agent 顺序完成两半。

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] 订阅改为鱼眼/TCP pose/gripper width。
- [ ] _tcp_pose_cb/_gripper_cb 新增并调 collector 新方法。
- [ ] 旧 callback 删除。
- [ ] _image_cb 图像处理保留。
- [ ] _publish_observation_if_ready 门控保留。
- [ ] 发布侧未动（_create_publishers/_control_tick 仍是旧逻辑）。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- pi05_vla_deploy_node.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改订阅侧内容、新增 callback、验收结果、成功标准勾选、真机影响（无）、回滚、**与 L2-04 的协调说明**（发布侧待改）、未做事项（没改发布侧/collector/policy_loader）、后续建议（deploy_012 dry-run + L2-04 发布侧）。
