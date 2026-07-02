# L3 微元改造任务：新 launch + shadow-run 全链路验证

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-05 硬件执行栈
来源 Delta：D1（拓扑）、D2（launch 入口）
L3 编号：deploy_022
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_022_launch与shadow_run全链路.md`
改造类型：new-feature
真机风险等级：low（shadow-run：全链路验证但机械臂不动，gate 关）

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_022
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_022_launch与shadow_run全链路.md
  group: l2-05-hardware
  branch: model_deploy
  wave: 3
  parallel_group: l2-05-hardware-p3
  depends_on: [deploy_017, deploy_018, deploy_019, deploy_020, deploy_021]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_023]
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/launch/pi05_rm65_deploy.launch.py
      - pi05_test/pi05/deploy/tests/test_shadow_run_integration.py
    modules:
      - deploy.launch
      - tests.shadow_integration
    config_keys: []
    runtime_modes:
      - shadow-run
    hardware_paths:
      - rm65_arm_left
      - rm65_arm_right
      - elephant_gripper_left
      - elephant_gripper_right
  robot_risk: low
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 pi05_rm65_deploy.launch.py（拉起 fisheye + tactile(可选) + rm65_driver + elephant_gripper + Pi05VlaDeployNode + command_bridge_sender_node），并在 shadow-run 下验证全链路：policy_action(16D) → bridge 七步检查 → status(sent_to_driver=false)，机械臂/夹爪不动。旧 launch 保留作回滚。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D1 + D2 |
| 变更对象 | 拓扑 + launch 入口 |
| AS-IS 契约 | pi05_picotele_mux.launch.py（picotele 拓扑）。 |
| TO-BE 契约 | pi05_rm65_deploy.launch.py（RM65+大象夹爪+bridge 拓扑）。shadow-run 全链路验证。 |
| 兼容性要求 | 新 launch（旧保留回滚）。 |
| 回滚要求 | 切回旧 launch。 |

### 所属 L2 改造工作包

- L2 名称：L2-05 硬件执行栈
- 本 L3 在该 L2 中的位置：集成验证。依赖 deploy_017~021 全部完成。
- 本 L3 完成后解锁：deploy_023（real-robot smoke test）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| pi05_picotele_mux.launch.py | deploy/launch/ | 旧拓扑 launch | 保留作回滚；新建 RM65 launch | 否（保留旧） |
| 各节点（deploy_017~021） | ros_nodes/ | bridge/rm65/gripper 新建 | 需 launch 拉起 | 否（只写 launch） |

### 必须保留的现有行为

- 旧 launch 保留（回滚路径）。

### 已知风险

- shadow-run 需要连 RM65 SDK（状态发布）但不动机器人（gate 关）。如果 RM65 未通电，状态 topic 无输出——shadow 验证可能受限。建议 shadow 验证分两层：①软件层（不连硬件，用 stub 状态数据验证 bridge 链路）；②硬件层（连 RM65 读状态，但 gate 关不动机）。
- launch 参数化（臂 IP、夹爪串口、mode、gate 开关）。

## 6. 真实改造边界

### 本次允许做

**新建 `pi05_rm65_deploy.launch.py`：**
- 拉起：fisheye_camera_node×2 + tactile_sensor_node（第一版可选/注释）+ rm65_driver_node + elephant_gripper_node + Pi05VlaDeployNode + command_bridge_sender_node。
- 参数化：mode（default=shadow-run）、臂 IP/端口、夹爪串口、gate 开关、ik_check_enabled。
- 读 deploy.yaml（deploy_008 改后的新 config）。

**shadow-run 全链路验证：**
- 启动 launch（mode=shadow-run）。
- 喂 observation 数据（或连真机状态）。
- 验证：policy_action(16D) 发布 → bridge 收到 → 七步检查 → status(sent_to_driver=false)。
- 验证：机械臂/夹爪不动（gate 关）。
- 验证：状态 topic（tcp_pose/gripper_state）有输出（如连真机）。

### 本次不做

- 不做 real-robot smoke test（deploy_023）。
- 不改各节点内部（deploy_017~021 已建）。
- 不删旧 launch。

### 明确禁止修改

- 禁止删旧 launch（pi05_picotele_mux）。
- 禁止在 shadow-run 开 gate 发硬件。
- 禁止改节点内部。

### Adapter / 直接修改策略

```text
新建 launch + 集成验证。旧 launch 保留。shadow-run gate 严格关。回滚：切回旧 launch。
```

## 7. 实施步骤

1. **新建 `pi05_rm65_deploy.launch.py`**：拉起所有节点，参数化，默认 shadow-run。
2. **启动 shadow-run**：mode=shadow-run，连真机状态（如可）或 stub。
3. **验证全链路**：policy_action → bridge → status(sent_to_driver=false)。
4. **验证不动**：机械臂/夹爪不动。
5. **记录结果**。

## 8. 验证方式

### 自动化验收命令

```bash
# launch 语法检查
python3 -c "
import ast
path = 'pi05_test/pi05/deploy/launch/pi05_rm65_deploy.launch.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)
for node in ['command_bridge_sender_node','rm65_driver_node','elephant_gripper_node','Pi05VlaDeployNode']:
    assert node in src, f'{node} not in launch'
assert 'shadow' in src.lower(), 'default mode should mention shadow'
print('deploy_022 launch验收通过')
"
# shadow-run 实际执行（需硬件环境或 stub）
# ros2 launch deploy pi05_rm65_deploy.launch.py mode:=shadow-run
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | launch AST | 上述命令通过 |
| shadow-run | 是 | 全链路 + 不动机器人 | status sent_to_driver=false；机械臂不动 |

### 真机风险控制

shadow-run：gate 关，不动机器人。robot_risk: low。连真机读状态但不发命令。
- 是否会真实发送命令：否（gate 关）
- 默认关闭：是（shadow）
- 回滚：切回旧 launch

## 9. 允许修改

- 新建 `pi05_test/pi05/deploy/launch/pi05_rm65_deploy.launch.py`
- 新建 `pi05_test/pi05/deploy/tests/test_shadow_run_integration.py`（可选）

## 10. 禁止修改

- 旧 launch（pi05_picotele_mux）。
- 节点内部。
- shadow-run 开 gate。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（拓扑 + launch）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D1/D2 + Q4 shadow-run）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-05-硬件执行栈.md`

### 必读代码

1. `pi05_test/pi05/deploy/launch/pi05_picotele_mux.launch.py`（参考旧 launch 写法）
2. 各新建节点（deploy_017~021 产物）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_017~021（全部完成）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_017~021]` 全部完成。

```text
新建 launch（AST 验收）
→ shadow-run 启动
→ 全链路验证（policy_action→bridge→status）
→ 确认不动
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] pi05_rm65_deploy.launch.py 新建（拉起全节点）。
- [ ] 旧 launch 保留。
- [ ] shadow-run 全链路：policy_action → bridge → status(sent_to_driver=false)。
- [ ] 机械臂/夹爪不动（gate 关）。
- [ ] 状态 topic 有输出（如连真机）。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：切回 pi05_picotele_mux.launch
移除 adapter：删除新 launch
回退文件：git clean
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新建 launch、shadow-run 全链路结果、sent_to_driver=false 确认、不动确认、验收结果、成功标准勾选、真机影响（low，shadow 不动）、回滚、未做事项（real-robot smoke test）、后续建议（deploy_023 real-robot，**shadow 通过后才做**）。
