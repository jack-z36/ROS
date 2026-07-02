---
tags:
  - 附件
---

# ObservationCollector (观测收集器)

> [!abstract]
> 把 ROS callback 来的"零散字段"聚合成完整的 `ObservationSnapshot`：每收到一帧 image / 关节 / 末端位姿就 update 一次；所有必需字段都齐了才生成 snapshot。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `ObservationCollector` |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py:20-154` |
| 实例位置 | `pi05_vla_deploy_node.py:39-41` |
| 现实含义 | 跨多个 ROS topic 的"等待齐了再 emit"型状态机，避免给模型喂半张图 |

## 状态字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `_images` | `dict[str, torch.Tensor]` | 已收到的图像（CHW float32） |
| `_values` | `dict[str, Any]` | 已收到的数值（np.float32 向量或 float） |
| `_stamps` | `dict[str, float]` | 每个字段最后一次更新的 monotonic 时间 |
| `_required_image_keys` | `tuple[str, ...]` | 触发 snapshot 所需的图像 key（默认 top/left_wrist/right_wrist） |
| `_proprioception_order` | `str` | "right_left" (pico 默认) 或 "left_right" |

## 必需字段（snapshot 触发条件）

| 类别 | 字段 | 来源 |
| --- | --- | --- |
| 图像 | `_required_image_keys`（默认 top, left_wrist, right_wrist） | 3 个相机 topic |
| 数值 | left_arm_q, right_arm_q | `/observation/proprioception` (12 维) |
| 数值 | left_hand_q, right_hand_q | `/observation/{left,right}_hand/joint_state` (1 维) |
| 数值 | left_ee_pos, left_ee_rpy | `/observation/left_arm/{ee_position,ee_rpy}` |
| 数值 | right_ee_pos, right_ee_rpy | `/observation/right_arm/{ee_position,ee_rpy}` |

任一字段缺失或超过 `max_age_s` 仍未更新 → `snapshot()` 返回 None。

## `snapshot()` 行为（核心）

```text
1. 锁内：检查所有 _required_image_keys 都已收 + 所有 _required_value_keys 都已收
2. 锁内：检查没有字段超过 max_age_s（默认 stale_observation_timeout_s=0.5s）
3. 锁内：deepcopy 当前的 images + values（避免释放锁后被改）
4. 锁外：构造 BimanualState + encode_bimanual_state → 26D float32 向量
5. 返回 ObservationSnapshot(images, state, encoded_state, captured_at_s=now)
```

## 关键设计决策

- **lock 内的"齐了再 emit"**：避免半张图被下游用
- **lock 内的 deep copy**：避免读时被 callback 改
- **lock 外做 `encode_bimanual_state`**：BimanualState 构造 + 编码可重，不持锁
- **`missing_fields()` 用于定期打日志**（节点第 191 行），2 秒一次节流

## 与 Pi05VlaDeployNode 的交互

```python
# pi05_vla_deploy_node.py:154-194
def _image_cb(self, name, msg):
    rgb = _decode_image(msg)
    image = preprocess_rgb_image(rgb, self.image_config)
    self.collector.update_image(name, image)
    self._publish_observation_if_ready()   # ← 触发 snapshot

def _publish_observation_if_ready(self):
    snapshot = self.collector.snapshot(max_age_s=self.config.safety.stale_observation_timeout_s)
    if snapshot is not None:
        self.shared_buffer.set_observation(snapshot)
```

## 关键约束

- **线程安全**：所有 `_images`/`_values`/`_stamps` 访问都加 `self._lock`（callback 在 ROS executor 线程，snapshot 在 timer 线程）
- **`proprioception_order` 决定 12 维如何拆分为 6+6**：pico 默认 right 在前
- **图像必须有 `detach().clone()`**：`update_image` 第 45 行，避免外部修改后 collector 内部也变
- 与 [[ObservationSnapshot 冻结的观测]]、[[SharedBuffer 线程安全桥接]]、[[Pi05VlaDeployNode ROS2 部署节点]] 上下游
