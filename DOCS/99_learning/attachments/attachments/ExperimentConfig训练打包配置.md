---
tags:
  - 附件
---

# ExperimentConfig训练打包配置

> [!abstract]
> 一句话说明：这是打包入口读取的训练配置对象，决定 bundle 的数据集来源、模型维度、相机列表和配置镜像内容。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `config` |
| 参考系 | 无 |
| 相对原点 | 不适用 |
| 物理锚点 | 无对应物理点，这是配置对象 |
| 阶段属性 | 原始输入配置 |
| 是否最终输出 | 否；其 `raw` 会写入配置镜像，部分字段会写入 manifest |
| 数据类型 | `ExperimentConfig` |
| 数据结构 | 多层配置对象，包含 logging/model/data 等子配置 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:25-55,107-136,139-152` |
| 现实含义 | 训练阶段的“说明书”，打包器按它找到数据集、写清模型与观测契约 |

## 关键澄清

### 1. 它在哪个参考系下？
它不是空间量，没有坐标参考系。

### 2. 它相对哪个原点？
不适用。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是配置对象；它描述模型、数据集和观测来源。

### 4. 它是不是最终输出？
对象本身不是最终输出；`dict(config.raw)` 会成为 [[experiment_config.yaml训练配置镜像]]，部分字段会成为 [[manifest.json部署清单契约]]。

### 5. 它不是什么？
它不是训练数据本身，也不是模型权重；它只是指向和描述这些资源。

## 对应源码

```python
def export_deploy_bundle(config: ExperimentConfig, *, adapter_dir: Path, output_dir: Path, overwrite: bool = False) -> Path:
    dataset = LeRobotDataset(
        repo_id=config.data.resolved_dataset_path.name,
        root=config.data.resolved_dataset_path,
    )
    _write_yaml(output_dir / EXPERIMENT_CONFIG_NAME, dict(config.raw))
```

## 一句话说清楚

> `config` 是 bundle 导出的配置根，负责告诉打包器从哪里读数据、怎么描述模型、最终写出哪些部署契约字段。

## 在数据流中的位置

- 上游：训练 CLI 或训练器加载 YAML 后构造
- 下游：[[LeRobotDataset统计来源]]、[[experiment_config.yaml训练配置镜像]]、[[manifest.json部署清单契约]]、[[tactile_preprocess.json触觉预处理元数据]]

