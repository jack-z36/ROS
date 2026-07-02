---
tags:
  - 附件
---

# resolve_bundle_adapter_dir (解析 adapter 路径)

> [!abstract]
> 部署侧拿 bundle 根目录解析出 `adapter/` 子目录的绝对路径；用于 `PeftModel.from_pretrained(adapter_dir)` 加载 LoRA。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `resolve_bundle_adapter_dir` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:86-91` |
| 调用方 | 部署侧加载 LoRA 时（`load_policy_runtime`） |
| 现实含义 | "bundle 根目录 → adapter 子目录的固定路径" |

## 函数签名

```python
def resolve_bundle_adapter_dir(bundle_dir: str | Path) -> Path:
    ...
```

## 行为

```python
bundle_dir = Path(bundle_dir).expanduser().resolve()
adapter_dir = bundle_dir / "adapter"
if not adapter_dir.exists():
    raise FileNotFoundError(f"Bundle adapter directory does not exist: {adapter_dir}")
return adapter_dir
```

## 在数据流中的位置

```text
load_bundle_manifest(bundle_dir)  →  manifest  (含 "artifacts": {"adapter_dir": "adapter"})
    ↓
resolve_bundle_adapter_dir(bundle_dir)  →  bundle_dir/adapter
    ↓
peft.PeftModel.from_pretrained(adapter_dir)  ←  LoRA 加载
```

## 关键约束

- **adapter 子目录必须存在**：缺失 → FileNotFoundError（与 manifest 描述不一致）
- **路径硬编码 "adapter"**：与 `export_deploy_bundle` 的 `output_dir / "adapter"` 约定一致
- 与 [[export_deploy_bundle 打包 deploy bundle]]、[[manifest.json bundle 契约]] 配套
