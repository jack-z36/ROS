---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# bundle payload

> [!abstract]
> 部署 bundle 中写出的最小运行时 payload：adapter、config、normalizers、manifest 和可选 tactile preprocess。

| 属性 | 值 |
| --- | --- |
| 生产者 | T06 导出部署 bundle |
| 消费者 | T07 写 manifest/normalizers/config |
| 源码位置 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:38-54` |

## 约束

如果使用 tactile camera，导出要求数据集 `meta/tactile_preprocess.json` 存在。

