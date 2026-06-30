# gopro_camera_launch 改造总结

本文档说明当前 `gopro_camera_launch` 相对于之前版本的变化。

当前结论是：

- 这个包已经收敛为一个 GoPro-only 的 ROS 2 启动包
- 主流程只保留 GoPro 图像节点启动
- MCAP 录制和外部位姿桥已经从实际代码路径中移除

## 1. 当前目标

当前包的唯一目标是：

- 启动 `v4l2_camera`
- 将 GoPro HDMI 图像发布为 ROS 2 topic

当前包不再承担：

- 位姿桥接
- TF 维护
- 多传感器采集链路
- MCAP 录制

## 2. 当前主链路

当前运行链路只有一段：

1. GoPro HDMI 输出进入采集卡
2. Linux 暴露为 `/dev/videoX`
3. `v4l2_camera` 读取该设备
4. 发布：
   - `/gopro/image_raw`
   - `/gopro/camera_info`

## 3. 相对旧版本删掉了什么

以下内容已经从主流程中移除：

- `external_pose_bridge`
- `sync_monitor`
- 动态 TF / 静态 TF 发布
- `ros2 bag record -s mcap`
- MCAP writer 配置
- rosbag QoS 配置

同时删除了这些源文件或配置文件：

- `gopro_camera_launch/external_pose_bridge.py`
- `gopro_camera_launch/image_activity_monitor.py`
- `gopro_camera_launch/sync_monitor.py`
- `config/mcap_writer.yaml`
- `config/record_qos.yaml`

## 4. 当前保留了什么

当前仍保留并参与主流程的内容：

- `launch/gopro_pose_record.launch.py`
- `config/gopro_camera.yaml`
- `start_capture_demo.sh`
- `README.md`
- `README_USAGE_CN.md`

其中：

- `launch/gopro_pose_record.launch.py`
  现在只启动 `v4l2_camera`
- `start_capture_demo.sh`
  现在只保留 `build`、`run`、`verify`

## 5. package.xml 的变化

运行依赖已经收敛，只保留 GoPro 节点启动真正需要的部分。

不再保留的运行依赖包括：

- `ros2bag`
- `rosbag2_storage_mcap`
- `tf2_ros`
- `geometry_msgs`
- `rclpy`

当前核心运行依赖只剩：

- `launch`
- `launch_ros`
- `sensor_msgs`
- `v4l2_camera`

## 6. setup.py 的变化

安装内容也已经收敛：

- 不再安装 MCAP 配置文件
- 不再暴露 `external_pose_bridge`
- 不再暴露 `sync_monitor`
- 不再暴露 `image_activity_monitor`

现在本质上这是一个：

- 只提供 launch 和相机配置的轻量 Python ROS 2 包

## 7. 当前默认 topic

当前主流程默认只保留：

- `/gopro/image_raw`
- `/gopro/camera_info`

当前不再由本包发布：

- `/camera/pose`
- `/sensor_time_reference`
- `/tf`
- `/tf_static`

## 8. 当前推荐启动方式

命令：

```bash
ros2 launch gopro_camera_launch gopro_pose_record.launch.py \
  video_device:=/dev/video4
```

或者：

```bash
./start_capture_demo.sh run
```

## 9. 当前定位

当前 `gopro_camera_launch` 的定位不再是：

- GoPro + pose + TF + MCAP 的完整采集管线

而是：

- 一个单纯负责启动 GoPro 图像节点的轻量包

如果后续你还需要：

- 位姿桥
- recorder
- bridge
- 数据同步

建议在当前版本之外单独新建独立包扩展，而不是把复杂逻辑重新塞回这个 GoPro-only 包里。

## 编译：

cd /home/hit/FastUMI_Data-main/FastUMI_Data-main
colcon build --packages-select gopro_camera_launch
source /home/hit/FastUMI_Data-main/FastUMI_Data-main/gopro_camera_launch/install/setup.bash

source /opt/ros/jazzy/setup.bash
source /home/hit/FastUMI_Data-main/FastUMI_Data-main/install/setup.bash
ros2 launch gopro_camera_launch gopro_pose_record.launch.py

## 启动 GoPro 节点

先确认采集卡已经出现在 Linux 中，例如：

```bash
ls /dev/video*
```

```bash
v4l2-ctl --list-devices
```

## 推荐启动方式：

ros2 launch gopro_camera_launch gopro_pose_record.launch.py
  video_device:=/dev/video4

## 看画面：

ros2 run rqt_image_view rqt_image_view
