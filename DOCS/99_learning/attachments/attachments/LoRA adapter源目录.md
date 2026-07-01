---
tags:
  - 附件
---

# LoRA adapter源目录

> [!abstract]
> 一句话说明：这是训练阶段保存最终 LoRA adapter 的输入目录，打包时会被复制到 bundle 内固定的 `adapter/` 子目录。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `adapter_dir` |
| 参考系 | 文件系统路径空间 |
| 相对原点 | 调用方传入路径；代码会 `expanduser().resolve()` 为绝对路径 |
| 物理锚点 | 无对应物理点，这是文件系统目录 |
| 阶段属性 | 原始输入路径 |
| 是否最终输出 | 否；复制后的 [[adapter运行时权重目录]] 才是 bundle artifact |
| 数据类型 | `Path` |
| 数据结构 | 一个目录路径，通常包含 adapter 权重和配置文件 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:28,33-40` |
| 现实含义 | 训练完成后的 LoRA 权重来源 |

## 关键澄清

### 1. 它在哪个参考系下？
在文件系统路径命名空间下，不是机器人坐标系。

### 2. 它相对哪个原点？
原始值相对调用方工作目录或用户目录；进入函数后解析为绝对路径。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是文件系统目录。

### 4. 它是不是最终输出？
不是。它是源目录，最终输出是复制到 bundle 内的 [[adapter运行时权重目录]]。

### 5. 它不是什么？
它不是完整基础模型目录；它只承载 LoRA adapter 相关产物。

## 对应源码

```python
adapter_dir = adapter_dir.expanduser().resolve()
if not adapter_dir.exists():
    raise FileNotFoundError(f"Adapter directory does not exist: {adapter_dir}")
adapter_target_dir = output_dir / "adapter"
shutil.copytree(adapter_dir, adapter_target_dir, dirs_exist_ok=overwrite)
```

## 一句话说清楚

> `adapter_dir` 是训练产物源路径，打包器检查它存在后完整复制到 bundle 的 `adapter/`。

## 在数据流中的位置

- 上游：`export_final_adapter()` 或 `export_bundle.py --adapter-dir`
- 下游：[[adapter运行时权重目录]]

