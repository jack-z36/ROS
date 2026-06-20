# L3 微元改造任务：bridge 接入 IK 预检 + workspace 检查

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-05 硬件执行栈
来源 Delta：D14 + Q5（IK 发前预检）
L3 编号：deploy_018
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_018_bridge_ik预检.md`
改造类型：new-feature
真机风险等级：low（IK 预检不执行运动，只查询可解性，但需连 RM65 SDK）
L2 Git 分支：model_deploy-l2-05-hardware
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware
对应 L2 运行验收场景：[S1, S3]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_018_验收卡片.md
验收模式：static-review
辅助验收模式：['hardware-blocked']
本地验收是否必须：false
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_018
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_018_bridge_ik预检.md
  group: l2-05-hardware
  branch: model_deploy-l2-05-hardware
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware
  acceptance_scenarios: [S1, S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_018_验收卡片.md
  acceptance_mode: static-review
  acceptance_secondary_modes: [hardware-blocked]
  local_acceptance_required: false
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs
  wave: 2
  parallel_group: l2-05-hardware-p2
  depends_on: [deploy_017]
  must_run_after: []
  can_run_parallel_with: [deploy_019]
  blocks: [deploy_022]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py
    modules:
      - pi05.deploy.ros_nodes.command_bridge_sender_node
    config_keys: []
    runtime_modes:
      - shadow-run
    hardware_paths:
      - rm65_sdk
  robot_risk: hardware-blocked
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
在 command_bridge_sender_node 的检查链中接入第 5 步 workspace 几何检查（TCP 位置在臂可达范围）和第 5.5 步 IK 预检（调 rm_inverse_kinematics，flag=0 四元数模式，不执行只查可解性），不可解则拒绝并写 failure_reason，坏命令零到达控制器。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D14 + Q5 |
| 变更对象 | Output / Command（IK 检查） |
| AS-IS 契约 | AS-IS 无 bridge，无发送前 IK 预检（依赖 picotele/mux）。 |
| TO-BE 契约 | bridge 发 movep_canfd 前调 rm_inverse_kinematics（flag=0 四元数）预检；不可解则不发。依据：Q5（发前预检）+ RM65 文档 `rm_inverse_kinematics_params_t.md`。 |
| 兼容性要求 | 增量（在 deploy_017 骨架的占位接入真实实现）。 |
| 回滚要求 | IK 检查降级为占位/跳过。 |

### 所属 L2 改造工作包

- L2 名称：L2-05 硬件执行栈
- 本 L3 在该 L2 中的位置：第二个，在 deploy_017 骨架基础上接入 IK。可与 deploy_019（gate/映射）并行（改同文件不同方法，但同文件需协调——见冲突说明）。
- 本 L3 完成后解锁：deploy_022（shadow 全链路验证 IK）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `_check_basic`（deploy_017 建） | command_bridge_sender_node.py | 四步基础检查（维度/finite/quat/width） | 加第 5 步 workspace + 5.5 步 IK | 是 |
| IK 占位（deploy_017 标注） | command_bridge_sender_node.py | 占位 TODO | 接入真实 rm_inverse_kinematics 调用 | 是 |

### 必须保留的现有行为

- deploy_017 的四步基础检查保留。
- 检查失败拒绝 + 写 status 的语义。

### 已知风险

- **IK 预检需要连 RM65 SDK**（rm_inverse_kinematics 是 SDK 调用）。shadow-run 下如果 RM65 未通电/未连接，IK 预检无法执行——需要降级策略（如 config 开关控制 IK 是否启用，或 shadow-run 跳过 IK）。
- **与 deploy_019 同文件**：deploy_018 改 IK 检查方法，deploy_019 改 gate/映射方法，同文件不同方法。理论可并行但同文件易冲突，建议串行或同 Agent。
- workspace 检查是纯几何（TCP 位置在可达球/盒内），不需 SDK，可独立实现。

## 6. 真实改造边界

### 本次允许做

- 新增 `_check_workspace(tcp_xyz, side)`：纯几何检查，TCP 位置在 RM65 可达范围（可用简单球半径或盒边界，参数化 config）。
- 新增 `_check_ik(tcp_pose_7d, side)`：调 RM65 SDK 的 `rm_inverse_kinematics`（flag=0 四元数模式，`q_pose` 传 TCP pose，不执行只查）；返回 bool（可解）+ 错误信息。
- 在 `_check_basic` 后、发布前插入 workspace + IK 检查（成为第 5/5.5 步）。
- IK 检查的 SDK 连接：bridge 持有 RM65 SDK handle（来自 deploy_020 的 rm65_driver 或独立 SDK client）。本 L3 可先用 SDK client stub（接口定义，真实连接在 deploy_020）；或 config 开关 `ik_check_enabled` 控制。
- 不可解时：拒绝发送，`/pi05/command/status.failure_reason = "ik_unsolvable"`。

### 本次不做

- 不改 gate/急停/deadman/width→angle 映射（deploy_019）。
- 不实现 rm65_driver_node 完整（deploy_020）。
- 不接真机运动（IK 只查询不执行）。
- 不做 launch（deploy_022）。

### 明确禁止修改

- 禁止改 deploy_017 的四步基础检查逻辑。
- 禁止接真机运动（rm_inverse_kinematics 只查不执行 movep）。
- 禁止改 Pi05 节点。

### Adapter / 直接修改策略

```text
增量接入。workspace 纯几何独立实现；IK 用 SDK client（接口先定义，真实连接依赖 deploy_020 的 driver 或独立 SDK）。config 开关控制 IK 是否启用（shadow-run 可关）。回滚：ik_check_enabled=False。
```

## 7. 实施步骤

1. **新增 `_check_workspace`**：纯几何，TCP xyz 在可达范围（参数化边界）。
2. **定义 IK SDK client 接口**：`inverse_kinematics_check(tcp_pose_7d, side) -> (bool, str)`（真实实现在 deploy_020 或独立 client）。
3. **新增 `_check_ik`**：调 IK client，flag=0 四元数，返回可解性。
4. **在检查链插入**：第 5 步 workspace + 第 5.5 步 IK（在四步基础检查后、发布前）。
5. **config 开关** `ik_check_enabled`（默认 True；shadow-run 可配 False 跳过）。
6. **不可解写 status**。
7. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
src = open('src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py', encoding='utf-8').read()
assert '_check_workspace' in src, 'workspace check missing'
assert '_check_ik' in src, 'ik check missing'
assert 'inverse_kinematics' in src.lower(), 'rm_inverse_kinematics call missing'
assert 'ik_unsolvable' in src or 'ik' in src.lower(), 'ik failure reason missing'
assert 'ik_check_enabled' in src, 'ik_check_enabled config switch missing'
print('deploy_018 验收通过: workspace+IK预检接入')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 断言 | 上述命令通过 |
| shadow-run | 否（deploy_022 做，需 RM65 SDK 连接） | — | — |

### 真机风险控制

IK 预检不执行运动（rm_inverse_kinematics 只查可解性）。robot_risk: hardware-blocked。需连 SDK 但不动机器人。
- 是否会真实发送命令：否（只查询 IK）
- 默认是否关闭真实发送：是（不发 movep）
- 回滚到原始发送路径：ik_check_enabled=False 跳过

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py`（IK/workspace 检查方法）

## 10. 禁止修改

- deploy_017 四步基础检查。
- rm65_driver_node（deploy_020）。
- Pi05 节点。
- 接真机运动。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D14 + Q5 七步）
2. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-05-硬件执行栈.md`

### 必读代码

1. `src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py`（deploy_017 建后）

### 必读硬件文档

1. `DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/Python 逆运动学参数结构体rm_inverse_kinematics_params_t  睿尔曼智能科技.md`（flag=0 四元数）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_017（bridge 骨架）。
2. 同组：deploy_017 已完成（deploy_019 并行/串行）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_017]` 已完成。

```text
最小复现 / 测试（AST 断言）
→ 最小实现（workspace + IK 检查方法 + SDK client 接口）
→ 验证通过
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] _check_workspace 实现（纯几何）。
- [ ] _check_ik 实现（rm_inverse_kinematics flag=0）。
- [ ] 检查链插入第 5/5.5 步。
- [ ] ik_check_enabled config 开关。
- [ ] 不可解写 failure_reason。
- [ ] 不执行运动（只查）。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：ik_check_enabled=False（跳过 IK 检查）
切回旧入口：不适用
移除 adapter：删除 _check_ik/_check_workspace 方法
回退文件：git checkout -- command_bridge_sender_node.py（回退到 deploy_017 骨架）
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新增方法、SDK client 接口、config 开关、验收结果、成功标准勾选、真机影响（low，只查不执行）、回滚、未做事项（gate/映射/驱动/launch）、后续建议（deploy_019 gate + deploy_022 shadow）。
