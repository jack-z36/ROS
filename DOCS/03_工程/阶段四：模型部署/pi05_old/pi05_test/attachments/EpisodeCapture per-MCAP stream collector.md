---
tags:
  - 附件
---

# EpisodeCapture (单 episode 流收集器)

> [!abstract]
> 内存中的 dataclass，把一个 MCAP 文件的所有 ROS topic 流（5 路图像 + 22 路数值 + VLA skew 监控）攒成按时间排序的 buffer，是 `_convert_one_mcap_into_dataset` 期间唯一的"工作态"。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `EpisodeCapture` |
| 数据类型 | `@dataclass` (Python) |
| 数据结构 | 11 个 series buffer + 4 个 VLA skew 元字段 |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:637-670` |
| 现实含义 | 一个 MCAP 文件对应一个 `EpisodeCapture` 实例；跑完一次即丢弃，不跨 episode 复用 |

## 字段清单（11 个流）

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| `top_img` | `ImageSeriesBuffer` | `/realsense/top/color/image_raw/compressed` → `observation.images.top` |
| `left_img` | `ImageSeriesBuffer` | `/realsense/left_hand/color/image_rect_raw/compressed` → `observation.images.left_wrist` |
| `right_img` | `ImageSeriesBuffer` | `/realsense/right_hand/color/image_rect_raw/compressed` → `observation.images.right_wrist` |
| `left_tactile` | `dict[str, ImageSeriesBuffer]` | 11 个 `/inspire/left_hand/tactile_*` |
| `right_tactile` | `dict[str, ImageSeriesBuffer]` | 11 个 `/inspire/right_hand/tactile_*` |
| `arm_q` | `NumericSeriesBuffer` | 12 维双臂 qpos → `state[0:12]` |
| `arm_cmd` | `NumericSeriesBuffer` | 14 维双指令 → `action[0:14]` |
| `left_ee_position` / `left_ee_rpy` | `NumericSeriesBuffer` | 6 维左末端 xyz+rpy → `state[14:20]` |
| `right_ee_position` / `right_ee_rpy` | `NumericSeriesBuffer` | 6 维右末端 xyz+rpy → `state[20:26]` |
| `left_hand_q` / `left_hand_cmd` | `NumericSeriesBuffer` | 1 维左灵巧手 |
| `right_hand_q` / `right_hand_cmd` | `NumericSeriesBuffer` | 1 维右灵巧手 |

## VLA skew 监控字段

```python
last_vla_action_stamp: Optional[float]   # /vla_teleop/action 的最新 header.stamp
last_vla_proprio_stamp: Optional[float]  # /vla_teleop/proprioception 的最新 header.stamp
vla_skew_warn_count: int                # 超过 50ms 累计告警次数
max_vla_skew_s: float                   # 记录最大偏斜量
```

监控逻辑：`check_vla_stamp_alignment(tol_s=0.050)`（第 659–670 行）每个 VLA 消息来时调一次，**不直接 drop**，仅打印前 5 条 WARN，真正的丢弃在 per-frame gate 兜底。

## 关键约束

- **append-only**：所有 buffer 的 `timestamps`/`values`/`frames` 都是 `list` + `append`，**不删不改**——用于离线扫描 + 按时间二分查找
- **left/right 区分**：除了 3 路相机 + 22 路数值流有 5 字段同名，tactile 拆 `left_tactile` / `right_tactile` 两个 dict 防混淆
- **不持有 baseline**：tactile baseline 在渲染阶段现算（开头 1.0 秒中位数），见 `TactilePreprocessStats.compute_baseline`
- 与 [[anchor_timestamps top camera timeline]] 是上下游关系
