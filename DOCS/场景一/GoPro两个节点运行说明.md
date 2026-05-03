# GoPro 两个节点运行说明

## 1. 文档目的

本文记录场景一中两个 GoPro ROS2 节点的实际运行方式。

目标是说明：

- GoPro right 节点如何启动；
- GoPro left 节点如何启动；
- 两个节点分别发布哪些 topic；
- 启动前如何确认 `/dev/videoX` 设备；
- 启动后如何验证 topic 是否正常发布。

## 2. 使用的 ROS2 包和 launch 文件

使用包：

```bash
gopro_camera_launch
```

使用 launch 文件：

```bash
/home/hit/ROS/src/gopro_camera_launch/launch/gopro_pose_record.launch.py
```

这个 launch 文件启动的是 `v4l2_camera` 包里的节点：

```bash
v4l2_camera_node
```

当前 launch 文件已经支持以下关键参数：

| 参数 | 作用 |
| --- | --- |
| `video_device` | 指定采集卡对应的 `/dev/videoX` |
| `camera_namespace` | 指定 ROS namespace，例如 `gopro_right` |
| `node_name` | 指定 ROS node name |
| `camera_name` | 指定相机名参数 |
| `frame_id` | 指定图像消息 header 的 frame_id |
| `publish_camera_info` | 是否发布 `camera_info` |

## 3. 启动前环境准备

每次启动前先进入工作区并 source 环境：

```bash
cd /home/hit/ROS
source /opt/ros/jazzy/setup.bash
source /home/hit/ROS/install/setup.bash
```

如果刚修改过 `gopro_camera_launch`，先重新构建：

```bash
cd /home/hit/ROS
source /opt/ros/jazzy/setup.bash
colcon build --packages-select gopro_camera_launch
source /home/hit/ROS/install/setup.bash
```

## 4. 确认采集卡设备

先查看系统识别到的 V4L2 设备：

```bash
ls /dev/video*
v4l2-ctl --list-devices
```

本次场景一实测时，两个 GoPro 采集卡映射为：

| 物理相机 | V4L2 视频设备 | ROS namespace |
| --- | --- | --- |
| GoPro right | `/dev/video5` | `gopro_right` |
| GoPro left | `/dev/video4` | `gopro_left` |

注意：

- `/dev/video4` 和 `/dev/video5` 是 Video Capture 设备。
- `/dev/video6` 和 `/dev/video7` 是 metadata capture 设备，不用于启动图像节点。
- 如果拔插 USB 采集卡，`/dev/videoX` 编号可能变化，需要重新用 `v4l2-ctl --list-devices` 确认。

可以用下面命令确认某个设备是否是真正的视频采集设备：

```bash
v4l2-ctl --device=/dev/video4 --all
v4l2-ctl --device=/dev/video5 --all
```

输出中需要看到类似：

```text
Device Caps      : ... Video Capture ...
Video input : 0 (Camera 1: ok)
Format Video Capture:
```

## 5. 启动 GoPro right 节点

GoPro right 使用 `/dev/video5`。

启动命令：

```bash
cd /home/hit/ROS
source /opt/ros/jazzy/setup.bash
source /home/hit/ROS/install/setup.bash

ros2 launch gopro_camera_launch gopro_pose_record.launch.py \
  video_device:=/dev/video5 \
  camera_namespace:=gopro_right \
  node_name:=gopro_right_camera \
  camera_name:=gopro_right \
  frame_id:=gopro_right_camera_optical_frame
```

启动后期望发布：

```text
/gopro_right/image_raw
/gopro_right/camera_info
```

## 6. 启动 GoPro left 节点

GoPro left 使用 `/dev/video4`。

启动命令：

```bash
cd /home/hit/ROS
source /opt/ros/jazzy/setup.bash
source /home/hit/ROS/install/setup.bash

ros2 launch gopro_camera_launch gopro_pose_record.launch.py \
  video_device:=/dev/video4 \
  camera_namespace:=gopro_left \
  node_name:=gopro_left_camera \
  camera_name:=gopro_left \
  frame_id:=gopro_left_camera_optical_frame
```

启动后期望发布：

```text
/gopro_left/image_raw
/gopro_left/camera_info
```

## 7. 验证 GoPro right topic

查看 topic：

```bash
ros2 topic list | sort | rg '^/gopro_right/'
```

验证图像消息：

```bash
ros2 topic echo /gopro_right/image_raw sensor_msgs/msg/Image --once --timeout 6 --no-arr
```

验证相机信息：

```bash
ros2 topic echo /gopro_right/camera_info sensor_msgs/msg/CameraInfo --once --timeout 6 --no-arr
```

可选：查看图像频率：

```bash
ros2 topic hz /gopro_right/image_raw
```

## 8. 验证 GoPro left topic

查看 topic：

```bash
ros2 topic list | sort | rg '^/gopro_left/'
```

验证图像消息：

```bash
ros2 topic echo /gopro_left/image_raw sensor_msgs/msg/Image --once --timeout 6 --no-arr
```

验证相机信息：

```bash
ros2 topic echo /gopro_left/camera_info sensor_msgs/msg/CameraInfo --once --timeout 6 --no-arr
```

可选：查看图像频率：

```bash
ros2 topic hz /gopro_left/image_raw
```

## 9. 本次实测结果

场景一实测结论：

| 节点 | 启动设备 | 验证结果 |
| --- | --- | --- |
| GoPro right | `/dev/video5` | `/gopro_right/image_raw` 和 `/gopro_right/camera_info` 可 echo 到数据 |
| GoPro left | `/dev/video4` | `/gopro_left/image_raw` 和 `/gopro_left/camera_info` 可 echo 到数据 |

图像消息实测特征：

```text
height: 1080
width: 1920
encoding: rgb8
```

## 10. 已知提示

启动时可能出现相机标定文件缺失提示：

```text
Camera calibration file /home/hit/.ros/camera_info/ugreen_25173:_ugreen_25173.yaml not found
```

该提示表示当前没有为 UGREEN 采集卡配置相机标定文件。

在本次场景一验证中，这个提示不阻断：

```text
/gopro_right/image_raw
/gopro_right/camera_info
/gopro_left/image_raw
/gopro_left/camera_info
```

的发布。

## 11. 和 Octopus 的关系

GoPro 节点只负责发布 ROS2 topic。

Octopus 是否能显示或录制这些 topic，还需要在 Octopus 侧确认：

```text
/gopro_right/image_raw
/gopro_right/camera_info
/gopro_left/image_raw
/gopro_left/camera_info
```

是否被加入显示或录制 topic 列表。

本说明只覆盖 GoPro 两个 ROS 节点如何启动与验证，不覆盖 Octopus MCAP 录制验证。
