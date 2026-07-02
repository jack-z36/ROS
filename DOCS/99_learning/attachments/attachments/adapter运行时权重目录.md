---
tags:
  - 附件
---

# adapter运行时权重目录

> [!abstract]
> 一句话说明：这是 bundle 内固定名为 `adapter/` 的 LoRA 权重目录，部署端会从这里加载 adapter 到基础模型上。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `adapter_target_dir`, `adapter_dir`, `manifest["artifacts"]["adapter_dir"]` |
| 参考系 | 文件系统路径空间 |
| 相对原点 | bundle 根目录 |
| 物理锚点 | 无对应物理点，这是模型参数目录 |
| 阶段属性 | 最终 artifact |
| 是否最终输出 | 是 |
| 数据类型 | `Path` directory |
| 数据结构 | 一个目录，通常包含 LoRA adapter 权重文件和 adapter 配置 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:39-40,86-91,132` |
| 现实含义 | 部署端加载训练后 LoRA 增量参数的位置 |

## 关键澄清

### 1. 它在哪个参考系下？
文件系统路径空间。

### 2. 它相对哪个原点？
固定相对 [[deploy bundle输出目录]]，路径名为 `adapter`。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是模型参数目录。

### 4. 它是不是最终输出？
是。

### 5. 它不是什么？
它不是基础模型完整权重；基础模型仍由配置中的 `pretrained_path` 指向。

## 对应源码

```python
adapter_target_dir = output_dir / "adapter"
shutil.copytree(adapter_dir, adapter_target_dir, dirs_exist_ok=overwrite)

def resolve_bundle_adapter_dir(bundle_dir: str | Path) -> Path:
    adapter_dir = bundle_dir / "adapter"
    if not adapter_dir.exists():
        raise FileNotFoundError(...)
    return adapter_dir
```

## 一句话说清楚

> `adapter/` 是 bundle 内部署端真正读取 LoRA adapter 参数的固定位置。

## 在数据流中的位置

- 上游：[[LoRA adapter源目录]]、[[deploy bundle输出目录]]
- 下游：`resolve_bundle_adapter_dir()`、部署侧 `_load_adapter()`

