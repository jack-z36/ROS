---
tags:
  - 附件
---

# ActionStateNormalizer (min-max 归一化)

> [!abstract]
> 把 state / action 向量按"训练集 min/max"线性缩放到 [-1, 1] 的归一化器，训练和推理对称使用（`normalize` 和 `unnormalize`）。支持 `identity_indices` 让某些维度跳过归一化。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `ActionStateNormalizer` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/data/normalization.py:22-127` |
| 实例化 | `build_state_action_normalizers(dataset)` → 2 个实例 |
| 现实含义 | "把关节角 / EE 位姿 [0, 1.5] 缩到 [-1, 1] 给模型；推理时把模型输出从 [-1, 1] 还原回 [0, 1.5]" |

## 字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `min_vals` | `torch.float32[vector_dim]` | 训练集 min |
| `max_vals` | `torch.float32[vector_dim]` | 训练集 max |
| `vector_dim` | `int` | 向量维度（state=26 / action=14） |
| `range_vals` | `torch.float32[vector_dim]` | `max - min` |
| `non_zero_mask` | `torch.bool[vector_dim]` | `range != 0`（避免除零） |
| `identity_mask` | `torch.bool[vector_dim]` | True 的维度跳过 normalize |

## 公式

```text
y = 2 * (x - min) / (max - min) - 1     for non_zero_mask = True
y = 0                                    for non_zero_mask = False (degenerate dim)
y = x                                    for identity_mask = True (skip normalize)

x = (y + 1) * 0.5 * (max - min) + min   for non_zero_mask = True
x = min                                  for non_zero_mask = False
x = y                                    for identity_mask = True
```

## 关键方法

| 方法 | 用途 | 调用方 |
| --- | --- | --- |
| `__init__(min_vals, max_vals, identity_indices)` | 构造 | [[build_state_action_normalizers 构造 normalizer]] |
| `normalize(data)` | x → y（→ [-1, 1]） | 训练时 `Pi05LeRobotDataset.__getitem__` |
| `unnormalize(norm_data)` | y → x（→ 物理单位） | 部署时 `InferenceWorker` 之后 |
| `__call__(data)` | 委托 `normalize` | 训练 dataloader |

## `identity_indices` 用法

```python
# 例：hand 维度是 [0, 1] 张合，永远不需要归一化
normalizer = ActionStateNormalizer(
    min_vals=[0]*14,
    max_vals=[1.5]*14,
    identity_indices=[12, 13],  # hand 维度
)
normalize(np.array([0.5, 0.5, ..., 0.7, 0.8]))[12] == 0.7  # 跳过归一化
```

## 关键约束

- **dtype 锁死 float32**：所有 tensor 都是 float32
- **`min_vals` 和 `max_vals` 长度必须一致**：`__init__` 内 `_as_vector(expected_dim=...)` 校验
- **归一化永远到 [-1, 1]**，不是 [0, 1]（Pi0.5 模型期望的输入范围）
- **degenerate 维度（max==min）→ 0**：避免除零
- 与 [[build_state_action_normalizers 构造 normalizer]] / [[normalizers.json 归一化 JSON]] 配套
