# L2-05 ACT 硬件执行栈

> [!info] 归属
> - 对应分层：独立子系统（自含分层，只依赖 `/act/policy_action` 16D 契约）
> - 关联 ACT Delta：A11（command_bridge + 驱动 + launch）、A12（失败语义）
> - 关联契约：[[ACT部署契约]]

> [!warning] 真机风险最高
> 本 L2 直接驱动 RM65 机械臂和大象夹爪。必须最后实现，且 shadow-run 全链路通过 + 8 项真机前置条件全部满足后，才允许 real-robot smoke test。

## 一句话定位

将 `/act/policy_action`（16D）转换成 RM65 / 大象夹爪可执行指令，在发送前执行硬件安全检查（workspace/IK预检/gripper限幅/急停 gate），并记录发送结果。

## 本次唯一目标

- 新建 `src/model_deploy/act/ui/ros_nodes/command_bridge_sender_node.py`：订阅 `/act/policy_action`，解析 16D，安全检查，发布 `/act/command/*`。
- 新建 `src/model_deploy/act/ui/ros_nodes/rm65_driver_node.py`（命令执行角色）：订阅 `/act/command/arm/*_target`（PoseStamped TCP 目标），调 RM65 `movep_canfd` 执行。
- 新建 `src/model_deploy/act/ui/ros_nodes/elephant_gripper_node.py`（命令执行角色）：订阅 `/act/command/gripper/*_target`（width→angle 映射后），执行夹爪开合。
- 新建 `src/model_deploy/act/launch/act_rm65_deploy.launch.py`：拉起状态发布节点 + ActVlaDeployNode + command_bridge + 驱动节点。

## 同事源码复用边界

| ACT 目标 | 同事源文件 | 方式 | 复用要点 |
|---|---|---|---|
| `act/ui/ros_nodes/command_bridge_sender_node.py` | `pi05_old/.../deploy/src/pi05/deploy/ros_nodes/pi05_bridge_node.py` (128行) | **参考** | 不搬运。参考同事 bridge 的 ROS 节点骨架（Node 类、订阅/发布创建、deadman 心跳、回调结构），但逻辑全部新写：16D policy_action 解析（而非关节翻译）+ workspace/IK 预检 + width→angle 映射 + gate(mode+急停)。同事 bridge 做的是 `/pi05_vla/command/*` → picotele safe_joint_target 翻译，语义完全不同 |
| `act/ui/ros_nodes/rm65_driver_node.py` | 无直接对应 | **新写** | picotele 臂节点和 RM65 SDK 完全不同。参考 RM65 硬件文档（`DOCS/01_知识/阶段四：模型部署/硬件开发文档/`）独立实现 |
| `act/ui/ros_nodes/elephant_gripper_node.py` | 无直接对应 | **新写** | 同事的 `picotele_hand_node` 是灵巧手 inspire，与大象夹爪 SDK 不同。参考大象夹爪 modbus/pymycobot 文档独立实现 |
| `act/launch/act_rm65_deploy.launch.py` | `pi05_old/.../deploy/launch/pi05_picotele_mux.launch.py` (414行) | **参考** | 不搬运。参考同事 launch 的编排结构（参数声明、节点装配、topic remap 写法），但节点列表完全不同（picotele/realsense/mux → RM65/大象夹爪/fisheye/command_bridge） |

> [!note] 硬件栈复用说明
> 本 L2 是**新写为主**的工作包，因为同事的硬件栈（picotele 臂 + 灵巧手 + bridge + mux）与 ACT 的硬件栈（RM65 + 大象夹爪 + command_bridge）硬件 SDK 和语义都不同。同事代码的价值在于**ROS 节点骨架写法**和**launch 编排模式**的参考，而非代码搬运。硬件文档参考路径：`DOCS/01_知识/阶段四：模型部署/硬件开发文档/`。

## 明确不做

- 不读 ActVlaDeployNode 内部状态（SharedBuffer/ActionChunk/ControlLoop），只消费 `/act/policy_action`。
- 不重新调用模型。
- 不修改 Pi0.5 硬件代码。

## `/act/policy_action` 16D 解析契约

| 维度 | 字段 | 下游用法 |
|---|---|---|
| [0:7] | left_tcp(x,y,z,qx,qy,qz,qw) | 直接填 `/act/command/arm/left_target`（PoseStamped，无需 rpy 转换） |
| [7] | left_gripper_width[0,1] | 映射 `angle=width*100`，限幅 [0,100]，发 `/act/command/gripper/left_target` |
| [8:15] | right_tcp | 填 `/act/command/arm/right_target` |
| [15] | right_gripper_width | 映射后发 `/act/command/gripper/right_target` |

## 发送前必须执行的检查（复用 Pi0.5 契约设计）

1. action 维度 = 16D
2. 全部 finite（NaN/Inf）
3. quaternion 归一化（模长≈1）
4. TCP 目标在 RM65 workspace 内
5. **IK 预检**（`rm_inverse_kinematics` flag=0 四元数模式，不执行只查；不可解则不发）
6. gripper_width ∈ [0,1]，映射 angle ∈ [0,100]
7. enable / 急停 / deadman gate

全通过后才发 `movep_canfd` + gripper 命令。任一失败，写入 `/act/command/status.failure_reason`，**不让坏命令到达控制器**。

## 硬件约定（复用 Pi0.5 契约）

- TCP pose 来源：RM65 `rm_pose_t` 的 quaternion 字段（xyzw），driver 内 euler→quaternion 转换一次，下游全走 quaternion。
- width↔angle 映射：`angle = width*100`（理论值，**实际系数需大象夹爪标定**，标定前不接真机）。
- 详见 [[ACT部署契约]] 和 [[TO-BE Contract]] 的硬件约定章节。

## 依赖

- 只依赖 `/act/policy_action` 16D 契约（不依赖 L2-01~04 代码）。
- 可在 ACT 推理链路就绪前独立开发和 shadow-run 验证（用 fake policy_action publisher）。

## L3 草案

| L3 | 目标 | 验收模式 |
|---|---|---|
| deploy_017 | 新建 command_bridge_sender_node.py：订阅 policy_action，16D 解析，安全检查骨架 | downstream-l2（shadow-run） |
| deploy_018 | bridge IK 预检 + workspace 检查 | downstream-l2 |
| deploy_019 | bridge gate（mode + 急停/deadman）+ width→angle 映射 + `/act/command/status` | downstream-l2 |
| deploy_020 | rm65_driver_node（命令执行角色，movep_canfd） | hardware-blocked（真机） |
| deploy_021 | elephant_gripper_node（命令执行角色） | hardware-blocked |
| deploy_022 | launch 整合 + shadow-run 全链路验证（fake policy_action） | direct-local（shadow-run） |
| deploy_023 | real-robot smoke test（保守动作阶梯） | hardware-blocked（真机验收） |

## 真机风险

**最高**。直接驱动机械臂和夹爪。

### real-robot smoke test 解除 blocked 的 8 项前置条件

1. deploy_022 shadow-run 全链路通过。
2. RM65 双臂连接/标定/工作空间确认。
3. 大象夹爪连接/标定/width 映射系数确认。
4. ACT 真 model bundle 就绪。
5. 物理急停和 deadman 可用。
6. 人在场 + 安全区域清空。
7. **用户或现场负责人明确授权**。
8. 回滚路径和停止策略已确认。

### real-robot smoke test 保守动作阶梯

- 保持当前位姿（验证链路，不动）
- 微小位移 1cm（验证 movep_canfd）
- 急停测试（运动中触发急停，机械臂立即停止）
- gripper 半开（验证夹爪映射）

## 回滚方式

节点不启动。launch 切回不包含硬件驱动的版本。

## L2 Gate（AI 侧自动化）

- required L3：deploy_017 ~ deploy_022（软件侧）。deploy_023 真机验收默认 blocked。
- 运行命令：shadow-run 启动全 launch（fake policy_action publisher）；`pytest`。
- 通过现象：16D→PoseStamped+Float64 转换正确；安全检查失败不发送；`/act/command/status` 记录正确；shadow-run 下机械臂不动。

## 人类验收标准

### 软件侧（shadow-run，验收性质「机械」）

| 验收项 | 运行命令 | 通过现象 |
|---|---|---|
| 1 | shadow-run 启动全 launch（fake policy_action publisher 发 16D） | 节点全部启动不报错 |
| 2 | `ros2 topic echo /act/command/arm/left_target` | PoseStamped 字段完整，position 单位 m，orientation quaternion |
| 3 | 构造 IK 不可解的 policy_action | `/act/command/status.failure_reason` 记录 IK 不可解，不发硬件命令 |
| 4 | `ros2 topic echo /act/command/status`（shadow-run） | sent_to_driver=false，safety_ok=true |

### 真机侧（real-robot，验收性质「人工」）

仅在 8 项前置条件全部满足后执行：

| 验收项 | 操作 | 通过现象 |
|---|---|---|
| 5 | safe-run 启动，保持当前位姿 | 机械臂不动，`/act/command/status` 正常 |
| 6 | 微小位移 1cm | 机械臂平滑移动到目标，无抖动 |
| 7 | 运动中触发急停 | 机械臂立即停止 |
| 8 | gripper 半开指令 | 夹爪正确开合到对应宽度 |

> [!danger] 真机验收必须人工
> 软件侧 shadow-run 可机械验收；真机侧（验收项 5-8）必须人工观察，且需用户明确授权 + 急停准备 + 人在场。禁止在无硬件环境下声明 real-robot 通过。

用户签字位置：`05_acceptance/l2-05-hardware/验收结果.md` 末尾「人类验收」段。真机验收项需额外附现场负责人签名和日期。
