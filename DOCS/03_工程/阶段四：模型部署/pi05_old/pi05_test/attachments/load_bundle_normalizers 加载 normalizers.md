---
tags:
  - 附件
---

# load_bundle_normalizers (加载 normalizers)

> [!abstract]
> 部署节点启动时调它读 `normalizers.json`，构造一对 `ActionStateNormalizer` (state + action) 实例，用于推理前的"反归一化"（把模型输出从 [-1, 1] 还原到物理单位）。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `load_bundle_normalizers` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:65-83` |
| 调用方 | 部署侧（`InferenceWorker` 之前 / `postprocessor` 之内） |
| 现实含义 | "训练时用的 min/max 是什么？推理时把模型输出乘回去" |

## 函数签名

```python
def load_bundle_normalizers(
    bundle_dir: str | Path,
) -> tuple[ActionStateNormalizer, ActionStateNormalizer]:
    ...
```

## 行为

```python
bundle_dir = Path(bundle_dir).expanduser().resolve()
normalizer_path = bundle_dir / NORMALIZERS_NAME  # "normalizers.json"
with normalizer_path.open("r", encoding="utf-8") as f:
    payload = json.load(f)

state_payload = payload["state"]
action_payload = payload["action"]
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
return state_normalizer, action_normalizer
```

## 在数据流中的位置

```text
normalizers.json
    ↓
load_bundle_normalizers(bundle_dir)  →  (state_norm, action_norm)
    ↓
ActionStateNormalizer.normalize(state)  →  [-1, 1]  (训练/推理前)
ActionStateNormalizer.unnormalize(action)  →  物理单位  (推理后)
    ↓
[14 DOF 关节目标位置] → /command/.../joint_target
```

## 关键约束

- **部署侧要保证 normalizer 加载顺序**：必须先 state 再 action（tuple 顺序固定）
- **`identity_indices` 可选**：某些维度（如归一化后保持原值的 marker）用 identity 而非 min-max
- **dtype 一致**：min/max 是 Python list，构造时 `torch.as_tensor(..., dtype=float32)`
- **shape 校验**：`_as_vector` 内部检查 min / max 长度一致
- 与 [[export_deploy_bundle 打包 deploy bundle]]、[[normalizers.json 归一化 JSON]]、[[ActionStateNormalizer min-max 归一化]] 配套
