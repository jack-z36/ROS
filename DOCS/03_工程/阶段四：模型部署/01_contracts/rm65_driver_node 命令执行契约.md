# rm65_driver_node 命令执行契约

关联总契约：[[TO-BE Contract#指令桥接与发送节点|指令桥接与发送节点]]

关联状态契约：[[rm65_driver_node 状态发布契约]]

## 节点定位

`rm65_driver_node` 的命令执行角色负责接收 `command_bridge_sender_node` 已经安全门控后的左 / 右 RM65 TCP 目标，并调用睿尔曼 RM65 四代机械臂 ROS2 driver 或 SDK 执行。

本节点不订阅 `/pi05/policy_action`，也不解析 14D policy action。14D 向左右 TCP 目标的拆分、workspace / IK / enable / deadman 等上游门控由 `command_bridge_sender_node` 完成；本节点只承担“已批准 TCP 目标 -> RM65 硬件执行”的边界。

## 上下游接口

| 方向 | topic | ROS msg | 现实语义 |
|---|---|---|---|
| 订阅 | `/pi05/command/arm/left_target` | `geometry_msgs/msg/PoseStamped` | 左 RM65 在左臂基座坐标系下的 TCP 目标位姿。 |
| 订阅 | `/pi05/command/arm/right_target` | `geometry_msgs/msg/PoseStamped` | 右 RM65 在右臂基座坐标系下的 TCP 目标位姿。 |
| 发布 | `/pi05/command/arm/left_result`（可选） | `std_msgs/msg/String` | 左臂 SDK / driver 接收、拒绝、超时或报错结果。 |
| 发布 | `/pi05/command/arm/right_result`（可选） | `std_msgs/msg/String` | 右臂 SDK / driver 接收、拒绝、超时或报错结果。 |

如果暂不单独实现 result topic，则必须把等价结果写入 `/pi05/command/status` 的聚合状态中；禁止静默吞掉 SDK 返回码。

## 输入 msg 契约

| 字段 | 左臂要求 | 右臂要求 |
|---|---|---|
| `header.stamp` | 上游目标生成时间；超过 `stale_target_sec` 必须拒绝。 | 同左。 |
| `header.frame_id` | 必须为 `left_arm_base`。 | 必须为 `right_arm_base`。 |
| `pose.position.x/y/z` | 单位 `m`，表示左臂基座坐标系下 TCP 目标位置。 | 单位 `m`，表示右臂基座坐标系下 TCP 目标位置。 |
| `pose.orientation` | ROS quaternion，字段顺序为 `x,y,z,w`。 | ROS quaternion，字段顺序为 `x,y,z,w`。 |

## RM65 执行后端映射

| 后端 | 使用方式 | 契约要求 |
|---|---|---|
| ROS2 `Movel.msg` | 将 `PoseStamped.pose` 转为 `rm_ros_interfaces/msg/Movel.pose`，并填写 `speed`、`trajectory_connect`、`block`。 | 官方 ROS2 文档中 `Movel.msg` 的 `pose` 为 `geometry_msgs/Pose`，位置单位 `m`，姿态为 quaternion；`speed` 是 `0..100` 速度百分比；`trajectory_connect=0` 表示立即规划；`block=false` 表示非阻塞。 |
| SDK `rm_movej_p` / `movej_p` | 将目标 pose 转为 `rm_pose_t`，调用睿尔曼轨迹规划接口执行到目标 TCP 位姿。 | `rm_pose_t.position` 使用 `m`；`rm_pose_t.euler` 使用 `rad`。如果由 ROS quaternion 转欧拉角，必须固定转换顺序并在代码注释中写明。 |
| SDK / ROS2 透传 pose | 仅在需要高频姿态透传时使用。 | 透传模式会绕过部分轨迹规划假设；必须另立 Contract Delta，完成真机安全验证后才能作为默认后端。 |

默认推荐使用 ROS2 `Movel.msg` 或 SDK `movej_p` 这类规划型 TCP 目标执行路径；不要在本契约中默认启用高频透传。

## 坐标系与姿态转换

| 项 | 契约 |
|---|---|
| 输入坐标系 | 只接受 `left_arm_base` / `right_arm_base`。 |
| RM65 工作坐标系 | 若底层 API 使用“当前工作坐标系”，启动时必须确认其与对应 base frame 的变换；不一致时必须显式转换或拒绝启动。 |
| 位置单位 | ROS topic 和 `rm_pose_t.position` 均按 `m` 处理。禁止把 `mm` 当 `m`。 |
| ROS quaternion 顺序 | ROS 为 `x,y,z,w`。 |
| 睿尔曼算法接口 quaternion 顺序 | 睿尔曼算法文档中的部分接口使用 `[w,x,y,z]`；与 ROS 互转时必须重排。 |
| 欧拉角单位 | 睿尔曼算法与 `rm_pose_t.euler` 使用 `rad`。 |

## 执行前校验

| 校验项 | 处理方式 |
|---|---|
| 左右 frame_id 不匹配 | 拒绝执行，并记录 error。 |
| target 过期 | 拒绝执行，不复用旧目标。 |
| pose 含 NaN / Inf | 拒绝执行。 |
| quaternion 范数异常 | 拒绝执行；不得把非法 quaternion 发给 SDK。 |
| 未使能 / 急停 / deadman 未满足 | 拒绝执行，并返回明确状态。 |
| 目标超出 workspace 或 IK 不可解 | 原则上由 `command_bridge_sender_node` 先拒绝；本节点若再次发现，也必须拒绝，不得强行下发。 |
| SDK / driver 未连接 | 不发布成功，不发送伪造执行结果。 |

## 执行参数契约

| 参数 | 类型 | 默认建议 | 含义 |
|---|---|---|---|
| `backend` | enum | `ros2_movel` | `ros2_movel`、`sdk_movej_p` 或经 Delta 批准的透传后端。 |
| `left_arm_namespace` | string | 必填 | 左臂 ROS2 driver namespace 或 SDK 连接别名。 |
| `right_arm_namespace` | string | 必填 | 右臂 ROS2 driver namespace 或 SDK 连接别名。 |
| `left_frame_id` | string | `left_arm_base` | 左臂目标 frame。 |
| `right_frame_id` | string | `right_arm_base` | 右臂目标 frame。 |
| `speed_percent` | int | 10-30 | RM65 运动速度百分比；必须限制在官方允许范围内。 |
| `trajectory_connect` | int | `0` | `0` 表示立即规划执行；`1` 不立即执行，不适合作为默认在线控制。 |
| `block` | bool | `false` | 默认非阻塞，避免执行线程被硬件长时间阻塞。 |
| `command_timeout_sec` | float | 必填 | SDK / driver 接受命令和执行回执超时。 |
| `stale_target_sec` | float | 必填 | 目标消息最大可用年龄。 |

## 执行结果语义

| 状态 | 含义 |
|---|---|
| `accepted` | SDK / driver 已接受本次目标。只能说明命令被接收，不等价于机械臂已到位。 |
| `rejected` | 本节点校验失败，未向 RM65 发送。 |
| `sdk_error` | 已调用 SDK / driver，但返回非成功码或异常。 |
| `timeout` | 等待 driver 接受或回执超时。 |
| `disabled` | enable / deadman / 急停条件不满足。 |

## 与 `command_bridge_sender_node` 对齐

| 上游保证 | 本节点补充保证 |
|---|---|
| 上游把 `/pi05/policy_action` 解析成左右 `PoseStamped`。 | 本节点不再重新解释 14D action。 |
| 上游完成 policy action 层和硬件层安全门控。 | 本节点仍做最后一层 frame、finite、quaternion、连接和 SDK 返回码检查。 |
| 上游发布的是 TCP 目标，不是关节角。 | 本节点选择 RM65 TCP pose 执行接口，不要求 Pi05 输出关节空间动作。 |

## 验收方式

| 检查项 | 标准 |
|---|---|
| topic 存在 | 能看到 `/pi05/command/arm/left_target` 和 `/pi05/command/arm/right_target` 订阅。 |
| frame 拒绝 | 向左臂 topic 发布 `right_arm_base` frame 时，节点拒绝执行。 |
| 单位正确 | 发送 `0.01m` 级小位移目标时，末端运动量级与米制一致。 |
| 姿态正确 | quaternion 合法且连续变化；非法 quaternion 被拒绝。 |
| 断连处理 | 断开任一 RM65 连接后，不再报告 `accepted`。 |
| 急停处理 | 急停 / deadman 未满足时，目标不下发。 |
