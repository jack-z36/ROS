---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T06
---

# T06 导出部署 bundle

> [!abstract]
> 将 final adapter、训练配置、normalizers 和 manifest 复制/写入部署目录。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据读写类 |
| 源码实现 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:25-55` |
| 输入数据 | final_adapter、ExperimentConfig |
| 输出数据 | bundle payload |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 33-40 | 校验 adapter 目录，准备输出目录，复制 adapter |
| 42-46 | 从训练数据集构建 state/action normalizers |
| 48-54 | 写 config、tactile preprocess、normalizers 和 manifest |

