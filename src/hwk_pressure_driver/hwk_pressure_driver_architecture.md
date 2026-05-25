# hwk_pressure_driver 架构说明

本文档说明 `src/hwk_pressure_driver` 触觉压力传感器 ROS2 驱动的功能、数据流、运行方式和配置项。该包服务于场景三和场景五：将真实 HWK 触觉硬件稳定映射为固定 ROS2 topic，供 Octopus 显示和 MCAP 录制。

## 1. 概述

`hwk_pressure_driver` 是 Python ROS2 包，核心节点为 `pressure_driver_node`。节点会打开配置中的串口候选设备，查询每个 HWK 传感器的 `HWK_CHIP_UID`，根据硬件身份映射表绑定到固定逻辑名称和 topic，然后周期性轮询压力帧并发布 `hwk_pressure_interfaces/msg/PressureFrame`。

当前项目目标 topic：

- `/pressure/left_hand/gripper_1`
- `/pressure/left_hand/gripper_2`
- `/pressure/right_hand/gripper_1`
- `/pressure/right_hand/gripper_2`

## 2. 目录结构

| 路径 | 职责 |
| --- | --- |
| `hwk_pressure_driver/pressure_driver_node.py` | ROS2 节点主逻辑；加载配置、创建 publisher、创建串口 worker、定时轮询并发布 PressureFrame。 |
| `hwk_pressure_driver/config.py` | YAML 配置、硬件身份映射和参数校验。 |
| `hwk_pressure_driver/protocol.py` | HWK 串口协议帧构造、CRC、解析和 chip UID payload 解码。 |
| `hwk_pressure_driver/serial_worker.py` | 单串口工作线程；打开串口、查询身份、读取字节流、同步帧边界并回调有效数据帧。 |
| `launch/pressure_driver.launch.py` | ROS2 launch 入口，传入 `config_file` 参数。 |
| `config/pressure_sensors.yaml` | 默认驱动配置；声明轮询频率、串口 glob、身份映射文件和严格身份匹配。 |
| `setup.py`、`setup.cfg`、`package.xml` | Python ROS2 包构建与安装配置。 |
| `resource/hwk_pressure_driver` | ament Python 包资源标记。 |

## 3. 数据流

本节重点说明驱动内部如何从“串口字节流”变成“固定 ROS2 topic”。这个包的核心难点不是发布消息，而是启动阶段先用硬件身份把真实设备绑定到逻辑 topic，并在运行阶段安全地处理串口半包、错包、CRC 错误和无响应。

```mermaid
flowchart TD
  LAUNCH[ros2 launch pressure_driver.launch.py] --> NODE[PressureDriverNode]
  NODE --> LOAD[load_config]
  LOAD --> PARAM[解析默认参数和 serial_port_globs]
  LOAD --> MAP[读取 hardware_identity_map.yaml]
  MAP --> PUB[按 UID target 预创建 publishers]
  PARAM --> WORKERS[为每个串口创建 SerialWorker]
  WORKERS --> OPEN[打开 serial.Serial]
  OPEN --> QUERY[发送 device-info GET 查询 HWK_CHIP_UID]
  QUERY --> IDRESP[解析 identity response]
  IDRESP --> BIND[UID 匹配 target 绑定 SensorRuntime]
  BIND --> TIMER[按最大 poll rate 创建 ROS timer]
  TIMER --> GET[send_get_data 构造并写 GET pressure frame]
  GET --> READ[reader thread 读取字节流]
  READ --> SYNC[按 HEAD/length/TAIL 同步完整帧]
  SYNC --> CRC[parse_frame 校验 CRC/channel/type/addr]
  CRC --> CALLBACK[_handle_frame]
  CALLBACK --> PAYLOAD[_parse_payload 解 uint16 压力矩阵]
  PAYLOAD --> MSG[填充 PressureFrame]
  MSG --> TOPIC[/pressure/...]
```

### 3.1 配置解析和硬件身份目标

`config.py` 的工作机理：

1. `load_config(config_file, node_name)` 先支持 ROS 风格 YAML：可读取 `pressure_driver_node.ros__parameters`，也可读取顶层 `ros__parameters` 或普通 mapping。
2. `_parse_driver_config()` 读取全局默认值：baudrate、poll rate、serial timeout、identity query timeout、strict_identity 等。
3. 如果配置了 `identity_map_file`，会解析硬件身份映射表，生成 `identity_targets: Dict[uid, IdentityTargetConfig]`。
4. `sensor_defaults` 在身份模式下主要提供协议地址和矩阵尺寸；topic 不再由 sensor 默认项决定。
5. 显式 `serial_ports` 与 `serial_port_globs` 会合并；glob 展开的端口会用 `discovered_<设备名>_<index>` 作为内部串口名。
6. 配置层会防止重复串口名、重复真实串口 realpath、非法 device_addr、非法 package_id、空 topic 等问题。

身份模式的关键原则：publisher 先按 UID target 创建，而不是按 `/dev/ttyUSB*` 创建。这样设备枚举顺序变化只影响“从哪个串口读到该 UID”，不影响最终 topic。

### 3.2 节点启动和 SensorRuntime 绑定

`PressureDriverNode.__init__()` 的工作机理：

1. 声明 ROS 参数 `config_file`。若未传入，则先找安装后的 package share 配置；找不到再回退到源码目录 `config/pressure_sensors.yaml`。
2. `_create_publishers()`：
   - 如果存在 `identity_targets`，为每个 UID target 创建 publisher，topic 来自硬件身份映射表。
   - 如果没有 identity targets，则按 legacy 配置中的 serial/sensor topic 创建 publisher，并立即生成 `_sensors`。
3. `_create_workers()` 为每个 `SerialPortConfig` 创建 `SerialWorker`，并传入 frame callback `_handle_frame`。
4. `worker.start()` 成功后，身份模式下调用 `_bind_identity_sensors()`：
   - 读取 `worker.identity_by_addr[device_addr]`。
   - 用 UID 查 `self._config.identity_targets`。
   - 未知 UID 会报错并忽略，不发布到任何 topic。
   - 重复 UID 会抛异常，避免同一硬件被绑定两次。
   - 成功时创建 `SensorRuntime`，key 是 `(serial_name, device_addr)`，其中保存 publisher、target、poll 状态、最近 package_id、接收时间等运行态。
5. 如果最终 `_sensors` 为空，节点会停止已打开 worker，并抛出 `RuntimeError`，避免看起来启动成功但没有任何 topic 可发布。

### 3.3 串口协议帧构造与解析

`protocol.py` 定义了驱动与硬件之间的帧格式：

- 帧头：`0x3C 0x3C`
- 帧尾：`0x3E 0x3E`
- `id_channel`：高 4 bit 是 `device_addr`，低 4 bit 是 channel。
- `flags`：高 6 bit 是 `package_id`，低 2 bit 是 frame type。
- `length`：payload 长度，小端。
- `checksum`：对 payload 计算 CRC16。

关键函数：

1. `build_get_data_frame(device_addr, package_id)` 构造压力数据 GET 请求，channel 为 `CHAN_DATA`，payload 固定为 `0x01`。
2. `build_get_device_info_frame(device_addr, package_id, cmd)` 构造设备信息查询请求，当前用 `CMD_CHIP_UID = 0x05` 查询 UID。
3. `parse_frame(frame)` 校验最小长度、HEAD、length、TAIL、CRC，然后解出 `ParsedFrame`。
4. `decode_chip_uid_payload(payload)` 优先按 ASCII 解析 UID；若不可打印则退化为大写 hex 分组字符串，保证映射文件仍可稳定引用。

### 3.4 SerialWorker 如何处理字节流

每个 `SerialWorker` 只拥有一个串口和一个 reader 线程：

1. `start()` 打开 `serial.Serial`，参数来自配置：port、baudrate、8N1、timeout。
2. reader 线程启动前先执行 `_query_configured_identities()`：
   - 对配置中的每个 `device_addr` 发送 chip UID 查询。
   - 查询前清空串口输入/输出 buffer，写 request 后在 `identity_query_timeout` 内循环读。
   - `_pop_identity_frame()` 从局部 buffer 中按 HEAD/length/TAIL 抽取完整帧，只接受 device-info channel、指定 package_id 的 response/ack。
   - 成功后写入 `identity_by_addr`。
3. reader 线程 `_reader_loop()` 每次从串口读最多 512 字节，追加到 `_rx_buffer`。
4. `_process_rx_buffer()` 是运行期同步器：
   - 找不到 HEAD 时清空 buffer，但保留可能是半个 HEAD 的最后一个字节。
   - 长度不够时等待下一次 read。
   - payload length 超过上限时丢弃当前 head 并重新同步。
   - TAIL 不匹配时丢弃当前 head，避免一个坏帧污染后续数据。
   - `parse_frame()` 失败时记录 CRC 或 parse warning。
   - 非 data channel、非 ACK、未知 device_addr 都会被忽略。
   - 有效帧通过 `_frame_callback(serial_name, parsed)` 交回节点。

### 3.5 轮询和发布 PressureFrame

运行期轮询由 ROS timer 驱动：

1. 节点计算所有已绑定 sensor 的最大 `poll_rate_hz`，timer period 取 `1 / max_poll_rate`，最低 1 ms。
2. 每次 `_poll_timer_callback()` 遍历 `_sensors`。如果当前时间达到该 sensor 的 `next_poll_time`，就通过对应 worker 发送 GET 数据帧。
3. 每个 sensor 有自己的 `next_package_id`，发送成功后记录到 `recent_package_ids`，再自增并按 `0x3F` 回绕。
4. `_handle_frame()` 收到 ACK 后用 `(serial_name, frame.device_addr)` 找 `SensorRuntime`。找不到说明该串口/地址没有绑定到发布目标，会 warning 并丢弃。
5. 如果 ACK package_id 不在最近请求队列中，只打 debug，不丢弃；这样能容忍硬件或串口延迟。
6. `_parse_payload()` 解释压力 payload：
   - 前 4 字节分别是 `total_packets`、`packet_index`、`payload_cols`、`payload_rows`。
   - rows/cols 为 0 时退回配置中的 rows/cols。
   - 后续 payload 按 little-endian `uint16` 数组解析。
   - 数据长度不是偶数时忽略最后一个字节。
   - `rows * cols` 与解析样本数不一致时仍发布，同时保留 `raw_payload` 供排查。
7. 节点填充 `PressureFrame`：
   - `header.stamp` 使用节点当前时间。
   - `header.frame_id` 优先来自 identity target，否则由 `frame_id_prefix/hand/gripper` 组成。
   - `hand`、`gripper` 优先来自 identity target。
   - `data` 和 `raw_payload` 同时发布。
8. 首次有效帧会打印 topic、rows、cols、samples；长时间未收到 ACK 时 `_check_sensor_timeout()` 按 `timeout_warn_sec` 节流打印 warning。

排障重点：

- 节点启动失败且提示没有 bound publisher，先看 `hardware_identity_map.yaml` 中 UID 是否与日志中检测到的 UID 一致。
- 串口能打开但无 topic 数据，先看 identity query 是否失败，再看 device_addr 是否正确。
- 频繁 CRC error 或 tail error 通常是串口噪声、波特率不匹配或硬件连接问题。
- topic 有数据但 Octopus 热力图异常，重点看 `rows/cols/data` 长度是否符合 6x15。

## 4. 依赖与运行

主要依赖：

- ROS2 Python：`rclpy`
- `hwk_pressure_interfaces`
- `pyserial`
- `PyYAML`
- `ament_index_python`

构建：

```bash
cd .
colcon build --packages-select hwk_pressure_driver hwk_pressure_interfaces
```

单独启动：

```bash
cd .
source install/setup.bash
ros2 launch hwk_pressure_driver pressure_driver.launch.py
```

指定配置：

```bash
ros2 launch hwk_pressure_driver pressure_driver.launch.py \
  config_file:=src/hwk_pressure_driver/config/pressure_sensors.yaml
```

场景三/五通常通过 `start_all_sensor.sh` 和 `launch/all_sensor_nodes.launch.py` 间接启动。

只启动触觉链路时，使用仓库根目录的组合启动脚本：

```bash
./start_pressure_only.sh l1 l2
./start_pressure_only.sh r1,l2
./start_pressure_only.sh
```

`start_pressure_only.sh` 不启动 Baton Mini、GoPro 或总传感器 launch。它支持 `l1/l2/r1/r2` 的任意子集和任意顺序，重复参数会自动去重；不传参数时默认选择四路触觉。脚本会在 `diagnostics/generated/` 下生成本次运行专用的 `hardware_identity_map_pressure_only_<组合>.yaml` 和 `pressure_sensors_pressure_only_<组合>.yaml`，再用生成的配置启动一个 `pressure_driver_node`。因此“选择 l1/l2/r1/r2”在当前架构中的含义是：同一个触觉节点只绑定并发布所选 UID 对应的 topic。

可用环境变量：

| 变量 | 默认值 | 含义 |
| --- | --- | --- |
| `AUTO_BUILD` | `1` | 启动前编译 `hwk_pressure_interfaces` 和 `hwk_pressure_driver`；设为 `0` 可跳过。 |
| `START_PRESSURE_ONLY_GENERATE_ONLY` | `0` | 设为 `1` 时只生成临时配置，不启动 ROS 节点。 |
| `PRESSURE_LOCAL_ONLY` | `1` | 设为 `1` 时限制 ROS discovery 到 `LOCALHOST`。 |
| `PRESSURE_IDENTITY_QUERY_TIMEOUT` | `0.3` | 触觉专用脚本生成多地址探测配置时，每个地址查询 UID 的超时时间。 |

## 5. 配置项说明

默认配置文件：`src/hwk_pressure_driver/config/pressure_sensors.yaml`。

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| `frame_id_prefix` | `pressure_sensor` | 未由身份映射指定 frame_id 时的前缀。 |
| `default_baudrate` | `460800` | 串口波特率。 |
| `default_poll_rate_hz` | `100.0` | 默认每个传感器轮询频率。 |
| `serial_timeout` | `0.01` | 串口读超时，单位秒。 |
| `timeout_warn_sec` | `1.0` | 传感器超过多久无有效 ACK 后打印 warning。 |
| `identity_map_file` | `config/hardware_identity_map.yaml` | 硬件 UID 到逻辑名称/topic 的映射表。 |
| `strict_identity` | `true` | 严格使用身份映射；未知 UID 不发布。 |
| `identity_query_timeout` | `1.0` | 查询 chip UID 的超时时间。 |
| `identity_query_package_id` | `29` | 身份查询使用的 package id，范围 0..63。 |
| `sensor_defaults.device_addr` | `6` | 默认 HWK 设备地址。 |
| `sensor_defaults.rows/cols` | `6/15` | 默认压力矩阵尺寸。 |
| `serial_port_globs` | `/dev/ttyUSB*`、`/dev/ttyACM*` | 自动发现串口候选。 |

身份映射开启后，`SensorConfig.topic` 不是最终依据；最终 topic 来自 `IdentityTargetConfig.topic`。若 UID 未在映射表中出现，节点会报错并忽略该硬件。

## 6. 发布消息

消息类型：`hwk_pressure_interfaces/msg/PressureFrame`。

关键字段：

| 字段 | 含义 |
| --- | --- |
| `header.stamp` | 驱动发布时刻。 |
| `header.frame_id` | 触觉传感器 frame，优先来自身份映射。 |
| `hand` | `left_hand` 或 `right_hand` 等逻辑手名。 |
| `gripper` | `gripper_1` 或 `gripper_2`。 |
| `device_addr` | HWK 协议设备地址。 |
| `package_id` | 请求/应答包序号。 |
| `total_packets`、`packet_index` | 多包字段，当前按 payload 原样发布。 |
| `rows`、`cols` | 压力矩阵行列数。 |
| `data` | `uint16[]` 压力数据，长度通常为 `rows * cols`。 |
| `raw_payload` | 原始 payload，便于排查协议解析问题。 |

## 7. UI 逻辑

该包本身没有图形界面。它的“使用界面”是 ROS2 launch、终端日志和 topic 输出：

- 启动日志会打印配置文件、串口数量、sensor 数量、身份映射数量和每个串口概要。
- 首次收到有效压力帧时会打印 topic、rows、cols、samples。
- 超过 `timeout_warn_sec` 未收到 ACK 时会按传感器打印 warning。
- Octopus 场景四的触觉热力图 UI 消费本包发布的 `PressureFrame`。

## 8. 与上下游的关系

上游：

- `config/hardware_identity_map.yaml` 维护硬件 UID 到逻辑 topic 的映射。
- `config/99-hwk-pressure.rules` 可提供稳定 `/dev/hwk_pressure_*` 软链接，但驱动当前也会扫描 `/dev/ttyUSB*` 和 `/dev/ttyACM*`。

下游：

- Octopus 订阅 4 路 `/pressure/...` topic 做实时显示和 MCAP 录制。
- `data_clean` 保留这些原始触觉 topic，后续可用于对齐和训练数据处理。

边界：

- 本包只负责串口协议、硬件身份绑定和 ROS2 发布，不负责 GoPro/Baton Mini 启动。
- 修改消息字段时必须同步更新 `hwk_pressure_interfaces`、Octopus schema 支持和相关 MCAP 处理链路。
- 修改 topic 命名或身份映射逻辑时，必须同步更新场景三、场景五和本文件。
