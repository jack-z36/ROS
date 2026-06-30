# start_all_sensor.sh 一键启动脚本的启动逻辑

以**当前代码**为准，完整拆解 `start_all_sensor.sh` 从执行到 GoPro 相机节点成功发布话题的每一层条件。Baton Mini 和 Pressure 传感器仅做简要对照，不做逐层展开。

---

## 零、脚本总流程概览

```
start_all_sensor.sh
  │
  ├─ 1. 编译工作区 (colcon build)
  ├─ 2. source ROS + workspace setup
  ├─ 3. 设 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
  ├─ 4. ros2 daemon stop
  │
  ├─ 5. all_sensor_status.py preflight     ← 启动前检查
  │     ├─ hardware_identity_scan.py validate   ← 条件组 A
  │     └─ 逐传感器设备检查                     ← 条件组 B
  │
  ├─ 6. ros2 launch all_sensor_nodes.launch.py  ← 真正启动
  │     ├─ _apply_identity_resolved()           ← 条件组 C
  │     └─ _gopro_include() → gopro_pose_record.launch.py  ← 条件组 D
  │
  └─ 7. sleep 20s → all_sensor_status.py postlaunch  ← 启动后验证 (条件组 E)
```

---

## 一、启动前检查（preflight）

`start_all_sensor.sh:109` 调用 `all_sensor_status.py preflight`。入口先处理 identity，再做逐设备检查。

### 条件组 A：硬件身份映射校验

`all_sensor_status.py` 在 preflight 模式下，先看 `all_sensor_nodes.yaml` 中 `hardware_identity.enabled` 是否为 true（当前为 true），然后调用：

```bash
python3 hardware_identity_scan.py validate \
  --map config/hardware_identity_map.yaml \
  --write-resolved log/start_all_sensor/hardware_identity_resolved.yaml
```

`hardware_identity_scan.py validate` 的执行逻辑（`hardware_identity_scan.py:365`）：

1. 实时扫描系统上所有 serial 设备（`/dev/ttyUSB*`、`/dev/ttyACM*`）和 video 设备（`/dev/video*`），通过 `udevadm info` 收集每个设备的属性
2. 遍历 `hardware_identity_map.yaml` 中 `pressure` 和 `gopro` 两个 group 的每条条目
3. 对每条条目，用其 `match` 字段在扫描结果中匹配设备

**匹配规则**（`device_matches()`，`:308`）：

- `match` 中的每个 key 都必须在设备属性中找到，且值完全相等
- `DEVLINKS` 特殊处理：可以是单个字符串或列表，要求设备的 devlinks 包含所有指定链接
- `HWK_PACKAGE_ID` 跳过不参与匹配
- `DEVNAME` 特殊处理：用设备 path 而非 properties

**校验规则**（`validate_mapping()`，`:365`）：

| 检查项 | 判定 | 后果 |
|--------|------|------|
| 条目 `required=false` | 跳过不校验 | 不影响启动 |
| `match` 字段为空 | FAIL | 硬失败 |
| 匹配到 0 台设备 | FAIL | 硬失败 |
| 匹配到 ≥2 台设备 | FAIL（match is not unique） | 硬失败 |
| 两台逻辑设备解析到同一 realpath | FAIL | 硬失败 |
| match 仅含 `ID_PATH` 等路径字段 | WARN（path/topology fallback only） | 不阻断 |
| match 无 `ID_SERIAL` 等强身份字段 | WARN（no serial-like identity key） | 不阻断 |

**当前状态**：
- `hardware_identity_map.yaml` 中**只有 pressure 的 4 条（l1/l2/r1/r2），没有 gopro 条目**
- pressure 的 4 条靠 `HWK_CHIP_UID`（烧录在芯片里的唯一ID）互相区分，每条能唯一匹配到一台物理设备
- 如果任意一条 pressure 匹配失败 → **整体返回 exit code 1，start_all_sensor.sh 停止启动**（不会进到 launch 阶段）
- 如果全部 pressure 通过 → 生成 `hardware_identity_resolved.yaml`，继续

> GoPro 在此阶段**不做身份校验**，因为 map 里没有它的条目。

### 条件组 B：逐传感器设备检查

identity 校验通过后，`all_sensor_status.py` 遍历 `expected_sensors()` 返回的传感器列表，对每个 gopro side（`all_sensor_nodes.yaml` 中 `enabled: true` 且 `image_raw` topic 启用的）逐项检查（`:386-410`）：

| # | 检查项 | 怎么判 | 失败级别 |
|---|--------|--------|----------|
| B1 | `video_device` 路径存在 | `Path(device).exists()` | **硬失败，停止启动** |
| B2 | `v4l2-ctl` 已安装 | `shutil.which("v4l2-ctl")` | **硬失败，停止启动** |
| B3 | 当前用户可读写设备 | `os.access(device, R_OK\|W_OK)` | **硬失败，停止启动** |
| B4 | 设备是 Video Capture | `v4l2-ctl --device=<dev> --all` 输出含 `Video Capture` | **硬失败，停止启动** |
| B5 | 设备未被占用 | `fuser -v <device>` | **WARN 级别，不阻断启动** |

**`video_device` 的取值优先级**（`apply_identity_resolved()`，`:96-104`）：

1. 如果 `hardware_identity_resolved.yaml` 中 `gopro.<side>.device` 存在 → 用 resolved 里的值覆盖
2. 否则 → 用 `all_sensor_nodes.yaml` 中 `gopro.<side>.video_device` 的硬编码值

**当前状态**：resolved 里 `gopro: {}`（空），所以实际生效的 `video_device` 就是 `all_sensor_nodes.yaml` 的硬编码：

```yaml
gopro:
  right:
    video_device: "/dev/v4l/by-path/pci-0000:00:0d.0-usb-0:3.4.1.1:1.0-video-index0"
  left:
    video_device: "/dev/v4l/by-path/pci-0000:00:0d.0-usb-0:3.4.4.3:1.0-video-index0"
```

---

## 二、启动阶段（launch）

preflight 全部通过后，`start_all_sensor.sh:116` 执行：

```bash
ros2 launch launch/all_sensor_nodes.launch.py \
  config_file:=config/all_sensor_nodes.yaml \
  identity_resolved_file:=log/start_all_sensor/hardware_identity_resolved.yaml
```

### 条件组 C：launch 时 identity 覆盖

`all_sensor_nodes.launch.py` 的 `_load_nodes()` 函数（`:178`）在构造启动动作之前：

1. 加载 `all_sensor_nodes.yaml`
2. 加载 `hardware_identity_resolved.yaml`
3. 调用 `_apply_identity_resolved(config, resolved)`（`:171-175`）：

```python
def _apply_identity_resolved(config, resolved):
    for side, resolved_cfg in (resolved.get("gopro") or {}).items():
        device = resolved_cfg.get("device")
        if device and side in (config.get("gopro") or {}):
            config["gopro"][side]["video_device"] = device
```

**当前状态**：resolved 里 `gopro: {}`，所以不覆盖任何东西。`video_device` 保持 `all_sensor_nodes.yaml` 的硬编码值不变。

### 条件组 D：单路相机 launch

对每个 enabled 且 image_raw topic 启用的 gopro side，`_gopro_include()`（`:113`）构造一个 `GroupAction(scoped=True, forwarding=False)` 包住 `gopro_pose_record.launch.py` 的 `IncludeLaunchDescription`。

**隔离机制**：
- `scoped=True`：每个 left/right 实例获得独立的 launch 上下文
- `forwarding=False`：阻止左右两路的参数互相串扰

传递的参数（从 `all_sensor_nodes.yaml` 的 per-side 配置提取）：

| 参数 | 来源 | 当前 right 值 | 当前 left 值 |
|------|------|---------------|--------------|
| `video_device` | `gopro.<side>.video_device` | `/dev/v4l/by-path/...0:3.4.1.1...` | `/dev/v4l/by-path/...0:3.4.4.3...` |
| `frame_rate` | `gopro.<side>.frame_rate` | `30` | `30` |
| `pixel_format` | `gopro.<side>.pixel_format` | `YUYV` | `YUYV` |
| `output_encoding` | `gopro.<side>.output_encoding` | `rgb8` | `rgb8` |
| `camera_namespace` | `gopro.<side>.namespace` | `gopro_right` | `gopro_left` |
| `node_name` | `gopro.<side>.node_name` | `gopro_right_camera` | `gopro_left_camera` |
| `frame_id` | `gopro.<side>.frame_id` | `gopro_right_optical_frame` | `gopro_left_optical_frame` |

`gopro_pose_record.launch.py` 每路执行两步（`:29-73`）：

**D1**：`v4l2-ctl -d <video_device> --set-parm <frame_rate>`
- 对当前路径设帧率
- 该命令**必须成功退出**
- 如果失败（设备不存在、无权限、不支持此操作等）→ `OnProcessExit` 不会触发 → 节点不会启动

**D2**：在 D1 成功退出后，通过 `RegisterEventHandler(OnProcessExit(...))` 触发起 `v4l2_camera_node`：
- 参数来源：`gopro_camera.yaml` 的基线参数 + `_launch_setup()` 中 launch 传参覆盖
- `use_v4l2_buffer_timestamps: true`
- `use_sensor_data_qos: true`（BEST_EFFORT, depth=5）
- `publish_camera_info: false`
- topic remap：`image_raw` → `image_raw`（保持默认名）

---

## 三、启动后验证（postlaunch）

`start_all_sensor.sh:146` sleep 20 秒后，调用 `all_sensor_status.py postlaunch`。

### 条件组 E：节点和 topic 验证

| # | 检查项 | 怎么判 | 失败级别 |
|---|--------|--------|----------|
| E1 | ROS node 出现 | `ros2 node list` 包含完整 node 名 | **FAIL** |
| E2 | topic 出现 | `ros2 topic list` 包含预期 topic | **FAIL** |

对 gopro left/right，预期的 node 和 topic：

| side | node | topic |
|------|------|-------|
| right | `/gopro_right/gopro_right_camera` | `/gopro_right/image_raw` |
| left | `/gopro_left/gopro_left_camera` | `/gopro_left/image_raw` |

**失败处理**（`:163-173`）：
- `STOP_ON_FAILURE=1`（默认）→ 杀掉 launch 进程，退出
- `STOP_ON_FAILURE=0` → 仅打印失败，不杀进程

---

## 四、GoPro 相机启动的必要条件总结

把上面所有条件组串起来，**当前代码下**两台 GoPro 相机要正常启动，需要满足：

```
条件链（AND 关系，任意一条失败即停止）：

A: hardware_identity_map.yaml 中所有 required 条目通过校验
    → 当前仅含 pressure，gopro 无条目
    → pressure 的 4 个 HWK_CHIP_UID 各自唯一匹配

B1: video_device 路径在文件系统上存在
    → /dev/v4l/by-path/pci-0000:00:0d.0-usb-0:3.4.1.1:1.0-video-index0
    → /dev/v4l/by-path/pci-0000:00:0d.0-usb-0:3.4.4.3:1.0-video-index0
    → 一旦换 USB 口，by-path 改变 → B1 失败 → 停止启动

B2: v4l2-ctl 已安装

B3: 当前用户对上述两个设备有读写权限

B4: 两个设备都是 Video Capture（非 metadata 节点）

C: （当前为空操作— resolved 中 gopro 为空）

D1: v4l2-ctl --set-parm 对两个设备均成功退出

E1: v4l2_camera_node 两个实例都出现在 ros2 node list 中

E2: /gopro_left/image_raw 和 /gopro_right/image_raw 两个 topic 都出现
```

**根本原因**：当前 gopro 没有走 identity map，直接硬编码 by-path。换口 → by-path 变 → B1 失败 → 启动失败。这是当前相机绑定方式最脆弱的环节。

---

## 五、Baton Mini 和 Pressure 的条件链（简要对照）

### Baton Mini

不走 identity 校验。preflight 检查网络可达性和 TCP 端口：

| 条件 | 怎么判 | 失败级别 |
|------|--------|----------|
| 本机绑定了 local_ip | `ip route get <server_ip>` 返回的网卡上有对应 IP | 硬失败 |
| 设备 IP 可 ping 通 | `ping -c 1 -W 1 <server_ip>` | WARN（设备可能禁 ICMP） |
| 设备 TCP 端口已开放 | 逐个尝试 TCP 连接 8000/9994/9996/9997/9998 | 硬失败 |

### Pressure

**必须在 `hardware_identity_map.yaml` 中有 match 条目，且通过 A 组校验。** 当前 4 条（l1/l2/r1/r2）靠 `HWK_CHIP_UID`（芯片唯一 ID）区分，通过 `hwk_query_device_info.py` 的私有协议查询获得。preflight 阶段还额外检查：

- 触觉配置文件存在
- 每个串口存在且可读写

---

## 六、相关文件索引

| 文件 | 作用 |
|------|------|
| [start_all_sensor.sh](../../start_all_sensor.sh) | 一键启动脚本入口 |
| [scripts/all_sensor_status.py](../../scripts/all_sensor_status.py) | preflight / postlaunch 检查逻辑 |
| [scripts/hardware_identity_scan.py](../../scripts/hardware_identity_scan.py) | 硬件扫描 + identity 校验引擎 |
| [config/all_sensor_nodes.yaml](../../config/all_sensor_nodes.yaml) | 传感器配置（设备路径、命名空间、话题） |
| [config/hardware_identity_map.yaml](../../config/hardware_identity_map.yaml) | 硬件身份映射表（match → target） |
| [launch/all_sensor_nodes.launch.py](../../launch/all_sensor_nodes.launch.py) | 总 launch 文件（编排各路传感器） |
| [src/data_collection/gopro_camera_launch/launch/gopro_pose_record.launch.py](../../src/data_collection/gopro_camera_launch/launch/gopro_pose_record.launch.py) | 单路 GoPro 相机 launch |
| [src/data_collection/gopro_camera_launch/config/gopro_camera.yaml](../../src/data_collection/gopro_camera_launch/config/gopro_camera.yaml) | v4l2_camera_node 基线参数 |
| [log/start_all_sensor/hardware_identity_resolved.yaml](../../log/start_all_sensor/hardware_identity_resolved.yaml) | preflight 生成的解析结果 |
