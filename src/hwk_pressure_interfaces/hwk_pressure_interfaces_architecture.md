# hwk_pressure_interfaces 架构说明

本文档说明 `/home/hit/ROS/src/hwk_pressure_interfaces` 自定义 ROS2 消息接口包。该包为 HWK 触觉压力传感器提供统一消息类型，供 `hwk_pressure_driver`、Octopus 和 MCAP 录制链路共享。

## 1. 概述

`hwk_pressure_interfaces` 是一个纯接口包，不包含运行节点或 UI。它定义 `hwk_pressure_interfaces/msg/PressureFrame`，用于承载单个触觉传感器的一帧压力矩阵以及硬件/逻辑身份信息。

所属场景：

- 场景三：Octopus 录制 4 路触觉 topic 到 MCAP。
- 场景四：Octopus UI 将 `PressureFrame` 显示为左右手触觉热力图。
- 场景五：硬件身份映射后，固定 topic 使用该消息类型。

## 2. 目录结构

| 路径 | 职责 |
| --- | --- |
| `msg/PressureFrame.msg` | 自定义触觉压力帧消息定义。 |
| `CMakeLists.txt` | 使用 `rosidl_generate_interfaces` 生成接口代码。 |
| `package.xml` | 声明 `ament_cmake`、`std_msgs`、`rosidl_default_generators/runtime` 依赖。 |

## 3. 数据流

接口包的数据流分为“构建期代码生成”和“运行期消息契约”两部分。它本身不读硬件、不发布 topic，但它决定了 Python 驱动、C++ Octopus 和 MCAP schema 共同遵守的数据结构。

```mermaid
flowchart TD
  MSG[msg/PressureFrame.msg] --> CMAKE[CMakeLists rosidl_generate_interfaces]
  CMAKE --> IDL[ROSIDL 生成中间接口]
  IDL --> PY[Python 消息模块]
  IDL --> CPP[C++ 头文件]
  IDL --> TYPE[ROS2 type support]
  PY --> DRIVER[hwk_pressure_driver 构造 PressureFrame]
  DRIVER --> RMW[ROS2 middleware 序列化发布]
  RMW --> TOPIC[/pressure/...]
  CPP --> OCTSUB[Octopus typed subscription]
  TOPIC --> OCTSUB
  TOPIC --> OCTREC[Octopus generic recorder]
  OCTREC --> MCAP[MCAP schema + cdr payload]
```

### 3.1 构建期：从 `.msg` 到可用代码

1. `CMakeLists.txt` 调用 `rosidl_generate_interfaces(${PROJECT_NAME} "msg/PressureFrame.msg" DEPENDENCIES std_msgs)`。
2. ROSIDL 读取 `.msg` 文本，展开 `std_msgs/Header` 依赖，并生成语言相关代码和 type support。
3. Python 侧生成的消息类被 `hwk_pressure_driver` 导入：`from hwk_pressure_interfaces.msg import PressureFrame`。
4. C++ 侧生成的头文件被 Octopus 导入：`#include <hwk_pressure_interfaces/msg/pressure_frame.hpp>`。
5. `ament_export_dependencies(rosidl_default_runtime)` 让下游包在运行时能找到接口类型支持。

### 3.2 运行期：字段如何被填充和消费

`PressureFrame` 的运行期含义由三个程序共同使用：

1. `hwk_pressure_driver` 从串口 payload 中解析出 `rows`、`cols`、`data`、`raw_payload`，并从硬件身份映射中填入 `hand`、`gripper`、`frame_id`。
2. ROS2 middleware 按接口生成的 type support 把消息序列化并发布到 `/pressure/...` topic。
3. Octopus 显示链路使用 typed subscription，所以编译期依赖这个接口包；收到消息后按 `gripper` 字段路由到 gripper_1 或 gripper_2 热力图。
4. Octopus 录制链路使用 generic subscription，运行时拿到的是 serialized payload；为了让 MCAP 下游工具理解消息类型，`McapRecorder::get_message_definition()` 还必须维护一份与 `PressureFrame.msg` 一致的手写 schema 文本。
5. MCAP 中保存的是 topic、schema 和 CDR payload；后续离线工具如果要解析触觉数据，也要使用同一消息定义。

### 3.3 契约约束

这个接口包最重要的是契约稳定性：

- 字段顺序是序列化契约的一部分。给 `.msg` 中间插字段会影响 CDR 布局，应当视为破坏性变更。
- `data` 是一维 `uint16[]`，语义上按 `rows * cols` 展平；显示端按行列恢复矩阵。
- `raw_payload` 是排障字段，不应替代 `data` 成为业务消费入口。
- `hand` 和 `gripper` 是逻辑身份字段，不是硬件 UID；硬件 UID 不在消息里，而是在驱动日志和身份映射文件中维护。
- 如果修改 `.msg`，必须同步更新 `hwk_pressure_driver` 的填充逻辑、Octopus 的 typed include/显示逻辑、Octopus MCAP 手写 schema，以及相关场景文档。

## 4. 消息定义

`PressureFrame.msg`：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `header` | `std_msgs/Header` | 时间戳和 frame_id。 |
| `hand` | `string` | 逻辑手名，例如 `left_hand`、`right_hand`。 |
| `gripper` | `string` | 逻辑夹爪名，例如 `gripper_1`、`gripper_2`。 |
| `device_addr` | `uint8` | HWK 协议设备地址。 |
| `package_id` | `uint8` | 请求/应答包序号。 |
| `total_packets` | `uint8` | 传感器 payload 声明的总包数。 |
| `packet_index` | `uint8` | 当前包序号。 |
| `rows` | `uint8` | 压力矩阵行数。 |
| `cols` | `uint8` | 压力矩阵列数。 |
| `data` | `uint16[]` | 展平后的压力矩阵，通常按 row-major 理解。 |
| `raw_payload` | `uint8[]` | 原始协议 payload，供排查解析和协议兼容问题。 |

`rows * cols` 应与 `data` 长度一致；驱动发现不一致时仍会发布解析出的数据并保留 `raw_payload`，以免丢失现场信息。

## 5. 依赖与运行

主要依赖：

- ROS2 `ament_cmake`
- `rosidl_default_generators`
- `rosidl_default_runtime`
- `std_msgs`

构建：

```bash
cd /home/hit/ROS
colcon build --packages-select hwk_pressure_interfaces
```

查看接口：

```bash
source /home/hit/ROS/install/setup.bash
ros2 interface show hwk_pressure_interfaces/msg/PressureFrame
```

该包没有单独启动命令。

## 6. 配置项说明

本包没有运行期配置项。字段语义由消息定义固定；topic 名称、frame_id、hand、gripper 等值由上游 `hwk_pressure_driver` 和硬件身份映射配置决定。

## 7. UI 逻辑

本包没有 UI。Octopus 的 `PressureDockWidget` 使用该消息：

- 根据 `gripper` 字段分流到 gripper_1 或 gripper_2。
- 使用 `rows`、`cols` 和 `data` 绘制热力图。
- 显示 max、avg、矩阵尺寸和更新时间。

## 8. 与上下游的关系

上游：

- `hwk_pressure_driver` 生成并发布 `PressureFrame`。

下游：

- Octopus C++ 侧依赖该包生成的头文件，并在 `McapRecorder::get_message_definition()` 中维护对应 schema 文本。
- MCAP 原始数据保留该消息，供后续离线分析。

边界：

- 修改 `PressureFrame.msg` 是跨包契约变更，必须同步更新 `hwk_pressure_driver`、Octopus 显示和录制 schema、相关文档以及 MCAP 回归验证。
- 不应在接口包中加入节点逻辑；运行逻辑属于 `hwk_pressure_driver`。
