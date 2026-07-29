# rm65_dual_arm

RM65 双臂 ROS 2 节点（C++ SDK，**单节点承载双臂所有功能**）。

一句话功能：把左右 RM65 的真实 TCP 状态发布给 ACT，并在人工许可有效时把 ACT 的左右末端目标位姿交给 RM65 执行。

---

## 1. Topic / Service

| 方向 | topic | 类型 | 说明 |
|---|---|---|---|
| 发布 | `/arm/left_tcp_pose` | `geometry_msgs/msg/Pose` | 无 header；坐标系约定 `left_arm_base`（ACT 大脑按 Pose 订阅） |
| 发布 | `/arm/right_tcp_pose` | `geometry_msgs/msg/Pose` | 无 header；坐标系约定 `right_arm_base`（ACT 大脑按 Pose 订阅） |
| 发布 | `/hardware/rm65/health` | `act_interfaces/msg/HardwareHealth` | 左右臂连接/急停/错误码 |
| 订阅 | `/act/command/arm/left_target` | `geometry_msgs/msg/PoseStamped` | frame_id 必须 `left_arm_base` |
| 订阅 | `/act/command/arm/right_target` | `geometry_msgs/msg/PoseStamped` | frame_id 必须 `right_arm_base` |
| 订阅 | `/act/command/permit` | `act_interfaces/msg/CommandPermit` | `allowed==true` 才执行新运动 |
| service | `/hardware/rm65/emergency_stop` | `std_srvs/srv/SetBool` | `true` 停两臂，`false` 恢复 |

launch 默认把 `/arm/{left,right}_tcp_pose` remap 到 `/act/observation/arm/{left,right}_tcp_pose`，让 ACT 零配置订阅。

注意两个方向类型不同：发布 TCP pose 是裸 `Pose`（大脑不读 header）；订阅命令目标仍是 `PoseStamped`（需要 frame_id/时间戳做安全校验）。

---

## 2. 多重闸门（每条目标必须全部通过才下发 `rm_movel`）

1. **permit_guard** — CommandPermit `allowed=true` 且未 stale（fail-closed）
2. **target_validator** — frame_id / finite / quaternion norm / stale
3. **delta_guard**（★核心安全）— 相对当前真实 TCP 位移在 `max_step_xyz_m` / `max_step_angle_rad` 内
4. 急停未激活
5. SDK 已连接

任一失败：不发 `rm_movel`，不伪造 accepted，health 记 reason。

---

## 3. ★ 微小运动安全闸（delta_guard）

直接落实"测试控制指令必须尽可能小、避免大范围运动"的硬性要求。每条目标相对当前真实 TCP 做差，超限即拒。

| 参数 | 默认 | 启动期硬上限 | 含义 |
|---|---|---|---|
| `safety.max_step_xyz_m` | 0.010 (1cm) | 0.05 (5cm) | 单步位移上限 |
| `safety.max_step_angle_rad` | 0.05 (~2.9°) | 0.2 (~11.5°) | 单步角度上限 |

硬上限在节点启动期校验，超过即拒绝启动（fail-fast），防止 YAML 误配成大运动。当前真实 TCP 必须来自 `rm_get_current_arm_state` 读数，不允许假设零位（首次未读到时 `CURRENT_MISSING` 拒绝）。

---

## 4. 构建

### 4.1 vendor SDK（真机部署前必须）

睿尔曼 C/C++ SDK 以 vendor 方式集成。官方 SDK 不提供 find_package/pkg-config。

1. 从官方 RM_API2 仓库 `C++/linux/linux_x86_c++_v1.1.6/` 拷入库文件到本包 `lib/`：
   - `libapi_cpp.so`（旧版叫 libRM_Service.so，导出接口不变）
2. 从官方 SDK `C++/include/` 拷入头文件到 `include/rm65_dual_arm/`：
   - `rm_define.h` / `rm_interface.h` / `rm_interface_global.h` / `rm_service.h` / `rm_version.h`
3. 装库到系统路径：`sudo bash src/model_deploy/rm65_dual_arm/lib/install_libs.sh`

详见 `lib/SDK_VENDOR_README.txt`。`.so` 与 vendor 头文件不提交（见 `.gitignore`）。

### 4.2 编译

```bash
# 纯逻辑层可在 SDK 缺失时单独编译验证（CMake 检测 rm_service.h 存在性）
colcon build --packages-select act_interfaces rm65_dual_arm
source install/setup.bash
```

当 `include/rm65_dual_arm/rm_service.h` 缺失时，节点可执行文件跳过构建，纯逻辑测试照常编译。

### 4.3 测试

```bash
colcon test --packages-select rm65_dual_arm
colcon test-result --all
# 预期：61 tests, 0 errors, 0 failures（pose_conversion/target_validator/delta_guard/permit_guard）
```

测试不依赖真机与 SDK，纯逻辑层全离线验证。

---

## 5. ★ 真机测试规约（强制）

任何连接真机的测试都必须遵守：

1. **物理急停就位** — 测试全程必须有人站在物理急停按钮旁，手不离开。
2. **首次只验证读、不验证写** — 第一次连真机只确认 `/arm/*_tcp_pose` 发布正常、位姿量级正确（手动拖动 10cm，topic 变化约 0.1m），不发任何运动命令。
3. **运动测试从最小指令开始** — 第一个运动指令的位移目标设为**当前 TCP + 1mm 以内**，确认机械臂只做微动。
4. **单臂逐个验证** — 先只连左臂验证，再只连右臂，最后双臂；禁止首次就双臂同时运动。
5. **速度锁低** — `motion.speed_percent` 测试期固定 ≤ 20，确认轨迹无误后再议。
6. **delta_guard 不绕过** — 任何真机测试不得通过改大 `max_step_xyz_m` 绕过闸门；如需调大，必须双人确认 + 物理急停就位，且不能超过启动期硬上限。
7. **急停预演** — 正式运动前先调一次 `ros2 service call /hardware/rm65/emergency_stop std_srvs/srv/SetBool "{data: true}"` 确认能立即停臂。

---

## 6. 启动

```bash
ros2 launch rm65_dual_arm rm65_dual_arm.launch.py
# 关闭 /arm -> /act/observation remap（用 /arm/* 原名）：
#   在 params_file 里把 topics.left_tcp_pose 设回 /arm/left_tcp_pose 等
```

启动期校验失败会直接退出（fail-fast），日志说明原因。

---

## 7. 未验证项 / 真机风险

- **未验证**（需 RM65 硬件在场）：真机连接、TCP 位姿量级、急停真机响应、UDP 主动上报频率、SDK 重连、双臂同步、Jazzy 兼容性。
- **Jazzy 兼容性风险**：官方 ROS2 文档只背书 humble/foxy（Ubuntu 22.04/20.04）；本环境为 ROS2 Jazzy / Ubuntu 24.04，SDK 库版本 v4.3.7，需真机验证。
- **单位陷阱**：睿尔曼 quaternion `[w,x,y,z]` vs ROS `[x,y,z,w]`，`pose_conversion.cpp` 注释写死 + 单测覆盖。
- **SDK 无心跳**：断线重连依赖 -1/-2 返回码 + UDP 断流判断，真机需观察稳定性。
- **UDP 端口冲突**：双臂 UDP 端口必须不同（默认左 8089 / 右 8090），否则数据串流。注意：UDP 端口配置当前在 SDK 层（rm_driver/config），本节点通过 TCP 句柄控制，UDP 端口隔离需在底层 SDK 初始化时区分。

---

## 8. 依赖

- ROS 2 包：`act_interfaces`（本分支同落）、`rclcpp`、`geometry_msgs`、`std_msgs`、`std_srvs`
- 外部：睿尔曼 C/C++ SDK（vendor，见 §4.1）
- 关联契约：`DOCS/03_工程/阶段四：模型部署/01_contracts/rm65_driver_node 命令执行契约.md`、`rm65_driver_node 状态发布契约.md`、`act_interfaces 契约.md`

## 9. 文件结构

```
rm65_dual_arm/
├── package.xml / CMakeLists.txt
├── include/rm65_dual_arm/      # 头文件（含 vendor SDK 头文件，不入库）
│   ├── pose_conversion.hpp     # 位姿转换（纯逻辑）
│   ├── target_validator.hpp    # 目标校验（纯逻辑）
│   ├── delta_guard.hpp         # ★ 微小运动闸（纯逻辑）
│   ├── permit_guard.hpp        # 许可守卫（纯逻辑）
│   ├── rm65_arm.hpp            # 单臂 SDK 封装（依赖 rm_service.h）
│   └── rm65_dual_arm_node.hpp  # 主节点
├── src/                        # 对应 .cpp 实现
├── lib/                        # vendor SDK 库 + install_libs.sh（.so 不入库）
├── config/rm65_dual_arm.yaml   # 默认参数（最保守安全值）
├── launch/rm65_dual_arm.launch.py
├── tests/                      # 4 个 gtest，61 个用例
└── README.md
```
