---
tags:
  - program-principle
analysis: pi05-deploy-dataflow
---

# ObservationCollector 详解

## 它是什么

`ObservationCollector` 是一个类，它的实例 `collector` 是一个**读写三个字典的管理员**。它不负责数值加工，只负责：

1. **写入**：接收各指令卡处理后的数据，存入内部字典
2. **检查**：判断所有必需字段是否到齐、是否过期
3. **读出**：把三个字典的数据拷贝出来，组装成 `ObservationSnapshot`

---

## 三个内部字典

```
ObservationCollector
├── _images:  dict[str, torch.Tensor]   # 图像字典
├── _values:  dict[str, Any]            # 状态值字典
└── _stamps:  dict[str, float]          # 时间戳字典
```

### `_images` — 图像字典

| key | value 类型 | 来源 | 说明 |
|-----|-----------|------|------|
| `"top"` | `torch.Tensor (3, 224, 224)` | `_image_cb("top", msg)` | 顶部相机，float32 $[0, 1]$ |
| `"left_wrist"` | `torch.Tensor (3, 224, 224)` | `_image_cb("left_wrist", msg)` | 左腕相机 |
| `"right_wrist"` | `torch.Tensor (3, 224, 224)` | `_image_cb("right_wrist", msg)` | 右腕相机 |

### `_values` — 状态值字典

| key | value 类型 | 来源 | 说明 |
|-----|-----------|------|------|
| `"left_arm_q"` | `np.ndarray (6,)` | `_proprio_cb` | 左臂 6 关节角 (rad) |
| `"right_arm_q"` | `np.ndarray (6,)` | `_proprio_cb` | 右臂 6 关节角 (rad) |
| `"left_hand_q"` | `float` | `_hand_cb("left", msg)` | 左夹爪 (300-1000) |
| `"right_hand_q"` | `float` | `_hand_cb("right", msg)` | 右夹爪 (300-1000) |
| `"left_ee_pos"` | `np.ndarray (3,)` | `_point_cb("left_ee_pos", msg)` | 左末端位置 xyz (m) |
| `"left_ee_rpy"` | `np.ndarray (3,)` | `_vec3_cb("left_ee_rpy", msg)` | 左末端姿态 rpy (rad) |
| `"right_ee_pos"` | `np.ndarray (3,)` | `_point_cb("right_ee_pos", msg)` | 右末端位置 xyz (m) |
| `"right_ee_rpy"` | `np.ndarray (3,)` | `_vec3_cb("right_ee_rpy", msg)` | 右末端姿态 rpy (rad) |

### `_stamps` — 时间戳字典

每个字段写入时自动记录 `time.monotonic()` 时间戳，用于过期检查。

| key | 对应字段 | 说明 |
|-----|---------|------|
| `"image_top"` | `_images["top"]` | 顶部相机最后更新时间 |
| `"image_left_wrist"` | `_images["left_wrist"]` | 左腕相机最后更新时间 |
| `"image_right_wrist"` | `_images["right_wrist"]` | 右腕相机最后更新时间 |
| `"proprioception"` | `_values["left_arm_q"]` + `_values["right_arm_q"]` | 关节角最后更新时间 |
| `"left_hand"` | `_values["left_hand_q"]` | 左夹爪最后更新时间 |
| `"right_hand"` | `_values["right_hand_q"]` | 右夹爪最后更新时间 |
| `"left_ee_pos"` | `_values["left_ee_pos"]` | 左末端位置最后更新时间 |
| `"left_ee_rpy"` | `_values["left_ee_rpy"]` | 左末端姿态最后更新时间 |
| `"right_ee_pos"` | `_values["right_ee_pos"]` | 右末端位置最后更新时间 |
| `"right_ee_rpy"` | `_values["right_ee_rpy"]` | 右末端姿态最后更新时间 |

---

## 具体数值示例

假设机器人在某一时刻正在执行倒水任务，所有传感器正常工作。以下是 `collector` 内部三个字典在某个瞬间的快照：

### `_images` 快照

```
{
    "top":         torch.Tensor (3, 224, 224) float32
                   值范围 [0.0, 1.0]
                   例如 pixel (0,0): [0.45, 0.38, 0.22]   # 桌面像素，偏棕色

    "left_wrist":  torch.Tensor (3, 224, 224) float32
                   值范围 [0.0, 1.0]
                   例如 pixel (0,0): [0.12, 0.15, 0.08]   # 左手腕视角，偏暗

    "right_wrist": torch.Tensor (3, 224, 224) float32
                   值范围 [0.0, 1.0]
                   例如 pixel (0,0): [0.85, 0.82, 0.78]   # 右手腕视角，偏亮（看到水瓶）
}
```

### `_values` 快照

```python
{
    # 左臂 6 关节角 (rad) — 从 /vla_teleop/proprioception 解码
    "left_arm_q":  np.array([0.12, -0.45, 0.78, -0.03, 0.56, 0.21], dtype=float32),

    # 右臂 6 关节角 (rad)
    "right_arm_q": np.array([-0.08, 0.52, -0.33, 0.15, -0.67, 0.44], dtype=float32),

    # 左夹爪 — 从 /inspire/left_hand/joint_states 读取
    "left_hand_q": 750.0,        # 半张开 (300=闭合, 1000=全开)

    # 右夹爪 — 从 /inspire/right_hand/joint_states 读取
    "right_hand_q": 420.0,       # 接近闭合，正在握持瓶子

    # 左末端位置 (m) — 从 /left_arm/ee_position 读取
    "left_ee_pos": np.array([0.45, 0.12, 0.38], dtype=float32),
                   # 基座前方45cm, 右侧12cm, 上方38cm

    # 左末端姿态 (rad) — 从 /left_arm/ee_rpy 读取
    "left_ee_rpy": np.array([0.05, -1.23, 0.78], dtype=float32),
                   # roll=2.9°, pitch=-70.5°, yaw=44.7°

    # 右末端位置 (m)
    "right_ee_pos": np.array([0.42, -0.15, 0.35], dtype=float32),
                    # 基座前方42cm, 左侧15cm, 上方35cm

    # 右末端姿态 (rad)
    "right_ee_rpy": np.array([-0.03, -1.18, -0.82], dtype=float32),
                    # roll=-1.7°, pitch=-67.6°, yaw=-47.0°
}
```

### `_stamps` 快照

```python
{
    "image_top":          891234.567,   # 顶部相机 0.010 秒前更新
    "image_left_wrist":   891234.565,   # 左腕相机 0.012 秒前更新
    "image_right_wrist":  891234.568,   # 右腕相机 0.009 秒前更新
    "proprioception":     891234.570,   # 关节角   0.007 秒前更新
    "left_hand":          891234.555,   # 左夹爪   0.022 秒前更新
    "right_hand":         891234.560,   # 右夹爪   0.017 秒前更新
    "left_ee_pos":        891234.569,   # 左位置   0.008 秒前更新
    "left_ee_rpy":        891234.569,   # 左姿态   0.008 秒前更新
    "right_ee_pos":       891234.569,   # 右位置   0.008 秒前更新
    "right_ee_rpy":       891234.569,   # 右姿态   0.008 秒前更新
}
# 所有时间戳都在 0.022 秒以内，远小于过期阈值 0.5 秒 → 数据有效
```

---

## 写入操作对照表

每个指令卡调用 collector 的写入方法时，实际发生的事：

| 指令卡调用 | 实际操作 |
|-----------|---------|
| `collector.update_image("top", tensor)` | `_images["top"] = tensor.detach().clone()` + `_stamps["image_top"] = now` |
| `collector.update_proprioception([right6, left6])` | `_values["left_arm_q"] = left` + `_values["right_arm_q"] = right` + `_stamps["proprioception"] = now` |
| `collector.update_hand("left", 750.0)` | `_values["left_hand_q"] = 750.0` + `_stamps["left_hand"] = now` |
| `collector.update_vector("left_ee_pos", [0.45, 0.12, 0.38])` | `_values["left_ee_pos"] = np.array([0.45, 0.12, 0.38])` + `_stamps["left_ee_pos"] = now` |

---

## 读出操作：`snapshot()`

当所有 11 个必需字段到齐且未过期时，`snapshot()` 把三个字典的数据拷贝出来：

```
snapshot() 读出流程：

_values 字典中的 8 个字段
  → 组装为 BimanualState 对象
  → encode_bimanual_state() 编码为 (26,) float32
       ↓
ObservationSnapshot {
    images:  从 _images 拷贝 3 个 tensor
    state:  BimanualState 对象（原始值）
    encoded_state: (26,) float32 编码向量（原始值，未归一化）
    captured_at_s: 当前时刻
}
```

> [!important] `_values` → `(26,)` 编码的具体过程
>
> 把上面示例的 `_values` 代入 `encode_bimanual_state()`：
>
> ```
> np.concatenate([
>     left_arm_q:   [0.12, -0.45, 0.78, -0.03, 0.56, 0.21]          # index 0-5
>     right_arm_q:  [-0.08, 0.52, -0.33, 0.15, -0.67, 0.44]         # index 6-11
>     left_hand_q:  [750.0]                                          # index 12
>     right_hand_q: [420.0]                                          # index 13
>     left_ee_pos:  [0.45, 0.12, 0.38]                               # index 14-16
>     left_ee_rpy:  [0.05, -1.23, 0.78]                              # index 17-19
>     right_ee_pos: [0.42, -0.15, 0.35]                              # index 20-22
>     right_ee_rpy: [-0.03, -1.18, -0.82]                            # index 23-25
> ])
> = [0.12, -0.45, 0.78, -0.03, 0.56, 0.21,
>    -0.08, 0.52, -0.33, 0.15, -0.67, 0.44,
>    750.0, 420.0,
>    0.45, 0.12, 0.38,
>    0.05, -1.23, 0.78,
>    0.42, -0.15, 0.35,
>    -0.03, -1.18, -0.82]
> → shape (26,) float32
> ```

---

## 相关笔记

- [[部署推理数据流框架#D02 传感器订阅 & 观测组装]] — collector 在数据流中的位置
- [[传感器数据详解]] — 各 topic 的原始数据格式
- [[预处理后数据详解]] — collector 产出物 ObservationSnapshot 的结构
