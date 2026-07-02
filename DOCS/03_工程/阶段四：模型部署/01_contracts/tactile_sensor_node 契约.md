# tactile_sensor_node 契约

关联总契约：[[TO-BE Contract#传感器数据发送节点|传感器数据发送节点]]

参考实现：

- `src/data_collection/hwk_pressure_driver/hwk_pressure_driver/protocol.py`
- `src/data_collection/hwk_pressure_driver/hwk_pressure_driver/serial_worker.py`
- `src/data_collection/hwk_pressure_driver/hwk_pressure_driver/pressure_driver_node.py`
- `src/data_collection/hwk_pressure_driver/config/pressure_sensors.yaml`
- `src/data_collection/hwk_pressure_interfaces/msg/PressureFrame.msg`
- `config/hardware_identity_map.yaml`

## 节点定位

`tactile_sensor_node` 是四片华威科触觉芯片的观测发送节点。

它负责串口发现、芯片身份绑定、协议轮询、解帧、校验、矩阵转换，并向 `Pi05VlaDeployNode` 发布四路独立触觉数组。

它不做夹爪控制、不合并四片触觉数据、不把触觉数据编码成 policy state。

## 上下游接口

| 方向 | topic | ROS msg | 现实语义 |
|---|---|---|---|
| 订阅 | 无 | 无 | 触觉节点按自身轮询周期读取硬件。 |
| 发布 | `/pi05/observation/tactile/l1` | `std_msgs/msg/Float32MultiArray` | 左夹爪第 1 片触觉芯片的压力矩阵。 |
| 发布 | `/pi05/observation/tactile/l2` | `std_msgs/msg/Float32MultiArray` | 左夹爪第 2 片触觉芯片的压力矩阵。 |
| 发布 | `/pi05/observation/tactile/r1` | `std_msgs/msg/Float32MultiArray` | 右夹爪第 1 片触觉芯片的压力矩阵。 |
| 发布 | `/pi05/observation/tactile/r2` | `std_msgs/msg/Float32MultiArray` | 右夹爪第 2 片触觉芯片的压力矩阵。 |

## 硬件身份映射

| 逻辑名 | 现实位置 | 目标 topic | 身份绑定依据 |
|---|---|---|---|
| `l1` | 左夹爪第 1 片触觉芯片 | `/pi05/observation/tactile/l1` | `HWK_CHIP_UID` 优先，其次才允许临时使用稳定串口名。 |
| `l2` | 左夹爪第 2 片触觉芯片 | `/pi05/observation/tactile/l2` | `HWK_CHIP_UID` 优先，其次才允许临时使用稳定串口名。 |
| `r1` | 右夹爪第 1 片触觉芯片 | `/pi05/observation/tactile/r1` | `HWK_CHIP_UID` 优先，其次才允许临时使用稳定串口名。 |
| `r2` | 右夹爪第 2 片触觉芯片 | `/pi05/observation/tactile/r2` | `HWK_CHIP_UID` 优先，其次才允许临时使用稳定串口名。 |

`config/hardware_identity_map.yaml` 中已有四片芯片的 `HWK_CHIP_UID`，开发时应沿用这个思路，把物理芯片绑定到 `l1` / `l2` / `r1` / `r2`，而不是依赖 `/dev/ttyUSB*` 的枚举顺序。

## 串口与协议契约

| 项 | 契约 |
|---|---|
| 串口参数 | 默认波特率 `460800`，`8N1`，串口 timeout 默认 `0.01s`；允许由配置覆盖。 |
| 默认轮询频率 | `100Hz`；允许由配置覆盖。 |
| 默认设备地址 | `device_addr = 6`。 |
| 默认矩阵尺寸 | `rows = 6`，`cols = 15`。 |
| 帧头 | `0x3C 0x3C`。 |
| 帧尾 | `0x3E 0x3E`。 |
| 数据通道 | `CHAN_DATA = 0x02`。 |
| 请求类型 | `TYPE_GET = 0x01`。 |
| 响应类型 | `TYPE_ACK = 0x03`。 |
| 校验 | 对 payload 计算 CRC16；CRC 错误的帧必须丢弃。 |
| package id | `0..63` 循环递增，用于关联近期请求与 ACK。 |

## payload 解析契约

触觉数据 payload 采用数据采集模块当前解析逻辑：

| payload 字节区间 | 含义 |
|---|---|
| `payload[0]` | `total_packets`。 |
| `payload[1]` | `packet_index`。 |
| `payload[2]` | `cols`。 |
| `payload[3]` | `rows`。 |
| `payload[4:]` | 小端 `uint16` 压力采样值序列。 |

若 payload 中的 `rows` 或 `cols` 为 `0`，允许退回配置中的 `rows` / `cols`，但必须记录 warn。

若 `rows * cols != sample_count`，允许发布解析出的数据，但必须记录 warn；`Pi05VlaDeployNode` 侧后续可按模型输入契约决定是否拒收。

## 发布 msg 契约

虽然数据采集模块内部已有 `hwk_pressure_interfaces/msg/PressureFrame`，本部署契约面向 `Pi05VlaDeployNode` 的最小接口固定为 `std_msgs/msg/Float32MultiArray`。

| 字段 | 值 |
|---|---|
| `layout.dim[0].label` | `rows`。 |
| `layout.dim[0].size` | 触觉矩阵行数。 |
| `layout.dim[0].stride` | `rows * cols`。 |
| `layout.dim[1].label` | `cols`。 |
| `layout.dim[1].size` | 触觉矩阵列数。 |
| `layout.dim[1].stride` | `cols`。 |
| `layout.data_offset` | `0`。 |
| `data` | `float32` 数组，按行优先从原始 `uint16` 压力值转换得到。 |

展平顺序固定为：

```text
data[row * cols + col] = pressure_matrix[row][col]
```

当前契约不要求节点做归一化。`data` 默认表示原始压力读数转成的 `float32`。若后续需要归一化，必须在 Contract Delta 中显式改写量纲和数值范围。

## 与 Pi05VlaDeployNode 对齐

| Pi05 需求 | 本节点保证 |
|---|---|
| Pi05 需要四路触觉 observation：`l1` / `l2` / `r1` / `r2`。 | 四片芯片分别发布到四个固定 topic，不合并。 |
| Pi05 用最新完整 observation 推理。 | 坏帧、CRC 错帧、未知芯片帧不发布，避免旧数据伪装成新数据。 |
| Pi05 需要矩阵维度明确。 | 每条 `Float32MultiArray` 都写入 `rows` / `cols` layout。 |
| Pi05 需要稳定语义而不是串口枚举顺序。 | 通过 `HWK_CHIP_UID` 绑定逻辑名。 |

## 异常处理契约

| 场景 | 处理方式 |
|---|---|
| 串口打开失败 | 记录 error；对应芯片 topic 不发布伪造数据。 |
| 芯片 UID 未匹配 | strict 模式下拒绝绑定并报错；非 strict 模式必须显式日志提示风险。 |
| CRC 错误 | 丢弃当前帧。 |
| 帧头 / 帧尾错误 | 丢弃并重新同步接收缓冲区。 |
| payload 长度异常 | 丢弃或按当前数据采集模块逻辑降级解析，并记录 warn。 |
| 触觉超时 | 超过 `timeout_warn_sec` 后周期性 warn；不重复发布最后一帧。 |

## 配置参数

| 参数 | 类型 | 含义 |
|---|---|---|
| `identity_map_file` | string | 芯片 UID 到 `l1/l2/r1/r2` 的映射文件。 |
| `strict_identity` | bool | 是否要求所有目标芯片必须通过 UID 匹配。 |
| `default_baudrate` | int | 默认 `460800`。 |
| `default_poll_rate_hz` | float | 默认 `100.0`。 |
| `serial_timeout` | float | 默认 `0.01`。 |
| `timeout_warn_sec` | float | 默认 `1.0`。 |
| `rows` / `cols` | int | 单片触觉芯片矩阵尺寸，默认 `6 x 15`。 |

## 验收方式

| 检查项 | 命令 / 标准 |
|---|---|
| topic 存在 | `ros2 topic list` 能看到四个 `/pi05/observation/tactile/*` topic。 |
| msg 类型 | `ros2 topic info /pi05/observation/tactile/l1` 显示 `std_msgs/msg/Float32MultiArray`。 |
| 维度正确 | `layout.dim` 中存在 `rows` 和 `cols`。 |
| 展平长度正确 | `len(data) == rows * cols`，除非日志明确说明硬件帧长度异常。 |
| 身份不混淆 | 分别按压四片芯片时，只对应一个 topic 数值变化。 |
