# baton_mini_sdk_demo

## Overview

`baton_mini_sdk_demo` is a baseline demo project for the Baton Mini / mini camera SDK. It includes:

- Device login and control interfaces
- Algorithm start-stop control and status access
- Stream pose result reception
- IMU, stereo image, and fast odom data reception
- ROS1 / ROS2 topic publishing
- Standalone non-ROS execution

The device software version should be no earlier than `2025-03-17`. If the device is older, upgrade the firmware first.

## Current Project Structure

The current project wraps ROS-related logic through `ros_interface`, so the main business flow no longer directly depends on ROS1 / ROS2 specific APIs:

- `src/baton_mini.cpp`: main flow, SDK login, command thread, and data callback binding
- `include/io/ros_interface.h`: unified ROS1 / ROS2 interface declarations
- `src/io/ros_interface.cpp`: ROS1 / ROS2 adaptation for parameters, logging, timestamps, and topic publishing
- `src/baton_cmd.cpp`: device control, parameter access, algorithm start-stop, and IMU / image / fast odom switching

## Build

### Non-ROS

Run in the project directory:

```bash
bash ./build_non_ros.sh
```

By default, it builds in `build_non_ros/` and runs:

```bash
cmake .. -DUSE_ROS=OFF
make
```

### ROS

Before running `ros_build.sh`, source the corresponding ROS environment first. The script distinguishes ROS1 and ROS2 automatically based on `ROS_VERSION`.

#### ROS1

```bash
source /opt/ros/noetic/setup.bash
bash ./ros_build.sh
```

For ROS1, the script runs:

```bash
catkin_make --cmake-args -DUSE_ROS=ON
```

#### ROS2

```bash
source /opt/ros/humble/setup.bash
bash ./ros_build.sh
```

For ROS2, the script runs:

```bash
colcon build --cmake-args -DUSE_ROS=ON
```

## Run

### Non-ROS

In non-ROS mode, the program does not read `server_ip` / `local_ip` from a ROS parameter server. If you need to change the default addresses, modify:

- `src/baton_mini.cpp`

After building, run:

```bash
./build_non_ros/baton_mini
```

### ROS1

Use launch:

```bash
roslaunch baton_mini baton_mini.launch server_ip:=192.168.1.10 local_ip:=192.168.1.18
```

### ROS2

Use launch:

```bash
ros2 launch baton_mini baton_mini.launch.py server_ip:=192.168.1.10 local_ip:=192.168.1.18
```

## ROS Parameters and Topics

Default parameters:

- `server_ip`: device IP, default `192.168.1.10`
- `local_ip`: local host IP, default `192.168.1.16` in code / `192.168.1.18` in launch
- `imu_topic`: default `/baton_mini/imu`
- `odom_topic`: default `/baton_mini/odometry`
- `fast_odom_topic`: default `/baton_mini/fast_odom`
- `image_left_topic`: default `/baton_mini/image_left`
- `image_right_topic`: default `/baton_mini/image_right`

Published topics:

- `/baton_mini/imu`
- `/baton_mini/odometry`
- `/baton_mini/fast_odom`
- `/baton_mini/image_left`
- `/baton_mini/image_right`

## Interaction

After startup, the terminal accepts `[0~5]`:

- `0`: exit and logout
- `1`: toggle algorithm start-stop
- `2`: restart the algorithm
- `3`: IMU reception on-off
- `4`: enable stereo image reception
- `5`: fast odom reception on-off

### 200Hz fast odom Notes (Internal Test)

After startup:

1. Enter `1` and press Enter to start the algorithm
2. Enter `5` and press Enter to enable fast odom reception

Note: If high-rate odometry is not required, enabling 200Hz fast odom by default is not recommended. After IMU interpolation, this data may show more jitter in high-vibration scenarios.

## Update History

- `[2026-04-01]`
  - Added support for automatic ROS1 / ROS2 build selection based on `ROS_VERSION`
- `[2025-07-14]`
  - Updated 200Hz odom reading and deprecated part of the old `odom_data_print` and `stream_callback` usage
