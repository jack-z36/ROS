---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# RuntimeMetrics

> [!abstract]
> 部署运行时的轻量监控状态，用于观察推理、chunk、fallback 和发布行为。

| 属性 | 值 |
| --- | --- |
| 源码名 | `RuntimeMetrics` |
| 生产者 | N03 SharedBuffer 的 record 方法 |
| 消费者 | N08 metrics publisher |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:105-153`; `pi05_vla_deploy_node.py:213-218` |

## 字段

包含 inference count/error/request、chunk result/discard/switch、fallback、published/held/rejected action、latency EMA 和 last error。

