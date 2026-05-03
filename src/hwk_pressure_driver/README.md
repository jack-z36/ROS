# 华威科灵巧手压力传感器 ROS2 驱动

这是一个面向 ROS 2 Jazzy 的 Python 串口驱动，用于读取华威科灵巧手压力传感器数据。节点会统一打开并管理配置中的多个串口，按传感器轮询读取压力数据；只有收到有效 ACK 响应并成功解析数据时，才发布对应夹爪的 topic。

驱动不会为无响应传感器发布空数组、默认值、假数据或超时占位数据。如果某个传感器没有返回有效帧，该传感器 topic 会保持静默。

## 功能说明

- 一个节点统一管理多个串口。
- 默认按一个串口对应一个夹爪压力传感器配置，共四个夹爪时配置四个串口。
- 每个串口有独立的 reader thread、RX buffer 和写锁。
- 支持帧头同步、帧尾检查、CRC16 校验、Channel/Type 过滤和未知地址过滤。
- 坏帧、CRC 错误、未知地址、串口异常和传感器超时都会打印日志，但不会导致整个节点崩溃。
- 支持启动时读取 `HWK_CHIP_UID`，并按硬件身份映射表发布到固定 topic。

## 编译方法

进入 ROS2 工作区根目录：

```bash
cd <ros2_ws>
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --packages-select hwk_pressure_interfaces hwk_pressure_driver
source install/setup.bash
```

如果当前环境中 `rosdep` 无法安装 Python 依赖，可以手动安装：

```bash
python3 -m pip install pyserial PyYAML
```

## 运行方法

使用包内默认配置启动：

```bash
ros2 launch hwk_pressure_driver pressure_driver.launch.py
```

指定自定义配置文件启动：

```bash
ros2 launch hwk_pressure_driver pressure_driver.launch.py config_file:=/path/to/pressure_sensors.yaml
```

也可以直接运行节点：

```bash
ros2 run hwk_pressure_driver pressure_driver_node --ros-args -p config_file:=/path/to/pressure_sensors.yaml
```

## 配置说明

默认配置文件为 `config/pressure_sensors.yaml`。节点使用 `config_file` 参数读取完整 YAML 配置，避免 ROS2 Python 参数系统对复杂 list/dict 支持有限的问题。

示例：

```yaml
pressure_driver_node:
  ros__parameters:
    frame_id_prefix: pressure_sensor
    default_baudrate: 460800
    default_poll_rate_hz: 100.0
    serial_timeout: 0.01
    timeout_warn_sec: 1.0

    serial_ports:
      - name: left_gripper_1_port
        port: /dev/ttyUSB0
        baudrate: 460800
        sensors:
          - hand: left_hand
            gripper: gripper_1
            device_addr: 1
            rows: 12
            cols: 6
            topic: /pressure/left_hand/gripper_1

      - name: left_gripper_2_port
        port: /dev/ttyUSB1
        baudrate: 460800
        sensors:
          - hand: left_hand
            gripper: gripper_2
            device_addr: 1
            rows: 12
            cols: 6
            topic: /pressure/left_hand/gripper_2

      - name: right_gripper_1_port
        port: /dev/ttyUSB2
        baudrate: 460800
        sensors:
          - hand: right_hand
            gripper: gripper_1
            device_addr: 1
            rows: 12
            cols: 6
            topic: /pressure/right_hand/gripper_1

      - name: right_gripper_2_port
        port: /dev/ttyUSB3
        baudrate: 460800
        sensors:
          - hand: right_hand
            gripper: gripper_2
            device_addr: 1
            rows: 12
            cols: 6
            topic: /pressure/right_hand/gripper_2
```

主要字段说明：

- `frame_id_prefix`：发布消息中 `header.frame_id` 的前缀，默认 `pressure_sensor`。
- `default_baudrate`：默认波特率，默认 `460800`。
- `default_poll_rate_hz`：默认轮询频率，默认 `100.0`。
- `serial_timeout`：串口读取 timeout，默认 `0.01` 秒。
- `timeout_warn_sec`：传感器无有效数据时的超时 warning 周期，默认 `1.0` 秒。
- `identity_map_file`：硬件身份映射表，默认场景五使用 `/home/hit/ROS/config/hardware_identity_map.yaml`。
- `serial_port_globs`：候选串口 glob，例如 `/dev/ttyUSB*`；串口只用于打开设备，不决定最终 topic。
- `serial_ports`：可选串口列表，每个串口包含 `name`、`port`、`baudrate` 和 `sensors`；不配置时会使用 `serial_port_globs` 动态发现串口。
- `sensors`：该串口下挂载的传感器列表；当前硬件拓扑下每个列表只配置一个 sensor。
- `device_addr`：传感器设备地址，范围 `0..15`；不同串口互相独立，可以使用相同地址。
- `rows`、`cols`：payload 行列数异常时使用的备用尺寸。
- `topic`：旧配置模式下该传感器对应的发布 topic；启用 `identity_map_file` 后，topic 来自 `HWK_CHIP_UID` 映射表。
- `poll_rate_hz`：单个传感器可选轮询频率；不配置时使用 `default_poll_rate_hz`。

## 查看 Topic

查看当前 topic：

```bash
ros2 topic list
```

查看单个夹爪压力数据：

```bash
ros2 topic echo /pressure/left_hand/gripper_1
ros2 topic echo /pressure/left_hand/gripper_2
ros2 topic echo /pressure/right_hand/gripper_1
ros2 topic echo /pressure/right_hand/gripper_2
```

如果某个 topic 不出现或不更新，说明该传感器暂时没有收到有效 ACK 帧。这是驱动的预期行为，程序不会发布空数据。

## 串口权限设置

Linux 下通常需要把当前用户加入串口设备组：

```bash
sudo usermod -a -G dialout $USER
```

执行后需要重新登录或重启系统。临时测试时也可以直接修改设备权限：

```bash
sudo chmod a+rw /dev/ttyUSB0
sudo chmod a+rw /dev/ttyUSB1
sudo chmod a+rw /dev/ttyUSB2
sudo chmod a+rw /dev/ttyUSB3
```

## Linux 固定串口名建议

不要长期依赖 `/dev/ttyUSB0` 到 `/dev/ttyUSB3` 这类枚举顺序，因为插拔顺序变化后编号可能改变。建议先查看稳定设备路径：

```bash
ls -l /dev/serial/by-id/
```

然后在配置文件中把 `port` 设置为 `/dev/serial/by-id/...`。

如果需要自定义固定名称，可以根据设备的 vendor/product 信息写 udev rules。先查看设备信息：

```bash
udevadm info -a -n /dev/ttyUSB0
```

创建规则文件：

```bash
sudo nano /etc/udev/rules.d/99-hwk-pressure.rules
```

示例规则：

```udev
SUBSYSTEM=="tty", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", SYMLINK+="hwk_pressure_left_gripper_1"
```

重新加载规则：

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

之后可以在配置中使用 `/dev/hwk_pressure_left_gripper_1` 这类固定路径，并为四个夹爪分别配置稳定名称。

## 调试建议

建议先只配置一个 `port` 和一个 `sensor`，确认能收到数据后，再逐步增加其他传感器。

使用下面命令确认 topic 是否出现：

```bash
ros2 topic list
```

再查看数据内容：

```bash
ros2 topic echo /pressure/left_hand/gripper_1
```

如果 topic 不出现或不更新，说明没有收到对应传感器的有效帧，驱动不会发布空数据。

Windows 下建议使用串口助手分别测试四个 COM 口，确认每个 COM 实际对应哪只手或哪个夹爪，并确认实际 `device_addr`。

Linux 下建议优先使用：

```bash
ls -l /dev/serial/by-id/
```

确认稳定设备路径，并在配置文件中使用 `/dev/serial/by-id/...`，不要优先使用 `/dev/ttyUSB0`。

如果没有 topic 发布，重点检查：

- 串口路径或 Windows COM 口是否正确。
- 波特率是否为 `460800`。
- 串口格式是否为 8 数据位、1 停止位、无校验。
- YAML 中的 `device_addr` 是否和硬件一致。
- 设备是否真的返回 Channel `0x02`、Type `0x03` 的 ACK 帧。
- CRC16 是否正确，校验值只对 PAYLOAD 计算。
- 帧尾是否为 `0x3E 0x3E`。
- LENGTH 和实际 payload 长度是否一致。

超时 warning 只表示节点正在轮询，但最近没有收到有效帧；它不会触发任何空消息发布。

##后续接上右手触觉后，执行

udevadm info -q property -n /dev/ttyUSBX | grep '^ID_PATH='

把实际 **ID_PATH** 填进 **config/99-hwk-pressure.rules** 里对应的 **TODO_RIGHT_*_ID_PATH**，取消注释，再复制到 **/etc/udev/rules.d/** 重载即可。
