# FrameAlignmentConfig

## 定义

`FrameAlignmentConfig` 是场景一位姿转换配置契约，用于把左右 Baton Mini raw pose 转换到同一个 common frame。首版 common frame 直接选择单侧 UMI 的初始坐标系，默认是 `left_umi_start_frame`。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[位姿转换配置生成]]。

## 核心语义

默认配置：

```yaml
frame_alignment:
  common_anchor: left
```

含义：

```text
common_frame = left_umi_start_frame
```

这里的 `left_umi_start_frame` 是每条 episode 开始时左手 UMI 放入固定底座并 reset/start tracking 后的静止初始坐标系，不是左手 UMI 实时运动中的当前坐标系。

## 推荐配置结构

```yaml
frame_alignment:
  common_anchor: left

  pose_streams:
    left:
      input_topic: /baton_mini_left/fast_odom
      output_camera_pose_common: /baton_mini_left/camera_pose_common
      output_tcp_pose_common: /baton_mini_left/tcp_pose_common
    right:
      input_topic: /baton_mini_right/fast_odom
      output_camera_pose_common: /baton_mini_right/camera_pose_common
      output_tcp_pose_common: /baton_mini_right/tcp_pose_common

  extrinsics:
    common_from_left_start:
      translation_m: [0.0, 0.0, 0.0]
      rotation_quat_xyzw: [0.0, 0.0, 0.0, 1.0]
    common_from_right_start:
      translation_m: [0.0, 0.0, 0.0]
      rotation_quat_xyzw: [0.0, 0.0, 0.0, 1.0]
    camera_from_left_tcp:
      translation_m: [0.0, 0.0, 0.0]
      rotation_quat_xyzw: [0.0, 0.0, 0.0, 1.0]
    camera_from_right_tcp:
      translation_m: [0.0, 0.0, 0.0]
      rotation_quat_xyzw: [0.0, 0.0, 0.0, 1.0]
```

## 有效性规则

- `common_anchor` 只能是 `left` 或 `right`。
- 当 `common_anchor: left` 时，`common_from_left_start` 必须是单位变换。
- `common_from_right_start` 表示 `right_start_frame -> common_frame` 的固定外参。
- 更换 `common_anchor` 时，左右外参方向必须重新计算，不能只改字段名。
- 四元数顺序固定为 `xyzw`。
- raw pose 必须保留或可追溯，不能只留下 common pose。

## 上游来源

- 固定 3D 打印底座的 CAD、测量或标定结果。
- 已有浏览器标定工具的旧 common frame 写配置逻辑。
- 左右 Baton Mini raw pose topic。

## 下游消费者

- [[common frame 位姿转换]]
- [[CommonFrameCameraPose]]
- [[CommonFrameTcpPose]]
- 场景二位姿滤波和 IK 前置输入。

## 相关链接

- [[CameraFromTcpExtrinsic]]
- [[Scene1Config]]
