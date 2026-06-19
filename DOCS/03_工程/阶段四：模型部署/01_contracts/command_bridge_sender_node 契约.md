# command_bridge_sender_node 契约

关联总契约：[[TO-BE Contract#指令桥接与发送节点|指令桥接与发送节点]]

## 节点定位

`command_bridge_sender_node` 位于 `Pi05VlaDeployNode` 下游，是 **policy action 到硬件命令 topic** 的唯一语义边界。

它负责：

- 订阅 `/pi05/policy_action`。
- 按固定 14D 顺序解析双臂 TCP 目标和双夹爪角度目标。
- 订阅当前 TCP pose / gripper state，用于时效性、单步变化和诊断检查。
- 执行硬件相关安全门控。
- 将安全通过的目标发布到 `/pi05/command/*`。
- 发布 `/pi05/command/status`，记录接收、拒绝、发布和下游执行反馈。

它不负责：

- 不调用模型。
- 不读取 `Pi05VlaDeployNode` 内部对象。
- 不改写 policy action 语义。
- 不把硬件执行失败伪装成推理成功。
- 不把 RM65 / 大象夹爪 SDK 细节塞回 `Pi05VlaDeployNode`。

## 上下游接口

| 方向 | topic | ROS msg | 现实语义 |
|---|---|---|---|
| 订阅 | `/pi05/policy_action` | `std_msgs/msg/Float32MultiArray` | Pi05 模型输出的下一步双臂 TCP 目标和夹爪目标。 |
| 订阅 | `/pi05/observation/arm/left_tcp_pose` | `geometry_msgs/msg/PoseStamped` | 左 RM65 当前 TCP pose，用于安全检查和诊断。 |
| 订阅 | `/pi05/observation/arm/right_tcp_pose` | `geometry_msgs/msg/PoseStamped` | 右 RM65 当前 TCP pose，用于安全检查和诊断。 |
| 订阅 | `/pi05/observation/gripper/left_state` | `std_msgs/msg/Float32` | 左大象夹爪当前角度值，用于步长检查和诊断。 |
| 订阅 | `/pi05/observation/gripper/right_state` | `std_msgs/msg/Float32` | 右大象夹爪当前角度值，用于步长检查和诊断。 |
| 发布 | `/pi05/command/arm/left_target` | `geometry_msgs/msg/PoseStamped` | 已通过安全检查、准备交给左 RM65 执行节点的 TCP 目标。 |
| 发布 | `/pi05/command/arm/right_target` | `geometry_msgs/msg/PoseStamped` | 已通过安全检查、准备交给右 RM65 执行节点的 TCP 目标。 |
| 发布 | `/pi05/command/gripper/left_target` | `std_msgs/msg/Float32` | 已通过限幅 / 检查、准备交给左夹爪执行节点的角度目标。 |
| 发布 | `/pi05/command/gripper/right_target` | `std_msgs/msg/Float32` | 已通过限幅 / 检查、准备交给右夹爪执行节点的角度目标。 |
| 发布 | `/pi05/command/status` | `std_msgs/msg/String` | JSON 字符串，记录最近一次 action 的桥接、拒绝、发送和反馈状态。 |

> [!note] 边界说明
> `/pi05/command/*` 是 Pi05 内部硬件命令 topic，不是睿尔曼或大象夹爪厂商原始 topic。RM65 的 `Cartepos` / `Movejp` / `Movel`、大象夹爪 Modbus RTU `0x06` 写寄存器等厂商指令，应由下游 `rm65_driver_node` / `elephant_gripper_node` 的命令执行角色适配。

## `/pi05/policy_action` 解析契约

`/pi05/policy_action.data` 必须是长度为 `14` 的 `float32` 数组。顺序固定如下：

| 维度范围 | 字段 | 单位 | 坐标系 / 值域 | 目标 topic 字段 |
|---|---|---|---|---|
| `[0:3]` | `left_tcp_xyz_m` | `m` | `left_arm_base` | `/pi05/command/arm/left_target.pose.position` |
| `[3:6]` | `left_tcp_rpy_rad` | `rad` | `left_arm_base` | 转 quaternion 后写入 `/pi05/command/arm/left_target.pose.orientation` |
| `[6]` | `left_gripper_angle` | 大象夹爪角度值 | `0..100` | `/pi05/command/gripper/left_target.data` |
| `[7:10]` | `right_tcp_xyz_m` | `m` | `right_arm_base` | `/pi05/command/arm/right_target.pose.position` |
| `[10:13]` | `right_tcp_rpy_rad` | `rad` | `right_arm_base` | 转 quaternion 后写入 `/pi05/command/arm/right_target.pose.orientation` |
| `[13]` | `right_gripper_angle` | 大象夹爪角度值 | `0..100` | `/pi05/command/gripper/right_target.data` |

禁止事项：

- 禁止把 14D action 解释为关节角。
- 禁止沿用 AS-IS 的 `left_arm_joint6 + right_arm_joint6 + hand` 语义。
- 禁止把 gripper 目标解释为 `300..800` 或 `300..1000`。
- 禁止在没有 Contract Delta 的情况下把 action 改成 delta pose。

## 输出命令 msg 契约

### RM65 TCP 目标

| 字段 | 左臂 | 右臂 |
|---|---|---|
| `header.stamp` | 桥接节点发布命令的 ROS time。 | 桥接节点发布命令的 ROS time。 |
| `header.frame_id` | `left_arm_base`。 | `right_arm_base`。 |
| `pose.position` | 来自 `left_tcp_xyz_m`，单位 `m`。 | 来自 `right_tcp_xyz_m`，单位 `m`。 |
| `pose.orientation` | 由 `left_tcp_rpy_rad` 转成 ROS quaternion，顺序 `x,y,z,w`。 | 由 `right_tcp_rpy_rad` 转成 ROS quaternion，顺序 `x,y,z,w`。 |

下游 RM65 命令执行角色可将该 `PoseStamped` 适配为睿尔曼 ROS2 / SDK 指令。已知可选方向：

| 厂商接口方向 | 适用场景 | 契约要求 |
|---|---|---|
| `rm_ros_interfaces/msg/Cartepos` | 位姿透传。 | 其 `pose` 为 `geometry_msgs/Pose`，单位 `m` + quaternion；`follow` 由下游执行节点配置。 |
| `rm_ros_interfaces/msg/Carteposcustom` | 需要配置高跟随模式、滤波或曲线拟合。 | `trajectory_mode` / `radio` 属于下游执行参数，不写入 `/pi05/policy_action`。 |
| `rm_ros_interfaces/msg/Movejp` / `Movel` | 规划到目标位姿或直线运动。 | 速度、阻塞、轨迹连接等参数由下游执行节点配置。 |

### 大象夹爪目标

| 字段 | 左夹爪 | 右夹爪 |
|---|---|---|
| `data` | 左夹爪 `gripper_angle`，值域 `0..100`。 | 右夹爪 `gripper_angle`，值域 `0..100`。 |

下游大象夹爪命令执行角色可将该 `Float32` 适配为：

| 厂商接口方向 | 契约要求 |
|---|---|
| Modbus RTU `0x06` 写保持寄存器 | 设置夹爪角度寄存器地址 `11`，写入 `0..100`。 |
| pymycobot / USB-485 Python SDK | 必须保持 `gripper_angle 0..100` 语义。 |

## 安全门控契约

桥接节点必须把每条 policy action 当成一个原子动作处理：**任一关键检查失败时，不发布任何 arm / gripper command**，只发布 `/pi05/command/status` 说明拒绝原因。

| 检查项 | 输入 | 失败行为 |
|---|---|---|
| action 长度 | `/pi05/policy_action.data` | 若长度不是 `14`，拒绝整条 action。 |
| finite 检查 | 14D action | 任一元素为 NaN / Inf，拒绝整条 action。 |
| observation 时效性 | 当前 TCP pose / gripper state | 若配置要求依赖当前状态，而状态缺失或过期，拒绝整条 action。 |
| 坐标系检查 | 当前 TCP pose 和目标 TCP pose | `frame_id` 必须与左右臂基座一致；不一致则拒绝。 |
| workspace 检查 | 左 / 右 TCP 目标位置 | 超出配置 workspace，拒绝整条 action。 |
| TCP 单步位移 | 当前 TCP pose 与目标 TCP pose | 超过 `max_tcp_delta_m`，拒绝整条 action。 |
| TCP 单步姿态变化 | 当前 TCP orientation 与目标 orientation | 超过 `max_tcp_rot_delta_rad`，拒绝整条 action。 |
| gripper 值域 | 左 / 右 `gripper_angle` | 默认 clamp 到 `0..100`；若 `strict_gripper_range=true`，则拒绝整条 action。 |
| gripper 单步变化 | 当前夹爪角度与目标角度 | 超过 `max_gripper_delta` 时按配置拒绝或限速。 |
| real robot enable | enable / deadman / 急停状态 | 未使能、deadman 未按下或急停触发时，拒绝整条 action。 |

> [!warning] 原子性要求
> 不允许出现“左臂命令已发布、右臂检查失败、夹爪命令又继续发布”的半发送状态。桥接节点应先完成所有检查，再一次性发布四路命令。

## 坐标系与姿态转换

| 项 | 契约 |
|---|---|
| 左臂坐标系 | policy action 中左 TCP 目标已经位于 `left_arm_base`。桥接节点不再额外做世界系到左臂基座的推断转换。 |
| 右臂坐标系 | policy action 中右 TCP 目标已经位于 `right_arm_base`。桥接节点不再额外做世界系到右臂基座的推断转换。 |
| RPY 单位 | `rad`。 |
| RPY 顺序 | 固定为 `roll, pitch, yaw`。 |
| quaternion 输出 | ROS `geometry_msgs/Quaternion` 顺序为 `x, y, z, w`。 |
| 绝对 / delta 语义 | 当前 TO-BE 固定为绝对 TCP 目标；若后续改成 delta，必须写入 Contract Delta。 |

## `/pi05/command/status` 契约

`/pi05/command/status` 使用 `std_msgs/msg/String`，内容为 JSON 字符串。

最小字段：

| 字段 | 类型 | 语义 |
|---|---|---|
| `action_id` | int | 桥接节点为每条 policy action 分配的递增 ID。 |
| `stamp` | string / float | 桥接节点处理该 action 的时间。 |
| `accepted` | bool | action 是否通过桥接节点检查。 |
| `published_to_command_topics` | bool | 是否已经发布四路 `/pi05/command/*`。 |
| `failure_reason` | string | 拒绝原因；成功时为空字符串。 |
| `left_arm_target` | object | 左臂目标摘要：`xyz_m`、`rpy_rad`。 |
| `right_arm_target` | object | 右臂目标摘要：`xyz_m`、`rpy_rad`。 |
| `left_gripper_target` | float | 左夹爪目标角度。 |
| `right_gripper_target` | float | 右夹爪目标角度。 |
| `safety_checks` | object | 各安全检查的通过 / 失败摘要。 |

如果下游执行节点提供执行结果 topic，可扩展字段：

| 字段 | 类型 | 语义 |
|---|---|---|
| `left_arm_driver_ok` | bool / null | 左 RM65 执行节点是否接受 / 执行成功。 |
| `right_arm_driver_ok` | bool / null | 右 RM65 执行节点是否接受 / 执行成功。 |
| `left_gripper_driver_ok` | bool / null | 左夹爪执行节点是否接受 / 执行成功。 |
| `right_gripper_driver_ok` | bool / null | 右夹爪执行节点是否接受 / 执行成功。 |
| `driver_failure_reason` | string | 下游执行失败原因。 |

> [!note] 成功语义
> 若下游没有独立执行结果 topic，`published_to_command_topics=true` 只能表示“桥接节点已发布命令 topic”，不能表示 RM65 或夹爪真实执行成功。

## 配置参数

| 参数 | 类型 | 默认 / 说明 |
|---|---|---|
| `policy_action_topic` | string | `/pi05/policy_action`。 |
| `left_arm_state_topic` | string | `/pi05/observation/arm/left_tcp_pose`。 |
| `right_arm_state_topic` | string | `/pi05/observation/arm/right_tcp_pose`。 |
| `left_gripper_state_topic` | string | `/pi05/observation/gripper/left_state`。 |
| `right_gripper_state_topic` | string | `/pi05/observation/gripper/right_state`。 |
| `left_arm_target_topic` | string | `/pi05/command/arm/left_target`。 |
| `right_arm_target_topic` | string | `/pi05/command/arm/right_target`。 |
| `left_gripper_target_topic` | string | `/pi05/command/gripper/left_target`。 |
| `right_gripper_target_topic` | string | `/pi05/command/gripper/right_target`。 |
| `status_topic` | string | `/pi05/command/status`。 |
| `left_workspace_xyz_min` / `left_workspace_xyz_max` | float[3] | 左臂 workspace 边界，单位 `m`。 |
| `right_workspace_xyz_min` / `right_workspace_xyz_max` | float[3] | 右臂 workspace 边界，单位 `m`。 |
| `max_tcp_delta_m` | float | 单步 TCP 位移上限，单位 `m`。 |
| `max_tcp_rot_delta_rad` | float | 单步 TCP 姿态变化上限，单位 `rad`。 |
| `max_gripper_delta` | float | 单步夹爪角度变化上限。 |
| `gripper_min` / `gripper_max` | float | 固定 `0` / `100`。 |
| `strict_gripper_range` | bool | `false` 时 clamp，`true` 时拒绝越界 action。 |
| `require_fresh_state` | bool | 是否要求当前 TCP / gripper observation 未过期。 |
| `state_stale_timeout_sec` | float | 状态过期阈值。 |
| `real_robot_enable_required` | bool | 真机执行是否需要 enable / deadman。 |
| `command_publish_qos_depth` | int | command topic publisher queue depth。 |

## 与其他节点的职责切分

| 节点 | 本契约中的职责边界 |
|---|---|
| `Pi05VlaDeployNode` | 只发布 `/pi05/policy_action`，不直接控制硬件。 |
| `command_bridge_sender_node` | 解析 action、做安全门控、发布 `/pi05/command/*`、记录桥接状态。 |
| `rm65_driver_node` 命令执行角色 | 订阅 `/pi05/command/arm/*_target`，适配睿尔曼 ROS2 / SDK 指令并执行。 |
| `elephant_gripper_node` 命令执行角色 | 订阅 `/pi05/command/gripper/*_target`，适配大象夹爪 Modbus / SDK 指令并执行。 |

## 验收方式

| 检查项 | 标准 |
|---|---|
| 14D 正常 action | 发布四路 `/pi05/command/*`，并发布 `accepted=true` 的 `/pi05/command/status`。 |
| action 维度错误 | 不发布任何 `/pi05/command/*`，`failure_reason` 包含维度错误。 |
| action 含 NaN / Inf | 不发布任何命令，`failure_reason` 指出非法数值。 |
| gripper 越界 | 默认 clamp 到 `0..100`；strict 模式下拒绝。 |
| TCP workspace 越界 | 不发布任何命令，status 指出左 / 右侧越界。 |
| 当前状态过期 | `require_fresh_state=true` 时拒绝整条 action。 |
| 急停 / 未 enable | 不发布任何命令。 |
| 坐标系正确 | 左右 arm target 的 `frame_id` 分别为 `left_arm_base` / `right_arm_base`。 |
| 姿态转换正确 | RPY 输入转 quaternion 后模长接近 `1`，无 NaN / Inf。 |
