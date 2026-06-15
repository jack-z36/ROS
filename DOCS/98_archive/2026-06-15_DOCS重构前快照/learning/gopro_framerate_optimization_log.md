# GoPro 帧率优化执行记录

更新时间：2026-04-28

## 问题背景

GoPro 相机通过 UGREEN 4K60Hz 采集卡 + USB 3.0 连接到主机，经 v4l2_camera_node 发布 ROS2 图像话题。初始状态下 Octopus 显示帧率仅 ~12fps，远低于预期的 30fps。

---

## 诊断过程

### 1. 硬件层排除

通过 `lsusb -t`、`v4l2-ctl --list-formats-ext`、`v4l2-ctl --stream-mmap` 逐层排查：

| 检查项 | 结果 |
| ------ | ---- |
| USB 协商速度 | 两张采集卡均 5000M（USB 3.0），非 USB 2.0 回退 |
| 采集卡能力 | YUYV 1080p60、MJPEG 1080p240，硬件能力充足 |
| 直接 V4L2 抓帧 | 1080p60 稳定 59.24fps，720p60 稳定 59.46fps |
| USB 控制器共享 | 两张采集卡在同一 USB 3.0 控制器，但总带宽 20Gbps 充足 |

**结论：硬件和驱动层完全正常，瓶颈在 ROS 层。**

### 2. ROS 层定位

通过 `ps aux` CPU 占用和逐级话题帧率测量，定位到两级瓶颈：

```
60 fps → [v4l2_camera_node: YUYV→RGB8, CPU 109%] → ~38 fps → [Python relay, CPU 26%] → ~18 fps
```

| 环节 | CPU | 输出帧率 | 问题 |
| ---- | --- | -------- | ---- |
| v4l2_camera_node (1080p) | 109%（吃满一个核） | ~38 fps | YUYV→RGB8 逐像素 CPU 转换，单线程 |
| image_topic_relay (Python) | 26% | ~18 fps | 6MB 消息双端 DDS 序列化，Python GIL |

### 3. "降分辨率无效"的真相

用户曾将 image_size 改为 720p 但帧率不变。原因是只改了源码未 `colcon build`，install 目录下仍是 1080p 配置，节点实际运行的还是 1080p。改动没有生效。

### 4. 录制时帧率骤降

Octopus 录制 MCAP 时会创建独立的 ROS2 订阅者（McapRecorder 节点）。v4l2_camera_node 默认使用 RELIABLE QoS，每帧需等待所有订阅者 ACK。录制端写磁盘慢 → 反压发布者 → 帧率骤降。

### 5. 录制时显示 FPS 下降的二次定位

2026-04-28 17:08 生成的 MCAP 文件反推结果显示，两路 GoPro 实际都接近 60Hz：

| topic | count | duration | rate |
| --- | ---: | ---: | ---: |
| `/gopro_left/image_raw` | 817 | 13.6046s | 60.05Hz |
| `/gopro_right/image_raw` | 815 | 13.6046s | 59.91Hz |

这说明当前录制器并没有只收到 10fps；相反，它正在按接近 60fps 录制两路 `640x480 rgb8` 图像。Octopus 界面 FPS 和 `ros2 topic hz` 在录制时下降，更可能是显示订阅者和额外测速订阅者受到录制时的 CPU、DDS 传输、Zstandard 压缩与写盘压力影响。

---

## 执行的优化

### 优化 1：删除 Python relay 节点

**改动文件：**

| 文件 | 改动 |
| ---- | ---- |
| `gopro_camera_launch/launch/gopro_pose_record.launch.py` | 删除 relay Node，v4l2_camera_node 直接使用公开命名空间 |
| `launch/all_sensor_nodes.launch.py` | 删除 internal_* 参数传递 |
| `gopro_camera_launch/setup.py` | 删除 image_topic_relay entry_point |
| `gopro_camera_launch/image_topic_relay.py` | 删除源文件 |
| `cleanup_ros_residue.sh` | 更新进程匹配逻辑 |

**效果：** 消除 relay 造成的 53% 帧丢失，预计帧率从 18fps 提升到 ~38fps。

**对 Octopus 无影响：** Octopus 订阅的是最终话题名 `/gopro_left/image_raw` 和 `/gopro_right/image_raw`，v4l2_camera_node 通过 namespace + remapping 直接发布到相同话题名，Octopus 无需改动。

### 优化 2：启用 BEST_EFFORT QoS

在 launch 文件中为 v4l2_camera_node 添加 `use_sensor_data_qos: True`，将发布 QoS 从 RELIABLE 切换为 BEST_EFFORT。

**效果：** 录制时不再因 ACK 等待而反压采集循环。

### 优化 3：降低分辨率到 480p

配置 `image_size: [640, 480]`。

**效果：** 单帧数据从 6MB 降至 0.9MB（RGB8），大幅减少 CPU 转换、DDS 序列化和内存拷贝开销。

### 优化 4：使用 v4l2-ctl 显式设置 30fps

本机安装的 `ros-jazzy-v4l2-camera 0.7.1` 参数文档和本地二进制检查均未发现 `publish_rate` 参数；`publish_rate: 30.0` 不是当前节点的有效锁帧参数。进一步检查发现，本地头文件和二进制字符串里也没有 `time_per_frame` 参数名，因此仅在 YAML 中写 `time_per_frame: [1, 30]` 不能保证当前 `v4l2_camera_node` 真正设置采集卡帧率。

实测 `v4l2-ctl --set-parm=30` 对两张 UGREEN 采集卡有效：

```text
/dev/video4: Frame rate set to 30.000 fps
/dev/video6: Frame rate set to 30.000 fps
```

因此当前 launch 已改为：启动 `v4l2_camera_node` 前先执行 `v4l2-ctl -d <video_device> --set-parm <frame_rate>`，默认 `frame_rate:=30`。

2026-04-28 17:40 补充验证：在总 launch 同时启动左右 GoPro 时，必须保证两次 include 的 launch 参数作用域彼此隔离。当前 `launch/all_sensor_nodes.launch.py` 已为每个 GoPro include 增加 scoped `GroupAction`，`gopro_pose_record.launch.py` 已改用 `OpaqueFunction` 提前解析参数，避免延迟启动的相机节点拿到另一侧 GoPro 的 namespace 或设备路径。

短测 `log/start_all_sensor/20260428_173834.log` 已确认：

| 项目 | 结果 |
| ---- | ---- |
| right GoPro 设备 | `usb-0000:00:0d.0-3.4.1.3` |
| left GoPro 设备 | `usb-0000:00:0d.0-3.4.1.4` |
| right GoPro topic | `/gopro_right/image_raw` 通过 postlaunch 检查 |
| left GoPro topic | `/gopro_left/image_raw` 通过 postlaunch 检查 |
| 驱动帧率设置 | 两路均输出 `Frame rate set to 30.000 fps` |

### 优化 5：降低 FFmpeg 版本要求

Octopus 的 CMakeLists.txt 原本要求 `FFmpeg 7.0`，系统为 6.1.1。改为 `find_package(FFmpeg REQUIRED)` 去掉版本约束。

---

## 当前配置状态

```yaml
# gopro_camera.yaml
image_size: [640, 480]
time_per_frame: [1, 30]      # 保留配置项；实机以 launch 前置 v4l2-ctl 为准
pixel_format: "YUYV"
output_encoding: "rgb8"
frame_rate: 30               # all_sensor_nodes.yaml 中配置，传给 launch 的 v4l2-ctl --set-parm
use_sensor_data_qos: True     # launch 中保留；实际 QoS 仍需用 topic info -v 实测确认
```

---

## 待验证项

- [x] rebuild `gopro_camera_launch` 并确认安装目录中的 GoPro 配置已同步
- [x] 验证 `v4l2-ctl --set-parm=30` 可将两张采集卡设为 30fps
- [x] 重启后确认 relay 节点不再存在
- [x] 总 launch 同时启动左右 GoPro 时，确认 right/left 不再串 namespace 或 video device
- [ ] rebuild + 重启后确认 `/gopro_right/image_raw` 和 `/gopro_left/image_raw` 的 MCAP 计数约为 30Hz
- [ ] 确认 Octopus 显示帧率在录制前后不再明显从约 40fps 掉到约 10fps
- [ ] 确认 QoS 已切换为 BEST_EFFORT（`ros2 topic info /gopro_right/image_raw -v`）

---

## 相关文档

- [帧率影响微元分析](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/learning/gopro_framerate_factors.md)
- [ROS2 相机节点学习笔记](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/learning/ros2_camera_topic_notes.md)
- [GoPro 包架构文档](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/gopro_camera_launch/ARCHITECTURE.md)
