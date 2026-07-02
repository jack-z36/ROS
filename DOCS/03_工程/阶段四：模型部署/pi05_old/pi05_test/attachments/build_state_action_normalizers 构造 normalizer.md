---
tags:
  - 附件
---

# build_state_action_normalizers (从 LeRobot dataset 构造 normalizer)

> [!abstract]
> 工厂函数：打开一个 LeRobot v3 dataset，从 `meta/stats.json` 优先读 vector min/max，回退到 linspace 采样 2048 帧计算；返回一对 (state_normalizer, action_normalizer)。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `build_state_action_normalizers` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/data/normalization.py:177-199` |
| 调用方 | `build_train_dataloader` (training) + `export_deploy_bundle` (deployment) |
| 现实含义 | "打开磁盘上的 dataset，立刻知道 (min, max) 是什么" |

## 函数签名

```python
def build_state_action_normalizers(
    dataset: LeRobotDataset,
    max_samples: int = DEFAULT_SAMPLE_COUNT,  # 2048
    identity_indices: Mapping[str, Sequence[int] | torch.Tensor | np.ndarray] | None = None,
) -> tuple[ActionStateNormalizer, ActionStateNormalizer]:
    ...
```

## 行为

```text
1. ensure_vector_stats(dataset, keys=("observation.state", "action"))
   └ 缺 stats 或维度不对 → 扫描全 dataset 重算 (min/max/mean/std) → write_stats
2. 构造 state normalizer:
   state_normalizer = build_normalizer_from_lerobot(
       dataset, key="observation.state", max_samples=2048,
       identity_indices=identity_indices.get("observation.state"),
       refresh_invalid_stats=False,
   )
3. 构造 action normalizer: 同上 (key="action")
4. 返回 (state_normalizer, action_normalizer)
```

## `_build_from_stats` 优先路径

```python
# normalization.py:215-233
stats = dataset.meta.stats  # LeRobot 内部加载的 stats
feature_stats = stats.get("observation.state")
min_vals = feature_stats.get("min")
max_vals = feature_stats.get("max")
return ActionStateNormalizer(min_vals=min_vals, max_vals=max_vals, identity_indices=...)
```

## `_scan_vector_stats` 回退路径

```python
# normalization.py:254-263（被 ensure_vector_stats 调用）
for idx in range(len(dataset)):
    row = dataset.hf_dataset[idx]
    for key in ["observation.state", "action"]:
        accumulator.update(row[key])
return {key: accumulator.finalize() for key, accumulator in accumulators.items()}
```

累加器 `_VectorStatsAccumulator`（L276-310）维护 `min / max / sum / sum_sq / count`，最后算 `mean = sum/count`、`std = sqrt(max(sum_sq/count - mean^2, 0))`。

## 关键约束

- **`max_samples=2048`**：dataset < 2048 帧时按实际帧数算
- **`ensure_vector_stats` 会写盘**：如果 `meta/stats.json` 缺 key 或维度不对，会全扫一次并 `write_stats(merged_stats, dataset.root)` 落盘
- **`refresh_invalid_stats=False`**：外层 `ensure_vector_stats` 已经处理过，build_normalizer_from_lerobot 不再重复
- **两次调用此函数（训练 + bundle export）结果一致**：都是同一个 dataset
- 与 [[ActionStateNormalizer min-max 归一化]] / [[export_deploy_bundle 打包 deploy bundle]] 配套
