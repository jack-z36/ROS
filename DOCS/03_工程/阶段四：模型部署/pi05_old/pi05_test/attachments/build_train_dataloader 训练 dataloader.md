---
tags:
  - 附件
---

# build_train_dataloader (训练 dataloader)

> [!abstract]
> 从 `DataConfig.dataset_path` 加载 LeRobot v3 数据集，构造两次 `Pi05LeRobotDataset`（第一次算 normalizer，第二次带 normalizer），最后包成 `torch.utils.data.DataLoader`。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `build_train_dataloader` |
| 所在文件 | `pi05_test/pi05/train/src/pi05/train/engine/builders.py:17-51` |
| 调用位置 | `trainer.py:85` |
| 现实含义 | 把"磁盘上的 LeRobot v3 数据集" 变成"训练循环能 iterate 的 batch 流" |

## 流程

```text
1. 解析 dataset_path（不存在 → FileNotFoundError）
2. 第一次构造 Pi05LeRobotDataset（无 normalizer）用于 bootstrap
3. build_state_action_normalizers(bootstrap_dataset.dataset)  →  (state_normalizer, action_normalizer)
4. 第二次构造 Pi05LeRobotDataset（带 normalizer）
5. 包成 DataLoader:
     - batch_size = training_cfg.batch_size
     - shuffle = True
     - num_workers = data_cfg.num_workers
     - pin_memory = torch.cuda.is_available()
     - drop_last = False
```

## 输出

```python
DataLoader(
    dataset=Pi05LeRobotDataset(...),  # 包含 state/action normalizer
    batch_size=...,
    shuffle=True,
    num_workers=...,
    pin_memory=...,
    drop_last=False,
)
```

## 关键约束

- **`pin_memory` 仅在 CUDA 下开启**：CPU 训练不 pin
- **`drop_last=False`**：不舍弃最后不完整的 batch（小数据集避免浪费）
- **`shuffle=True`**：标准训练 shuffle，validation 不走这个函数
- **两次构造 dataset**：先 bootstrap normalizer，再带 normalizer 训练（避免泄漏）
- 与 [[Pi05LoraTrainer LoRA 训练器]]、[[Pi05LeRobotDataset 数据集类]] 配套
