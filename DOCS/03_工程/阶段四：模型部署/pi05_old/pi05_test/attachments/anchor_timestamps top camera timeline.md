---
tags:
  - 附件
---

# anchor_timestamps (top 相机时间轴)

> [!abstract]
> 一个 episode 的主时间轴 = top 相机所有消息的 `header.stamp`（去重 + 排序）。所有其他模态（wrist 图像、触觉、关节位置、末端位姿）都在这个时间轴上做最近邻/线性插值采样。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `anchor_timestamps` |
| 数据类型 | `np.ndarray` (float64) |
| 数据结构 | 一维数组，长度 = top 相机帧数 |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:1831-1854` |
| 现实含义 | "哪个相机决定了整个 episode 的节奏"——选 top 是因为它是场景主视角，FPS 稳定，ROS 侧一般配锁相时钟 |

## 构造代码

```python
# mcap_to_lerobot_v3.py:1831-1854
top_stamps = np.asarray(cap.top_img.timestamps, dtype=np.float64)
if top_stamps.size == 0:
    raise RuntimeError("No top camera frames; cannot build anchor timeline")

# 1) 去重 + 排序
order = np.argsort(top_stamps, kind="stable")
top_stamps = top_stamps[order]
_, unique_idx = np.unique(top_stamps, return_index=True)
unique_idx.sort()
top_stamps = top_stamps[unique_idx]

# 2) 重新对齐各路 buffer 的索引（按排序后的时间序重排）
#    因为 ROS bag 写入顺序不保证时间序

# 3) 重新分配 left_img / right_img / tactile 各帧的索引
```

## 使用位置

| 用途 | 函数 | 行为 |
| --- | --- | --- |
| 主循环遍历 | `_convert_one_mcap_into_dataset:1950` | `for anchor_t in top_stamps: ...` |
| episode 切分 | 同上 1954 行 | 帧间 gap > `split_gap_s` → 切新 episode |
| 关节采样 | `_sample_linear_numeric_at` (L1363) | 在 `arm_q.timestamps` 上做线性插值 |
| 末端位姿采样 | 同上 | 在 `left_ee_position.timestamps` 上做线性插值 |
| 图像采样 | `_sample_nearest_index_with_gate` (L1344) | 在 `left_img.timestamps` 上做最近邻 + 50ms 闸门 |
| 触觉采样 | `_sample_tactile_indices` (L1244) | 在 `left_tactile[taxel_id].timestamps` 上做最近邻 + 50ms 闸门 |

## 关键设计决策

- **为什么用 top 而非 VLA action**？VLA action 是策略输出，频率可能抖动（10/15/20Hz 自适应）；top 相机是硬件时钟锁相
- **为什么用 `header.stamp` 而非 message 到达时间**？录制时 ROS 用软件时间同步，`header.stamp` 是 source-level 时间
- **为什么去重**？压缩图像 (`compressed`) 在 MCAP writer 偶发重复写入（如 heartbeat 重发）

## 在数据流中的位置

- **上游**：`EpisodeCapture.top_img`（来自 `/realsense/top/color/image_raw/compressed`）
- **下游**：决定每条 frame 何时被 `ds.add_frame` 写入，决定何时切 episode
- 与 [[EXTRAPOLATION_TOLERANCE_S 50ms gate]] 共同决定哪些 anchor 有效
- 与 [[frame per-frame LeRobot record]] 是 1:1 的关系
