# L3 微元改造任务：rm65_driver_node（状态发布 + 命令执行）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-05 硬件执行栈
来源 Delta：D5（机械臂 picotele→RM65）、D15（arm msg PoseStamped）
L3 编号：deploy_020
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_020_rm65_driver_node.md`
改造类型：new-feature
真机风险等级：high（直接驱动 RM65 机械臂）
L2 Git 分支：model_deploy-l2-05-hardware
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware
对应 L2 运行验收场景：[S5]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_020_验收卡片.md
验收模式：static-review
辅助验收模式：['hardware-blocked']
本地验收是否必须：false
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_020
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-hardware/deploy_020_rm65_driver_node.md
  group: l2-05-hardware
  branch: model_deploy-l2-05-hardware
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware
  acceptance_scenarios: [S5]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_020_验收卡片.md
  acceptance_mode: static-review
  acceptance_secondary_modes: [hardware-blocked]
  local_acceptance_required: false
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs
  wave: 1
  parallel_group: l2-05-hardware-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_017, deploy_021]
  blocks: [deploy_022, deploy_023]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/rm65_driver_node.py
    modules:
      - pi05.deploy.ros_nodes.rm65_driver_node
    config_keys: []
    runtime_modes: []
    hardware_paths:
      - rm65_arm_left
      - rm65_arm_right
      - rm65_sdk
  robot_risk: hardware-blocked
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 rm65_driver_node 适配层：状态发布角色（把厂商 rm_pose_t/UDP 推送的 quaternion 转成 /pi05/observation/arm/*_tcp_pose PoseStamped quaternion 归一化）+ 命令执行角色（收 /pi05/command/arm/*_target PoseStamped → 调 movep_canfd pose_quat 模式驱动机械臂）。复用厂商 rm_driver，不重写底层驱动。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D5 + D15 |
| 变更对象 | 机械臂 + arm msg 类型 |
| AS-IS 契约 | picotele_arm_node 消费 JointState(6D)；状态由 picotele 内部发布。 |
| TO-BE 契约 | rm65_driver_node：状态发布 PoseStamped(quaternion xyzw 归一化, m, frame_id)；命令执行收 PoseStamped → movep_canfd pose_quat。依据：TO-BE Contract RM65 约定 + 硬件文档。 |
| 兼容性要求 | 新增适配节点（不重写厂商驱动）。 |
| 回滚要求 | 节点不启动。 |

### 所属 L2 改造工作包

- L2 名称：L2-05 硬件执行栈
- 本 L3 在该 L2 中的位置：与 deploy_017（bridge）/deploy_021（gripper）并行（新建不同文件）。
- 本 L3 完成后解锁：deploy_022（shadow 全链路，需 driver 状态发布）、deploy_023（real-robot）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| 厂商 rm_driver（ROS2 包） | 外部依赖 | /rm_driver/udp_joint_pose_euler 状态 + movep_canfd 命令 | 复用，不重写 | 否（复用） |
| rm_realtime_arm_joint_state_t | 硬件文档 | waypoint = rm_pose_t（含 quaternion） | 取 quaternion 字段 | 否（只读） |
| 无（全新适配节点） | — | — | 全新建 | 是（新建） |

### 必须保留的现有行为

- 厂商 rm_driver 的底层驱动逻辑（不重写）。
- movep_canfd 的帧间限制（≤10°/帧, ≤180°/s，控制器侧强制）。

### 已知风险

- **直接驱动 RM65 机械臂**（high risk）。命令执行角色发 movep_canfd 会让机械臂运动。
- 状态发布角色：厂商 UDP 推送的 waypoint 含 rm_pose_t（quaternion+euler），优先取 quaternion；若某路只给 euler 则 euler→quaternion。
- quaternion 归一化：厂商数据可能未归一化，发布前必须归一化（TO-BE Contract warning）。
- movep_canfd pose_quat 单位是定点数 ×1e6（m 和 quaternion 分量），需从 PoseStamped 的 float 转定点数。

## 6. 真实改造边界

### 本次允许做

新建 `rm65_driver_node.py`（rclpy Node），含：

**状态发布角色：**
- 订阅厂商 `/rm_driver/udp_arm_current_status`（或直接调 SDK 状态 API）。
- 从 `rm_realtime_arm_joint_state_t.waypoint`（rm_pose_t）取 quaternion（优先）或 euler（转 quaternion）。
- quaternion 归一化。
- 发布 `/pi05/observation/arm/left_tcp_pose`、`/right_tcp_pose`（PoseStamped，position m, orientation quaternion xyzw, frame_id=left_arm_base/right_arm_base）。

**命令执行角色：**
- 订阅 `/pi05/command/arm/left_target`、`/right_target`（PoseStamped）。
- 把 PoseStamped 的 position(m) + orientation(quaternion) 转成 movep_canfd 的 pose_quat 定点数（×1e6）。
- 调厂商 movep_canfd（pose_quat 模式，follow=true 高跟随）。
- 记录 SDK 返回码，错误透传（供 bridge status 用，或独立发布 driver_status）。

**配置：**
- 左右臂 IP / 端口（SDK 连接参数）。
- frame_id 映射。

### 本次不做

- 不改 bridge（deploy_017~019）。
- 不重写厂商 rm_driver（复用）。
- 不做 launch（deploy_022）。
- 不做 real-robot smoke test（deploy_023）。
- 不实现 IK 预检（那是 bridge 的 deploy_018；driver 只负责执行 + 状态）。

### 明确禁止修改

- 禁止改厂商 rm_driver 源码。
- 禁止改 bridge / Pi05 节点。
- 禁止在本 L3 做 real-robot smoke test（deploy_023）。

### Adapter / 直接修改策略

```text
全新适配节点。复用厂商 rm_driver（状态 API + movep_canfd）。状态发布取 quaternion 归一化；命令执行转定点数。回滚：节点不启动。真机风险 high：movep_canfd 直接驱动机械臂。
```

## 7. 实施步骤

1. **新建 `rm65_driver_node.py`**。
2. **__init__**：连左右臂 SDK（或复用厂商 rm_driver 的连接）；创建状态订阅 + 命令订阅 + 状态发布器。
3. **状态发布**：取 waypoint.quaternion（或 euler→quat）→ 归一化 → 发 PoseStamped。
4. **命令执行**：收 PoseStamped → 转定点数 → movep_canfd pose_quat → 记录返回码。
5. **config**：臂 IP/端口/frame_id。
6. **AST 验收**。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
import ast
path = 'src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/rm65_driver_node.py'
src = open(path, encoding='utf-8').read()
ast.parse(src)
assert 'movep_canfd' in src or 'movep' in src.lower()
assert 'pose_quat' in src or 'quaternion' in src.lower()
assert 'observation/arm' in src or 'tcp_pose' in src
assert 'command/arm' in src or 'target' in src
assert 'normalize' in src.lower() or 'norm' in src.lower()
print('deploy_020 验收通过: rm65_driver_node(状态发布quaternion+命令执行movep_canfd)')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 结构断言 | 上述命令通过 |
| dry-run | 否（driver 需连硬件） | — | — |
| shadow-run | 部分（状态发布可验，命令执行 gate 关） | 状态 topic 有输出 | deploy_022 |
| real-robot | 是（命令执行驱动机械臂） | 机械臂按 PoseStamped 运动 | deploy_023 smoke test |

### 真机风险控制

> [!danger] high risk
> 本 L3 的命令执行角色直接驱动 RM65 机械臂。必须在 deploy_022（shadow-run，gate 关闭）验证状态发布正确后，才在 deploy_023 做 real-robot smoke test。
> - 是否会真实发送命令：是（movep_canfd 驱动机械臂）
> - 默认是否关闭真实发送：是（bridge gate 关 / shadow-run 时 driver 收不到 command，因 bridge 不发）
> - 回滚到原始发送路径：节点不启动；bridge gate 关
> - 急停优先：物理急停必须优先于软件 gate

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/logs/
```
## 9. 允许修改

- 新建 `src/model_deploy/pi05/deploy/src/pi05/deploy/ros_nodes/rm65_driver_node.py`

## 10. 禁止修改

- 厂商 rm_driver 源码。
- bridge / Pi05 节点。
- 本 L3 不做 real-robot smoke test（deploy_023）。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（RM65 约定 + quaternion 归一化 warning）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D5/D15）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-05-硬件执行栈.md`

### 必读代码

1. 厂商 rm_driver ROS2 包（状态 topic + movep_canfd 接口）

### 必读硬件文档

1. `DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/Python 机械臂实时状态推送信息结构体rm_realtime_arm_joint_state_t  睿尔曼智能科技.md`（waypoint rm_pose_t）
2. `DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/JSON 协议：运动指令集  睿尔曼智能科技.md`（movep_canfd pose_quat 定点数）
3. `DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/Python 表示一个坐标系的结构体rm_pose_t  睿尔曼智能科技.md`

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 无直接上游（全新节点；与 bridge 通过 topic 解耦）。
2. 同组：deploy_017（并行）。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on` 为空。

> [!danger] 真机任务
> 本 L3 涉及真机驱动。代码实现可在无硬件环境完成（AST 验收），但**命令执行角色的真实测试必须在 deploy_023（real-robot smoke test）做，且有人在场 + 急停就绪**。状态发布角色可在 shadow-run（deploy_022）验证。

```text
代码实现（AST 验收）
→ 状态发布 shadow 验证（deploy_022）
→ 命令执行 real-robot smoke test（deploy_023，急停就绪）
```

## 13. 成功标准

- [ ] 已完成任务文件身份校验。
- [ ] 已确认当前分支符合所属 L2 分支规范。
- [ ] rm65_driver_node.py 新建。
- [ ] 状态发布：取 quaternion 归一化 → PoseStamped。
- [ ] 命令执行：PoseStamped → 定点数 → movep_canfd pose_quat。
- [ ] SDK 返回码记录。
- [ ] 复用厂商 rm_driver（不重写）。
- [ ] 已完成自动化验收（AST）。
- [ ] 真机测试标注（deploy_023 做）。
- [ ] 已写明回滚方式。

## 14. 回滚方式

```text
关闭参数 / 配置：节点不启动（launch 不拉起）
切回旧入口：切回 pi05_picotele_mux.launch（picotele）
移除 adapter：删除 rm65_driver_node.py
回退文件：git clean（新文件）
不可自动回滚的人工步骤：急停（如机械臂在运动中需物理急停）
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、新建文件、状态发布/命令执行逻辑、quaternion 归一化、定点数转换、SDK 返回码、验收结果（AST）、成功标准勾选、**真机影响（high，movep_canfd 驱动机械臂）**、回滚、未做事项（launch/smoke test）、后续建议（deploy_022 shadow 状态验证 + deploy_023 real-robot）。
