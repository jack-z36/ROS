# elephant_gripper_node 状态发布契约

关联总契约：[[TO-BE Contract#传感器数据发送节点|传感器数据发送节点]]

## 节点定位

`elephant_gripper_node` 的状态发布角色负责读取左 / 右大象 myGripper F100 力控夹爪的当前角度值，并发布给 `Pi05VlaDeployNode` 作为 gripper observation。

本契约只描述“作为传感器 / 状态源”的发布边界：它可以读取夹爪串口、Modbus RTU 或 SDK 状态，但不订阅 Pi05 命令 topic、不执行 policy action。实际工程中可以和夹爪命令执行角色放在同一个 driver node 内实现，但 topic 职责必须保持清楚。

> [!note] 大象夹爪文档依据
> - [[01-doing/ROS/DOCS/01_知识/阶段四：模型部署/硬件开发文档/大象夹爪开发/modbus rtu协议控制.md]]：Modbus RTU 仅支持 `0x03` 读保持寄存器和 `0x06` 写保持寄存器；设置夹爪角度寄存器地址 `11`，读取夹爪角度寄存器地址 `12`，角度值域 `0..100`；读取夹持状态地址 `14`。
> - [[01-doing/ROS/DOCS/01_知识/阶段四：模型部署/硬件开发文档/大象夹爪开发/pymycobot库控制.md]]：`get_pro_gripper_angle(gripper_id)` 返回 `0..100`；`get_pro_gripper_status(gripper_id)` 返回 `0..3` 夹持状态；文档注明 pymycobot API 目前仅适用 myCobot 320 和 Mercury 系列，若本项目使用 RM65 搭配夹爪，应优先视为 USB-485 / Modbus RTU 接入。
> - [[01-doing/ROS/DOCS/01_知识/阶段四：模型部署/硬件开发文档/大象夹爪开发/python USB-485库控制.md]]：USB-485 方式需连接 `24V`、`GND`、`485_A`、`485_B`，并使用 `pyserial`；`get_gripper_value()` 读取夹爪当前位置数据，`get_gripper_status()` 返回 `0..3` 状态。

## 上下游接口

| 方向 | topic / 来源 | ROS msg / 接口类型 | 现实语义 |
|---|---|---|---|
| 读取 | 左夹爪 USB-485 / Modbus RTU / SDK 状态源 | Modbus `0x03` 读寄存器，或 `get_pro_gripper_angle()` / `get_gripper_value()` | 左大象夹爪当前角度值。 |
| 读取 | 右夹爪 USB-485 / Modbus RTU / SDK 状态源 | Modbus `0x03` 读寄存器，或 `get_pro_gripper_angle()` / `get_gripper_value()` | 右大象夹爪当前角度值。 |
| 发布 | `/pi05/observation/gripper/left_state` | `std_msgs/msg/Float32` | 左夹爪当前 `gripper_angle`。 |
| 发布 | `/pi05/observation/gripper/right_state` | `std_msgs/msg/Float32` | 右夹爪当前 `gripper_angle`。 |
| 订阅 | Pi05 命令 topic | 无 | 状态发布角色不订阅 `/pi05/policy_action` 或 `/pi05/command/*`。 |

## 读取来源

| 来源 | 使用方式 | 契约要点 |
|---|---|---|
| USB-485 / Modbus RTU | 推荐作为 RM65 + 大象夹爪组合的默认接入方式。节点通过串口对左 / 右夹爪分别发送 `0x03` 读寄存器指令。 | 读取夹爪角度寄存器地址 `12`，寄存器长度为 `1`。设备默认 ID 在 SDK 文档中常见为 `14`，实际项目必须配置显式写明左 / 右夹爪 ID。 |
| pymycobot API | 可在使用 myCobot 320 / Mercury 系列直连夹爪时使用。 | `get_pro_gripper_angle(gripper_id)` 返回 `0..100`。文档明确限制 pymycobot API 适用机型，不能在 RM65 方案中默认它可用。 |
| elephant USB-485 Python 库 | 可作为直接串口读取的封装。 | `get_gripper_value()` 读取当前位置数据；需确认底层与寄存器 `12` 语义一致后再写入 Pi05 topic。 |
| 其他驱动封装 | 可用，但必须被适配成统一 `gripper_angle` 语义。 | 不允许输出 `300..800`、`300..1000` 或百分比尺度冒充大象夹爪角度值。 |

左右夹爪必须通过配置显式绑定串口路径、USB-485 适配器物理位置、设备 ID 或 SDK 连接参数。禁止依赖 `/dev/ttyUSB*` 枚举顺序判断左右夹爪。

## 发布 msg 契约

| 字段 | 值 |
|---|---|
| `data` | `gripper_angle`，类型为 `float32`。 |
| 值域 | `0..100`。这是大象夹爪文档中“设置 / 读取夹爪角度”的寄存器值域。 |
| 单位语义 | 夹爪角度 / 开合程度的设备内部尺度，不是 `mm`，也不是无条件百分比。 |
| `0` | 闭合端语义：按大象夹爪“夹爪角度”控制口径理解，具体机械开口宽度需以实机标定为准。 |
| `100` | 张开端语义：文档中“张开角度”示例使用 `0x64`，即十进制 `100`。 |

`std_msgs/msg/Float32` 没有 header。`Pi05VlaDeployNode` 应以 ROS 消息接收时间作为该字段的观测时间。本节点不得通过重复发布旧值来伪造新观测。

## 可选诊断状态

本契约的 Pi05 最小 observation 只需要左 / 右 `gripper_angle`。若工程中需要诊断夹持成功、夹持失败或掉落状态，可额外发布诊断 topic，但不应替代 `/pi05/observation/gripper/*_state`。

| 来源 | 状态值 | 语义 |
|---|---|---|
| Modbus 寄存器 `14` / `get_pro_gripper_status()` / `get_gripper_status()` | `0` | 正在运动。 |
| 同上 | `1` | 停止运动，未检测到夹到物体。 |
| 同上 | `2` | 停止运动，检测到夹到物体。 |
| 同上 | `3` | 检测到夹到物体后，物体掉落。 |

## 与 Pi05VlaDeployNode 对齐

| Pi05 需求 | 本节点保证 |
|---|---|
| Pi05 需要左右夹爪当前角度值作为 observation。 | 固定发布 `/pi05/observation/gripper/left_state` 和 `/pi05/observation/gripper/right_state`。 |
| Pi05 的 policy action 中夹爪目标同样使用 `gripper_angle`。 | observation 和 action 共享大象夹爪文档的 `0..100` 语义。 |
| Pi05 不再沿用 AS-IS 手部尺度。 | 禁止发布 `300..800`、`300..1000` 或其他旧手部尺度。 |
| Pi05 依赖 observation 时效性判断。 | 读取失败或超时时停止发布旧值，不把旧角度伪造成新 observation。 |

## 异常处理契约

| 场景 | 处理方式 |
|---|---|
| 左 / 右夹爪串口或 SDK 连接失败 | 不发布伪造值；日志明确指出是左夹爪还是右夹爪离线。 |
| Modbus CRC 校验失败 / 帧长度不对 | 丢弃当前帧，不更新 Pi05 observation topic；按配置节流 warn。 |
| SDK 返回 `-1` 或读不到数据 | 视为状态读取失败，停止发布旧值。 |
| 状态读取超时 | 停止发布旧值，并按配置间隔 warn。 |
| 读数小于 `0` | 丢弃当前样本，记录 error。默认不 clamp 后发布，避免掩盖硬件或协议异常。 |
| 读数大于 `100` | 丢弃当前样本，记录 error。默认不 clamp 后发布。 |
| 左右夹爪映射冲突 | 节点启动失败，避免把右夹爪状态发布到左夹爪 topic。 |
| `/dev/ttyUSB*` 枚举顺序变化 | 不允许靠枚举顺序自动假定左右；必须使用稳定设备路径、物理端口标识或配置文件显式绑定。 |

## 配置参数

| 参数 | 类型 | 含义 |
|---|---|---|
| `left_source_type` | enum | 左夹爪读取方式：`modbus_rtu` / `usb485_python` / `pymycobot` / `custom_driver`。 |
| `right_source_type` | enum | 右夹爪读取方式：`modbus_rtu` / `usb485_python` / `pymycobot` / `custom_driver`。 |
| `left_serial_port` | string | 左夹爪 USB-485 串口路径或稳定设备别名。 |
| `right_serial_port` | string | 右夹爪 USB-485 串口路径或稳定设备别名。 |
| `left_gripper_id` | int | 左夹爪 Modbus 从站 ID / SDK `gripper_id`。文档示例常用 `14`，实际必须显式配置。 |
| `right_gripper_id` | int | 右夹爪 Modbus 从站 ID / SDK `gripper_id`。若与左夹爪共用一条 485 总线，ID 必须不同。 |
| `baudrate` | int | 485 波特率；文档中寄存器值 `0` 表示 `115200` 默认波特率，也可配置 `1000000`、`57600`、`19200`、`9600`、`4800` 等对应模式。 |
| `angle_register` | int | 读取夹爪角度寄存器，固定为 `12`，除非 Contract Delta 改写。 |
| `status_register` | int | 读取夹持状态寄存器，默认 `14`，用于诊断，不是 Pi05 最小 observation 必需 topic。 |
| `publish_hz` | float | 状态发布频率。 |
| `read_timeout_sec` | float | 单次状态读取超时。 |
| `stale_timeout_sec` | float | 判定状态过期的时间阈值。 |
| `min_angle` | float | 固定为 `0`，除非 Contract Delta 改写。 |
| `max_angle` | float | 固定为 `100`，除非 Contract Delta 改写。 |

## 验收方式

| 检查项 | 命令 / 标准 |
|---|---|
| topic 存在 | `ros2 topic list` 能看到 `/pi05/observation/gripper/left_state` 和 `/pi05/observation/gripper/right_state`。 |
| msg 类型 | `ros2 topic info /pi05/observation/gripper/left_state` 显示 `std_msgs/msg/Float32`。 |
| 值域正确 | `ros2 topic echo ...` 中 `data` 始终在 `0..100`。 |
| 左右不混淆 | 手动开合左 / 右夹爪时，只对应的 topic 变化。 |
| 旧尺度未泄漏 | 不出现 `300..800`、`300..1000` 等 AS-IS 手部尺度。 |
| 串口 / ID 绑定正确 | 拔掉或禁用某一侧夹爪时，日志明确指出左 / 右夹爪，不依赖 `/dev/ttyUSB*` 顺序猜测。 |
| 读取失败处理 | 模拟 CRC 错误、SDK 返回 `-1` 或超时时，节点停止发布旧值并记录 warn / error。 |
