# act_system — ACT 系统集成包（一键启动）

model_deploy 栈的系统集成包，只做**启动编排**：提供总 launch 与一键启动脚本，
一条命令拉起 ACT 运行所需的全部节点。本包不含 SDK、模型推理或 deadman 逻辑。

## 一键启动

在已配置 ROS 环境的终端中执行（无需手动 source，脚本内部自动完成）：

```bash
bash src/model_deploy/act_system/scripts/start_act_system.sh
```

脚本流程：

1. source `/opt/ros/jazzy/setup.bash`（`ROS_SETUP` 可覆盖）
2. 检查 `act_interfaces / rm65_dual_arm / elephant_gripper / dual_fisheye_camera / act_system`
   是否已编译，缺失的包自动 `colcon build --packages-select`（`AUTO_BUILD=0` 跳过）
3. source `install/setup.bash` 后后台执行 `ros2 launch act_system act_system.launch.py`，
   输出 tee 到 `log/act_system/<时间戳>.log`
4. 等待 `STARTUP_WAIT`（默认 15s）后用 `ros2 node list` 逐组件核对并打印成败摘要：

```
===== act_system 组件启动核对 =====
OK   RM65 双臂节点
OK   大象夹爪节点
FAIL 双鱼眼相机节点（缺少节点: /camera_health_node）
FAIL ACT 部署节点（缺少节点: /act_deploy_node）
===================================
```

5. `Ctrl+C` 停止全部节点（对 launch 进程组发 INT/TERM 优雅退出）

## 启动的组件

| 组件 | 来源 | 节点 |
|---|---|---|
| RM65 双臂 | `rm65_dual_arm/launch/rm65_dual_arm.launch.py` | `/rm65_dual_arm_node` |
| 大象夹爪 | `elephant_gripper/launch/elephant_gripper.launch.py` | `/elephant_gripper_node` |
| 双鱼眼相机 | `dual_fisheye_camera/launch/dual_fisheye_camera.launch.py` | `/dual_fisheye_{left,right}/{left,right}_fisheye_camera`、`/camera_health_node` |
| ACT 部署节点 | `ExecuteProcess: python3 -m model_deploy.act.ui.act_deploy_node` | `/act_deploy_node` |

`/act_deploy_node` 自己发布 20 Hz `/act/command/permit` 心跳；RM65 或夹爪
收不到新鲜许可时保持 fail-closed，不执行运动。

## 运行模式

ACT 只接受两种模式：

| `runtime.mode` | 启动开关 | 行为 |
|---|---|---|
| `dry-run` | `ENABLE_COMMAND_OUTPUT=0` | 真实观测、真实模型和完整安全检查；只发布 policy/status/metrics，不发布四路硬件命令 |
| `real-run` | `ENABLE_COMMAND_OUTPUT=1` | 安全检查和 permit 均通过后，连续发布双臂与双夹爪目标 |

模式与启动开关不一致时，ACT 在加载模型前直接拒绝启动。`real-run` 还会在
启动阶段有界等待双驱动健康、permit/四路命令订阅者和双急停服务；任一缺失
都会 fail-fast。

## 参数

脚本环境变量：

| 变量 | 默认 | 说明 |
|---|---|---|
| `ROS_SETUP` | `/opt/ros/jazzy/setup.bash` | ROS 环境 setup 文件 |
| `AUTO_BUILD` | `1` | 缺包时自动编译；`0` 只报错并提示手动命令 |
| `STARTUP_WAIT` | `15` | launch 后等待秒数再核对组件 |
| `ACT_CONFIG` | 空（用 launch 默认值） | ACT deploy.yaml 路径 |
| `ENABLE_COMMAND_OUTPUT` | `0` | 只接受 `0/1`；`1` 仅能与配置 `mode: real-run` 搭配 |

launch 参数（也可直接 `ros2 launch act_system act_system.launch.py` 使用）：

| 参数 | 默认 | 说明 |
|---|---|---|
| `act_config` | `src/model_deploy/act/config_files/deploy.yaml` | ACT 部署配置 |
| `enable_command_output` | `false` | ACT 真实命令输出总开关（fail-closed） |

## 真机前置条件

- 机械臂、夹爪、相机驱动已按实际部署条件连接/配置。
- ACT 节点真正推理成功需要先在 deploy.yaml 里把 `bundle.bundle_dir`
  配成真实模型 bundle 路径。
- `real-run` 前确认物理急停可用；双臂 frame 必须为
  `left_arm_base/right_arm_base`，夹爪目标域必须为 normalized `[0,1]`。

## 故障排查

- 核对表出现 FAIL 时，脚本会自动 tail 最近 launch 日志；完整日志在
  `log/act_system/<时间戳>.log`。
- 任一组件进程中途退出时，launch 内会打印
  `[act_system] 组件进程退出: <进程名> (returncode=N)`。
- 相机设备路径必须用 `/dev/v4l/by-path/...` 或 `/dev/v4l/by-id/...`
  （见 dual_fisheye_camera 包配置）。
- 机器上装有 conda 时，CMake FindPython3 会按版本优先选中 conda 的更高版本
  Python，导致 act_interfaces 的 C 扩展与系统 Python 不匹配
  （`ImportError: libpython3.13.so` / `UnsupportedTypeSupport`）。脚本已用
  `-DPython3_EXECUTABLE` 钉死系统 Python；若仍遇到，删除
  `build/act_interfaces` 与 `install/act_interfaces` 后重跑脚本即可。

## 验证边界

`dry-run` 可用于验证真实观测、模型推理、SafetyGuard、status 和 metrics，
且四路硬件 command 必须为零。ROS `publish` 成功不等于真机动作成功；
`real-run` 最终验收仍以 TCP/夹爪实测反馈变化、驱动 health 无 fault、急停能
立即撤销 permit 为准。
