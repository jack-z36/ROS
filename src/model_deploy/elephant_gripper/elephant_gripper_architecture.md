# elephant_gripper 架构说明

ROS 2（Jazzy，ament_python）节点，通过两路 USB-485（自定义 Modbus 帧）读取并驱动
左右两个大象 myGripper-F100 力控夹爪。

## ROS 接口

| 方向 | 名称 | 类型 |
|------|------|------|
| 发布 | `/gripper/left_state` | `geometry_msgs/Pose`（宽度∈[0,1] 在 `position.x`，0=闭合 1=张开） |
| 发布 | `/gripper/right_state` | `geometry_msgs/Pose` |
| 发布 | `/hardware/gripper/health` | `act_interfaces/HardwareHealth` |
| 订阅 | `/act/command/gripper/left_target` | `std_msgs/Float64` |
| 订阅 | `/act/command/gripper/right_target` | `std_msgs/Float64` |
| 订阅 | `/act/command/permit` | `act_interfaces/CommandPermit` |
| 服务 | `/hardware/gripper/emergency_stop` | `std_srvs/srv/SetBool`（true=触发锁存，false=解除） |

> 发布 TCP state 用裸 `Pose`（宽度承载在 `position.x`）以匹配 ACT 大脑 `decode_gripper_width` 的
> Pose 订阅分支；launch 默认把 `/gripper/*_state` remap 到 `/act/observation/gripper/*_state`，
> ACT 侧零配置订阅。命令订阅方向（`/act/command/gripper/*_target`）仍是 `Float64`，不受影响。

**安全默认拒绝**：仅当人工许可有效（`allowed` 且未过期 `permit_timeout_s`）且未急停时，才执行新的夹爪目标；
否则丢弃新命令、保持上次位置，遥测继续发布。

## 分层（六架构，依赖自上而下）

```
types  →  config  →  repo  →  service  →  runtime  →  ui
```

- `types/`：纯数据契约（禁止 import ROS/serial）。`GripperSide`、`ClampStatus`、
  `GripperStateSample`、`GripperCommand`、`HealthLevel`/`DeviceHealth`/`NodeHealth`、本地 `CommandPermit`。
- `config/`：`schema.py` 参数类型 + 默认值 + 校验（`ConfigError`），无文件 I/O。
- `repo/`：`config_loader.py` 解析 ROS 风格 YAML（`elephant_gripper_node.ros__parameters`）→ `NodeConfig`。
- `service/`：纯函数，可无硬件/无 ROS 单测。`frame_codec`（CRC16-MODBUS 查表 + 帧编解码，
  移植自 `gripper_ctrl.py`）、`mapping`（width↔angle）、`permit_gate`（许可判定）、
  `health_aggregator`（健康聚合，整体取较差者）。
- `runtime/`：`serial_link.py`（每夹爪一个 `serial.Serial` + 一个守护事务线程，串口工厂可注入）、
  `gripper_supervisor.py`（编排左右两路 + 许可 + 急停）、`fake_serial.py`（无硬件回放）。
- `ui/`：`elephant_gripper_node.py`，唯一 import rclpy 与 `act_interfaces` msg 的层；
  `MultiThreadedExecutor`，ROS 回调只做 O(1) 槽读写，串口 I/O 全在 worker 线程。

## 并发模型

- 每夹爪一个事务 worker 线程负责所有串口 I/O（请求/响应含等待），避免阻塞 executor。
- 命令/许可订阅在 `MutuallyExclusiveCallbackGroup`（只校验并写「最新命令槽」，latest-command-wins）。
- 急停 service 在 `ReentrantCallbackGroup`：`trigger_estop` **立即持写锁**直接下发
  `stop`(0x27) + `disable`(0x0A=0)，独立于 worker 睡眠周期。
- 发布/健康定时器各自成组，只读非阻塞快照。

## 自定义协议帧

```
FE FE | len(0x08) | gripper_id(0x0E) | func | reg_hi reg_lo | data_hi data_lo | crc_hi crc_lo
```

- func：`0x03` 读 / `0x06` 写；寄存器：使能 `0x0A`、设角度 `0x0B`(0–100)、读角度 `0x0C`、
  夹持状态 `0x0E`、停止 `0x27`。CRC-16/MODBUS，大端。
- golden 向量（已单测）：读角度请求 `FE FE 08 0E 03 00 0C 00 00 B1 C0`；
  使能 `FE FE 08 0E 06 00 0A 00 01 70 2D`；停止 `FE FE 08 0E 06 00 27 00 00 B9 7C`。

## Fail-safe

- 串口异常全捕获，标记断连 → 上限指数退避重连（`reconnect_backoff_min/max_s`），绝不抛入循环。
- 连续错误计数 / 接收时延 → `HardwareHealth`（OK/DEGRADED/FAULT）。
- 关停时保底 `disable`；`use_fake_serial=true` 可无硬件运行。

## 未验证 / 待真机确认

- 左右 `ID_PATH`、`ttyACM` vs `ttyUSB`、急停后夹爪保持/掉电行为、串口等待/超时调优、
  width↔angle 标定系数，均待真机验证。
- 启动自检（查询固件/状态防左右接反）为后续增强项，当前依赖 udev 稳定符号链接 + 配置显式 left/right_port。
