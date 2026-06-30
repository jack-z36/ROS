# gopro_camera_launch 运行操作指南

## 编译

```bash
cd .
source /opt/ros/jazzy/setup.bash
colcon build --packages-select gopro_camera_launch
source install/setup.bash
```

## 确认采集卡设备

```bash
ls /dev/video*
v4l2-ctl --list-devices
```

默认设备为 `/dev/video4`。

## 确认或设置采集帧率

当前 launch 会在启动 `v4l2_camera_node` 前自动执行：

```bash
v4l2-ctl -d /dev/video4 --set-parm=30
```

手动验证时可查看当前驱动层帧率：

```bash
v4l2-ctl -d /dev/video4 --get-parm
```

## 启动 GoPro 节点

```bash
ros2 launch gopro_camera_launch gopro_pose_record.launch.py video_device:=/dev/video4
```

如需临时改为其他帧率：

```bash
ros2 launch gopro_camera_launch gopro_pose_record.launch.py video_device:=/dev/video4 frame_rate:=60
```

一键启动左右两路 GoPro 时，推荐通过工作区总入口启动：

```bash
cd .
./start_all_sensor.sh
```

总 launch 会为 right/left 两个 GoPro include 使用独立作用域，避免两个相机节点串用同一个 namespace 或 video device。

或者使用自动化脚本：

```bash
cd src/gopro_camera_launch
./start_capture_demo.sh run
```

## 查看画面

```bash
ros2 run rqt_image_view rqt_image_view
```

## 验证话题

```bash
ros2 topic list
ros2 topic hz /gopro/image_raw
ros2 topic echo /gopro/camera_info --once
```
