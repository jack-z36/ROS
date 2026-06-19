# elephant_gripper_node 命令执行契约

关联总契约：[[TO-BE Contract#指令桥接与发送节点|指令桥接与发送节点]]

关联状态契约：[[elephant_gripper_node 状态发布契约]]

## 节点定位

`elephant_gripper_node` 的命令执行角色负责接收 `command_bridge_sender_node` 已经限幅和安全门控后的左 / 右大象夹爪目标角度，并通过 USB-485 / Modbus RTU / 厂商 SDK 执行夹爪开合。

本节点不订阅 `/pi05/policy_action`，也不解析 14D action。`left_gripper_angle` / `right_gripper_angle` 从 action 中拆出来以后，才进入本节点。

## 上下游接口

| 方向 | topic | ROS msg | 现实语义 |
|---|---|---|---|
| 订阅 | `/pi05/command/gripper/left_target` | `std_msgs/msg/Float32` | 左大象夹爪目标角度 `gripper_angle`。 |
| 订阅 | `/pi05/command/gripper/right_target` | `std_msgs/msg/Float32` | 右大象夹爪目标角度 `gripper_angle`。 |
| 发布 | `/pi05/command/gripper/left_result`（可选） | `std_msgs/msg/String` | 左夹爪命令发送、拒绝、超时或返回码。 |
| 发布 | `/pi05/command/gripper/right_result`（可选） | `std_msgs/msg/String` | 右夹爪命令发送、拒绝、超时或返回码。 |

如果暂不单独实现 result topic，则必须把等价结果写入 `/pi05/command/status` 的聚合状态中。

## 输入 msg 契约

| 字段 | 契约 |
|---|---|
| `data` | `gripper_angle`，目标夹爪角度。 |
| 值域 | 必须在 `0..100`。 |
| 类型 | ROS 为 `float32`，但硬件协议按整数角度执行；默认在校验通过后四舍五入为 `int`。 |
| 旧尺度 | 禁止接收或透传 `300..800`、`300..1000` 等旧手部尺度。 |

## 大象夹爪执行后端映射

| 后端 | 使用方式 | 契约要求 |
|---|---|---|
| Modbus RTU | 使用功能码 `0x06` 写保持寄存器。 | 官方文档中寄存器 `11` 为“设置夹爪角度”，值域 `0..100`；功能码只使用 `0x06` 写单寄存器。 |
| USB-485 Python 库 | 调用 `set_gripper_value(value, speed)`。 | `value` 使用 `0..100`；`speed` 使用 `1..100`。返回值必须记录。 |
| pymycobot | 调用 `set_pro_gripper_angle(gripper_id, gripper_angle)` 或 `set_pro_gripper_abs_angle(...)`。 | `gripper_angle` 使用 `0..100`，返回 `0` 失败、`1` 成功；该路径只在实际硬件连接方式与文档适配时启用，不作为 RM65 挂载场景的默认假设。 |

默认推荐使用 USB-485 / Modbus RTU 路径，因为当前硬件拓扑是 RM65 机械臂外挂大象夹爪，而不是 myCobot 本体控制链路。

## Modbus 寄存器契约

| 功能 | 寄存器 | 读写 | 值域 / 返回 |
|---|---:|---|---|
| 设置夹爪角度 | `11` | 写 | `0..100` |
| 读取夹爪角度 | `12` | 读 | `0..100` |
| 读取夹爪夹持状态 | `14` | 读 | `0` 运动中；`1` 停止未夹物；`2` 停止并夹到物体；`3` 夹到后物体掉落。 |
| 设置夹爪速度 | `32` | 写 | `1..100` |

写寄存器后必须校验从站地址、功能码、寄存器地址、写入值和 CRC；校验失败不得报告成功。

## 执行前校验

| 校验项 | 处理方式 |
|---|---|
| 目标值 NaN / Inf | 拒绝执行。 |
| 目标值小于 `0` 或大于 `100` | 默认拒绝；如启用 clamp，必须记录 warn 并在 Contract Delta 中说明。 |
| 非整数目标 | 默认四舍五入到最近整数；若启用 strict 模式，则拒绝非整数。 |
| 串口 / 从站 ID 未绑定 | 节点启动失败。 |
| 左右夹爪映射冲突 | 节点启动失败，避免把右夹爪目标发给左夹爪。 |
| 急停 / enable / deadman 未满足 | 拒绝执行，不写寄存器。 |
| 状态读取超时 | 不影响拒绝逻辑；但不得把未知状态包装成成功执行。 |

## 指令频率与去抖

| 项 | 契约 |
|---|---|
| 最小指令间隔 | 必须配置 `command_min_interval_sec`。若使用 pymycobot 路径，按文档约束建议不小于 `1.5s`。 |
| 重复目标 | 若目标与最近一次已发送目标差值小于 `angle_deadband`，可选择不重复发送，但必须更新状态为 `skipped_same_target`。 |
| 运动中再次下发 | 必须由配置决定：`allow_preempt=true` 才能覆盖运动中目标；否则等待状态寄存器不为 `0` 后再发。 |

## 配置参数

| 参数 | 类型 | 默认建议 | 含义 |
|---|---|---|---|
| `backend` | enum | `modbus_rtu` | `modbus_rtu`、`usb485_python` 或 `pymycobot`。 |
| `left_device` | string | 必填 | 左夹爪串口、SDK id 或 Modbus 入口。 |
| `right_device` | string | 必填 | 右夹爪串口、SDK id 或 Modbus 入口。 |
| `left_gripper_id` | int | 显式配置 | 左夹爪从站 ID。 |
| `right_gripper_id` | int | 显式配置 | 右夹爪从站 ID。 |
| `baudrate` | int | `115200` | 485 波特率；需与设备配置一致。 |
| `min_angle` | int | `0` | 最小夹爪角度。 |
| `max_angle` | int | `100` | 最大夹爪角度。 |
| `speed` | int | 50 | 夹爪运动速度，必须在 `1..100`。 |
| `command_min_interval_sec` | float | 必填 | 连续命令最小间隔。 |
| `readback_timeout_sec` | float | 必填 | 等待读回角度 / 状态的超时。 |
| `strict_integer` | bool | `false` | 是否拒绝非整数目标。 |

## 执行结果语义

| 状态 | 含义 |
|---|---|
| `accepted` | 底层库或 Modbus 应答确认命令已被设备接收。 |
| `rejected` | 目标值、enable、急停、映射或频率校验失败，未下发。 |
| `write_error` | 串口写入、CRC、从站应答或 SDK 返回失败。 |
| `timeout` | 等待读回或设备应答超时。 |
| `skipped_same_target` | 目标与最近已发送目标在 deadband 内，按配置跳过重复发送。 |

## 与 `command_bridge_sender_node` 对齐

| 上游保证 | 本节点补充保证 |
|---|---|
| 上游从 14D policy action 中拆出左右 gripper angle。 | 本节点不再解析 action，只执行左右 target topic。 |
| 上游完成 `0..100` 限幅和 enable 门控。 | 本节点仍执行最终 finite、值域、串口映射和设备返回码检查。 |
| 上游认为失败不发送。 | 本节点发现硬件失败时必须返回失败状态，不能伪装为已执行。 |

## 验收方式

| 检查项 | 标准 |
|---|---|
| topic 存在 | 能看到左右 `/pi05/command/gripper/*_target` 订阅。 |
| 值域正确 | 发布 `-1`、`101`、`300` 等目标时，节点拒绝。 |
| 左右不混淆 | 手动只给左 target，只有左夹爪动作。 |
| Modbus 正确 | 写寄存器 `11`，读寄存器 `12` 能读回接近目标的 `0..100` 值。 |
| 旧尺度未泄漏 | 不出现 `300..800` 或 `300..1000` 作为硬件目标。 |
| 断连处理 | 拔掉 USB-485 后，节点返回 `write_error` 或 `timeout`，不报告成功。 |
