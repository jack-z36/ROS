---
tags:
  - 附件
---

# frame (单帧 LeRobot 记录)

> [!abstract]
> 一个 anchor 对应的最终 LeRobot 记录字典，所有键都对齐 `build_features_pi05` 注册的特征 schema；只有当所有模态都通过 50ms 闸门时才生成 frame，否则 skip。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `frame` |
| 数据类型 | `dict[str, np.ndarray]` |
| 数据结构 | 4–8 个 key-value 对，对应一个时刻的完整观测+动作 |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:2014-2062` |
| 现实含义 | LeRobotDataset 训练时一次 `__getitem__` 拿到的"一张样本" |

## Schema 完整键

```python
frame = {
    "observation.images.top":         np.uint8[224, 224, 3],   # 必有
    "observation.images.left_wrist":  np.uint8[224, 224, 3],   # 必有
    "observation.images.right_wrist": np.uint8[224, 224, 3],   # 必有
    "observation.images.left_tactile":  np.uint8[224, 224, 3], # --include-tactile
    "observation.images.right_tactile": np.uint8[224, 224, 3], # --include-tactile
    "observation.state": np.float32[26],  # 必有（见 STATE_DIM）
    "action":          np.float32[14],    # 必有（见 ACTION_DIM）
}
```

3 图像 + 2 数值 = 至少 5 个 key；+2 触觉 = 7 个 key。

## 构造顺序

`_convert_one_mcap_into_dataset:2014-2062` 的构造步骤（重要顺序——失败则 skip 整帧）：

1. **采样 3 相机**：`_sample_image_indices` → 3 个 idx → 解码 → `preprocess_to_vla_shape` → 3 个 `np.uint8[224,224,3]`
2. **采样 11+11 触觉**（如果启用）：`_sample_tactile_indices` → 22 个 idx → 解码 → `_render_tactile_hand_image` × 2 → 2 个 `np.uint8[224,224,3]`
3. **采样 6 数值流**：arm_q、arm_cmd、left/right_ee_pose、left/right_hand_q/cmd → 6 个 `np.float32[6/1/...]`
4. **构造 26D state**（见 [[STATE_DIM 26D state schema]]）
5. **构造 14D action**（见 [[ACTION_DIM 14D action schema]]）
6. **任一返回 None 标记 → 整帧 skip**

## 关键约束

- **3 相机必选**：top + left_wrist + right_wrist，少任一路 → 整帧 drop
- **action 字段为 None 也 drop**：动作缺失 = 训练时无法构成 (s, a, s') 转移
- **dtype 严格**：图像 `uint8`、状态/动作 `float32`，见 `_pack_position_state` / `_pack_action`
- **不可变性**：`frame` dict 一旦构造就不修改，避免 dataloader 读到中间态
- 与 [[anchor_timestamps top camera timeline]] 是一对一关系
