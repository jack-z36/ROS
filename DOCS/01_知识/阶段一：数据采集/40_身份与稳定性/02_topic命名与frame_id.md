# topic 命名与 frame_id

本页记录阶段一的 topic 命名规范和 frame_id 实例，以及背后的稳定性约定。

## 定位

本页回答：topic 怎么命名的？frame_id 有哪些实例？哪些命名是"锁定不变"的？

本页是各模态命名约定的汇总，不涉及身份映射机制本身（见 `01_硬件身份策略.md`）。

## topic 命名空间模型

阶段一三类模态各有清晰的命名空间结构：

### 触觉（pressure）

```text
/pressure/{hand}/{gripper}
       │       │       │
       │       │       └─ gripper_1 或 gripper_2（逻辑夹爪名）
       │       └─ left_hand 或 right_hand（逻辑手名）
       └─ 固定前缀
```

实例：`/pressure/left_hand/gripper_1`、`/pressure/right_hand/gripper_2`

四段结构，语义完全自描述。命名中的 `left/right` 和 `gripper_1/2` 是**逻辑身份**，由 `hardware_identity_map.yaml` 根据 `HWK_CHIP_UID` 决定，不是物理串口位置。

### 相机（gopro）

```text
/gopro_{left,right}/image_raw
/gopro_{left,right}/camera_info
```

左右两路相机是两个独立的 `v4l2_camera_node` 实例，通过 namespace 区分。

### 位姿（baton_mini）

```text
/baton_mini_{left,right}/{imu,odometry,fast_odom,image_left,image_right}
```

外层 `baton_mini_{left,right}` 是左右两台设备；内层 `image_{left,right}` 是单台设备的双目左右摄像头。

## frame_id 实例

### 触觉

```text
{frame_id_prefix}/{hand}/{gripper}
```

默认值：`pressure_sensor/left_hand/gripper_1`

- `frame_id_prefix` 默认 `pressure_sensor`，可在配置中修改。
- 若身份映射表（`hardware_identity_map.yaml`）的 target 显式指定了 `frame_id`，则优先用映射值。

### 相机

```text
gopro_{left,right}_optical_frame
```

- 即 `gopro_left_optical_frame`、`gopro_right_optical_frame`。
- 由 `all_sensor_nodes.yaml` 的 `gopro.{left,right}.frame_id` 配置。
- launch 参数 `frame_id` 默认值是 `camera_optical_frame`，但生产配置覆盖为带左右前缀的形式。

### 位姿

Baton Mini 发布的 `nav_msgs/Odometry` 含 `child_frame_id`，表示位姿参考坐标系。具体 frame_id 值由设备固件和 SDK 决定。

## 逻辑身份 vs 物理 UID

这是理解阶段一命名的关键：

| 概念 | 含义 | 稳定性 |
|---|---|---|
| `PressureFrame.hand` (`left_hand`/`right_hand`) | 逻辑手名，由身份映射决定 | 稳定（UID 不变则不变） |
| `PressureFrame.gripper` (`gripper_1`/`gripper_2`) | 逻辑夹爪名，由身份映射决定 | 稳定（UID 不变则不变） |
| `device_addr` | HWK 协议设备地址（0..15） | 可能变（取决于硬件配置） |
| `HWK_CHIP_UID` | 芯片唯一 ID | 永久稳定（硬件级） |
| 串口号 `/dev/ttyUSB0` | 操作系统枚举顺序 | 易漂移（重启后可能变） |

推论：**读取触觉数据时，应以 `hand`/`gripper` 逻辑身份为准，不应以 device_addr 或串口号为准。**

## topic 名稳定性约定

阶段一对 topic 名的稳定性有明确约定：

| 模态 | 稳定性锚点 | 可变项 | 不可变项 |
|---|---|---|---|
| 触觉 | HWK_CHIP_UID → 映射表 | 物理串口位置 | topic 名（UID 不变则不变） |
| 相机 | topic 名锁定 `gopro` | **相机本体可替换** | **topic 名固定 `/gopro_*/image_raw` 不变** |
| 位姿 | 固定 IP + namespace | 无 | topic 名固定 |

### 相机 topic 名锁定的含义

相机本体可替换（GoPro → 工业相机或其它），但 **topic 名始终是 `/gopro_*/image_raw`**：

- 更换相机只需调整 `video_device`、`pixel_format`、`output_encoding` 等接入参数。
- 下游（Octopus 显示、raw MCAP 录制、阶段二清洗）对 `/gopro_*/image_raw` 的依赖保持稳定，无需同步改名。
- 这是阶段一的明确设计决策，`gopro` 已成为"图像 topic"的语义标签，不再特指 GoPro 品牌。

## 左右对称性

三类模态都遵循 `left`/`right` 对称命名：

- 触觉：`left_hand`/`right_hand`
- 相机：`gopro_left`/`gopro_right`
- 位姿：`baton_mini_left`/`baton_mini_right`

这种对称性使得下游代码可以用循环处理左右两路数据，无需特判。

## 详细内容

- 触觉命名推断：`src/data_collection/hwk_pressure_driver/hwk_pressure_driver/config.py`（`_infer_hand_gripper_from_topic`）
- 相机 frame_id 配置：`config/all_sensor_nodes.yaml`（`gopro.left/right.frame_id`）
- Baton topic 参数：`src/data_collection/baton_mini_sdk_demo/launch/baton_mini.launch.py`
- 身份映射机制：`01_硬件身份策略.md`
- 各模态契约：`20_传感器模态语义/`
