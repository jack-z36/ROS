# L3 微元改造任务：real-robot smoke test（safe-run + 急停）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-05 硬件执行栈
来源 Delta：D1/D5/D6/D14/D15/D16/D18/D19（真机执行的综合验收）
L3 编号：deploy_023
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_023_real_robot_smoke_test.md`
改造类型：test-coverage
真机风险等级：critical（直接驱动 RM65 + 大象夹爪真机运动）

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_023
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_023_real_robot_smoke_test.md
  group: l2-05-hardware
  branch: model_deploy
  wave: 4
  parallel_group: l2-05-hardware-p4
  depends_on: [deploy_022]
  must_run_after: [deploy_022]
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: []
    modules: []
    config_keys: []
    runtime_modes:
      - safe-run
    hardware_paths:
      - rm65_arm_left
      - rm65_arm_right
      - elephant_gripper_left
      - elephant_gripper_right
      - estop_physical
      - deadman_physical
  robot_risk: critical
  dispatch_status: blocked
  blocked_reason: "必须 deploy_022 shadow-run 全链路通过后才解除；必须有人在场 + 急停就绪"
```

## 3. 本次唯一目标

```text
在 deploy_022 shadow-run 全链路通过后，执行 real-robot smoke test：mode=safe-run（gate 开），给保守动作（如"保持当前位姿"或微小位移），验证 RM65 + 大象夹爪按 policy_action 预期运动，并测试急停即时切断。这是整个阶段四改造的真机最终验收。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D1/D5/D6/D14/D15/D16/D18/D19 综合 |
| 变更对象 | 真机执行综合验收 |
| AS-IS 契约 | picotele 拓扑真机（已停用）。 |
| TO-BE 契约 | RM65+大象夹爪+bridge 拓扑真机执行（safe-run）。 |
| 兼容性要求 | 最终验收。 |
| 回滚要求 | 切回旧 launch + shadow-run。 |

### 所属 L2 改造工作包

- L2 名称：L2-05 硬件执行栈
- 本 L3 在该 L2 中的位置：最后一个，整个阶段四的真机最终验收。
- **前置条件**：deploy_022 shadow-run 全链路通过 + 急停就绪 + 人在场。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| 全套节点 + launch（deploy_017~022） | ros_nodes/ + launch/ | shadow 验证通过 | 需 safe-run 真机测试 | 否（只测） |
| 真模型 bundle | 待就绪（Q1 两天后） | — | 需新 bundle（16D） | 否（消费） |

### 必须保留的现有行为

- 不改代码（纯验收）。

### 已知风险

> [!danger] critical risk
> 本 L3 直接驱动 RM65 机械臂 + 大象夹爪真机运动。任何 bug 都可能导致机械臂异常运动、碰撞、损坏。
> - 必须前置：deploy_022 shadow-run 全链路通过（policy_action 16D 正确、bridge 七步检查通过、gate 逻辑正确）。
> - 必须前置：width↔angle 标定完成（deploy_021）。
> - 必须前置：真模型 bundle 就绪（Q1）。
> - 必须现场：人在场 + 物理急停就绪 + deadman 开关。

## 6. 真实改造边界

### 本次允许做

**smoke test 流程（safe-run）：**
1. 确认前置：shadow-run 通过 + 标定完成 + bundle 就绪 + 急停就绪。
2. mode=safe-run 启动（gate 开）。
3. **第一个测试动作：保守**（如"保持当前位姿"——policy_action 的 TCP = 当前 TCP，gripper = 当前 width）。验证机械臂不动（目标=当前）。
4. **第二个测试动作：微小位移**（如 TCP 前移 1cm）。验证机械臂缓慢前移 1cm 后停止。
5. **急停测试**：运动中触发物理急停，验证立即停止。
6. **gripper 测试**：width 0→0.5（半开），验证夹爪半开。
7. 记录结果。

### 本次不做

- 不改任何代码。
- 不做复杂动作（只保守 smoke test）。
- 不做长时间运行（只短时验证）。

### 明确禁止修改

- 禁止改代码。
- 禁止跳过前置条件（shadow/标定/bundle/急停）。
- 禁止无人值守运行。
- 禁止第一个动作就给大位移（必须从"保持当前"开始）。

### Adapter / 直接修改策略

```text
纯验收。不改代码。保守动作阶梯：保持当前 → 微小位移 → 急停测试 → gripper 半开。回滚：切回 shadow-run / 旧 launch。
```

## 7. 实施步骤

1. **前置检查**：shadow-run 通过 + 标定 + bundle + 急停 + 人在场。
2. **safe-run 启动**。
3. **保守动作 1**（保持当前位姿）→ 验证不动。
4. **保守动作 2**（微小位移 1cm）→ 验证缓慢移动。
5. **急停测试**→ 验证即时停止。
6. **gripper 半开测试**。
7. **记录结果 + 归档**。

## 8. 验证方式

### 验收标准（人工 + 观察）

| 测试项 | 通过标准 |
|---|---|
| 保持当前位姿 | 机械臂不动（目标=当前 TCP） |
| 微小位移 1cm | 机械臂缓慢前移 ~1cm 后停止 |
| 急停 | 运动中触发急停，机械臂立即停止 |
| gripper 半开 | 夹爪从闭合到半开（width 0→0.5） |
| status 记录 | /pi05/command/status 显示 sent_to_driver=true，无 failure |

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| real-robot | 是（critical） | 保守动作 + 急停 + gripper | 上述全部通过 |

### 真机风险控制

> [!danger] critical
> - 是否会真实发送命令：是（movep_canfd + modbus 驱动真机）
> - 默认是否关闭：否（safe-run gate 开）—— 这正是 smoke test 的目的
> - 回滚：切回 shadow-run（gate 关）；切回旧 launch
> - 急停：物理急停必须优先，随时可用
> - 保守阶梯：必须从"保持当前"开始，逐步加量，不跳级

## 9. 允许修改

- 无（纯验收，不改代码）

## 10. 禁止修改

- 任何代码。
- 跳过前置条件。
- 无人值守。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（全套契约）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（全套 Delta + Q1/Q2/Q3/Q4/Q5）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-05-硬件执行栈.md`

### 必读代码

1. 全套节点（deploy_017~021 产物）
2. launch（deploy_022 产物）

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_022（shadow-run 全链路通过）。
2. 全部前置：deploy_017~022 + L2-01~04 全部 L3。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_022]` 已完成且 **shadow-run 通过**。

> [!danger] 解除 blocked 状态的条件
> dispatch_status: blocked。必须满足以下全部条件才解除：
> 1. deploy_022 shadow-run 全链路通过（policy_action 16D + bridge 七步检查 + sent_to_driver=false + 不动）
> 2. width↔angle 标定完成（deploy_021 实测系数已写入）
> 3. 真模型 bundle 就绪（Q1，16D 训练）
> 4. 人在场 + 物理急停就绪 + deadman 开关可用
> 5. 主 Agent 或用户明确授权解除 blocked

```text
前置检查（5 项全部满足）
→ 解除 blocked
→ safe-run 启动
→ 保守动作阶梯（保持→微移→急停→gripper）
→ 记录 + 归档
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 前置 5 项全部满足（shadow/标定/bundle/急停/人在场）。
- [ ] 保持当前位姿：机械臂不动。
- [ ] 微小位移：机械臂缓慢移动预期距离。
- [ ] 急停：即时停止。
- [ ] gripper 半开：夹爪按预期开合。
- [ ] status：sent_to_driver=true，无 failure。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：切回 mode=shadow-run（gate 关，不动）
切回旧入口：切回 pi05_picotele_mux.launch
不可自动回滚的人工步骤：物理急停（运动中需手动按急停）
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、前置 5 项确认、smoke test 每项结果（保持/微移/急停/gripper）、status 记录、成功标准勾选、**真机影响（critical，已驱动真机运动）**、回滚、**这是阶段四真机最终验收**、后续建议（如通过，阶段四改造完成；如失败，定位问题回到对应 L2/L3）。
