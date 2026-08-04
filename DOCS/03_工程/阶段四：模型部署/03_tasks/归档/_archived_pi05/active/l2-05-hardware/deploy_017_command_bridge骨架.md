# L3 微元改造任务：command_bridge_sender_node 骨架

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-05 硬件执行栈
来源 Delta：D14（新建 command_bridge_sender_node）
L3 编号：deploy_017
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_017_command_bridge骨架.md`
改造类型：new-feature
真机风险等级：none（shadow 可验，本 L3 不接真机驱动）

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_017
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_017_command_bridge骨架.md
  group: l2-05-hardware
  branch: model_deploy
  wave: 1
  parallel_group: l2-05-hardware-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_020, deploy_021]
  blocks: [deploy_018, deploy_019, deploy_022]
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py
    modules:
      - pi05.deploy.ros_nodes.command_bridge_sender_node
    config_keys: []
    runtime_modes:
      - shadow-run
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 command_bridge_sender_node 骨架：订阅 /pi05/policy_action（16D）+ 左右 TCP pose + 左右 gripper state；做前四步基础安全检查（维度/finite/quaternion归一化/width值域）；把 16D 拆成左右 PoseStamped + Float64；发布 /pi05/command/arm/*_target + /pi05/command/gripper/*_target + /pi05/command/status。本 L3 只搭骨架（订阅+基础检查+拆分+发布），IK 预检（deploy_018）和 gate/映射（deploy_019）后续接入。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D14 |
| 变更对象 | Output / Command（新建 bridge） |
| AS-IS 契约 | 无此节点。AS-IS 由 Pi05BridgeNode（topic 适配）+ CommandMuxNode（仲裁）承担，TO-BE 停用。 |
| TO-BE 契约 | `command_bridge_sender_node`：收 policy_action(16D) → 安全检查 → 拆 PoseStamped/Float64 → 发 command topic → 写 status。承担 D13 下移的硬件安全检查。依据：TO-BE Contract command_bridge 契约 + policy_action 解析表。 |
| 兼容性要求 | 新增节点（需适配接入，旧 bridge/mux 停用）。 |
| 回滚要求 | 节点不启动即回滚。 |

### 所属 L2 改造工作包

- L2 名称：L2-05 硬件执行栈
- 本 L3 在该 L2 中的位置：第一个。bridge 骨架是整个硬件栈的核心抽象。可与 deploy_020/021（硬件适配节点）并行（新建不同文件）。
- 本 L3 完成后解锁：deploy_018（IK 预检）、deploy_019（gate/映射）、deploy_022（shadow 全链路）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| 无（全新节点） | — | — | 全新建 | 是（新建） |
| 可参考：AS-IS Pi05BridgeNode | pi05_bridge_node.py | topic 适配 + finite 检查 + delta 限幅思路 | 可参考框架，但语义全变，实现重写 | 否（只参考，不改旧文件） |

### 必须保留的现有行为

- AS-IS bridge 的「finite 检查」思路可复用（融入七步检查）。
- AS-IS 的 status 记录思路可复用。

### 已知风险

- bridge 是全新节点，没有 AS-IS 参考实现（AS-IS 的 bridge 语义完全不同）。
- 本 L3 只搭骨架（订阅 + 基础四步检查 + 拆分 + 发布），IK 预检（deploy_018）和 gate/width→angle 映射（deploy_019）是占位，后续接入。骨架阶段 width→angle 先用简单 `angle=width*100`，标定在 deploy_019/021。
- 不接真机驱动（rm65/gripper 节点在 deploy_020/021，可并行新建但本 L3 不依赖它们运行）。

## 6. 真实改造边界

### 本次允许做

新建 `command_bridge_sender_node.py`，包含：

**订阅（输入）：**
- `/pi05/policy_action`（Float32MultiArray 16D）
- `/pi05/observation/arm/left_tcp_pose`、`/right_tcp_pose`（PoseStamped，作 TCP anchor + workspace 参考）
- `/pi05/observation/gripper/left_state`、`/right_state`（Float32 width，作步长参考）
- 急停/enable/deadman（本 L3 占位，用参数/topic stub；deploy_019 接入真实 gate）

**安全检查（本 L3 实现前四步，IK/gate 占位）：**
1. action 维度 == 16
2. 全部 finite（NaN/Inf）
3. quaternion 归一化（pose 段 [0:7]/[8:15] 的 [3:7] 模长≈1）
4. gripper_width ∈ [0,1]
（5. workspace/IK 预检 → deploy_018）
（6. width→angle 映射 → deploy_019，本 L3 先 `angle=width*100`）
（7. gate → deploy_019）

**拆分（16D → PoseStamped/Float64）：**
- 左：[0:7] → PoseStamped(position=[0:3], orientation=[3:7], frame_id=left_arm_base)；[7] → Float64(angle=width*100)
- 右：[8:15] → PoseStamped(frame_id=right_arm_base)；[15] → Float64

**发布（输出）：**
- `/pi05/command/arm/left_target`、`/right_target`（PoseStamped）
- `/pi05/command/gripper/left_target`、`/right_target`（Float64 angle）
- `/pi05/command/status`（String JSON：action_id/safety_ok/sent_to_driver/failure_reason）

**action_id 单调计数。**

### 本次不做

- IK 预检（deploy_018）。
- gate/急停/deadman 真实接入 + width→angle 标定（deploy_019）。
- rm65/gripper 驱动节点（deploy_020/021）。
- launch（deploy_022）。
- 单测（deploy_022 验证）。

### 明确禁止修改

- 禁止改 Pi05 节点 / collector / safety_guard / config 等已有文件（L2-01~04 产物）。
- 禁止接真机驱动（本 L3 只发 command topic，不连 RM65/夹爪 SDK）。
- 禁止改 AS-IS 的 pi05_bridge_node.py / command_mux_node.py（保留 git 回滚）。

### Adapter / 直接修改策略

```text
全新建。command_bridge_sender_node 是核心抽象，对外只暴露 /pi05/command/* 和 /pi05/command/status。回滚：节点不启动。骨架用占位（gate/IK），后续 L3 接入。
```

## 7. 实施步骤

1. **新建文件** `command_bridge_sender_node.py`（rclpy Node 子类）。
2. **__init__**：创建订阅（policy_action + tcp_pose×2 + gripper_state×2 + gate stub）+ 发布器（command arm×2 + gripper×2 + status）+ action_id 计数器 + 最新 tcp/gripper 缓存。
3. **policy_action_cb**：收 16D → 四步基础检查 → 拆 PoseStamped/Float64 → 发布 command topic → 写 status。
4. **tcp_pose_cb/gripper_cb**：缓存最新 TCP pose / gripper width。
5. **_check_basic（四步）**：维度/finite/quaternion归一化/width值域。
6. **_build_status_json**：action_id/safety_ok/sent_to_driver/failure_reason。
7. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
import ast
path = 'pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)
# 订阅
for s in ['/pi05/policy_action','left_tcp_pose','right_tcp_pose','left_gripper_state','right_gripper_state']:
    assert s in src, f'subscribe {s} missing'
# 发布
for p in ['command/arm/left_target','command/arm/right_target','command/gripper/left_target','command/gripper/right_target','command/status']:
    assert p in src, f'publish {p} missing'
# 四步检查
assert '16' in src and 'isfinite' in src.lower() and ('quat' in src.lower() or 'norm' in src.lower())
# action_id
assert 'action_id' in src
# status 字段
for f in ['safety_ok','sent_to_driver','failure_reason']:
    assert f in src
print('deploy_017 验收通过: bridge骨架(订阅+四步检查+拆分+发布+status)')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 结构断言 | 上述命令通过 |
| dry-run | 否（deploy_022 做） | — | — |
| shadow-run | 否（deploy_022 做，本 L3 骨架不接 gate） | — | — |

### 真机风险控制

不触发真机。本 L3 只发 command topic（无下游驱动消费）。robot_risk: none。

- 是否会真实发送命令：否（command topic 无驱动订阅）
- 默认是否关闭真实发送：是
- 回滚到原始发送路径：不适用（节点不启动）

## 9. 允许修改

- 新建 `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py`

## 10. 禁止修改

- Pi05 节点 / collector / safety_guard / config / codec 等已有文件。
- AS-IS pi05_bridge_node.py / command_mux_node.py（保留）。
- rm65/gripper 驱动（deploy_020/021）。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（command_bridge 契约 + policy_action 解析表 + 七步检查）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D14/D15/D16/D19 + Q5 七步）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-05-硬件执行栈.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py`（参考 rclpy Node 写法 + publisher/subscriber 模式）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 无直接上游（全新节点；通过 topic 契约与 L2-04 解耦）。
2. 同组：无已完成（本 L3 是 L2-05 第一个）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on` 为空（bridge 通过 topic 契约解耦，不需 L2-04 代码完成）。

```text
最小复现 / 测试（AST 结构断言）
→ 最小实现（新建节点骨架）
→ 验证通过
→ 必要整理（docstring + 占位注释标明 deploy_018/019 接入点）
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] command_bridge_sender_node.py 新建。
- [ ] 订阅 policy_action + tcp_pose + gripper_state。
- [ ] 四步基础检查实现。
- [ ] 16D 拆分 PoseStamped/Float64。
- [ ] 发布 command arm/gripper + status。
- [ ] action_id 单调计数。
- [ ] IK/gate 占位标注（deploy_018/019 接入点）。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：节点不启动（launch 不拉起）
切回旧入口：切回 pi05_picotele_mux.launch（旧 bridge/mux）
移除 adapter：删除新建的 command_bridge_sender_node.py
回退文件：git clean（新文件）
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新建文件、节点结构、占位标注、验收结果、成功标准勾选、真机影响（无，command topic 无下游）、回滚、未做事项（IK/gate/驱动/launch/单测）、后续建议（deploy_018 IK + deploy_019 gate）。
