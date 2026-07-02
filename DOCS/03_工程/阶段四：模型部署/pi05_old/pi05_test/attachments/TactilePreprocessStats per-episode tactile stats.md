---
tags:
  - 附件
---

# TactilePreprocessStats (单 episode 触觉预统计)

> [!abstract]
> 单 episode 级别的触觉预统计记录：包含 22 个 (side, taxel) 的 baseline mask 数组（用于渲染时算 \|raw - baseline\|）+ 估算阶段累计的 q99.5 scale + 全 episode 的 raw/timestamp 缓存。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `TactilePreprocessStats` |
| 数据类型 | `@dataclass` (Python) |
| 数据结构 | 4 个字段：baseline_by_side_id + pressure_scale + delta_scale + 缓存 |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:1168-1176`（定义） |
| 现实含义 | 同一个 episode 的 11×2 触觉流共享一组 baseline，确保"接触 = 当前 - 无接触" 的物理语义 |

## 字段清单

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| `baseline_by_side_id` | `dict[tuple[str,str], np.ndarray]` | (side, taxel_id) → 中位数参考帧 |
| `pressure_scale` | `float` | 估算阶段写入；渲染阶段只读 |
| `delta_scale` | `float` | 同上 |
| `raw_values_by_side_id` | `dict[tuple[str,str], list[np.ndarray]]` | 估算阶段缓存，跑完即释放 |
| `raw_timestamps_by_side_id` | `dict[tuple[str,str], list[float]]` | 同上 |
| `skip_render` | `bool` | --no-include-tactile 时的快路径 |

## 计算流程

### 1. Baseline 估算
- 起点 = 第一个 `top_img` 的 `header.stamp`
- 窗口 = `[start, start + TACTILE_BASELINE_SECONDS=1.0]`
- 11×2 个 taxel 在窗口内的所有 raw 值，沿 axis=0 取中位数 → `baseline`
- 形状：每个 taxel 自己的 `H×W`（不是统一 224×224）

### 2. q99.5 scale 估算（仅首次 build）
- 调用 `_estimate_fixed_tactile_scales` 跑完全部 MCAP，对每 (side, taxel) 通道取 0.995 分位
- 写入 `meta/tactile_preprocess.json`，后续 episode 共用

### 3. 渲染阶段只读
- `pressure = |raw - baseline|`
- `delta = pressure - previous_pressure`（stateful，`TactileRenderState.previous_pressure`）
- 见 [[TACTILE_LAYOUT inspire_hand_v1]] 通道定义

## 关键约束

- **per-episode 重建**：每个 MCAP 对应一个新的 `TactilePreprocessStats` 实例；不要跨 episode 复用 baseline
- **baseline 形状因 taxel 而异**：taxel 12 = 16×8，taxel 61 可能是 64×8（视硬件版本）—— 渲染前必须形状校验
- **scale 跨 episode 共享**：scale 是 dataset-level，不是 episode-level
- 与 [[EpisodeCapture per-MCAP stream collector]]、[[TACTILE_SCALE_PERCENTILE q99.5 fixed scale]] 配套使用
