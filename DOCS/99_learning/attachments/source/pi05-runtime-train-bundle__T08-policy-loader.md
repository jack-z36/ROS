---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T08
---

# T08 部署端加载 policy runtime

> [!abstract]
> 校验 bundle，重建模型，加载 adapter 和 normalizers，返回可推理的 `Pi05PolicyRuntime`。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据读写类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py:110-155` |
| 输入数据 | deploy bundle |
| 输出数据 | Pi05PolicyRuntime |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 117-124 | 校验 bundle、读 manifest/config、构建 LoRA 模型并加载 adapter |
| 129-138 | 找到 policy，配置 chunk/device/dtype，并创建 preprocessor/normalizers |
| 141-155 | 返回 runtime 封装，包含 action_dim、image_names、compile 参数 |
| 63-78 | runtime 推理时构造 batch、调用 policy、反归一化 action chunk |

