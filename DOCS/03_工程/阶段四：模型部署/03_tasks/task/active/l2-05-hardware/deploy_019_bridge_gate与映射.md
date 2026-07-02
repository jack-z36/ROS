# L3 微元改造任务：bridge width→angle 映射 + mode/gate 控制

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-05 硬件执行栈
来源 Delta：D16（gripper width→angle）、D18（mode/gate）、D19（失败语义）
L3 编号：deploy_019
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_019_bridge_gate与映射.md`
改造类型：new-feature
真机风险等级：low（gate 控制，shadow-run 不发硬件；真机发送在 safe-run + gate 开）

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_019
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_019_bridge_gate与映射.md
  group: l2-05-hardware
  branch: model_deploy
  wave: 2
  parallel_group: l2-05-hardware-p2
  depends_on: [deploy_017]
  must_run_after: []
  can_run_parallel_with: [deploy_018]
  blocks: [deploy_022]
  conflict_scope:
    files:
      - pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py
    modules:
      - pi05.deploy.ros_nodes.command_bridge_sender_node
    config_keys: []
    runtime_modes:
      - shadow-run
      - safe-run
    hardware_paths: []
  robot_risk: low
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
在 command_bridge_sender_node 接入：第 6 步 width→angle 映射（gripper_width[0,1]→gripper_angle[0,100]，参数化标定系数）+ 第 7 步 gate（mode shadow/safe + 急停/deadman/enable 与运算），shadow-run gate 关不发硬件但写 status(sent_to_driver=false)，safe-run gate 开发硬件，失败语义完整记录（D19）。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D16 + D18 + D19 |
| 变更对象 | gripper 映射 + mode/gate + 失败语义 |
| AS-IS 契约 | AS-IS 无 bridge gate（mux 控制）；gripper 用 trigger 转换（300..1000）。 |
| TO-BE 契约 | width→angle 线性映射（标定系数）；gate = mode(shadow=关/safe=开) AND 急停 AND deadman AND enable；shadow 写 status(sent_to_driver=false)；safe 发硬件；失败不伪装成功。依据：Q4 三档 + D16/D18/D19。 |
| 兼容性要求 | 增量（deploy_017 占位接入真实）。 |
| 回滚要求 | gate 强制关闭（shadow）。 |

### 所属 L2 改造工作包

- L2 名称：L2-05 硬件执行栈
- 本 L3 在该 L2 中的位置：与 deploy_018（IK）并行/串行（同文件不同方法）。gate/映射是发布前最后两步。
- 本 L3 完成后解锁：deploy_022（shadow 全链路验证 gate）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| width→angle 占位（deploy_017 用 width*100） | command_bridge_sender_node.py | 简单映射 | 接入参数化标定系数 | 是 |
| gate 占位（deploy_017 stub） | command_bridge_sender_node.py | 占位 | 接入 mode + 急停/deadman/enable | 是 |
| status 写入（deploy_017 建） | command_bridge_sender_node.py | action_id/safety_ok/failure_reason | 补 sent_to_driver 字段语义 | 是 |

### 必须保留的现有行为

- deploy_017 的基础检查 + 拆分 + status 框架。
- deploy_018 的 IK/workspace 检查（如已完成）。

### 已知风险

- **gate 的 mode 来源**：bridge 需知道当前 mode（dry/shadow/safe）。mode 在 Pi05 节点的 RuntimeConfig，bridge 是独立节点——需通过 config 或 topic 同步 mode。建议 bridge 读自己的 config（mode 参数）或订阅一个 mode topic。
- 急停/deadman/enable 的输入源：物理开关（topic 或 service）。本 L3 定义接口，真实物理接在 deploy_022/023。
- width→angle 标定系数：理论 `angle=width*100`，但实物零点偏移需标定（D16 warning）。本 L3 参数化（config 系数），标定值待 deploy_021 实测。

## 6. 真实改造边界

### 本次允许做

- **第 6 步 width→angle 映射**：`_map_width_to_angle(width) -> angle`，用 config 参数（`gripper_angle_scale`/`gripper_angle_offset`，默认 scale=100, offset=0）；映射后限幅 [0,100]；strict mode 越界拒绝。
- **第 7 步 gate**：`_evaluate_gate() -> bool`，gate = `(mode == safe-run) AND (not estop) AND (not deadman) AND enable`。
  - mode 来源：bridge config 参数 `mode`（或订阅 mode topic）。
  - estop/deadman/enable 来源：订阅物理开关 topic（接口定义，真实接 deploy_022/023）。
- **发布决策**：
  - gate=True（safe-run + 开关全正常）→ 发 command arm/gripper + status(sent_to_driver=true)。
  - gate=False（shadow-run 或开关触发）→ **不发 command**，只写 status(sent_to_driver=false, failure_reason="gate_closed/shadow_mode/estop")。
- **失败语义（D19）**：每次发送记录 action_id/safety_ok/sent_to_driver/failure_reason；硬件超时/SDK 错误透传（驱动错误来自 deploy_020/021 的返回）。

### 本次不做

- 不改 IK/workspace（deploy_018）。
- 不实现物理开关真实接入（接口定义，接在 deploy_022/023）。
- 不做 width→angle 实物标定（参数化，标定值 deploy_021）。
- 不做 launch（deploy_022）。

### 明确禁止修改

- 禁止改 deploy_017/018 的检查逻辑。
- 禁止在 shadow-run 发硬件命令。
- 禁止把失败伪装成成功（D19）。

### Adapter / 直接修改策略

```text
增量接入。映射参数化（标定待实测）。gate 用 config mode + 物理开关接口。shadow-run 严格不发硬件。回滚：gate 强制 False（shadow）。
```

## 7. 实施步骤

1. **新增 `_map_width_to_angle`**：参数化映射 + 限幅。
2. **新增 `_evaluate_gate`**：mode + estop + deadman + enable 与运算。
3. **定义物理开关订阅接口**：estop/deadman/enable topic（stub，真实接 deploy_022/023）。
4. **改发布决策**：gate=True 发 + status(sent_to_driver=true)；gate=False 不发 + status(sent_to_driver=false)。
5. **补 status 字段语义**：sent_to_driver + failure_reason 完整。
6. **config 参数**：gripper_angle_scale/offset + mode + strict_mode。
7. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
src = open('pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py', encoding='utf-8').read()
assert '_map_width_to_angle' in src
assert '_evaluate_gate' in src
assert 'gripper_angle_scale' in src or 'scale' in src
assert 'sent_to_driver' in src
assert 'shadow' in src.lower() and 'safe' in src.lower()
assert 'estop' in src.lower() or 'deadman' in src.lower() or 'enable' in src.lower()
print('deploy_019 验收通过: width→angle映射 + gate(mode/急停) + 失败语义')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 断言 | 上述命令通过 |
| shadow-run | 否（deploy_022 做） | — | — |

### 真机风险控制

gate 控制：shadow-run 严格不发硬件。robot_risk: low。真机发送仅在 safe-run + gate 全开。
- 是否会真实发送命令：取决于 gate（shadow=否，safe=是）
- 默认是否关闭真实发送：是（默认 shadow/gate 关）
- 回滚到原始发送路径：gate 强制 False

## 9. 允许修改

- `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py`（映射/gate/status 部分）

## 10. 禁止修改

- deploy_017/018 检查逻辑。
- 物理开关真实接入（deploy_022/023）。
- shadow-run 发硬件。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（夹爪语义约定 + mode 三档 + 失败语义）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D16/D18/D19 + Q4 三档）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-05-硬件执行栈.md`

### 必读代码

1. `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/command_bridge_sender_node.py`（deploy_017/018 建后）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/文档体系/阶段二任务体系/L3调度元数据规则.md`
4. `DOCS/02_约束/文档体系/阶段二任务体系/L3任务身份校验规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_017（骨架）。
2. 同组：deploy_017/018（deploy_018 并行/串行）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_017]` 已完成。与 deploy_018 同文件，建议串行或同 Agent。

```text
最小复现 / 测试（AST 断言）
→ 最小实现（映射 + gate + status）
→ 验证通过
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] _map_width_to_angle 参数化 + 限幅。
- [ ] _evaluate_gate（mode + 急停/deadman/enable）。
- [ ] shadow-run 不发硬件 + status(sent_to_driver=false)。
- [ ] safe-run gate 开发硬件 + status(sent_to_driver=true)。
- [ ] 失败不伪装成功（D19）。
- [ ] 已完成自动化验收。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：mode=shadow-run（gate 强制关，不发硬件）
切回旧入口：不适用
移除 adapter：删除映射/gate 方法
回退文件：git checkout -- command_bridge_sender_node.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新增方法、gate 逻辑、映射参数、status 语义、验收结果、成功标准勾选、真机影响（low，shadow 不发）、回滚、未做事项（物理开关真实接入/标定/launch）、后续建议（deploy_022 shadow 全链路）。
