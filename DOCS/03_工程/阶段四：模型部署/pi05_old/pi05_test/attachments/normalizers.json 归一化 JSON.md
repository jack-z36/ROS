---
tags:
  - 附件
---

# normalizers.json (归一化 JSON)

> [!abstract]
> 每个 deploy bundle 根目录的 `normalizers.json` 文件：state 和 action 两个向量的 min-max 归一化参数，部署侧加载后用于"反归一化"。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 文件名 | `normalizers.json`（常量 `NORMALIZERS_NAME`） |
| 生成位置 | `bundle.py:50-54`（`_write_json` + `_normalizer_payload`） |
| 加载位置 | `load_bundle_normalizers(bundle_dir)` |
| 现实含义 | "训练时把 state/action 缩到 [-1, 1] 用的 (min, max) 是什么？推理时把它乘回去" |

## 完整结构

```json
{
  "state": {
    "min": [0.0, 0.0, 0.0, ...],
    "max": [1.5, 1.5, 1.5, ...],
    "identity_indices": []
  },
  "action": {
    "min": [0.0, 0.0, 0.0, ...],
    "max": [1.2, 1.2, 1.2, ...],
    "identity_indices": []
  }
}
```

每个 state / action 都是 `vector_dim` 长度的 list（state=26，action=14）。

## 字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `min` | `list[float]` | 每个维度的训练集最小值 |
| `max` | `list[float]` | 每个维度的训练集最大值 |
| `identity_indices` | `list[int]` | 哪些维度用"恒等映射"（跳过 min-max），默认 `[]` |

## 写入算法

```python
# bundle.py:155-174
def _normalizer_payload(state_normalizer, action_normalizer):
    return {
        "state": _single_normalizer_payload(state_normalizer),
        "action": _single_normalizer_payload(action_normalizer),
    }

def _single_normalizer_payload(normalizer):
    return {
        "min": normalizer.min_vals.tolist(),       # 26 / 14 floats
        "max": normalizer.max_vals.tolist(),
        "identity_indices": _identity_indices(normalizer),
    }
```

`min_vals / max_vals` 来自 `ActionStateNormalizer.__init__` 的输入（在 `build_state_action_normalizers` 中从 LeRobot dataset 的 `meta.stats` 或 linspace 采样算出）。

## 加载算法

```python
# bundle.py:65-83
state_normalizer = ActionStateNormalizer(
    min_vals=state_payload["min"],
    max_vals=state_payload["max"],
    identity_indices=state_payload.get("identity_indices"),
)
action_normalizer = ActionStateNormalizer(
    min_vals=action_payload["min"],
    max_vals=action_payload["max"],
    identity_indices=action_payload.get("identity_indices"),
)
```

## 关键约束

- **长度严格匹配**：state=26、action=14（由 `vector_dim` 校验）
- **`min` / `max` 长度一致**：`ActionStateNormalizer._as_vector` 内部硬校验
- **`identity_indices` 可缺省**：`.get("identity_indices")` 返 None
- **序列化用 `tolist()`**：`min_vals` 是 torch.Tensor，转 Python list 写 JSON
- 与 [[load_bundle_normalizers 加载 normalizers]]、[[ActionStateNormalizer min-max 归一化]] 配套
