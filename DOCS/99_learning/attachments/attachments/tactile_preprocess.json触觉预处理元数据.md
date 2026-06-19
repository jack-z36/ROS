---
tags:
  - 附件
---

# tactile_preprocess.json触觉预处理元数据

> [!abstract]
> 一句话说明：这是 VTLA/触觉相机场景才会复制进 bundle 的预处理元数据，用于保持触觉输入尺度一致。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `TACTILE_PREPROCESS_NAME`, `tactile_preprocess_path`, `source`, `target` |
| 参考系 | 文件系统路径空间 / 触觉预处理参数空间 |
| 相对原点 | 源文件相对 dataset `meta/`；目标文件相对 bundle 根目录 |
| 物理锚点 | 物理对象状态；描述触觉传感输入的预处理规则，不是空间点 |
| 阶段属性 | 条件 artifact |
| 是否最终输出 | 部分是；只有触觉 camera 存在时输出 |
| 数据类型 | JSON file 或 `None` |
| 数据结构 | 触觉预处理元数据文件；具体字段由数据集生成流程决定 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:21,49,129,139-152` |
| 现实含义 | 触觉输入从原始传感尺度进入模型特征尺度所需的附加规则 |

## 关键澄清

### 1. 它在哪个参考系下？
它在触觉预处理参数空间和文件路径空间下，不是几何坐标系。

### 2. 它相对哪个原点？
源文件位于 `config.data.resolved_dataset_path/meta/`；复制后位于 bundle 根目录。

### 3. 它对应哪个物理点 / 物理对象？
它描述触觉传感对象状态的预处理规则，不对应单一物理点。

### 4. 它是不是最终输出？
只有 `config.data.cameras` 包含 `left_tactile` 或 `right_tactile` 时才是最终输出；否则返回 `None`。

### 5. 它不是什么？
它不是必有文件；普通纯视觉 bundle 不应该强行包含它。

## 对应源码

```python
tactile_cameras = {"left_tactile", "right_tactile"}
if not tactile_cameras.intersection(config.data.cameras):
    return None

source = config.data.resolved_dataset_path / "meta" / TACTILE_PREPROCESS_NAME
if not source.exists():
    raise FileNotFoundError(...)
target = output_dir / TACTILE_PREPROCESS_NAME
shutil.copy2(source, target)
return TACTILE_PREPROCESS_NAME
```

## 一句话说清楚

> `tactile_preprocess.json` 是触觉输入场景下必须随 bundle 携带的预处理尺度说明。

## 在数据流中的位置

- 上游：[[ExperimentConfig训练打包配置]] 和 dataset `meta/`
- 下游：[[manifest.json部署清单契约]] 的 `observation.tactile_preprocess_path`

