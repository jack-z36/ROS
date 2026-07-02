---
tags:
  - 附件
---

# experiment_config.yaml训练配置镜像

> [!abstract]
> 一句话说明：这是原始训练配置 `config.raw` 的 YAML 镜像，部署侧用它重建 `ExperimentConfig` 后再覆盖 runtime 相关字段。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `EXPERIMENT_CONFIG_NAME`, `dict(config.raw)` |
| 参考系 | YAML 配置文件结构空间 |
| 相对原点 | bundle 根目录 |
| 物理锚点 | 无对应物理点，这是配置文件 |
| 阶段属性 | 最终 artifact |
| 是否最终输出 | 是 |
| 数据类型 | YAML file |
| 数据结构 | 多层 YAML 配置，来源于训练配置原始 dict |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:20,48,182-184` |
| 现实含义 | 让部署端复用训练时模型构建参数 |

## 关键澄清

### 1. 它在哪个参考系下？
配置字段命名空间下。

### 2. 它相对哪个原点？
文件路径相对 [[deploy bundle输出目录]]。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是配置文件。

### 4. 它是不是最终输出？
是。

### 5. 它不是什么？
它不是部署 YAML；部署端会在加载后用 `DeployConfig` 覆盖 device/dtype/chunk/action_dim 等运行时字段。

## 对应源码

```python
_write_yaml(output_dir / EXPERIMENT_CONFIG_NAME, dict(config.raw))

def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
```

## 一句话说清楚

> `experiment_config.yaml` 是训练配置的离线副本，帮助部署端重建同一套 Pi0.5 模型结构。

## 在数据流中的位置

- 上游：[[ExperimentConfig训练打包配置]]
- 下游：部署侧 `_load_bundle_experiment_config()`

