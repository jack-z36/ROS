# ROS2 相机节点与 Topic 学习笔记

更新时间：2026-04-27

## 1. 这次对话的提问拓扑

```text
一键启动脚本为什么像黑盒？
├── 一键启动脚本的整体原理
│   ├── start_all_sensor.sh 做环境加载、预检、启动、检查、停止
│   ├── all_sensor_nodes.launch.py 读取 YAML 并启动各子节点
│   └── all_sensor_nodes.yaml 控制设备、topic 名称和启停
│
├── GoPro 节点的内在机理
│   ├── GoPro 本身不是 ROS 设备，只输出 HDMI 视频
│   ├── 采集卡把 HDMI 变成 Linux 视频设备
│   └── v4l2_camera_node 读取采集卡并直接发布 ROS Image
│
├── 视频数据流和格式变化
│   ├── 采集卡输出 YUYV 1920x1080 视频帧
│   ├── v4l2_camera_node 可转换为 rgb8
│   └── ROS Image 消息增加时间戳、宽高、编码、像素数据等字段
│
├── ROS2 topic 和消息类型
│   ├── topic 名字是通信通道
│   ├── topic 数据类型规定消息结构
│   ├── 消息类型由 .msg 文件定义
│   └── 发布者节点代码选择发布哪种消息类型
│
└── GoPro 和 Baton Mini 的差异
    ├── GoPro：通用 V4L2 驱动直接发布到公开 topic
    └── Baton Mini：SDK 节点本身按配置选择采集和发布
```

## 2. 一键启动脚本的角色

当前一键启动不是简单地“执行四条命令”，而是分层完成：

```text
start_all_sensor.sh
  -> launch/all_sensor_nodes.launch.py
    -> Baton Mini 子 launch
    -> GoPro 子 launch
    -> 压力传感器相关节点
```

`start_all_sensor.sh` 主要负责：

- 加载 ROS2 和工作区环境。
- 读取 `config/all_sensor_nodes.yaml`。
- 启动前检查设备状态。
- 启动总 launch。
- 启动后检查节点和 topic 是否出现。
- 失败时清理已启动节点。

`config/all_sensor_nodes.yaml` 主要负责：

- 控制哪些设备启用。
- 控制 topic 是否发布。
- 控制 topic 名称。
- 记录设备 IP、视频设备路径、节点名等参数。

## 3. GoPro 数据链路

GoPro 链路可以这样理解：

```text
GoPro 相机
  -> HDMI 视频输出
  -> USB/HDMI 采集卡
  -> Linux V4L2 视频设备
  -> v4l2_camera_node
  -> 公开 ROS topic（如 /gopro_right/image_raw）
```

GoPro 本身不懂 ROS。它只负责输出视频画面。采集卡把 HDMI 信号变成 Linux 能读取的视频设备，例如：

```text
/dev/video4
/dev/v4l/by-path/...
```

当前项目更推荐使用 `/dev/v4l/by-path/...`，因为它比 `/dev/video4` 这种编号更稳定。

## 4. Linux 视频设备是什么

Linux 视频设备可以理解成 Linux 给摄像头或采集卡开的一个“设备入口”。

程序打开这个入口：

```text
/dev/v4l/by-path/...
```

Linux 内核会通过驱动去读取采集卡中的视频帧。

这类接口叫 V4L2，意思是 Video4Linux2。`v4l2_camera_node` 就是 ROS2 中用来读取 V4L2 视频设备的节点。

## 5. 采集卡原始数据格式

当前日志中 GoPro 采集卡输出格式是：

```text
YUYV @ 1920x1080
```

意思是：

- 每帧图像宽 1920。
- 每帧图像高 1080。
- 像素格式是 YUYV。

YUYV 的字节大概长这样：

```text
Y0 U0 Y1 V0   Y2 U1 Y3 V1   ...
```

每 4 个字节表示 2 个像素：

```text
Y0 / Y1 表示两个像素的亮度
U0 / V0 表示两个像素共用的颜色信息
```

它不是 RGB，而是视频采集常用的 YUV 类格式。

## 6. v4l2_camera_node 的核心功能

`v4l2_camera_node` 的核心功能不是单纯做格式转换，而是：

```text
读取 Linux 视频设备中的视频帧
  -> 按配置解析图像尺寸和格式
  -> 必要时做编码转换
  -> 包装成 ROS2 标准图像消息
  -> 发布到 ROS topic
```

当前配置中有：

```yaml
pixel_format: "YUYV"
output_encoding: "rgb8"
```

所以它会做：

```text
YUYV / yuv422_yuy2
  -> rgb8
```

如果将输出编码改成兼容 YUV 的格式，可能减少或避免转换。但 topic 类型通常仍然是：

```text
sensor_msgs/msg/Image
```

## 7. ROS Image 消息是什么

GoPro 的公开视频 topic 是：

```text
/gopro_right/image_raw
/gopro_left/image_raw
```

消息类型是：

```text
sensor_msgs/msg/Image
```

它不是只有像素数据，还包含解释这帧图像所需的元信息：

```text
header.stamp     采集时间
header.frame_id  相机坐标系
height           图像高度
width            图像宽度
encoding         像素编码，例如 rgb8
step             每一行占多少字节
data             真正的图像像素字节
```

可以理解为：

```text
裸图像字节 + 说明书 = ROS Image 消息
```

## 8. image_raw 和 camera_info 的含义

GoPro 驱动常见两个 topic：

```text
image_raw
camera_info
```

`image_raw` 是真正的视频帧：

```text
类型：sensor_msgs/msg/Image
内容：每一帧图像的时间戳、尺寸、编码和像素数据
```

`camera_info` 是相机标定信息：

```text
类型：sensor_msgs/msg/CameraInfo
内容：内参、畸变参数、投影矩阵等
```

简单区别：

```text
image_raw   给图像本身
camera_info 说明这台相机如何成像
```

当前项目默认只公开 GoPro 的：

```text
/gopro_right/image_raw
/gopro_left/image_raw
```

`camera_info` 默认关闭，只有后续算法需要相机标定参数时再开启。

## 9. 话题命名与发布

GoPro 当前设计里，`v4l2_camera_node` 直接发布到公开命名空间下的 topic，例如：

```text
/gopro_right/image_raw
/gopro_right/camera_info
```

v4l2_camera_node 的命名空间和话题名通过 launch 参数控制：

- `camera_namespace`：控制节点所在命名空间（如 `gopro_right`）
- `image_raw_topic`：控制图像话题名（默认 `image_raw`）
- `camera_info_topic`：控制相机信息话题名（默认 `camera_info`）
- `publish_camera_info`：控制是否发布 camera_info（默认 `true`）

早期版本曾使用 `image_topic_relay` 中转节点，后因帧率瓶颈问题已移除。

## 10. ROS2 topic 数据类型

ROS2 topic 数据类型可以理解为：

```text
这个 topic 上每条消息的固定格式
```

例如：

```text
/gopro_right/image_raw
类型：sensor_msgs/msg/Image

/baton_mini_right/odometry
类型：nav_msgs/msg/Odometry

/baton_mini_right/imu
类型：sensor_msgs/msg/Imu
```

topic 名字只是通信通道。数据类型规定这个通道里每条消息有哪些字段。

## 11. 消息类型如何定义

ROS2 消息类型由 `.msg` 文件定义。

例如 `sensor_msgs/msg/Image` 的定义可以通过命令查看：

```bash
ros2 interface show sensor_msgs/msg/Image
```

常用查表命令：

```bash
ros2 topic info /gopro_right/image_raw
ros2 interface show sensor_msgs/msg/Image
ros2 interface show nav_msgs/msg/Odometry
ros2 interface show sensor_msgs/msg/Imu
ros2 interface show sensor_msgs/msg/CameraInfo
```

完整理解流程：

```text
先查 topic 是什么类型
  -> ros2 topic info <topic名>

再查这个类型有哪些字段
  -> ros2 interface show <消息类型>
```

发布者节点在代码里选择消息类型，例如概念上：

```cpp
create_publisher<sensor_msgs::msg::Image>("image_raw", 10)
```

这表示：

```text
image_raw 这个 topic 发布 sensor_msgs/msg/Image 类型
```

因此，YAML 通常只能改 topic 名字和启停，不能直接改变 topic 数据类型。

## 12. 如何修改发布内容

配置文件能改：

```text
topic 是否发布
topic 名字
部分节点参数
```

配置文件通常不能直接改：

```text
topic 的 ROS 消息类型
```

如果要把一种类型变成另一种类型，推荐新增转换节点：

```text
订阅 /baton_mini_right/odometry
类型 nav_msgs/msg/Odometry

发布 /baton_mini_right/pose
类型 geometry_msgs/msg/PoseStamped
```

这样原始驱动不动，只增加一个“翻译器”，风险更低。

## 13. GoPro 和 Baton Mini 的关键差异

GoPro 当前是：

```text
通用 v4l2_camera_node
  -> 通过 launch 参数控制命名空间和话题名
  -> 直接发布到公开 topic
```

Baton Mini 当前是：

```text
baton_mini SDK 节点
  -> 根据配置直接决定采集和发布哪些 topic
```

两者的共同点：

- 都通过配置文件控制话题名称和启停
- 都直接发布到公开命名空间，不经过中转节点

Baton Mini 的额外能力：

- Baton Mini 节点代码已经支持 `publish_imu`、`publish_odometry`、`publish_fast_odom`、`publish_image_left`、`publish_image_right` 等开关。
- 未启用的 publisher 不会创建。
- 对 IMU、fast odom、图像等数据流，还会尽量关闭设备侧接收。

## 14. 当前项目默认公开的相机 topic

当前默认重点采集 4 个相机 topic：

```text
/baton_mini_right/odometry
/baton_mini_left/odometry
/gopro_right/image_raw
/gopro_left/image_raw
```

含义：

```text
Baton Mini odometry：VIO 位姿数据，nav_msgs/msg/Odometry
GoPro image_raw：视频帧数据，sensor_msgs/msg/Image
```

这些 topic 是 Octopus 后续采集和写入 MCAP 的核心输入之一。

## 15. 一句话总览

```text
GoPro 负责输出 HDMI 画面，采集卡把画面变成 Linux 视频设备，
v4l2_camera_node 把视频帧变成 ROS Image 并直接发布到公开 topic。

Baton Mini 通过 SDK 和设备通信，
节点本身按配置选择发布 odometry、imu、图像等 topic。

ROS2 topic 的数据类型由 .msg 定义和发布者代码决定，
YAML 主要控制 topic 名称、启停和部分运行参数。
```
