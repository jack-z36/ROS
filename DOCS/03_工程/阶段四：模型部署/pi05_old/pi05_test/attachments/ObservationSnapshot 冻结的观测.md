---
tags:
  - 附件
---

# ObservationSnapshot (冻结的观测)

> [!abstract]
> 一个 monotonic 时间点上"所有观测字段齐全"的不可变快照，从 `ObservationCollector.snapshot()` 发出，通过 `SharedBuffer.set_observation()` 桥接到控制循环和推理后台线程。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `ObservationSnapshot` (frozen dataclass) |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:22-29` |
| 构造位置 | `observation_collector.py:98-103` |
| 现实含义 | 模型的"一次输入"，所有字段在同一时间点对齐、不可变 |

## 字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `images` | `Mapping[str, torch.Tensor]` | 3 相机 (top/left_wrist/right_wrist) + 可选 tactile 伪图像 |
| `state` | `BimanualState` | 强类型结构化状态（arm_q, hand_q, ee_pos, ee_rpy） |
| `encoded_state` | `np.float32[26]` | 26D 状态向量，与 [[STATE_DIM 26D state schema]] 一致 |
| `captured_at_s` | `float` | 构造时刻的 `time.monotonic()` 值 |

## 生命周期

```text
ROS callback (e.g. _image_cb)
    ↓
collector.update_image(...)
    ↓
collector.snapshot(max_age_s=...)  ← 在 lock 内 deep copy
    ↓
ObservationSnapshot(images, state, encoded_state, captured_at_s)
    ↓
shared_buffer.set_observation(snapshot)  ← lock 内赋值给 _latest_observation
    ↓
control_loop.tick()  →  latest_observation(max_age_s=...)  →  用作 infer 输入
inference_worker     →  policy.predict_action_chunk(observation)
```

## 关键约束

- **frozen=True**：构造后字段不能再改，避免下游误改
- **图像 deep copy**：collector 在 lock 内做 `value.detach().clone()`，snapshot 不引用共享 tensor
- **`encoded_state` 与 `state` 冗余**：`state` 强类型方便上层调用，`encoded_state` 直接给模型。两份保证"既能调试又能跑"
- **`captured_at_s` 用 monotonic 而非 wall clock**：避免 NTP 跳变影响超时判断
- 与 [[ObservationCollector 观测收集器]]、[[SharedBuffer 线程安全桥接]] 是上下游
