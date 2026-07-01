# rm65_driver_node 状态发布契约

关联总契约：[[TO-BE Contract#传感器数据发送节点|传感器数据发送节点]]

## 节点定位

`rm65_driver_node` 的状态发布角色负责把左 / 右睿尔曼 RM65 四代 6DOF 机械臂的当前末端 TCP 位姿转换为 Pi05 统一 observation topic，供 `Pi05VlaDeployNode` 构造模型输入使用。

本契约只描述“作为传感器 / 状态源”的发布边界：它可以订阅或读取睿尔曼原始状态源，但不订阅 Pi05 命令 topic、不执行 policy action。实际工程中可以和命令执行角色放在同一个 driver node 内实现，但 topic 职责必须保持清楚。

> [!note] 睿尔曼文档依据
> - [[01-doing/ROS/DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/ROS2：rm_driver功能包说明  睿尔曼智能科技.md]]：列出 `/rm_driver/udp_joint_pose_euler` 等 UDP 主动上报 topic。
> - [[01-doing/ROS/DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/ROS2：rm_ros_interface功能包说明  睿尔曼智能科技.md]]：`Jointposeeuler.msg` 字段为 `float32[3] euler` 和 `float32[3] position`，`euler` 精度 `0.001rad`，`position` 精度 `0.000001M`。
> - [[01-doing/ROS/DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/C、C++ 机械臂位置姿态结构体rm_pose_t  睿尔曼智能科技.md]]：`rm_pose_t.position` 单位为 `m`，`rm_pose_t.euler` 单位为 `rad`，同时提供 `quaternion`。
> - [[01-doing/ROS/DOCS/01_知识/阶段四：模型部署/硬件开发文档/睿尔曼r65四代技术文档/Python 机械臂当前状态的结构体rm_current_arm_state_t  睿尔曼智能科技.md]]：`rm_current_arm_state_t.pose` 是机械臂当前位姿信息，`joint` 虽然存在但不属于 Pi05 TO-BE 最小 observation 契约。

## 上下游接口

| 方向 | topic / 来源 | ROS msg / API 类型 | 现实语义 |
|---|---|---|---|
| 读取 / 订阅 | 左臂睿尔曼原始状态源，例如 namespaced `/rm_driver/udp_joint_pose_euler` 或当前状态 API | `rm_ros_interfaces/msg/Jointposeeuler` 或 `rm_current_arm_state_t.pose` | 左 RM65 当前末端位姿。 |
| 读取 / 订阅 | 右臂睿尔曼原始状态源，例如 namespaced `/rm_driver/udp_joint_pose_euler` 或当前状态 API | `rm_ros_interfaces/msg/Jointposeeuler` 或 `rm_current_arm_state_t.pose` | 右 RM65 当前末端位姿。 |
| 发布 | `/pi05/observation/arm/left_tcp_pose` | `geometry_msgs/msg/PoseStamped` | 左 RM65 末端 TCP 在 `left_arm_base` 坐标系下的当前位姿。 |
| 发布 | `/pi05/observation/arm/right_tcp_pose` | `geometry_msgs/msg/PoseStamped` | 右 RM65 末端 TCP 在 `right_arm_base` 坐标系下的当前位姿。 |
| 订阅 | Pi05 命令 topic | 无 | 状态发布角色不订阅 `/pi05/policy_action` 或 `/pi05/command/*`。 |

## RM65 位姿来源

| 来源 | 使用方式 | 契约要点 |
|---|---|---|
| `/rm_driver/udp_joint_pose_euler` | 可作为 ROS2 优先来源。运行两台 RM65 时，必须通过 namespace 或 remap 把左右臂的该 topic 区分开，再转发到 Pi05 topic。 | 消息类型是 `rm_ros_interfaces/msg/Jointposeeuler`，包含 `position[3]` 和 `euler[3]`；该消息没有 `header`，Pi05 `PoseStamped.header.stamp` 应使用本节点接收或转换时的 ROS clock。 |
| `rm_get_current_arm_state()` / `rm_current_arm_state_t.pose` | 可作为 API 轮询或驱动内部替代来源。 | `pose` 本身包含 position、quaternion 和 euler。若可直接获取 quaternion，优先直接填入 `PoseStamped.pose.orientation`。 |
| UDP 主动上报回调 `rm_realtime_arm_joint_state_t.waypoint` | 可作为非 ROS2 封装实现时的来源。 | `waypoint` 类型为 `rm_pose_t`，表示当前位置姿态。主动上报周期可配置，文档默认 5ms。 |
| 关节角 topic / `joint` 字段 | 不属于本 TO-BE 最小 observation 契约。 | 只允许用于调试、安全检查或下游执行链路，不反向引入 Pi05 模型输入。 |

左右两台机械臂必须通过配置显式区分，例如 ROS namespace、IP、设备别名或驱动实例名。禁止用“先启动的是左臂”这类隐式假设。

## 发布 msg 契约

| 字段 | 左臂值 | 右臂值 |
|---|---|---|
| `header.stamp` | 状态接收 / 转换时间，使用 ROS clock。若原始来源自带硬件时间戳，可在代码注释中说明并转用该时间戳。 | 状态接收 / 转换时间，使用 ROS clock。若原始来源自带硬件时间戳，可在代码注释中说明并转用该时间戳。 |
| `header.frame_id` | `left_arm_base` | `right_arm_base` |
| `pose.position.x/y/z` | TCP 在左臂基座坐标系下的位置，单位 `m`。 | TCP 在右臂基座坐标系下的位置，单位 `m`。 |
| `pose.orientation` | TCP 姿态 quaternion，按 ROS `geometry_msgs/Quaternion` 顺序 `x, y, z, w` 填写。 | TCP 姿态 quaternion，按 ROS `geometry_msgs/Quaternion` 顺序 `x, y, z, w` 填写。 |

## 单位与姿态转换

| 项 | 契约 |
|---|---|
| 位置单位 | Pi05 对外发布一律为 `m`。睿尔曼 `rm_pose_t.position` 文档单位是 `m`；`Jointposeeuler.position` 文档写明精度为 `0.000001M`，因此默认按 `m` 处理。只有当实际使用的其他 API 明确返回 `mm` 时，才允许除以 `1000`，且必须在配置中标明。 |
| 姿态输出 | Pi05 对外发布一律为 quaternion。 |
| 四元数来源 | 如果来源是 `rm_current_arm_state_t.pose` 或 `rm_realtime_arm_joint_state_t.waypoint` 且可获取 `rm_pose_t.quaternion`，优先直接使用该 quaternion。需注意睿尔曼 quaternion 文档 / API 常见顺序为 `w, x, y, z`，写入 ROS `geometry_msgs/Quaternion` 时必须转成 `x, y, z, w`。 |
| 欧拉角来源 | 如果来源是 `/rm_driver/udp_joint_pose_euler`，则按 `Jointposeeuler.euler[3]` 转 quaternion。 |
| 欧拉角单位 | 睿尔曼 `rm_pose_t.euler` 和 ROS2 `Jointposeeuler.euler` 文档均写明为 `rad`，因此该来源不需要 deg -> rad 转换。只有换用明确返回 `deg` 的其他 API 时，才允许转换。 |
| 欧拉角顺序 | 按睿尔曼文档和算法接口中常用的 `[rx, ry, rz]` 理解，在代码中固定为 `roll_pitch_yaw`。若后续实测发现厂商 topic 顺序与文档不一致，必须写入 Contract Delta。 |

## 与 Pi05VlaDeployNode 对齐

| Pi05 需求 | 本节点保证 |
|---|---|
| Pi05 只需要左 / 右 TCP pose，不需要关节角作为必需输入。 | 只发布 `/pi05/observation/arm/*_tcp_pose` 两个 observation topic；不把 `/joint_states`、`joint_position` 或 `rm_current_arm_state_t.joint` 纳入 Pi05 最小 observation 契约。 |
| Pi05 的 policy action 是 TCP + gripper 目标，不是关节空间动作。 | 本节点提供与 action 语义对齐的当前 TCP 状态。 |
| Pi05 需要坐标系和单位无歧义。 | `frame_id` 固定为 `left_arm_base` / `right_arm_base`，位置单位固定为 `m`，姿态固定为 ROS quaternion。 |
| Pi05 依赖 observation 时效性判断。 | 若原始 `Jointposeeuler` 没有 header，则用节点接收或转换时间生成 `PoseStamped.header.stamp`，不留空。 |

## 异常处理契约

| 场景 | 处理方式 |
|---|---|
| 左 / 右 RM65 连接失败 | 不发布伪造 pose；日志明确指出是左臂还是右臂离线。 |
| 厂商 topic / API 超时 | 停止发布旧 pose，并记录 warn。不允许把过期 TCP pose 当成新 observation 发给 Pi05。 |
| `Jointposeeuler` 或 API 返回位姿含 NaN / Inf | 丢弃当前样本，不更新 Pi05 observation topic。 |
| quaternion 非法或模长近似 0 | 丢弃当前样本，记录姿态转换错误。 |
| 单位无法确认 | 节点不得静默发布；必须报错并要求配置明确单位。 |
| 左右臂映射冲突 | 节点启动失败，避免把右臂 pose 发布到左臂 topic。 |
| 两个 RM65 driver 没有 namespace 隔离，原始 `/rm_driver/*` topic 冲突 | 启动失败或拒绝转发，要求配置 `left_source_topic` / `right_source_topic` 为不同的 namespaced topic。 |

## 配置参数

| 参数 | 类型 | 含义 |
|---|---|---|
| `left_source_type` | enum | 左臂来源类型：`ros_udp_joint_pose_euler` / `python_current_arm_state` / `python_realtime_push`。 |
| `right_source_type` | enum | 右臂来源类型：`ros_udp_joint_pose_euler` / `python_current_arm_state` / `python_realtime_push`。 |
| `left_source_topic` | string | 左臂 ROS2 原始位姿 topic，例如 `/left_rm65/rm_driver/udp_joint_pose_euler`。 |
| `right_source_topic` | string | 右臂 ROS2 原始位姿 topic，例如 `/right_rm65/rm_driver/udp_joint_pose_euler`。 |
| `left_arm_ip` | string | 使用 Python API 或直连 driver 时的左臂 IP。 |
| `right_arm_ip` | string | 使用 Python API 或直连 driver 时的右臂 IP。 |
| `position_unit` | enum | 默认 `m`。仅在换用明确返回 `mm` 的 API 时允许配置为 `mm`。 |
| `orientation_source` | enum | `quaternion` 或 `euler`。对 `/rm_driver/udp_joint_pose_euler` 应为 `euler`。 |
| `euler_unit` | enum | 默认 `rad`。睿尔曼 `Jointposeeuler` 和 `rm_pose_t.euler` 均应使用 `rad`。 |
| `euler_order` | string | 默认 `roll_pitch_yaw`，对应文档常用 `[rx, ry, rz]`。 |
| `publish_hz` | float | Pi05 observation 输出频率。若原始 UDP 频率更高，可以降采样发布。 |
| `stale_timeout_sec` | float | 判定厂商状态过期的时间阈值。 |

## 验收方式

| 检查项 | 命令 / 标准 |
|---|---|
| topic 存在 | `ros2 topic list` 能看到 `/pi05/observation/arm/left_tcp_pose` 和 `/pi05/observation/arm/right_tcp_pose`。 |
| msg 类型 | `ros2 topic info /pi05/observation/arm/left_tcp_pose` 显示 `geometry_msgs/msg/PoseStamped`。 |
| 原始来源隔离 | 左 / 右臂原始来源 topic 或 IP 明确不同，不依赖启动顺序判断左右。 |
| 坐标系正确 | `header.frame_id` 分别为 `left_arm_base`、`right_arm_base`。 |
| 时间戳有效 | `header.stamp` 不为 0；若读取 `/rm_driver/udp_joint_pose_euler`，由于原始 msg 无 header，应使用接收 / 转换时间。 |
| 单位正确 | 手动移动 TCP 约 `10cm`，topic 中 position 变化约 `0.1m`。不应出现 `100` 这种明显 mm 未转换的量级。 |
| 姿态正确 | 手动转动末端，quaternion 连续变化、无 NaN / Inf，且模长接近 1。 |
| 过期处理 | 停止某一侧 RM65 原始状态源后，对应 Pi05 TCP pose topic 不继续发布旧值，日志指出左 / 右侧超时。 |
