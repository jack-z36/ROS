---
tags:
  - 附件
---

# _estimate_fixed_tactile_scales (首次构建时跑一次的 q99.5 估算器)

> [!abstract]
> 离线"全训练集扫描器"：第一次构建数据集时跑一遍，遍历全部 MCAP 的全部触觉帧，按 (side, taxel) 通道算 0.995 分位数，得到 dataset-level 固定尺度。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `_estimate_fixed_tactile_scales` |
| 入参 | `mcap_paths: list[Path]`, `anno_paths: list[Path] \| None`, `taxel_ids: tuple[str,...]`, `split_gap_s: float`, `max_episode_seconds: float \| None` |
| 出参 | `dict[side, dict[taxel_id, dict[channel, float]]]` —— per-taxel per-channel 的 q99.5 scale |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:1179-1266` |
| 现实含义 | 解决"触觉 0~255 原始值没归一化，训练 loss 会因为量纲爆炸" 的离线预计算 |

## 算法步骤

```text
1. 对每个 mcap_path:
   1.1 解析 MCAP（复用 _open_mcap_reader_with_warnings，不做 episode 切分细节）
   1.2 找到第一个 top 相机 anchor 之前的 1.0 秒窗口
   1.3 收集该窗口内所有 22 个 taxel 帧 → 中位数 → baseline（暂存到局部，不写入 dataset）
   1.4 遍历该 mcap 全部触觉帧:
       pressure[t] = |raw[t] - baseline|
       delta[t]    = pressure[t] - pressure[t-1]   (stateful per-taxel)
       → 把 pressure、delta 都 append 到 per-taxel buffer
2. 对每个 (side, taxel):
   pressure_scale = np.quantile(buffer_pressure, 0.995)
   delta_scale    = np.quantile(buffer_delta,    0.995)
3. 返回嵌套 dict
```

## 触发条件

| 场景 | 是否执行 |
| --- | --- |
| 第一次 build 数据集 + `--include-tactile` | 是 |
| `--no-include-tactile` | 否，快路径 |
| append 到已有数据集 + scale 校验通过 | 否，读旧 scale |
| append 到已有数据集 + scale 偏差 >5% | **抛异常**：避免数据集被破坏 |

## 与正式转换的差异

| 维度 | _estimate_fixed_tactile_scales | _render_tactile_hand_image |
| --- | --- | --- |
| 输出 | 嵌套 dict（dataset-level scale） | np.uint8[224,224,3]（单帧伪图像） |
| 触发时机 | 转换开始前一次性 | 每个 anchor 一次 |
| 帧数据 | 缓存到内存（可能 GB 级） | 渲染完即释放 |
| Episode 切分 | 不做 | 严格遵守 |

## 关键约束

- **必须是首次 build**：append 模式不重算，依赖已有 meta
- **必须等所有 MCAP 扫完**：分位数是 dataset-level，不能 per-episode 算
- **Q 太大内存**：默认 30 FPS × 30s/ep × N ep × 11 taxels × 2 sides = 上 GB；进度条靠 `--log-every-N-mcap` 节流
- 与 [[TACTILE_SCALE_PERCENTILE q99.5 fixed scale]]、[[TactilePreprocessStats per-episode tactile stats]] 配套使用
