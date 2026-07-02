---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T07
---

# T07 写 manifest/normalizers/config

> [!abstract]
> 定义 bundle manifest 和 normalizer JSON 的具体结构。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据定义类 |
| 源码实现 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:107-184` |
| 输入数据 | bundle payload |
| 输出数据 | deploy bundle |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 107-136 | manifest 记录 schema、project、model、observation、artifact 路径 |
| 139-152 | tactile camera 启用时复制 tactile preprocess metadata |
| 155-170 | normalizer JSON 写 state/action min/max/identity indices |
| 177-184 | JSON/YAML 均用 UTF-8 写入 |

