---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# deploy bundle

> [!abstract]
> 部署端加载模型所需目录，连接训练产物和 ROS2 runtime。

| 属性 | 值 |
| --- | --- |
| 组成 | `adapter/`、`manifest.json`、`normalizers.json`、`experiment_config.yaml`、可选 `tactile_preprocess.json` |
| 生产者 | T07 写 manifest/normalizers/config |
| 消费者 | T08 `load_policy_runtime()` |
| 源码位置 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:107-184`; `policy_loader.py:167-173` |

## 约束

部署端会校验 `manifest.json`、`normalizers.json`、`experiment_config.yaml` 三个必需文件。

