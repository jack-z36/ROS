---
tags:
  - 附件
---

# EXTRAPOLATION_TOLERANCE_S (50ms 严格对齐闸门)

> [!abstract]
> 50 毫秒硬闸门：当图像/触觉流距离 top 相机 anchor 超过 50ms，或数值流两侧都不在 anchor 50ms 之内，整个 anchor frame 会被丢弃而不是用过期数据凑合。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `EXTRAPOLATION_TOLERANCE_S` |
| 数据类型 | `float` |
| 数据结构 | 标量（单位：秒） |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:160` |
| 现实含义 | 跨模态时间对齐的容差上限——超过就当 anchor 不可靠，丢弃整帧而不是引入伪数据 |

## 适用环节

| 环节 | 函数 | 行为 |
| --- | --- | --- |
| Wrist 图像最近邻 | `_sample_nearest_index_with_gate` (L1344) | 最近邻超过 50ms → 报 "nearest sample is X ms away (gate 50 ms)" → drop frame |
| 触觉 11 路最近邻 | `_sample_tactile_indices` (L1244) | 任一路超过 50ms → 全部 drop |
| 数值流严格插值 | `_sample_linear_numeric_at` (L1363) | 两侧都超过 50ms → 报 "bracketing samples are too far" → drop |
| 数值流连续插值 | `_sample_continuous_linear_numeric_at` (L1413) | 端点处仍走最近邻（gate 仍生效），只放宽内部 gap |
| VLA action/proprio skew | `EpisodeCapture.check_vla_stamp_alignment` (L659) | 整体时间偏斜告警（不直接 drop，但 per-frame gate 会兜底） |

## 关键设计决策

- **不用线性外推**：超过容差就 drop，宁缺毋滥
- **RGB 用最近邻 + 闸门，数值流用线性插值**：图像不能用插值（瞬时性），关节/末端位姿可以插值
- **`continuous` 模式不绕过闸门**：文档明示"即使使用 --numeric-interp-mode continuous，触觉图像仍使用 50 ms 最近邻 gate"

## 在数据流中的位置

- **上游触发**：所有 `EpisodeCapture` 中的流（图像、触觉、数值）
- **下游反馈**：被丢弃的 anchor 不写入 `frame`、不调用 `ds.add_frame`，并在 `_convert_one_mcap_into_dataset` 末尾统计 `dropped_unreliable` 数量打印 WARN

## 副作用

- 数据集可能比 anchor 数量少几帧，但每帧都保证所有模态在 50ms 内对齐
- Episode split 也基于此容差：`split_gap_s = max(0.050, 1.5/fps)`（L1954），50ms 是下界
- 与 [[anchor_timestamps top camera timeline]] 共同决定 episode 的时间基准
