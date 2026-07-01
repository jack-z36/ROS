---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T01
---

# T01 训练 CLI 加载配置

> [!abstract]
> 解析 `--config`，读取 `ExperimentConfig`，然后调用 `train_from_config()`。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 外部接口类 |
| 源码实现 | `pi05_test/pi05/train/src/pi05/train/cli/train.py:18-24` |
| 输出数据 | ExperimentConfig |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 20 | 加载 YAML 为 typed experiment config |
| 21-24 | bootstrap 路径后延迟导入 trainer 并启动训练 |

