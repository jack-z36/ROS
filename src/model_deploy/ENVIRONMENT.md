# Model Deploy — 环境依赖

## 运行环境

**不使用 conda 环境**。硬件驱动节点依赖 ROS2 系统包 + 系统 Python（`/usr/bin/python3`）。

> 注意：本机默认 shell 可能激活了 conda `base`（`/home/hit/miniforge3`），其中不含 `pytest`/`rclpy`。
> 运行本包测试与节点请使用系统 Python，或先 `conda deactivate` 再 `source /opt/ros/jazzy/setup.bash`。

### 系统依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| ROS2 Jazzy | `/opt/ros/jazzy/setup.bash` | 系统 apt |
| python3-serial | 夹爪 USB-485 串口通信 | `sudo apt install python3-serial` |
| python3-yaml | 配置文件解析 | `sudo apt install python3-yaml` |
| std_msgs / std_srvs | 话题与急停服务消息 | 随 ROS2 Jazzy |

### 构建方式

从工作空间根目录执行（colcon 会按依赖拓扑先构建 `act_interfaces` 再构建 `elephant_gripper`）：

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select act_interfaces elephant_gripper
source install/setup.bash
```

### 测试

无硬件、无 ROS spin 的纯层/运行时单测（注入 `FakeSerial`）：

```bash
# 用系统 Python 直接跑（推荐；不依赖已 source 的 overlay）
cd src/model_deploy/elephant_gripper && /usr/bin/python3 -m pytest tests -q

# 或经 colcon（需先 build+source）
colcon test --packages-select elephant_gripper
colcon test-result --verbose
```

### 包列表

| 包名 | 路径 | 说明 |
|------|------|------|
| act_interfaces | act_interfaces/ | ACT 硬件接口消息（CommandPermit、HardwareHealth） |
| elephant_gripper | elephant_gripper/ | 大象 myGripper-F100 双夹爪 USB-485 驱动节点 |

### 启动入口

```bash
ros2 launch elephant_gripper elephant_gripper.launch.py
# 覆盖配置：
ros2 launch elephant_gripper elephant_gripper.launch.py config_file:=/abs/path/elephant_gripper.yaml
```

### udev（真机手动应用）

两路 USB-485 适配器很可能同为 CH340（`1a86:7523`），无法靠 VID/PID 区分左右。
使用 `elephant_gripper/config/99-elephant-gripper.rules` 基于 `ID_PATH` 建立稳定符号链接
`/dev/elephant_gripper_left`、`/dev/elephant_gripper_right`（详见规则文件内注释）。
