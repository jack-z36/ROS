# raw MCAP 产物语义

本页定义阶段一核心产物 raw MCAP 的内容契约，以及录制链路对产物内容的几处关键影响。

## 定位

本页回答：raw MCAP 文件里到底有什么？录制过程会以什么方式改写原始数据流？

本页不涉及单个消息类型的字段细节（见 `20_传感器模态语义/`），也不涉及录制的启动/停止操作（见 `30_Octopus运转逻辑/03_录制链路.md`）。

## MCAP 文件里有什么

raw MCAP 是 [MCAP](https://mcap.dev/) 格式的 ROS2 topic 日志。它由 Octopus 的录制链路（`recorder` 节点 + `McapRecorder` 类）写出，包含：

| 组成 | 内容 | 来源 |
|---|---|---|
| 消息数据 | 传感器原始的 CDR 序列化字节流 | `create_generic_subscription` 收到的 `SerializedMessage`，**不反序列化** |
| topic 名 | 录制时勾选的 topic 全名 | Start 时遍历勾选项 |
| schema | 每种消息类型的 `ros2msg` 文本定义 | `McapRecorder::get_message_definition()`，**手写维护** |
| channel | 每个 topic 一个 channel，绑定 schema | `create_channel()` |
| 双时间戳 | 见下节 | `rclcpp::MessageInfo` |
| 压缩 | 整文件压缩 | `scanner.json` 的 `compression` 字段（ZSTD 等） |

## 双时间戳契约

每条 MCAP 消息携带两个时间戳，这是阶段二对齐工作的关键输入：

| MCAP 字段 | ROS 来源 | 语义 |
|---|---|---|
| `logTime` | `info.get_rmw_message_info().received_timestamp` | Octopus 收到该消息的时刻 |
| `publishTime` | `info.get_rmw_message_info().source_timestamp` | 发布者打该消息的时刻（即消息自己的 `header.stamp` 对应的内部时钟值） |

阶段二做跨 topic 对齐时选用哪个时间戳，由阶段二的数据定义决定。阶段一只保证两者都如实写入。

## fast_odom 节流会改写 MCAP 内容

这是录制链路对产物最实质的影响，阶段二必须知晓：

- topic 名包含 `fast_odom` 的消息，在录制时按 **60Hz** 节流（`kFastOdomMinIntervalNs = 16,666,666 ns`）。
- 节流依据是 `source_timestamp`：连续两条 fast_odom 消息的 source_timestamp 差小于 16.67ms 时，**后一条被丢弃，不写入 MCAP**。
- 原因：Baton Mini 的 fast_odom 原始频率约 200Hz，录制时降为 60Hz 以控制文件体积。

推论：raw MCAP 里 fast_odom 的实际频率约 60Hz，而非传感器原始的 200Hz。阶段二若需要完整 200Hz，无法从 raw MCAP 获得——这是阶段一的有意设计。

## 默认录制的 8 个 topic

Octopus 内置 8 个默认录制 topic（`config.cpp` 硬编码，`scanner.json` 可覆盖）：

| topic | 消息类型 |
|---|---|
| `/gopro_left/image_raw` | `sensor_msgs/msg/Image` |
| `/gopro_right/image_raw` | `sensor_msgs/msg/Image` |
| `/baton_mini_left/fast_odom` | `nav_msgs/msg/Odometry` |
| `/baton_mini_right/fast_odom` | `nav_msgs/msg/Odometry` |
| `/pressure/left_hand/gripper_1` | `hwk_pressure_interfaces/msg/PressureFrame` |
| `/pressure/left_hand/gripper_2` | `hwk_pressure_interfaces/msg/PressureFrame` |
| `/pressure/right_hand/gripper_1` | `hwk_pressure_interfaces/msg/PressureFrame` |
| `/pressure/right_hand/gripper_2` | `hwk_pressure_interfaces/msg/PressureFrame` |

完整 topic 路由表见 `20_传感器模态语义/04_核心topic清单.md`。

## schema 维护约定

`McapRecorder::get_message_definition()` 中的 schema 文本是**手写**的，目前覆盖 5 种类型：

- `sensor_msgs/msg/Image`
- `sensor_msgs/msg/CompressedImage`
- `sensor_msgs/msg/JointState`
- `nav_msgs/msg/Odometry`
- `hwk_pressure_interfaces/msg/PressureFrame`

新增消息类型加入录制时，**必须在此函数中补上手写 schema**，否则 MCAP 中该类型的 schema 为空，后续解析工具无法正确解码。

## 产物的物理形态

- 文件命名：录制开始时生成时间戳命名的 `.mcap` 文件。
- 输出目录：由 `scanner.json` 的 `recording.mcap.path` 决定，默认 Qt Documents 目录，启动脚本会改成 `mcap` 目录。
- 录制停止：点击 Stop 时 `recorder_.reset()`，析构关闭 writer 并 cancel executor。

## 与阶段二的关系

阶段二读取 raw MCAP 后，逐步生成 cleaned MCAP、MCAP_A、aligned MCAP 和训练格式桥接产物。阶段一交付的就是本页定义的 raw MCAP，不包含任何阶段二的语义。

## 详细内容

- 录制器源码：`src/data_collection/VTLA_octopus-master/octopus/src/mcap-recorder.cpp`
- 配置项源码：`src/data_collection/VTLA_octopus-master/octopus/src/utils/config.cpp`
- 录制链路运转细节：`30_Octopus运转逻辑/03_录制链路.md`
