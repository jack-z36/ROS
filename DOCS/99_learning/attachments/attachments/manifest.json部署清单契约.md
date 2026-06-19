---
tags:
  - 附件
---

# manifest.json部署清单契约

> [!abstract]
> 一句话说明：这是 bundle 的清单文件，告诉部署端模型维度、观测相机、schema 版本和 artifact 相对路径。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `MANIFEST_NAME`, `_manifest_payload(...)`, `manifest_path`, `manifest` |
| 参考系 | JSON 文件结构空间 |
| 相对原点 | bundle 根目录 |
| 物理锚点 | 无对应物理点，这是配置/契约文件 |
| 阶段属性 | 最终 artifact |
| 是否最终输出 | 是 |
| 数据类型 | JSON file / `dict[str, Any]` |
| 数据结构 | 包含 `schema_version`, `created_at_utc`, `project`, `model`, `observation`, `artifacts` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:18,51-54,58-62,107-136` |
| 现实含义 | 部署端理解 bundle 内容和模型输入输出形状的说明书 |

## 关键澄清

### 1. 它在哪个参考系下？
文件结构和配置字段命名空间下。

### 2. 它相对哪个原点？
文件路径相对 [[deploy bundle输出目录]]；其中 `artifacts.*` 也是相对 bundle 根目录。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是部署契约文件。

### 4. 它是不是最终输出？
是。

### 5. 它不是什么？
它不是权重文件，也不保存 normalizer 的数值细节；normalizer 数值在 [[normalizers.json归一化契约]]。

## 对应源码

```python
def _manifest_payload(config: ExperimentConfig, *, tactile_preprocess_path: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "model": {
            "chunk_size": config.model.chunk_size,
            "state_dim": config.model.state_dim,
            "action_dim": config.model.action_dim,
        },
        "observation": {
            "cameras": list(config.data.cameras),
            "tactile_preprocess_path": tactile_preprocess_path,
        },
        "artifacts": {
            "adapter_dir": "adapter",
            "normalizers_path": NORMALIZERS_NAME,
            "experiment_config_path": EXPERIMENT_CONFIG_NAME,
        },
    }
```

## 一句话说清楚

> `manifest.json` 是部署端打开 bundle 时先读的目录说明书。

## 在数据流中的位置

- 上游：[[ExperimentConfig训练打包配置]]、[[tactile_preprocess.json触觉预处理元数据]]
- 下游：`load_bundle_manifest()`、部署侧 `_manifest_image_names()` 和 runtime action 维度设置

