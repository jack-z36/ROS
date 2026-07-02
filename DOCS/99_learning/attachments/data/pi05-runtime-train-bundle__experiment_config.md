---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# ExperimentConfig

> [!abstract]
> 训练侧配置根对象，也是 bundle 导出和部署重建模型的契约。

| 属性 | 值 |
| --- | --- |
| 源码名 | `ExperimentConfig` |
| 生产者 | T01 训练 CLI 加载配置 |
| 消费者 | T02/T03/T06/T08 |
| 源码位置 | `pi05_test/pi05/common/src/pi05/common/config/schema.py:198`; `train.py:18-24` |

## 生命周期

CLI 读取 YAML 得到 `ExperimentConfig`，trainer 用它构建训练，bundle 导出写回 `experiment_config.yaml`，部署端再读它并覆盖 runtime device/dtype/chunk/action/state 设置。

