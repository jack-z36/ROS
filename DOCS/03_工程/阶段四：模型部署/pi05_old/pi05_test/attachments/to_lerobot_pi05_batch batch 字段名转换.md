---
tags:
  - 附件
---

# to_lerobot_pi05_batch (batch 字段名转换)

> [!abstract]
> 一个 19 行的 batch 适配器：把本地 dataset 产出的 `{state, action_chunk, task, image_*, ...}` dict 映射成 LeRobot PI0.5 preprocessor 期待的 `{observation.state, action, task, observation.images.*, ...}` 命名。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `to_lerobot_pi05_batch` |
| 所在文件 | `pi05_test/pi05/train/src/pi05/train/engine/batches.py:8-19` |
| 调用位置 | `trainer.py:182`（每个 batch） |
| 现实含义 | 解耦"我们自己 dataset 的内部命名" 和"开源 LeRobot PI0.5 期望的命名" |

## 字段映射

| 源 (本仓库) | 目标 (LeRobot PI0.5) |
| --- | --- |
| `state` | `observation.state` |
| `action_chunk` | `action` |
| `task` | `task` |
| `image_top` | `observation.images.top` |
| `image_left_wrist` | `observation.images.left_wrist` |
| `image_right_wrist` | `observation.images.right_wrist` |
| `image_left_tactile` | `observation.images.left_tactile`（如果启用） |
| `image_right_tactile` | `observation.images.right_tactile`（如果启用） |

转换规则：源 key 以 `image_` 开头 → 去掉前缀 + 加 `observation.images.` 前缀。

## 完整实现

```python
def to_lerobot_pi05_batch(batch: dict[str, Any]) -> dict[str, Any]:
    model_batch = {
        "observation.state": batch["state"],
        "action": batch["action_chunk"],
        "task": list(batch["task"]),
    }
    for key, value in batch.items():
        if key.startswith("image_"):
            camera = key.removeprefix("image_")
            model_batch[f"observation.images.{camera}"] = value
    return model_batch
```

## 在数据流中的位置

```text
dataloader  →  batch = {state, action_chunk, task, image_top, image_left_wrist, image_right_wrist, ...}
    ↓
to_lerobot_pi05_batch(batch)
    ↓
model_batch = {observation.state, action, task, observation.images.*, ...}
    ↓
preprocessor(model_batch)  →  真正送进 Pi0.5 的 tensors
    ↓
model(processed_batch)  →  loss, loss_dict
```

## 关键约束

- **`action` (目标) ≠ `action_chunk`**：dataset 输出叫 `action_chunk`（强调是整段），转换后变 `action`（LeRobot 接口）
- **`task` 强制转 list**：有些 processor 期望 list 而非 str
- **没有 fallback**：缺失 `state` / `action_chunk` / `task` → KeyError（dataset 出 bug 了）
- 与 [[make_pi05_pre_post_processors LeRobot PI0.5 preprocessor]]、[[build_train_dataloader 训练 dataloader]] 上下游
