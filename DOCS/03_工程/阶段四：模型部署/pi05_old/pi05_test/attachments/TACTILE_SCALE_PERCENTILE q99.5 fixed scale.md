---
tags:
  - 附件
---

# TACTILE_SCALE_PERCENTILE (q99.5 触觉固定尺度)

> [!abstract]
> 触觉伪图像的取值尺度 = 全训练集每个 taxel 通道的 99.5 分位数。第一次跑数据集扫描一遍全量 ep，归一化统计后落到 `meta/tactile_preprocess.json`，**之后所有 train/infer 都用同一组 scale，不再 per-batch 重新统计**。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `TACTILE_SCALE_PERCENTILE` |
| 数据类型 | `float` |
| 数据结构 | 标量（百分比，0.995） |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:153-158` |
| 现实含义 | 99.5 分位固定尺度，让触觉伪图像在 [0, 1] 区间内有稳定的动态范围，不会因 outlier 拉到 255 也不会因空载时整帧全 0 |

## 派生变量

```python
# 估算阶段（仅在首次转换时跑一次）
pressure_scale = quantile(|raw - baseline|, 0.995)   # per-taxel + per-side + per-channel
delta_scale    = quantile(|pressure - prev_pressure|, 0.995)

# 运行阶段（每个 episode 都用估算出来的固定值）
red   = clip(|raw - baseline| / pressure_scale, 0, 1)
green = clip(+delta / delta_scale, 0, 1)
blue  = clip(-delta / delta_scale, 0, 1)
```

对应函数：
- 估算：`_estimate_fixed_tactile_scales`（第 1179–1266 行）
- 渲染：`_render_tactile_hand_image`（第 1267–1311 行）→ `_tactile_pressure_delta_to_rgb`（第 1314–1325 行）

## 元数据落地

`write_tactile_preprocess_metadata`（第 482–502 行）会把以下内容写到数据集根目录的 `meta/tactile_preprocess.json`：

```json
{
  "tactile_layout_version": "inspire_hand_v1",
  "pressure_percentile": 0.995,
  "delta_percentile": 0.995,
  "baseline_seconds": 1.0,
  "per_side_taxel": {
    "left": {
      "12": {"pressure_scale": 18.7, "delta_scale": 4.2, "shape": [16, 8]},
      "13": {"pressure_scale": 19.1, "delta_scale": 4.5, "shape": [16, 8]},
      ...
    },
    "right": { ... }
  }
}
```

## 关键约束

- **fixed 不是 adaptive**：不用 LeRobot 的 `Normalizer` 自动统计，而是离线算一次 + 持久化
- **append 校验**：新 episode 必须用同一 layout_version，pressure/delta scale 在 ±5% 内一致（`_validate_existing_tactile_preprocess_metadata` 第 504–551 行）
- **不包含 baseline**：`baseline` 仍然每 episode 算（用每个 episode 自己开头 1.0 秒的中位数），见 [[EpisodeCapture]] 的初始化
- 与 [[TACTILE_LAYOUT inspire_hand_v1]]、`TACTILE_BASELINE_SECONDS=1.0` 共同决定伪图像的取值
