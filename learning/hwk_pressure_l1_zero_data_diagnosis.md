# l1 触觉传感器全 0 数据排查总结

## 正常工作框架

一个正常的 l1 触觉传感器链路应按下面方式工作：

```text
触觉片受力
  -> l1 MCU 采集 6x15 压力矩阵
  -> MCU 通过 UART 返回 HWK 压力数据帧
  -> CH340 把 UART 转成 /dev/ttyUSBx
  -> hwk_pressure_driver 读取串口帧并解析 PressureFrame
  -> ROS topic: /pressure/left_hand/gripper_1
  -> Octopus 订阅 topic 并渲染热力图
```

正常状态下，l1 MCU 不只会返回 UID，还应持续返回非零压力矩阵。按压时，`PressureFrame.data` 和原始 `raw_payload` 中的压力值应明显增大。

## 问题现象

l1 在 Octopus 中热力图没有有效变化，看起来像“不灵敏、无反馈”。

进一步确认后，问题不是 topic 没发布，也不是 Octopus 没订阅，而是 l1 发布的数据内容异常：

- l1 topic 能持续发布，频率约 70Hz 以上。
- l1 能返回 UID：`003F000F-3035510B-3735333`。
- l1 能返回合法压力帧，payload 结构正确：`[1, 1, 15, 6] + 180 bytes`。
- 但 90 个 uint16 压力采样值全是 `0`。

因此直接原因是：

```text
Octopus 收到了 l1 数据，但收到的是全 0 压力矩阵，所以热力图没有有效反馈。
```

这些 0 不是上位机程序默认填充的，而是 l1 MCU 通过串口返回的原始压力 payload。

## 测试场景与结论

| 场景 | 硬件拓扑 | 测试内容 | 关键结果 | 证明/排除 |
|---|---|---|---|---|
| l1 单独接一个 CH340 | `l1 MCU -> CH340 -> 电脑` | 查询 l1 UID；单独启动 l1 driver；绕过 ROS 直接请求压力帧 | UID 正确；topic 正常发布；压力帧结构合法；压力矩阵全 0 | CH340 到电脑正常；上位机到 l1 MCU 的 UART 通信正常；ROS driver 绑定、解析、发布正常；Octopus 不是根因；在独立 CH340/单 MCU 拓扑下，l1 返回全 0 payload |
| l1/l2 各自独立 CH340 | `l1 MCU -> CH340 A -> 电脑`；`l2 MCU -> CH340 B -> 电脑` | 分别查询 UID/address；分别采样原始压力；交换两个 CH340/线材后复测 | 交换前：l1 `peak_max=0`，l2 `peak_max=6`；交换后：l2 `peak_max=819`，l1 `peak_max=0` | 问题不跟 CH340 芯片、USB 口、`/dev/ttyUSB0/1` 编号、上位机串口配置走；现象跟随 l1 设备身份出现，但不能据此判断 l1 硬件损坏 |
| 两个 MCU 重新接回同一个 CH340 | `l1 MCU + l2 MCU -> 同一个 CH340 -> 电脑` | 在同一个 `/dev/ttyUSB0` 上分别请求 addr6(l1) 和 addr5(l2) 的原始压力帧 | l1 `peak_max=1626`；l2 `peak_max=990` | l1 MCU 能产生有效压力数据；l1 触觉片、MCU、采样能力本身并未损坏；l1 地址、UID、固件版本不是根因；恢复原双 MCU/共用 CH340 拓扑后，l1 压力采样恢复 |

## 最终判断

问题根因不在 Octopus、ROS topic 绑定、UID 映射、数据解析、CH340 芯片本身或 USB 枚举。

最核心的事实是：

```text
同一块 l1 MCU：

- 在“独立 CH340/单 MCU 拓扑”下，返回全 0 压力矩阵。
- 在“同一 CH340/双 MCU 拓扑”下，返回非 0 压力矩阵。
```

因此不能说 l1 硬件层面损坏。l1 硬件本体已经被证明具备正常采样能力。

更严谨的判断是：

```text
问题只在 l1 独立 CH340/单 MCU 拓扑下出现。
根因更可能与拓扑相关的软件/协议/初始化/轮询模式差异有关，
也可能与单独接线拓扑缺少某个原双 MCU 线束中的公共条件有关。
```

当前更值得优先验证的软件侧可能性：

- 独立 CH340 时，l1 使用异步 reader 轮询模式；同 CH340 双 MCU 时，使用同步 serialized polling 模式。
- l1 MCU 可能依赖某种请求顺序、初始化顺序、轮询间隔或总线状态副作用。
- 同 CH340 双 MCU 时，先后访问 addr6/addr5 可能让设备进入了能正常采样的状态。

仍需保留的拓扑/接线可能性：

- 触觉片供电
- 模拟前端供电
- 公共 GND
- EN/使能线
- 参考电压
- 原双 MCU 线束中由另一分支提供的公共连接

所以，l1 独立 CH340 时并不是“不能通信”，而是：

```text
l1 MCU 能通信、能回压力帧，但该拓扑/轮询条件下采样值全 0。
```

恢复双 MCU 共用 CH340 后，l1 又能产生非零压力值，说明需要继续排查“独立拓扑”和“共用拓扑”之间的软件轮询差异与接线差异。

## 后续排查方向

### 排查原则

优先做软件轮询模式对照：

- 在 l1 独立 CH340 下，强制启用与同 CH340 双 MCU 相同的同步 `serialized_polling` 请求模式。
- 保持 l1 仍单独接线，只改变上位机轮询方式。
- 如果 l1 恢复非零，说明根因在 driver 请求/读取模式或设备初始化时序。
- 如果仍然全 0，再继续排查接线拓扑差异。

再做接线拓扑对照：

- 保留 l1 MCU，逐根恢复原线束中的公共供电/GND/EN/参考线。
- 每恢复一根线，直接采样 l1 原始压力值。
- 判断标准：`l1 peak_max` 是否从 `0` 恢复为非零。

临时可用方案：

```bash
PRESSURE_ONLY_PORT=/dev/ttyUSB0 ./start_pressure_only.sh l1 l2
```

该方案强制 l1/l2 共用同一个 CH340。当前实测此拓扑下 l1/l2 都能返回有效压力数据。

### 实验记录表

表格只记录关键指标。每次执行前先说明命令含义、为什么运行、期望结果；执行后把 `frames_ok`、`peak_max`、`nonzero_frames`、`avg_hz`、topic 频率和结论补到结果列。

| 实验编号 | 硬件拓扑 | 软件变量 | 运行命令 | 命令含义 | 为什么运行 | 采集指标 | 结果 | 结论 | 下一步 |
|---|---|---|---|---|---|---|---|---|---|
| E1 | `l1 MCU + l2 MCU -> 同一个 CH340 -> 电脑` | raw 同步采样 l1/l2 | `python3 scripts/hwk_pressure_raw_sample.py --port /dev/ttyUSB0 --addr 6 --frames 100 --rate 50 --label l1_shared_retry`；`python3 scripts/hwk_pressure_raw_sample.py --port /dev/ttyUSB0 --addr 5 --frames 100 --rate 50 --label l2_shared` | 绕过 ROS/Octopus，直接请求两个地址的压力帧 | 确认当前“共用 CH340”基线下 l1/l2 是否仍返回非零原始压力值 | `frames_ok`、`peak_max`、`nonzero_frames`、`avg_hz` | l1：`frames_ok=100`，`peak_max=0`，`nonzero_frames=0`，`avg_hz=49.62`；l2：`frames_ok=100`，`peak_max=217`，`nonzero_frames=100`，`avg_hz=49.64` | 当前共用 CH340 拓扑下，raw 同步采样链路正常，l2 有效，l1 仍返回全 0；这与先前“共用 CH340 下 l1 可非零”的历史结果不一致 | 先复查当前接线/按压位置/触觉片连接是否等价于先前有效拓扑；再决定是否继续 E2 |
| E2 | `l1 MCU + l2 MCU -> 同一个 CH340 -> 电脑` | 只请求 l1，不访问 l2 | `python3 scripts/hwk_pressure_raw_sample.py --port /dev/ttyUSB0 --addr 6 --frames 100 --rate 50 --label l1_shared_only` | 在共用硬件拓扑下只向 l1 发数据请求 | 判断 l1 非零是否依赖 l2 被同时访问或先访问 | `frames_ok`、`peak_max`、`nonzero_frames`、`avg_hz` | 未开始 | 未判断 | 若 E1 非零但 E2 全 0，重点查请求顺序/初始化副作用；否则继续 E3 |
| E3 | `l1 MCU -> 独立 CH340 -> 电脑` | raw 同步采样 l1 | `python3 scripts/hwk_pressure_raw_sample.py --port /dev/ttyUSBx --addr 6 --frames 100 --rate 50 --label l1_independent_raw` | 绕过 ROS/Octopus，直接请求独立拓扑下 l1 压力帧 | 判断 MCU 原始 payload 在独立拓扑下是否已经全 0 | `frames_ok`、`peak_max`、`nonzero_frames`、`avg_hz` | 未开始 | 未判断 | 若 raw 非零但 ROS 全 0，查 driver；若 raw 全 0，继续 E4/E5 |
| E4 | `l1 MCU -> 独立 CH340 -> 电脑` | 现有 driver 异步模式 | `./start_pressure_only.sh l1`；`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ros2 topic hz /pressure/left_hand/gripper_1`；`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ros2 topic echo /pressure/left_hand/gripper_1 --once` | 启动现有 l1 ROS 链路并查看频率与单帧数据 | 验证现有异步 reader 模式下 topic 是否持续发布全 0 | topic hz、单帧 `data` 峰值、driver 错误日志 | 未开始 | 未判断 | 若 E3 非零但 E4 全 0，根因在 driver/ROS 路径；否则继续 E5 |
| E5 | `l1 MCU -> 独立 CH340 -> 电脑` | 强制单 sensor 使用 `serialized_polling` | 使用临时配置把 l1 port 设置为 `serialized_polling: true` 后启动 driver | 让独立 l1 使用与共用 CH340 相同的同步请求路径 | 验证异步 reader/同步轮询差异是否导致全 0 | topic hz、单帧 `data` 峰值、driver 错误日志 | 未开始 | 未判断 | 若 l1 从 0 变非 0，根因优先锁定在轮询/读取模式差异 |
| E6 | `l1 MCU -> CH340 A -> 电脑`；`l2 MCU -> CH340 B -> 电脑` | 双独立 CH340 同时启动 | `./start_pressure_only.sh l1 l2`；分别测 `/pressure/left_hand/gripper_1` 和 `/pressure/left_hand/gripper_2` | 同时启动两个独立串口 topic | 验证多 topic、Octopus 并行显示是否影响 l1 | 两路 topic hz、两路单帧峰值、Octopus 观察 | 未开始 | 未判断 | 若 l1 仍全 0、l2 正常，排除 Octopus/多 topic 为主因 |
| E7 | `l1 MCU -> 独立 CH340 -> 电脑`，逐步恢复原线束公共连接 | 每次只恢复一类公共连接 | 每恢复一根线后运行 `python3 scripts/hwk_pressure_raw_sample.py --port /dev/ttyUSBx --addr 6 --frames 100 --rate 50 --label l1_wire_step` | 对照接线公共条件变化后的 raw payload | 判断是否存在 GND、供电、EN、参考线等拓扑公共条件 | `peak_max` 是否从 0 变非零 | 未开始 | 未判断 | 若某根线恢复后非零，根因锁定到该公共条件 |

### 收敛规则

- 若 E5 让 l1 从全 0 变非 0：根因优先锁定为 driver 轮询/读取模式差异。
- 若 E2 非 0、E3 全 0：根因优先锁定为共用拓扑带来的初始化或总线状态副作用。
- 若 raw 采样非 0、ROS topic 全 0：根因锁定在 driver 解析/发布路径。
- 若所有软件对照都全 0，但恢复某条公共线后非 0：根因锁定在硬件拓扑公共条件。
- 采用“强证据即收敛”：一旦单变量实验让 l1 从 0 变非 0，立即围绕该变量分析，不机械跑完整矩阵。
