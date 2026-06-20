# L3 微元改造任务：elephant_gripper_node（状态发布 + 命令执行 + 标定）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-05 硬件执行栈
来源 Delta：D6（夹爪 inspire→大象）、D16（width→angle 映射标定）
L3 编号：deploy_021
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_021_elephant_gripper_node.md`
改造类型：new-feature
真机风险等级：high（直接驱动大象夹爪）
L2 Git 分支：model_deploy-l2-05-hardware
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware
对应 L2 运行验收场景：[S5]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_021_验收卡片.md
验收模式：static-review
辅助验收模式：['hardware-blocked']
本地验收是否必须：false
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_021
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_021_elephant_gripper_node.md
  group: l2-05-hardware
  branch: model_deploy-l2-05-hardware
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware
  acceptance_scenarios: [S5]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_021_验收卡片.md
  acceptance_mode: static-review
  acceptance_secondary_modes: [hardware-blocked]
  local_acceptance_required: false
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs
  wave: 1
  parallel_group: l2-05-hardware-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_017, deploy_020]
  blocks: [deploy_022, deploy_023]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/elephant_gripper_node.py
    modules:
      - pi05.deploy.ros_nodes.elephant_gripper_node
    config_keys: []
    runtime_modes: []
    hardware_paths:
      - elephant_gripper_left
      - elephant_gripper_right
      - gripper_modbus
  robot_risk: hardware-blocked
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 elephant_gripper_node 适配层：状态发布角色（读硬件寄存器 angle[0,100] → 映射 width[0,1] → 发 /pi05/observation/gripper/*_state Float32）+ 命令执行角色（收 /pi05/command/gripper/*_target Float64 angle → 调大象夹爪 modbus/SDK）+ width↔angle 标定（实测闭合点/全开点寄存器值，提供给 bridge 的映射系数）。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D6 + D16 |
| 变更对象 | 末端执行器 + gripper 映射 |
| AS-IS 契约 | picotele_hand_node 消费 Float64 trigger(0..1)；状态 /inspire/*/joint_states；hand_min/max=300/1000。 |
| TO-BE 契约 | elephant_gripper_node：状态发 width[0,1]；命令收 angle[0,100]；modbus/SDK。width↔angle 标定实测。依据：D6/D16 + TO-BE Contract 夹爪语义约定。 |
| 兼容性要求 | 新增适配节点。 |
| 回滚要求 | 节点不启动。 |

### 所属 L2 改造工作包

- L2 名称：L2-05 硬件执行栈
- 本 L3 在该 L2 中的位置：与 deploy_017（bridge）/deploy_020（rm65）并行（新建不同文件）。
- 本 L3 完成后解锁：deploy_022（shadow 全链路）、deploy_023（real-robot）。
- **标定职责**：本 L3 负责实测 width↔angle 标定系数，反馈给 bridge 的 deploy_019 映射参数。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| 大象夹爪 modbus/pymycobot SDK | 外部依赖 | 寄存器读写 angle[0,100] | 复用 | 否（复用） |
| 无（全新适配节点） | — | — | 全新建 | 是（新建） |

### 必须保留的现有行为

- SDK 的寄存器读写逻辑（不重写）。

### 已知风险

- **直接驱动大象夹爪**（high risk）。命令执行会让夹爪开合。
- **width↔angle 标定**（D16 warning）：理论 `width=angle/100`，但闭合点/全开点的真实寄存器值需实测。标定前不接真机命令执行。
- angle 值域 [0,100] 是名义值，实物可能有零点偏移。

## 6. 真实改造边界

### 本次允许做

新建 `elephant_gripper_node.py`（rclpy Node），含：

**状态发布角色：**
- 读大象夹爪寄存器值 angle[0,100]（modbus/SDK）。
- 映射 width = (angle - offset) / scale（用标定系数）。
- 发布 `/pi05/observation/gripper/left_state`、`/right_state`（Float32 width[0,1]）。

**命令执行角色：**
- 订阅 `/pi05/command/gripper/left_target`、`/right_target`（Float64 angle[0,100]）。
- 调大象夹爪 modbus/SDK 设寄存器。
- 记录 SDK 返回码。

**width↔angle 标定：**
- 实测闭合点寄存器值（angle_closed）和全开点寄存器值（angle_open）。
- 推导映射：width = (angle - angle_closed) / (angle_open - angle_closed)。
- 标定系数提供给 bridge（deploy_019 的 gripper_angle_scale/offset）。

**配置：**
- 左右夹爪串口/端口（modbus 连接）。
- 标定系数（angle_closed/angle_open 或 scale/offset）。

### 本次不做

- 不改 bridge（deploy_017~019）。
- 不重写 SDK。
- 不做 launch（deploy_022）。
- 不做 real-robot smoke test（deploy_023）。

### 明确禁止修改

- 禁止改 SDK 源码。
- 禁止改 bridge / Pi05 节点。
- 禁止标定前接真机命令执行。

### Adapter / 直接修改策略

```text
全新适配节点。复用 modbus/SDK。状态发布 angle→width 映射；命令执行直接设寄存器。标定实测反馈给 bridge。回滚：节点不启动。真机 high：直接驱动夹爪。
```

## 7. 实施步骤

1. **新建 `elephant_gripper_node.py`**。
2. **__init__**：连左右夹爪 modbus/SDK；创建状态发布器 + 命令订阅。
3. **状态发布**：读寄存器 angle → 映射 width → 发 Float32。
4. **命令执行**：收 Float64 angle → 设寄存器 → 记录返回码。
5. **标定流程**：实测闭合/全开寄存器值 → 推导系数 → 写 config / 反馈 bridge。
6. **config**：串口/端口/标定系数。
7. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/elephant_gripper_node.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)
assert 'gripper' in src.lower() and ('modbus' in src.lower() or 'pymycobot' in src.lower())
assert 'observation/gripper' in src or 'gripper_state' in src
assert 'command/gripper' in src or 'gripper_target' in src
assert 'width' in src.lower() and 'angle' in src.lower()
assert 'calib' in src.lower() or 'angle_closed' in src.lower() or 'scale' in src.lower()
print('deploy_021 验收通过: elephant_gripper_node(状态width+命令angle+标定)')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 结构断言 | 上述命令通过 |
| shadow-run | 部分（状态发布可验） | 状态 topic 有输出 | deploy_022 |
| real-robot | 是（命令执行驱动夹爪） | 夹爪按 angle 开合 | deploy_023 |

### 真机风险控制

> [!danger] high risk
> 命令执行直接驱动大象夹爪。标定前不接命令执行。shadow-run（gate 关）时 driver 收不到 command。
> - 是否会真实发送命令：是（modbus 设寄存器驱动夹爪）
> - 默认是否关闭：是（bridge gate 关 / shadow）
> - 回滚：节点不启动
> - 标定：必须先实测闭合/全开寄存器值，再接命令执行

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs/
```
## 9. 允许修改

- 新建 `src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/elephant_gripper_node.py`

## 10. 禁止修改

- SDK 源码。
- bridge / Pi05 节点。
- 标定前接真机命令执行。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（夹爪语义约定 + width↔angle 映射表）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D6/D16）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-05-硬件执行栈.md`

### 必读代码

1. 大象夹爪 modbus/pymycobot SDK 文档

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游（全新节点）。
2. 同组：deploy_017/020（并行）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on` 为空。

> [!danger] 真机任务
> 代码实现可无硬件完成（AST）。命令执行真实测试在 deploy_023。**标定必须在接命令执行前完成**。

```text
代码实现（AST）
→ 标定（实测闭合/全开寄存器值）
→ 状态发布 shadow 验证（deploy_022）
→ 命令执行 real-robot smoke test（deploy_023，急停就绪）
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] elephant_gripper_node.py 新建。
- [ ] 状态发布：angle→width 映射 → Float32。
- [ ] 命令执行：Float64 angle → modbus。
- [ ] 标定流程定义（闭合/全开实测）。
- [ ] SDK 返回码记录。
- [ ] 已完成 AST 验收。
- [ ] 真机测试标注（deploy_023）。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：节点不启动
切回旧入口：picotele_mux（inspire）
移除 adapter：删除 elephant_gripper_node.py
回退文件：git clean
不可自动回滚的人工步骤：急停
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新建文件、状态/命令逻辑、标定系数（实测值或待标定）、验收（AST）、成功标准勾选、**真机影响（high）**、回滚、未做事项（launch/smoke test）、后续建议（deploy_022 shadow + deploy_023 real-robot）。**标定系数反馈给 deploy_019 bridge 映射参数。**
