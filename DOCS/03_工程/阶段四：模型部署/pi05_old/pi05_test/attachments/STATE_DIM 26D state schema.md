---
tags:
  - 附件
---

# STATE_DIM (26D state schema)

> [!abstract]
> 26 维观测状态向量，由 12 维机械臂关节位置 + 2 维手部张合 + 12 维双末端 xyz+rpy 拼接而成。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `STATE_DIM` |
| 数据类型 | `int` (Python) / `float32[26]` (numpy) |
| 数据结构 | 标量（维度数）+ 26 维向量（实际状态） |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:170` |
| 现实含义 | 训练时给策略网络"看"到的本体感知状态：关节位置 + 末端位姿 + 灵巧手张合 |

## 维度拆分

```
state[0:6]    = left_arm_qpos0..5        (左臂 6 DoF 关节位置)
state[6:12]   = right_arm_qpos0..5       (右臂 6 DoF 关节位置)
state[12:13]  = left_hand_qpos0          (左手张合)
state[13:14]  = right_hand_qpos0         (右手张合)
state[14:17]  = left_ee_position_x/y/z   (左末端 xyz)
state[17:20]  = left_ee_pose_roll/pitch/yaw (左末端 rpy)
state[20:23]  = right_ee_position_x/y/z  (右末端 xyz)
state[23:26]  = right_ee_pose_roll/pitch/yaw (右末端 rpy)
```

派生自：`STATE_DIM = ACTION_DIM + 2*EE_POSE_DOF = 14 + 2*6 = 26`。

## 构造代码

`mcap_to_lerobot_v3.py:1978-1988`：

```python
state = np.concatenate(
    [
        arm_q_value[6:12],   # 注意: left/right 顺序与 ROS payload 相反
        arm_q_value[:6],
        left_hand_q_value[:HAND_DOF],
        right_hand_q_value[:HAND_DOF],
        left_ee_pose_value[:EE_POSE_DOF],
        right_ee_pose_value[:EE_POSE_DOF],
    ],
    axis=0,
).astype(np.float32)
```

## 在数据流中的位置

- **上游**：`arm_q_value` (12D 双臂 qpos) + `left/right_ee_pose_value` (各 6D xyz+rpy) + 双手 `hand_q_value` (各 1D)，分别在每个 anchor 时间由 `_sample_linear_numeric_at` 采样得到
- **下游**：经 `_pack_position_state` 写入 `frame["observation.state"]`，最终落到 `LeRobotDataset.add_frame`

## 关键约束

- **与 action 的拆分边界**：`state` 包含 EE pose（附加信息），`action` 不包含（控制指令只到关节/张合层）
- **`arm_q_value` 的 left/right 顺序翻转**：ROS 上 `/vla_teleop/proprioception` 习惯先 right 后 left（参见代码 `[6:12]` 在前、`[:6]` 在后）
- 与 [[ACTION_DIM]] 形成对照，与 [[TACTILE_LAYOUT]]、`observation.images.*` 同属一个 frame
