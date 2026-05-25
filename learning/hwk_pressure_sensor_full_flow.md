# HWK 触觉传感器采集全流程原理

> 这是一份按我们对话重新整理的学习文档。
>
> 目标不是背源码，而是建立一个清楚的心智模型：触觉传感器的数据如何从硬件进入电脑，最后变成 ROS topic。

## 1. 先记住一句话

触觉采集链路可以压缩成这一句：

```text
SerialWorker 负责和某个串口说话；
SensorRuntime 负责记录这个传感器该往哪里发、状态如何；
PressureDriverNode 负责调度轮询、解析数据、发布消息；
PressureFrame 负责承载某一帧要发布的压力数据。
```

如果这句话暂时还抽象，先看下面这个完整小故事。

## 2. 一个具体例子：`/dev/ttyUSB1` 最后发到左手夹爪 2

假设电脑当前扫到了一个串口：

```text
/dev/ttyUSB1
```

电脑一开始只知道“有一个 USB 串口”，不知道它是左手夹爪 1、左手夹爪 2，还是右手夹爪。

### 第一步：打开串口，查询 UID

程序创建一个 `SerialWorker` 对象来管理这个串口：

```text
SerialWorker B -> 管 /dev/ttyUSB1
```

`SerialWorker` 通过串口向后面的 HWK 触觉板发送：

```text
你是谁？把你的 HWK_CHIP_UID 告诉我。
```

如果触觉板正常响应，它可能返回：

```text
HWK_CHIP_UID = 005C0039-3035510B-3735333
```

这个 UID 不是压力数据。它是这个传感器的“身份证号”。

### 第二步：用 UID 查表，确定 topic

`PressureDriverNode` 拿 UID 去查：

```text
config/hardware_identity_map.yaml
```

查到：

```text
UID 005C0039-3035510B-3735333
  -> 左手夹爪 2
  -> /pressure/left_hand/gripper_2
```

于是程序知道：

```text
/dev/ttyUSB1 后面这个真实传感器，是左手夹爪 2。
它的数据应该发到 /pressure/left_hand/gripper_2。
```

### 第三步：创建 `SensorRuntime`

这一步不是“记在心里”，而是创建一个具体的数据对象：

```text
SensorRuntime
```

它保存的是这个传感器的运行状态，例如：

```text
serial_name = "discovered_ttyUSB1_0"
identity_uid = "005C0039-3035510B-3735333"
target.topic = "/pressure/left_hand/gripper_2"
publisher = 发布到 /pressure/left_hand/gripper_2 的 ROS publisher
next_poll_time = 下次什么时候读取数据
next_package_id = 下次请求用哪个包号
last_rx_time = 最近一次收到有效压力数据的时间
```

然后 `PressureDriverNode` 把它存进一个字典：

```text
_sensors[(serial_name, device_addr)] = SensorRuntime(...)
```

简化成例子就是：

```text
_sensors[("discovered_ttyUSB1_0", 6)] = SensorRuntime(
  uid = "005C...",
  topic = "/pressure/left_hand/gripper_2",
  publisher = <ROS publisher>
)
```

### 第四步：后续不断读取压力数据

绑定完成后，`PressureDriverNode` 的定时器会周期性触发。

到时间后，它会看 `SensorRuntime`：

```text
这个传感器该读取数据了吗？
下一个 package_id 是多少？
它在哪个 SerialWorker 上？
```

然后让对应的 `SerialWorker` 发送：

```text
给我当前压力数据。
```

触觉板返回一帧压力数据。为了好理解，假设返回的是一个 `2 x 3` 小矩阵：

```text
rows = 2
cols = 3
data = [10, 12, 9, 0, 3, 20]
```

真实项目里通常是 `6 x 15`。

### 第五步：临时创建 `PressureFrame` 并发布

收到压力数据后，`PressureDriverNode` 会临时创建一个 ROS 消息：

```text
PressureFrame()
```

然后把这一帧数据填进去：

```text
hand = left_hand
gripper = gripper_2
rows = 2
cols = 3
data = [10, 12, 9, 0, 3, 20]
```

接着从 `SensorRuntime` 里取出之前保存好的 `publisher`，执行：

```text
runtime.publisher.publish(msg)
```

于是这帧数据就被发布到：

```text
/pressure/left_hand/gripper_2
```

注意：`PressureFrame` 是“一帧数据的包裹”。发布完以后，这一帧数据交给 ROS topic。`SensorRuntime` 不会长期保存每一帧压力数据历史。

## 3. 四个核心角色分别是什么

### `PressureDriverNode`

`PressureDriverNode` 是 ROS2 节点类，是总负责人。

它负责：

```text
加载配置
创建 publisher
创建 SerialWorker
创建 SensorRuntime
定时轮询传感器
收到压力帧后解析 payload
创建 PressureFrame
发布到 ROS topic
```

它不是一个普通函数，也不是 `main()`。它是节点对象。真正的 `main()` 会创建这个节点对象，然后交给 ROS2 运行。

### `SerialWorker`

`SerialWorker` 是一个类，不是 `main()` 函数。

源码里的注释说它拥有：

```text
一个串口
一个 reader thread
一个接收缓冲区
```

可以把它理解成“串口工人”：

```text
SerialWorker A -> 管 /dev/ttyUSB0
SerialWorker B -> 管 /dev/ttyUSB1
SerialWorker C -> 管 /dev/ttyUSB2
SerialWorker D -> 管 /dev/ttyUSB3
```

它负责：

```text
打开串口
发送读取 UID 指令
发送读取压力数据指令
在 reader thread 中不断读串口返回的字节
解析出有效帧后回调给 PressureDriverNode
```

它不决定 topic。topic 的决定来自 UID 和 `hardware_identity_map.yaml`。

### `SensorRuntime`

`SensorRuntime` 是一个 `@dataclass`，不是函数，也不是线程。

它更像“某一个传感器的运行状态卡”。

它保存：

```text
这个传感器来自哪个 serial_name
这个传感器的 UID 是什么
这个 UID 对应哪个 target/topic
用哪个 publisher 发布
下一次什么时候轮询
下一个 package_id 是多少
最近发过哪些 package_id
最近一次收到有效数据是什么时候
是否已经打印过首次收到数据日志
```

它不负责主动执行逻辑。真正做事的是 `PressureDriverNode` 和 `SerialWorker`。

还要特别注意：

```text
SensorRuntime 不是压力数据仓库。
UID、topic、publisher、轮询状态会存在里面；
每一帧压力 data 不会长期存在里面。
```

压力数据只是经过它找到正确的 publisher，然后被封装成 `PressureFrame` 发出去。

### `PressureFrame`

`PressureFrame` 是 ROS 消息类型。

每次收到一帧有效压力数据，程序会创建一个新的 `PressureFrame` 消息对象。

它承载的是“这一帧要发布的数据”：

```text
header.stamp
hand
gripper
device_addr
package_id
rows
cols
data
raw_payload
```

可以把它理解成“一次快递包裹”。包裹里装着这一帧压力数据，交给 ROS topic 后就发出去了。

## 4. 真实代码里的两个关键字典

### `SerialWorker.identity_by_addr`

`SerialWorker` 查询 UID 后，会把结果存到：

```text
identity_by_addr[device_addr] = uid
```

比如：

```text
identity_by_addr[6] = "005C0039-3035510B-3735333"
```

这表示：

```text
在这个 SerialWorker 管理的串口上，
device_addr = 6 的触觉板，
UID 是 005C...
```

### `PressureDriverNode._sensors`

`PressureDriverNode` 拿 UID 查到 topic 后，会创建 `SensorRuntime`，再存到：

```text
_sensors[(serial_name, device_addr)] = SensorRuntime(...)
```

比如：

```text
_sensors[("discovered_ttyUSB1_0", 6)] = SensorRuntime(
  identity_uid = "005C...",
  target.topic = "/pressure/left_hand/gripper_2",
  publisher = <publisher>
)
```

后续收到压力帧时，程序就用：

```text
(serial_name, frame.device_addr)
```

回到 `_sensors` 里找对应的 `SensorRuntime`。

找到后，就知道：

```text
这帧数据属于哪个传感器
这帧数据应该发到哪个 topic
应该使用哪个 publisher
```

## 5. 运行后，进程和线程大概是什么样

启动触觉 ROS 节点后，可以先这样理解：

```text
一个 pressure_driver_node 进程
  -> 一个 PressureDriverNode 对象
  -> 多个 SerialWorker 对象
      -> 每个 SerialWorker 管一个串口
      -> 每个 SerialWorker 有自己的 reader thread
  -> 多个 SensorRuntime 对象
      -> 每个已识别传感器一个运行状态卡
```

如果 4 个触觉传感器分别对应 4 个独立串口，通常可以粗略理解为：

```text
1 个进程
1 个 PressureDriverNode
4 个 SerialWorker
4 个 reader thread
4 个 SensorRuntime
```

但不是“4 个线程都运行 PressureDriverNode”。

更准确是：

```text
PressureDriverNode 是总负责人；
每个 SerialWorker 的 reader thread 负责盯一个串口；
SensorRuntime 只是状态卡；
PressureFrame 是每一帧临时创建的消息。
```

## 6. 为什么要先查 UID

因为 `/dev/ttyUSB0`、`/dev/ttyUSB1` 这些名字不可靠。

今天可能是：

```text
/dev/ttyUSB0 = 左手夹爪 1
/dev/ttyUSB1 = 左手夹爪 2
```

明天重新插拔后可能变成：

```text
/dev/ttyUSB0 = 左手夹爪 2
/dev/ttyUSB1 = 左手夹爪 1
```

如果只按 `/dev/ttyUSB0` 来决定 topic，就可能把左手 2 的数据误发到左手 1。

所以正确流程是：

```text
打开串口
  -> 问后面的触觉板：你的 UID 是什么？
  -> 用 UID 查 hardware_identity_map.yaml
  -> 确定它应该对应哪个 topic
```

一句话：

```text
/dev/ttyUSB* 负责找到通道；
HWK_CHIP_UID 负责确认身份；
hardware_identity_map.yaml 负责决定 topic；
PressureDriverNode 负责轮询和发布。
```

## 7. 从启动到发布的一次完整流程

下面是完整流程，按发生顺序写：

```text
1. 运行 pressure_driver_node。

2. main() 创建 PressureDriverNode。

3. PressureDriverNode 加载：
   - pressure_sensors.yaml
   - hardware_identity_map.yaml

4. PressureDriverNode 根据映射表预先创建 publisher。
   比如为 /pressure/left_hand/gripper_2 创建 publisher。

5. PressureDriverNode 扫描候选串口：
   - /dev/ttyUSB*
   - /dev/ttyACM*

6. 每个串口创建一个 SerialWorker。

7. SerialWorker 打开自己的串口。

8. SerialWorker 发送“读取 UID”指令。

9. 触觉板返回 HWK_CHIP_UID。

10. SerialWorker 存：
    identity_by_addr[device_addr] = UID

11. PressureDriverNode 读取这个 UID。

12. PressureDriverNode 用 UID 查 hardware_identity_map.yaml。

13. 查到 hand、gripper、topic。

14. PressureDriverNode 创建 SensorRuntime。

15. PressureDriverNode 存：
    _sensors[(serial_name, device_addr)] = SensorRuntime(...)

16. PressureDriverNode 的定时器开始轮询。

17. 到时间后，PressureDriverNode 查看 SensorRuntime：
    - 下次该不该读？
    - package_id 用多少？
    - 对应哪个 SerialWorker？

18. PressureDriverNode 让 SerialWorker 发送“读取压力数据”指令。

19. 触觉板返回压力 ACK 帧。

20. SerialWorker 的 reader thread 读取并解析出有效帧。

21. SerialWorker 回调 PressureDriverNode._handle_frame(...)

22. PressureDriverNode 用：
    (serial_name, frame.device_addr)
    查 _sensors，找回 SensorRuntime。

23. PressureDriverNode 解析 payload，得到 rows、cols、data。

24. PressureDriverNode 临时创建 PressureFrame。

25. PressureDriverNode 把这一帧数据填入 PressureFrame。

26. PressureDriverNode 从 SensorRuntime 取 publisher。

27. 执行：
    runtime.publisher.publish(msg)

28. 这一帧压力数据进入对应 ROS topic。
```

## 8. 启动脚本和配置文件在这条链路里的位置

总启动脚本是：

```bash
./start_all_sensor.sh
```

它不是触觉驱动本身，而是总启动入口。

它大致负责：

```text
source ROS 环境
可选 colcon build
运行启动前检查
启动 launch/all_sensor_nodes.launch.py
等待后检查节点和 topic
```

`launch/all_sensor_nodes.launch.py` 读取：

```text
config/all_sensor_nodes.yaml
```

当它发现：

```yaml
pressure:
  enabled: true
```

就会启动触觉驱动：

```text
hwk_pressure_driver/launch/pressure_driver.launch.py
  -> pressure_driver_node
```

触觉驱动自己的配置来自：

```text
src/hwk_pressure_driver/config/pressure_sensors.yaml
```

硬件 UID 到 topic 的映射来自：

```text
config/hardware_identity_map.yaml
```

## 9. 四个最终 topic

项目期望 4 路触觉 topic：

| 逻辑位置 | ROS topic |
|---|---|
| 左手夹爪 1 | `/pressure/left_hand/gripper_1` |
| 左手夹爪 2 | `/pressure/left_hand/gripper_2` |
| 右手夹爪 1 | `/pressure/right_hand/gripper_1` |
| 右手夹爪 2 | `/pressure/right_hand/gripper_2` |

下游系统关心的是这些 topic 是否稳定存在、是否持续有真实 `PressureFrame` 数据。

## 10. 左手两个触觉连不上时，按哪几层理解

这一节只是帮助理解故障位置，不要求马上执行命令。

### USB 枚举层

问题表现：

```text
系统看不到足够数量的 CH340
/dev/ttyUSB* 数量不够
内核日志里出现 disconnect、unable to enumerate 等信息
```

含义：

```text
电脑还没有稳定看见硬件，ROS 驱动没有机会通信。
```

### Linux 串口/权限层

问题表现：

```text
设备文件存在，但当前用户不可读写
或者串口被其他进程占用
```

含义：

```text
硬件被系统看见了，但 SerialWorker 没法正常打开或使用它。
```

### HWK 协议层

问题表现：

```text
串口能打开，但 HWK_CHIP_UID 查询 timeout/no ACK
```

含义：

```text
CH340 通道可能存在，但后面的触觉板没有按协议回应。
```

### 身份映射层

问题表现：

```text
UID 能查出来，但不在 hardware_identity_map.yaml 里
```

含义：

```text
程序知道有个硬件，但不知道它应该对应哪个 topic。
```

### ROS 发布层

问题表现：

```text
UID 绑定成功，但 topic 不出现，或者 topic 没有持续数据
```

含义：

```text
启动身份识别可能通过了，但运行期读取压力数据不稳定。
```

## 11. 最后再压缩成一张脑图

```text
电脑看见 CH340
  -> Linux 生成 /dev/ttyUSB*
  -> PressureDriverNode 创建 SerialWorker
  -> SerialWorker 打开串口并查询 UID
  -> UID 存在 identity_by_addr
  -> PressureDriverNode 用 UID 查 hardware_identity_map.yaml
  -> 创建 SensorRuntime
  -> SensorRuntime 存 topic、publisher、轮询状态
  -> 定时器触发读取压力数据
  -> SerialWorker 收到压力 ACK
  -> PressureDriverNode 解析 payload
  -> 临时创建 PressureFrame
  -> runtime.publisher.publish(msg)
  -> 数据进入 /pressure/... topic
```

读完这份文档后，你可以用一句话判断自己是否理解了：

```text
UID 决定“这个传感器是谁”，
SensorRuntime 保存“它该怎么运行、往哪发”，
PressureFrame 承载“这一帧具体数据”，
publisher.publish() 把这一帧送进 ROS topic。
```
