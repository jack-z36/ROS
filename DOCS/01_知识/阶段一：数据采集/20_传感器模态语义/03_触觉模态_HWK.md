# 触觉模态（华威科 HWK 压力传感器）

本页定义阶段一触觉模态的消息契约、硬件链路和身份语义。触觉数据是阶段四模型部署最常复用的前置知识。

## 定位

本页回答：PressureFrame 消息里每个字段是什么含义？压力数据是怎么从串口变成 ROS topic 的？

本页是跨阶段复用价值最高的知识页之一——阶段四模型部署读取触觉数据的代码与阶段一共享同一套 `PressureFrame.msg` 契约。

## 消息契约：PressureFrame.msg

消息定义位于 `hwk_pressure_interfaces/msg/PressureFrame.msg`：

```text
std_msgs/Header header
string hand
string gripper
uint8 device_addr
uint8 package_id
uint8 total_packets
uint8 packet_index
uint8 rows
uint8 cols
uint16[] data
uint8[] raw_payload
```

### 字段详解

| 字段 | 类型 | 含义 | 说明 |
|---|---|---|---|
| `header.stamp` | `builtin_interfaces/Time` | 驱动发布时刻 | 由节点 `get_clock().now()` 打，ROS 时钟 |
| `header.frame_id` | `string` | 触觉坐标系 | 优先来自身份映射，否则 `{frame_id_prefix}/{hand}/{gripper}` |
| `hand` | `string` | 逻辑手名 | `left_hand` 或 `right_hand`，**逻辑身份非物理 UID** |
| `gripper` | `string` | 逻辑夹爪名 | `gripper_1` 或 `gripper_2`，**逻辑身份非物理 UID** |
| `device_addr` | `uint8` | HWK 协议设备地址 | 0..15，用于串口协议寻址 |
| `package_id` | `uint8` | 请求/应答包序号 | 0..63 循环，匹配请求与应答 |
| `total_packets` | `uint8` | 多包总包数 | 当前按 payload 原样发布 |
| `packet_index` | `uint8` | 多包当前索引 | 当前按 payload 原样发布 |
| `rows` | `uint8` | 压力矩阵行数 | 默认 6 |
| `cols` | `uint8` | 压力矩阵列数 | 默认 15 |
| `data` | `uint16[]` | 压力数据 | **一维数组，按 rows×cols 展平，行优先**（默认 90 元素） |
| `raw_payload` | `uint8[]` | 原始 payload 字节 | **仅排障用**，不作业务字段 |

### data 字段契约（关键）

`data` 是一维 `uint16` 数组，长度通常为 `rows * cols`（默认 6×15=90）。数据按**行优先**展平：

```text
data[0]            = 第0行第0列
data[1]            = 第0行第1列
...
data[cols-1]       = 第0行最后一列
data[cols]         = 第1行第0列
...
data[rows*cols-1]  = 最后一行最后一列
```

读取时必须用 `rows` 和 `cols` 重建二维矩阵，不能假设固定尺寸。

### CDR 序列化契约（关键）

PressureFrame 的字段顺序是 **CDR 序列化契约**的一部分。在中间插入新字段属于**破坏性变更**，会导致已录制的 raw MCAP 无法被正确反序列化。新增字段只能追加到末尾。

## 硬件链路

```text
华威科压力传感器 ×4 (每个一个串口)
  → /dev/ttyUSB* (460800 波特率, 8N1)
  → SerialWorker (每串口一个 reader 线程)
  → 协议帧解析 (帧头0x3C3C, 帧尾0x3E3E, CRC16)
  → HWK_CHIP_UID 身份匹配
  → PressureFrame 发布
```

### 串口协议帧格式

- 帧头：`0x3C 0x3C`
- 帧尾：`0x3E 0x3E`
- `id_channel`：高 4 bit = `device_addr`，低 4 bit = channel
- `flags`：高 6 bit = `package_id`，低 2 bit = frame type
- `length`：payload 长度（小端）
- `checksum`：对 payload 计算 CRC16

### 轮询机制

- 每个 sensor 按配置的 `poll_rate_hz`（默认 100Hz）被 ROS timer 轮询。
- timer period 取所有已绑定 sensor 的最大 poll rate 的倒数。
- 每次轮询发送 GET 数据帧，等待 ACK 后发布。

## 身份语义：hand/gripper ≠ 物理 UID

这是触觉模态最容易误解的点：

- `hand`（`left_hand`/`right_hand`）和 `gripper`（`gripper_1`/`gripper_2`）是**逻辑身份**，由硬件身份映射表（`hardware_identity_map.yaml`）根据 `HWK_CHIP_UID` 决定。
- 它们**不是**物理串口号、不是 device_addr、不是 UID。
- 设备枚举顺序变化（`/dev/ttyUSB0` 和 `/dev/ttyUSB1` 互换）只影响"从哪个串口读到该 UID"，不影响最终发布的 topic 名。

完整身份策略见 `40_身份与稳定性/01_硬件身份策略.md`。

## 发布的 topic

| topic | 消息类型 | 说明 |
|---|---|---|
| `/pressure/left_hand/gripper_1` | `PressureFrame` | 左手夹爪1 |
| `/pressure/left_hand/gripper_2` | `PressureFrame` | 左手夹爪2 |
| `/pressure/right_hand/gripper_1` | `PressureFrame` | 右手夹爪1 |
| `/pressure/right_hand/gripper_2` | `PressureFrame` | 右手夹爪2 |

这 4 个 topic 是 Octopus 默认录制和显示的核心 topic。

## 详细内容

- 消息定义：`src/data_collection/hwk_pressure_interfaces/msg/PressureFrame.msg`
- 接口包说明：`src/data_collection/hwk_pressure_interfaces/hwk_pressure_interfaces_architecture.md`
- 驱动源码：`src/data_collection/hwk_pressure_driver/hwk_pressure_driver/`（`pressure_driver_node.py`、`config.py`、`protocol.py`、`serial_worker.py`）
- 驱动架构：`src/data_collection/hwk_pressure_driver/hwk_pressure_driver_architecture.md`
- 默认配置：`src/data_collection/hwk_pressure_driver/config/pressure_sensors.yaml`
- 身份映射：`config/hardware_identity_map.yaml`
