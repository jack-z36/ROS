---
tags:
  - 附件
---

# Pi05LeRobotDataset (训练数据集)

> [!abstract]
> `pi05/train/data/dataset.py` 实现的 LeRobot v3 dataset 包装：从 `meta/info.json` 读 features schema → 构造 state/action normalizer → __getitem__ 返回 dict[image_*, state, action_chunk, task]。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `Pi05LeRobotDataset` |
| 位置 | `pi05_test/pi05/train/src/pi05/train/data/dataset.py` |
| 构造 | `build_train_dataloader` (builders.py:17-51) |
| 现实含义 | "从 LeRobot v3 落盘数据中读 30 步 action chunk + 3 张图像 + 26D state + 任务 prompt" |

## 构造参数

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `dataset_path` | `Path` | LeRobot v3 数据集根目录 |
| `chunk_size` | `int` | 30（一个样本要预测未来 30 步动作） |
| `use_color_jitter` | `bool` | 训练时图像增强 |
| `image_size` | `int` | 224 |
| `state_dim` | `int` | 26 |
| `action_dim` | `int` | 14 |
| `cameras` | `tuple[str, ...]` | `("top", "left_wrist", "right_wrist")` |
| `state_normalizer` | `Normalizer` | 26D state 的 (mean, std) 或 q99.5 scale |
| `action_normalizer` | `Normalizer` | 14D action 的 (mean, std) 或 q99.5 scale |

注意 `build_train_dataloader` 会构造**两次**：
- 第一次：只为了跑 `build_state_action_normalizers(bootstrap_dataset.dataset)` 算 normalizer
- 第二次：把 normalizer 注入 dataset，正式使用

## `__getitem__(idx)` 返回

```python
{
    "image_top":         torch.float32[3, 224, 224],
    "image_left_wrist":  torch.float32[3, 224, 224],
    "image_right_wrist": torch.float32[3, 224, 224],
    "state":             torch.float32[26],         # normalized
    "action_chunk":      torch.float32[30, 14],     # normalized
    "task":              str,                        # task prompt from annotation
}
```

## 数据流位置

```text
LeRobot v3 parquet
    ↓
Pi05LeRobotDataset.__getitem__
    ↓
build_state_action_normalizers  →  (state_norm, action_norm)
    ↓
build_train_dataloader  →  DataLoader(batch_size, shuffle=True, ...)
    ↓
to_lerobot_pi05_batch  (engine/batches.py:8-19)
    ↓  ←  key 重命名: state→observation.state, action_chunk→action, image_xxx→observation.images.xxx
make_pi05_pre_post_processors (LeRobot)
    ↓
PI05Policy.forward(batch)
```

## 关键约束

- **`dataset_path` 必须存在**：`build_train_dataloader` 用 `.exists()` 校验，缺失抛 FileNotFoundError
- **state/action_dim 必须 = 26/14**：与 [[STATE_DIM 26D state schema]] / [[ACTION_DIM 14D action schema]] 锁死
- **`use_color_jitter` 仅在 train 模式打开**：eval 时不打开
- 与 [[build_train_dataloader 训练 dataloader]]、[[to_lerobot_pi05_batch 批处理适配器]] 上下游
